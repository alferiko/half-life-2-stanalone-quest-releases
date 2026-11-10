# Local PC game cache / Кеш из ПК-установок

[English README](../README.md#optional-pc-cache-builder) · [Русская инструкция](../README.ru.md#вспомогательный-сборщик-кеша-на-пк)

## What the helper does

The Windows and Linux entry points use one Python implementation, so filtering, game layouts, DLC priority and integrity checks are identical. Python **3.10 or newer**, including its standard `lzma` module, is required. No pip dependencies, network downloads or administrator privileges are required.

Use the official **1.01 APK**, which contains `assets/hl2quest_steam_overlay.zip` and compressed resource blobs. Do not use the historical 0.989 overlay or an unrelated APK. The APK's SHA-256 is recorded in the build report. Obtain it from [the project's release](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.01), and compare it with the release's checksum file.

All source games and the APK are read-only. Close the games and pause Steam updates while building. The result is a new folder containing:

```text
game_cache/
  srceng/                  # copy this folder to /sdcard/
  cache-files.sha256        # hashes of all final files, relative to srceng/
  hl2q3vr-cache.json        # selected campaigns, language, APK hash, counts
```

The final folder appears only after successful verification. On failure, the `.NAME.building-*` folder is retained for inspection and is **not** a finished cache. Existing outputs are refused, even with an empty directory; use a new destination for each build. The helper never deletes an existing cache and has no force-overwrite switch.

## Windows

For prompts, double-click `BUILD_GAME_CACHE.bat`. Enter each Steam root, the APK path, a new output path and language. Enter `-` to skip a game. Detected Steam libraries are suggested, including libraries on other disks.

For an unattended build, run this in PowerShell from the repository directory (adjust paths):

```powershell
.\BUILD_GAME_CACHE.bat `
  -GameRoot 'C:\Program Files (x86)\Steam\steamapps\common\Half-Life 2' `
  -PortalRoot 'C:\Program Files (x86)\Steam\steamapps\common\Portal' `
  -Portal2Root 'D:\SteamLibrary\steamapps\common\Portal 2' `
  -ApkPath '.\hl2quest-vr.apk' `
  -OutputRoot '.\game_cache' `
  -Language russian
```

The batch entry point launches `tools/build_game_cache.ps1` with a process-local execution-policy bypass; it does not change the system policy. `-Plan` validates paths, VPK references and the overlay manifest and displays the proposed build without creating output. `-Interactive` prompts for unspecified paths. `-GameRoot`, `-PortalRoot` and `-Portal2Root` are individually optional; provide at least one for unattended use. PowerShell 5.1 is supported.

## Linux

For prompts: `bash BUILD_GAME_CACHE.sh`. For a command-line build:

```bash
bash BUILD_GAME_CACHE.sh \
  --hl2-root "$HOME/.local/share/Steam/steamapps/common/Half-Life 2" \
  --portal-root "$HOME/.local/share/Steam/steamapps/common/Portal" \
  --portal2-root "/mnt/games/SteamLibrary/steamapps/common/Portal 2" \
  --apk ./hl2quest-vr.apk \
  --output-root ./game_cache \
  --language russian
```

Use `--plan` for a read-only preflight, `--interactive` for prompts, or `--help` for all options. Only explicitly supplied game roots are selected in unattended mode. Native Linux paths and Steam installations are supported; in WSL use `/mnt/c/...`, `/mnt/d/...` and `/mnt/e/...` paths.

For Portal 2 alone:

```bash
bash BUILD_GAME_CACHE.sh --portal2-root "/path/to/Portal 2" \
  --apk ./hl2quest-vr.apk --output-root ./portal2_cache --language english
```

## Layout and language

| PC installation | Cache directories |
|---|---|
| Half-Life 2 | `hl2`, `platform`, installed `episodic`, `ep2`, `lostcoast` and their localization folders |
| Portal | `portal`, its own `portal_hl2`, `portal_platform` and their localization folders |
| Portal 2 | `portal2`, `portal2_dlc1`, `portal2_dlc2`, `update`, `portal2_platform` and their localization folders |

Portal's shared content is kept separate from Anniversary HL2. Portal 2 mounts **update → DLC2 → DLC1 → base**, with selected localized voice packs before their base packs. All installed localization folders and VPKs are retained. `--language` chooses the initial voice mounts; if that voice content is absent, the helper records an English fallback. Install another language in Steam before rebuilding if needed. The launcher can select among installed voice languages later.

`gameinfo.txt` files are generated in the format recognized by the 1.01 launcher. Its own managed shader/weapon/mod paths are added during preparation on the headset. The helper deliberately does not copy old `gameinfo.txt` files, mod mount blocks or “resources ready” / Steam verification markers from another cache.

## Integrity and exclusions

- Checks VPK header/tree structure and that every referenced numbered or embedded archive exists and is long enough. This is a completeness check, not Steam authenticity verification.
- Checks the APK overlay's uncompressed sizes and SHA-256 values, including XZ and shared asset references.
- Copies game files while hashing them and detects size/mtime changes during each copy. Verifies **every final output file** by SHA-256 before publication.
- Refuses overlapping source/output paths, existing output folders, destination case collisions, unsafe archive paths and symbolic links/junctions within selected content.
- Omits desktop binaries, `save`/`saves`, `custom`, Workshop, download folders, screenshots, logs, puzzles, replays, generated sound caches and known personal configuration files such as `config.cfg`, `autoexec.cfg` and `video.txt`.

Loose files inside normal game directories are treated as installed game content. The helper cannot tell an official file from a manually replaced map/material. If your PC game has such modifications, restore or verify it in Steam before creating a clean cache. The reference-cache comparison used during development does not turn arbitrary PC files into verified Steam depots.

After copying `srceng` to the headset, open the **1.01 launcher**. It automatically installs the matching versioned weapons, bodies, fonts and compatibility resources from its APK. Wait until preparation finishes, then launch the campaign normally. Do not bypass this step by starting SDLActivity directly. No Steam sign-in is needed for local content.

## Важное для русскоязычных пользователей

- Это вспомогательная офлайн-сборка из ваших ПК-игр; основной способ установки остаётся в лаунчере на шлеме.
- Укажите корни Steam-игр, а не папки `save` или `custom`. Для Portal 2 нужны также установленные `portal2_dlc1`, `portal2_dlc2` и `update` — сборщик переносит их автоматически, если они есть.
- Для русской озвучки сначала установите русский язык игры в Steam и передайте `-Language russian` / `--language russian`. Если озвучки нет, в отчёте будет указан английский вариант.
- Нужны Python 3.10+ и релизный APK 1.01. Старый `vr_game_resources` из 0.989 больше не используется.
- Выходная папка должна быть новой. Игры, сохранения на ПК, существующие кеши и эталон не изменяются.
- На шлем копируется только папка `srceng`. После копирования откройте лаунчер и дождитесь подготовки VR-ресурсов. Исходные сохранения шлема предварительно сохраните отдельно.

## Developer checks

```bash
python3 -B -m unittest discover -s tests -v
```

The test fixtures contain no commercial game data. They exercise independent Portal installs, DLC ordering, localization, unsafe paths, VPK truncation, excluded user data, compressed APK resources, existing-cache protection and the Linux wrapper.
