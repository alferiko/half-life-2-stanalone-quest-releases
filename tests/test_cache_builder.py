"""Safety and cache-layout regression checks; no commercial game fixtures."""
import contextlib
import hashlib
import importlib.util
import io
import json
import lzma
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools/build_game_cache.py"
spec = importlib.util.spec_from_file_location("cache_builder", SCRIPT)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def put(root, path, data=b"fixture"):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def apk_fixture(path, rows=None, corrupt=False):
    payload = b"verified VR data\n"
    sha = hashlib.sha256(payload).hexdigest()
    rows = rows or [("portal2/cfg/sourcevr_portal2.cfg", len(payload), sha, "xz/" + sha),
                    ("questvr/scripts/shared.txt", len(payload), sha, "xz/" + sha),
                    ("portal/cfg/sourcevr_portal.cfg", len(payload), sha, "xz/" + sha),
                    ("hl2/cfg/sourcevr_hl2.cfg", len(payload), sha, "xz/" + sha)]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("manifest.tsv", "".join("\t".join(map(str, row)) + "\n" for row in rows))
        if any(row[3].startswith("xz/") for row in rows):
            z.writestr("xz/" + sha, lzma.compress(b"wrong" if corrupt else payload))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("assets/hl2quest_steam_overlay.zip", stream.getvalue())
        z.writestr("assets/hl2quest_asset_blobs/" + sha + ".xz", lzma.compress(payload))
    return sha


def source_fixture(root, game="portal2"):
    put(root, game + "/gameinfo.txt", b"PC gameinfo")
    put(root, game + "/maps/start.bsp", b"VBSP-fixture")
    put(root, "platform/resource/ui.txt")
    if game == "portal":
        put(root, "hl2/maps/shared.bsp", b"VBSP-shared")
    return root


def vpk_fixture(root, inline=False):
    data = b"VBSP-demo"
    entry = struct.pack("<IHHIIH", 0, 0, 0x7FFF if inline else 0, 0, len(data), 0xFFFF)
    tree = b"bsp\0maps\0test\0" + entry + b"\0\0\0"
    path = put(root, "pak01_dir.vpk", struct.pack("<III", 0x55AA1234, 1, len(tree)) + tree + (data if inline else b""))
    if not inline:
        put(root, "pak01_000.vpk", data)
    return path


class CacheBuilderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hl2quest-cache-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = source_fixture(self.root / "Steam games/Portal 2")
        self.apk = self.root / "release.apk"
        apk_fixture(self.apk)
        self.output = self.root / "New cache"

    def args(self, *extra):
        return b.arguments(["--portal2-root", str(self.source), "--apk", str(self.apk),
                            "--output-root", str(self.output), *extra])

    def run_build(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return b.build(self.args(*extra))

    def test_standalone_portal2_and_private_data_exclusion(self):
        excluded = ["portal2/save/old.sav", "portal2/custom/mod/map.bsp", "portal2/bin/game.dll",
                    "portal2/maps/workshop/map.bsp", "portal2/cfg/config.cfg", "portal2/cfg/autoexec.cfg",
                    "portal2/sound/sound.cache", "portal2/puzzles/user.p2c", "portal2/crash.log",
                    "portal2/pak01.vpk.sound.cache", "portal2/modelsounds.cache",
                    "portal2/workshop_log.txt", "portal2/DownloadLists/map.lst",
                    "portal2/gamestate.txt", "portal2/portal2_gamestats.dat",
                    "platform/config/serverbrowser.vdf"]
        for path in excluded:
            put(self.source, path)
        for path in ("update/materials/new.vmt", "portal2_dlc1/maps/dlc.bsp", "portal2_dlc2/maps/dlc.bsp",
                     "portal2_russian/sound/voice.wav", "portal2_dlc1_russian/sound/voice.wav"):
            put(self.source, path)
        before = {p.relative_to(self.source).as_posix(): b.hash_file(p) for p in self.source.rglob("*") if p.is_file()}
        result = self.run_build("--language", "russian")
        cache = self.output / "srceng"
        self.assertEqual(result["campaigns"], ["portal2"])
        self.assertFalse((cache / "hl2").exists())
        self.assertFalse((cache / "portal").exists())
        self.assertTrue((cache / "questvr/scripts/shared.txt").is_file())
        self.assertTrue((cache / "portal2_platform/resource/ui.txt").is_file())
        for path in excluded:
            self.assertFalse((cache / path).exists(), path)
        self.assertEqual(result["audio_languages"]["portal2"], "russian")
        info = (cache / "portal2/gameinfo.txt").read_text()
        self.assertLess(info.index('"update/pak01.vpk"'), info.index('"portal2_dlc2/pak01.vpk"'))
        self.assertLess(info.index('"portal2_dlc2/pak01.vpk"'), info.index('"portal2_dlc1/pak01.vpk"'))
        self.assertLess(info.index('"portal2_dlc1/pak01.vpk"'), info.index('"portal2/pak01.vpk"'))
        for relative, digest in before.items():
            self.assertEqual(b.hash_file(self.source / relative), digest)
        for line in (self.output / "cache-files.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            self.assertEqual(b.hash_file(cache / relative), digest)
        self.assertFalse(any(cache.glob(".steam-*")))

    def test_existing_cache_is_never_replaced(self):
        sentinel = put(self.output, "srceng/portal2/save/precious.sav")
        with self.assertRaisesRegex(b.CacheError, "already exists"):
            self.run_build()
        self.assertEqual(sentinel.read_bytes(), b"fixture")

    def test_overlay_source_case_collision_rejected_before_output(self):
        put(self.source, "portal2/CFG/personal.txt")
        with self.assertRaisesRegex(b.CacheError, "destination collision"):
            self.run_build()
        self.assertFalse(self.output.exists())

    def test_destination_file_directory_collision(self):
        with self.assertRaisesRegex(b.CacheError, "File/directory"):
            b.validate_destinations(["portal2/cfg", "portal2/cfg/vr.cfg"])

    def test_output_cannot_overlap_source(self):
        for output in (self.source / "generated", self.source.parent):
            with self.assertRaises(b.CacheError):
                b.safe_output(output, [self.source.resolve()], self.apk)

    def test_plan_creates_nothing(self):
        self.run_build("--plan")
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.output.parent.glob(".New cache.building-*")))

    def test_portal_shared_content_has_its_own_namespace(self):
        root = source_fixture(self.root / "Portal", "portal")
        files, games, _ = b.collect({"portal": root})
        self.assertEqual(games, ["portal"])
        self.assertIn("portal_hl2/maps/shared.bsp", files)
        self.assertIn("portal_platform/resource/ui.txt", files)
        self.assertNotIn("hl2/maps/shared.bsp", files)

    def test_vpk_missing_numbered_archive(self):
        path = vpk_fixture(self.root)
        self.assertEqual(b.validate_vpk(path), 1)
        (self.root / "pak01_000.vpk").unlink()
        with self.assertRaisesRegex(b.CacheError, "Missing/truncated"):
            b.validate_vpk(path)

    def test_vpk_inline_and_truncated_tree(self):
        path = vpk_fixture(self.root, inline=True)
        self.assertEqual(b.validate_vpk(path), 1)
        path.write_bytes(path.read_bytes()[:15])
        with self.assertRaisesRegex(b.CacheError, "Truncated"):
            b.validate_vpk(path)

    def test_unsafe_overlay_paths_rejected_before_output(self):
        for path in ("../escaped.txt", "/absolute.txt", "portal2/../escaped.txt", "portal2/C:/x", "portal2/NUL.txt"):
            apk_fixture(self.apk, [(path, 16, hashlib.sha256(b"verified VR data\n").hexdigest(), "xz/" + hashlib.sha256(b"verified VR data\n").hexdigest())])
            with self.assertRaises(b.CacheError):
                self.run_build()
            self.assertFalse(self.output.exists())

    def test_corrupt_overlay_does_not_publish_cache(self):
        apk_fixture(self.apk, corrupt=True)
        with self.assertRaisesRegex(b.CacheError, "checksum mismatch"):
            self.run_build()
        self.assertFalse(self.output.exists())
        self.assertEqual(len(list(self.output.parent.glob(".New cache.building-*"))), 1)

    def test_compressed_shared_asset_fallback(self):
        data = b"verified VR data\n"
        digest = hashlib.sha256(data).hexdigest()
        apk_fixture(self.apk, [("portal2/cfg/sourcevr_portal2.cfg", len(data), digest,
                                "asset/hl2quest_portal_runtime/files/cfg/sourcevr_portal2.cfg")])
        self.run_build()
        self.assertEqual((self.output / "srceng/portal2/cfg/sourcevr_portal2.cfg").read_bytes(), data)

    def test_missing_language_falls_back_to_english(self):
        result = self.run_build("--language", "german")
        self.assertEqual(result["audio_languages"], {"portal2": "english"})

    def test_linux_wrapper_and_paths_with_spaces(self):
        if sys.platform == "win32":
            self.skipTest("Run under Linux to exercise bash wrapper")
        result = subprocess.run(["bash", str(SCRIPT.parents[1] / "BUILD_GAME_CACHE.sh"),
                                 "--portal2-root", str(self.source), "--apk", str(self.apk),
                                 "--output-root", str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.output / "srceng/portal2/gameinfo.txt").exists())

    def test_source_symlink_is_rejected(self):
        outside = put(self.root, "outside/file.txt")
        try:
            (self.source / "portal2/link.txt").symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation unavailable on this platform")
        with self.assertRaisesRegex(b.CacheError, "Not a regular"):
            self.run_build()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
