#!/usr/bin/env python3
"""Build a fresh HL2Quest cache from owned PC games and a release APK.

Layout and gameinfo format follow SteamCacheLayout.java in release 1.01.
Only the APK's base Steam overlay is prepared here. The launcher installs its
versioned weapon/body/shader bundles on first open, just as for Steam downloads.
No network access, third-party Python packages, deletion or in-place updates.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import tempfile
import zipfile

RELEASE_ROOT = Path(__file__).resolve().parent.parent
ROOTS = {
    "hl2": ("hl2", "platform", "episodic", "ep2", "lostcoast"),
    "portal": ("hl2", "platform", "portal"),
    "portal2": ("platform", "portal2", "portal2_dlc1", "portal2_dlc2", "update"),
}
CAMPAIGNS = ("hl2", "episodic", "ep2", "lostcoast", "portal", "portal2")
EXCLUDED_DIRS = {"bin", "save", "saves", "custom", "workshop", "download", "downloads",
                 "screenshots", "logs", "puzzles", "replays", "cache", "downloadlists"}
EXCLUDED_FILES = {"config.cfg", "autoexec.cfg", "video.txt", "videoconfig.txt",
                  "videodefaults.txt", "voice_ban.dt", "gameinfo.txt", "sound.cache",
                  "steam_autocloud.vdf", "remotecache.vdf", "stats.txt", "gamestate.txt",
                  "modelsounds.cache", "workshop_log.txt", "console.txt",
                  "ingamedialogconfig.vdf", "serverbrowser.vdf"}
EXCLUDED_SUFFIXES = {".exe", ".dll", ".so", ".dylib", ".pdb", ".dmp", ".mdmp",
                     ".log", ".dem", ".sav", ".bak", ".tmp", ".dxvk-cache"}
CHUNK = 1024 * 1024


class CacheError(Exception):
    pass


def safe_relative(value: str) -> str:
    value = value.replace("\\", "/")
    parts = value.split("/")
    if any(not p or p in (".", "..") or p.endswith((" ", ".")) or
           re.search(r'[\x00-\x1f<>:"|?*]', p) or
           re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
           for p in parts):
        raise CacheError("Unsafe content path: " + value)
    return value


def is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(CHUNK), b""):
            digest.update(data)
    return digest.hexdigest()


def target_path(game: str, relative: str) -> str | None:
    relative = safe_relative(relative)
    parts = relative.split("/")
    root = parts[0]
    if not any(root == base or re.fullmatch(re.escape(base) + r"_[a-z]{2,24}", root)
               for base in ROOTS[game]):
        return None
    lowered = [p.lower() for p in parts]
    if any(p in EXCLUDED_DIRS or p.startswith(".") for p in lowered):
        return None
    name = lowered[-1]
    if (name in EXCLUDED_FILES or Path(name).suffix in EXCLUDED_SUFFIXES or
            name.endswith((".sound.cache", "_gamestats.dat"))):
        return None
    if name.startswith(("hl2quest-", "hl2q3vr-")) and name.endswith(".txt"):
        return None
    if game == "portal" and (root == "hl2" or root.startswith("hl2_") or
                              root == "platform" or root.startswith("platform_")):
        return "portal_" + relative
    if game == "portal2" and (root == "platform" or root.startswith("platform_")):
        return "portal2_" + relative
    return relative


def payload_exists(root: Path, game: str, pack: str) -> bool:
    folder = root / game
    return (any(p.stat().st_size > 0 for p in (folder / "maps").glob("*.bsp")) or
            ((folder / (pack + "_dir.vpk")).is_file() and
             (folder / (pack + "_000.vpk")).is_file()))


def resolve_source(value: str, game: str) -> Path:
    path = Path(os.path.expandvars(value.strip().strip('"'))).expanduser().resolve(strict=True)
    if path.name == game and (path / "gameinfo.txt").is_file():
        path = path.parent
    if not (path / game / "gameinfo.txt").is_file() or not (path / "platform").is_dir():
        raise CacheError(f"Not a {game} installation: {path}; expected {game}/gameinfo.txt and platform/")
    if game == "portal" and not (path / "hl2").is_dir():
        raise CacheError("Portal requires its own hl2 shared content")
    pack = {"hl2": "hl2_misc", "portal": "portal_pak", "portal2": "pak01"}[game]
    if not payload_exists(path, game, pack):
        raise CacheError(f"Missing game payload in {path / game}; verify the installation in Steam")
    if game == "portal" and not payload_exists(path, "hl2", "hl2_misc"):
        raise CacheError("Portal shared HL2 payload is incomplete")
    return path


def validate_vpk(path: Path) -> int:
    """Check VPK directory bounds and all referenced numbered/inline archives."""
    with path.open("rb") as stream:
        header = stream.read(12)
        if len(header) != 12:
            raise CacheError(f"Truncated VPK header: {path}")
        magic, version, size = struct.unpack("<III", header)
        if magic != 0x55AA1234 or version not in (1, 2) or size > 64 * 1024 * 1024:
            raise CacheError(f"Unsupported or corrupt VPK: {path}")
        header_size = 12 if version == 1 else 28
        if version == 2 and len(stream.read(16)) != 16:
            raise CacheError(f"Truncated VPK v2 header: {path}")
        tree = stream.read(size)
    if len(tree) != size:
        raise CacheError(f"Truncated VPK tree: {path}")
    offset = count = 0
    extents: dict[int, int] = {}

    def string() -> bytes:
        nonlocal offset
        end = tree.find(b"\0", offset)
        if end < 0:
            raise CacheError(f"Unterminated VPK tree: {path}")
        result = tree[offset:end]
        offset = end + 1
        return result

    while string():
        while string():
            while string():
                if offset + 18 > size:
                    raise CacheError(f"Truncated VPK entry: {path}")
                _, preload, index, start, length, end = struct.unpack_from("<IHHIIH", tree, offset)
                offset += 18 + preload
                if end != 0xFFFF or offset > size:
                    raise CacheError(f"Invalid VPK entry: {path}")
                if length:
                    extents[index] = max(extents.get(index, 0), start + length)
                count += 1
    if offset != size:
        raise CacheError(f"Unexpected VPK tree tail: {path}")
    prefix = path.name[:-8]  # remove _dir.vpk
    for index, required in extents.items():
        archive = path if index == 0x7FFF else path.with_name(f"{prefix}_{index:03}.vpk")
        needed = required + (header_size + size if index == 0x7FFF else 0)
        if not archive.is_file() or archive.stat().st_size < needed:
            raise CacheError(f"Missing/truncated VPK archive: {archive}; need at least {needed} bytes")
        if is_link(archive):
            raise CacheError(f"Linked VPK archive is not allowed: {archive}")
    return count


def collect(sources: dict[str, Path]) -> tuple[dict[str, Path], list[str], int]:
    files: dict[str, Path] = {}
    folded: set[str] = set()
    campaigns = []
    vpk_entries = 0
    for game, source in sources.items():
        available = [game]
        if game == "hl2":
            for child, pack in (("episodic", "ep1_pak"), ("ep2", "ep2_pak"), ("lostcoast", "lostcoast_pak")):
                if (source / child / "gameinfo.txt").is_file():
                    if not payload_exists(source, child, pack):
                        raise CacheError(f"Incomplete campaign: {source / child}")
                    available.append(child)
        campaigns.extend(available)
        for directory in sorted(source.iterdir()):
            if not any(directory.name == base or re.fullmatch(re.escape(base) + r"_[a-z]{2,24}", directory.name)
                       for base in ROOTS[game]):
                continue
            if not directory.is_dir():
                continue
            if is_link(directory):
                raise CacheError(f"Linked content directory is not allowed: {directory}")
            for parent, dirs, names in os.walk(directory, followlinks=False):
                dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED_DIRS and not d.startswith("."))
                for name in dirs:
                    if is_link(Path(parent) / name):
                        raise CacheError(f"Linked content directory is not allowed: {Path(parent) / name}")
                for name in sorted(names):
                    path = Path(parent) / name
                    target = target_path(game, path.relative_to(source).as_posix())
                    if target is None:
                        continue
                    if is_link(path) or not path.is_file():
                        raise CacheError(f"Not a regular source file: {path}")
                    if target.casefold() in folded:
                        raise CacheError(f"Case-insensitive destination collision: {target}")
                    folded.add(target.casefold())
                    files[target] = path
                    if name.lower().endswith("_dir.vpk"):
                        vpk_entries += validate_vpk(path)
    return dict(sorted(files.items())), [g for g in CAMPAIGNS if g in campaigns], vpk_entries


def content_dirs(game: str) -> list[str]:
    if game == "portal2":
        return ["update", "portal2_dlc2", "portal2_dlc1", "portal2"]
    return [game] + (["episodic"] if game == "ep2" else []) + ([] if game == "hl2" else ["portal_hl2" if game == "portal" else "hl2"])


def validate_destinations(paths):
    """Reject ambiguous casing, including parent folders across source and APK."""
    seen = {}
    files = set(paths)
    for path in files:
        parts = path.split("/")
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            previous = seen.setdefault(prefix.casefold(), prefix)
            if previous != prefix:
                raise CacheError(f"Case-insensitive destination collision: {previous} / {prefix}")
            if length < len(parts) and prefix in files:
                raise CacheError("File/directory destination collision: " + prefix)


def voice_prefix(directory: str) -> str:
    return "hl2" if "hl2" in directory else {"episodic": "ep1", "ep2": "ep2"}.get(directory, directory)


def audio_language(files: dict[str, Path], game: str, requested: str) -> str:
    if requested == "english":
        return requested
    if game == "portal2":
        if any(f"{d}_{requested}/pak01_dir.vpk" in files for d in content_dirs(game)):
            return requested
    elif f"{game}/{voice_prefix(game)}_sound_vo_{requested}_dir.vpk" in files:
        return requested
    if any(p.startswith(f"{game}_{requested}/sound/") for p in files):
        return requested
    return "english"


def gameinfo(game: str, language: str) -> str:
    def mount(path: str) -> str:
        return f'game "{path}"\n'
    paths = f'game+mod "{game}/custom/*"\n'
    if game.startswith("portal"):
        paths += mount("questvr/custom/*") + mount("questvr")
    for directory in content_dirs(game):
        if game == "portal2":
            if language != "english":
                paths += mount(f"{directory}_{language}/pak01.vpk") + mount(f"{directory}_{language}")
            paths += mount(f"{directory}/pak01.vpk")
        else:
            prefix = f"{directory}/{voice_prefix(directory)}"
            if language != "english":
                paths += mount(f"{directory}_{language}") + mount(f"{prefix}_sound_vo_{language}.vpk")
            paths += mount(f"{prefix}_sound_vo_english.vpk")
            packs = ("hl2_pak", "hl2_sound_misc", "hl2_textures", "hl2_misc") if "hl2" in directory else (voice_prefix(directory) + "_pak",)
            for pack in packs:
                paths += mount(f"{directory}/{pack}.vpk")
        paths += mount(directory)
    platform = game + "_platform" if game.startswith("portal") else "platform"
    paths += f'platform "{platform}/platform_misc.vpk"\nplatform "{platform}"\nmod+mod_write+default_write_path "|gameinfo_path|."\ngamebin "{game}/bin"\n'
    app = {"portal": 400, "portal2": 620}.get(game, 220)
    return f'"GameInfo"\n{{\ngame "{game}"\nsupportsvr 1\nFileSystem\n{{\nSteamAppId {app}\nSearchPaths\n{{\n' + paths + "}\n}\n}\n"


class Overlay:
    def __init__(self, apk: Path, campaigns: list[str]):
        self.stack = ExitStack()
        try:
            self.apk = self.stack.enter_context(zipfile.ZipFile(apk))
            if len(self.apk.namelist()) != len(set(self.apk.namelist())):
                raise CacheError("APK has duplicate ZIP entries")
            raw = self.apk.read("assets/hl2quest_steam_overlay.zip")
            self.zip = self.stack.enter_context(zipfile.ZipFile(io.BytesIO(raw)))
            if len(self.zip.namelist()) != len(set(self.zip.namelist())):
                raise CacheError("Overlay has duplicate ZIP entries")
            self.rows = []
            targets = set()
            contents = {}
            for line in self.zip.read("manifest.tsv").decode("utf-8").splitlines():
                fields = line.split("\t")
                if len(fields) != 4:
                    raise CacheError("Invalid APK overlay manifest")
                target, size, digest, origin = fields
                target, origin = safe_relative(target), safe_relative(origin)
                size = int(size)
                top = target.split("/")[0]
                if (top not in (*CAMPAIGNS, "questvr") or size < 0 or size > 512 * CHUNK or
                    not re.fullmatch(r"[a-f0-9]{64}", digest) or target.casefold() in targets or
                    not (origin in ("blob/" + digest, "xz/" + digest) or origin.startswith("asset/hl2quest_"))):
                    raise CacheError("Invalid APK overlay content: " + target)
                if origin in contents and contents[origin] != (size, digest):
                    raise CacheError("Conflicting APK overlay origin: " + origin)
                contents[origin] = (size, digest)
                targets.add(target.casefold())
                if top in campaigns or (top == "questvr" and any(g.startswith("portal") for g in campaigns)):
                    self.rows.append((target, size, digest, origin))
            if not self.rows:
                raise CacheError("No selected campaign resources in APK")
            for name in self.zip.namelist():
                if name != "manifest.tsv" and name not in contents:
                    raise CacheError("Unexpected overlay archive entry: " + name)
            for _, _, digest, origin in self.rows:
                if origin.startswith("asset/"):
                    if "assets/" + origin[6:] not in self.apk.namelist() and "assets/hl2quest_asset_blobs/" + digest + ".xz" not in self.apk.namelist():
                        raise CacheError("Missing compressed APK resource: " + origin)
                elif origin not in self.zip.namelist():
                    raise CacheError("Missing overlay resource: " + origin)
        except BaseException:
            self.stack.close()
            raise

    def close(self):
        self.stack.close()

    def install(self, destination: Path) -> dict[str, str]:
        groups = defaultdict(list)
        for target, size, digest, origin in self.rows:
            groups[(origin, size, digest)].append(target)
        hashes = {}
        for (origin, size, digest), targets in groups.items():
            with ExitStack() as stack:
                compressed = False
                if origin.startswith("asset/"):
                    name = "assets/" + origin[6:]
                    if name not in self.apk.namelist():
                        name = "assets/hl2quest_asset_blobs/" + digest + ".xz"
                        compressed = True
                    stream = stack.enter_context(self.apk.open(name))
                else:
                    stream = stack.enter_context(self.zip.open(origin))
                    compressed = origin.startswith("xz/")
                if compressed:
                    stream = stack.enter_context(lzma.LZMAFile(stream))
                path = destination / targets[0]
                path.parent.mkdir(parents=True, exist_ok=True)
                actual, count = hashlib.sha256(), 0
                with path.open("wb") as out:
                    for block in iter(lambda: stream.read(CHUNK), b""):
                        count += len(block)
                        if count > size:
                            raise CacheError("Oversized APK resource: " + origin)
                        actual.update(block)
                        out.write(block)
                if count != size or actual.hexdigest() != digest:
                    raise CacheError("APK resource checksum mismatch: " + origin)
            hashes[targets[0]] = digest
            for target in targets[1:]:
                other = destination / target
                other.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, other)
                hashes[target] = digest
        return hashes


def safe_output(output: Path, sources: list[Path], apk: Path) -> Path:
    output = output.expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise CacheError(f"Output already exists; choose a NEW directory. Nothing was deleted: {output}")
    resolved = output.resolve()
    # Do not build through symlinks/junctions, including an existing parent alias.
    if resolved != output:
        raise CacheError("Output contains a path alias: " + str(output))
    for source in sources + [apk.resolve()]:
        if resolved == source or resolved in source.parents or source in resolved.parents:
            raise CacheError("Output overlaps a game installation or APK: " + str(output))
    return resolved


def discover() -> dict[str, str]:
    steam_roots = [Path.home() / ".local/share/Steam", Path.home() / ".steam/steam"]
    if os.name == "nt":
        steam_roots.append(Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam")
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_roots.insert(0, Path(winreg.QueryValueEx(key, "SteamPath")[0]))
        except OSError:
            pass
    libraries = list(steam_roots)
    for root in steam_roots:
        config = root / "steamapps/libraryfolders.vdf"
        if config.is_file():
            text = config.read_text(encoding="utf-8", errors="replace")
            libraries.extend(Path(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"\n]+)"', text))
    found = {}
    for game, name in (("hl2", "Half-Life 2"), ("portal", "Portal"), ("portal2", "Portal 2")):
        for library in libraries:
            root = library / "steamapps/common" / name
            if (root / game / "gameinfo.txt").is_file():
                found[game] = str(root)
                break
    return found


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hl2-root", "--game-root", dest="hl2_root")
    parser.add_argument("--portal-root")
    parser.add_argument("--portal2-root")
    parser.add_argument("--apk", type=Path, help="Official release APK containing its matching VR overlay")
    parser.add_argument("--output-root", type=Path, default=RELEASE_ROOT / "game_cache", help="NEW directory; srceng will be created inside")
    parser.add_argument("--language", default="english", help="Preferred installed voice language, e.g. russian; all installed languages are copied")
    parser.add_argument("--plan", action="store_true", help="Validate inputs and display the plan without creating output")
    parser.add_argument("--interactive", action="store_true", help="Prompt for game/APK paths; - skips a game")
    args = parser.parse_args(argv)
    if args.interactive or not any((args.hl2_root, args.portal_root, args.portal2_root)) and not args.plan:
        found = discover()
        for game in ROOTS:
            attr = game + "_root"
            if getattr(args, attr):
                continue
            default = found.get(game, "")
            answer = input(f"{game} Steam root [{default}] (- to skip): ").strip().strip('"')
            setattr(args, attr, None if answer == "-" else answer or default or None)
        if args.apk is None:
            default = RELEASE_ROOT / "hl2quest-vr.apk"
            answer = input(f"Release APK [{default}]: ").strip().strip('"')
            args.apk = Path(answer) if answer else default
        answer = input(f"NEW output folder [{args.output_root}]: ").strip().strip('"')
        if answer:
            args.output_root = Path(answer)
        args.language = input(f"Voice language [{args.language}]: ").strip() or args.language
    if not re.fullmatch("[a-z]{2,24}", args.language):
        parser.error("Language must be a Steam language name, e.g. english or russian")
    if args.apk is None:
        args.apk = RELEASE_ROOT / "hl2quest-vr.apk"
    return args


def build(args) -> dict:
    sources = {game: resolve_source(value, game) for game in ROOTS
               if (value := getattr(args, game + "_root"))}
    if not sources:
        raise CacheError("Select at least one game installation")
    apk = args.apk.expanduser().resolve(strict=True)
    output = safe_output(args.output_root, list(sources.values()), apk)
    print("Scanning game data and checking VPK archives...", flush=True)
    files, campaigns, entries = collect(sources)
    overlay = Overlay(apk, campaigns)
    pending = None
    try:
        validate_destinations(list(files) + [r[0] for r in overlay.rows] +
                              [g + "/gameinfo.txt" for g in campaigns])
        languages = {g: audio_language(files, g, args.language) for g in campaigns}
        size = sum(p.stat().st_size for p in files.values())
        plan = {"format": 3, "port": "HL2Quest", "layout_version": "1.01", "campaigns": campaigns,
                "sources": {g: str(p) for g, p in sources.items()}, "output": str(output / "srceng"),
                "source_file_count": len(files), "source_size_bytes": size, "vpk_entries_checked": entries,
                "overlay_file_count": len(overlay.rows), "overlay_size_bytes": sum(r[1] for r in overlay.rows),
                "audio_languages": languages, "apk": str(apk), "apk_sha256": hash_file(apk),
                "runtime_preparation": "Open the installed release launcher after copying; it prepares versioned VR resources. No Steam login is needed for this local cache."}
        print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        if args.plan:
            return plan
        output.parent.mkdir(parents=True, exist_ok=True)
        required = size + plan["overlay_size_bytes"] + 512 * CHUNK
        if shutil.disk_usage(output.parent).free < required:
            raise CacheError(f"Not enough free space; need at least {required} bytes")
        pending = Path(tempfile.mkdtemp(prefix="." + output.name + ".building-", dir=output.parent))
        cache = pending / "srceng"
        cache.mkdir()
        hashes = {}
        for index, (relative, source) in enumerate(files.items(), 1):
            before = source.stat()
            target = cache / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with source.open("rb") as src, target.open("xb") as dst:
                for data in iter(lambda: src.read(CHUNK), b""):
                    digest.update(data)
                    dst.write(data)
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or target.stat().st_size != before.st_size:
                raise CacheError("Source changed during copying; close the game/Steam update and retry: " + str(source))
            shutil.copystat(source, target)
            hashes[relative] = digest.hexdigest()
            if index % 250 == 0 or index == len(files):
                print(f"Copied {index}/{len(files)} files", flush=True)
        print("Restoring and checking matching VR overlay from the APK...", flush=True)
        hashes.update(overlay.install(cache))
        for game in campaigns:
            relative = game + "/gameinfo.txt"
            data = gameinfo(game, languages[game]).encode("utf-8")
            (cache / relative).write_bytes(data)
            hashes[relative] = hashlib.sha256(data).hexdigest()
        print("Verifying every output file by SHA-256...", flush=True)
        for index, (relative, digest) in enumerate(sorted(hashes.items()), 1):
            if hash_file(cache / relative) != digest:
                raise CacheError("Output checksum mismatch: " + relative)
            if index % 500 == 0:
                print(f"Verified {index}/{len(hashes)} files", flush=True)
        (pending / "cache-files.sha256").write_text("".join(f"{h}  {p}\n" for p, h in sorted(hashes.items())), encoding="utf-8", newline="\n")
        plan.update({"generated_utc": datetime.now(timezone.utc).isoformat(), "file_count": len(hashes),
                     "size_bytes": sum((cache / p).stat().st_size for p in hashes), "sha256_verified": True})
        (pending / "hl2q3vr-cache.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            raise CacheError("Output was created by another process; refusing to replace it")
        pending.rename(output)
        pending = None
        print(f"Cache ready: {output / 'srceng'}\nCopy to /sdcard/srceng, then open the launcher to finish VR resource preparation.", flush=True)
        return plan
    finally:
        overlay.close()
        if pending:
            print(f"Incomplete build retained for inspection: {pending}\nIt is NOT a finished cache.", file=sys.stderr)


def main(argv=None) -> int:
    try:
        build(arguments(argv))
        return 0
    except (CacheError, OSError, ValueError, KeyError, zipfile.BadZipFile, lzma.LZMAError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("Cancelled. Existing caches and source games were not replaced.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        sys.exit("Python 3.10 or newer is required (standard library only).")
    sys.exit(main())
