# Local PC game cache / Кеш из ПК-установок

[English README](../README.md#optional-pc-cache-builder) · [Русская инструкция](../README.ru.md#вспомогательный-сборщик-кеша-на-пк)

## Start with the complete archive

**Update for release 1.02:** the Full archive is still 1.01 and remains compatible. Replace its `hl2quest-vr.apk` with the [1.02 APK](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.02/hl2quest-vr.apk) to include the Steam DNS download fix when installing on the headset. The game/VR resources are unchanged and existing caches do not need rebuilding. [Release notes](../RELEASE_NOTES_1.02.md).

**[Download HL2Quest-Cache-Builder-1.01-Full.zip — 752 MB](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.01/HL2Quest-Cache-Builder-1.01-Full.zip)** · [SHA-256 checksum](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.01/HL2Quest-Cache-Builder-1.01-Full.zip.sha256) · [Пошагово на русском](#полный-архив-пошагово)

The Full archive includes the scripts, guide, and **official `hl2quest-vr.apk` with its bundled VR resources**. There is no separate resource pack to download or unpack. Python, Android Platform Tools and your Steam game installations are separate prerequisites. The small script-only ZIP and GitHub's source ZIP do not include the APK.

1. Extract the **whole** ZIP to a writable folder, then open `HL2Quest-Cache-Builder-1.01-Full`. Do not run the scripts inside the ZIP viewer or move the BAT file out of its folder.
2. Install Python **3.10+** if needed. On Windows, enable its launcher/PATH option and reopen your terminal; the wrapper checks `py`, `python`, then `python3`. No pip packages are needed.
3. Install/update your owned games in Steam, including the desired voice language. Current Anniversary files are supported; no Legacy downgrade is needed. Close the games and pause their updates during the build.
4. Run `BUILD_GAME_CACHE.bat` on Windows or `bash BUILD_GAME_CACHE.sh` on Linux. Confirm each detected game root with Enter, provide a different path, or enter `-` to skip that game. At **Release APK**, press Enter to use the included APK. Choose a **new, nonexistent** output folder (default: `game_cache` beside the scripts), then enter a Steam language name such as `english` or `russian`.
5. Wait for all checks to finish successfully. Close the game on the headset, back up existing data and copy only the generated `srceng` folder as shown in [Transfer to the headset](#transfer-to-the-headset).

Expected extracted layout:

```text
HL2Quest-Cache-Builder-1.01-Full/
  BUILD_GAME_CACHE.bat
  BUILD_GAME_CACHE.sh
  hl2quest-vr.apk           # includes the matching VR resources; keep it here
  MANIFEST.sha256
  README.txt
  tools/
  docs/
  tests/
```

Allow space for the downloaded ZIP, its extracted contents and a separate copy of the selected game data. The 752 MB download is the builder/APK bundle, **not** a finished game cache. Actual cache size depends on selected games and installed languages.

## What the helper does

The Windows and Linux entry points use one Python implementation, so filtering, game layouts, DLC priority and integrity checks are identical. Python **3.10 or newer**, including its standard `lzma` module, is required. No pip dependencies, network downloads or administrator privileges are required.

Use the official **1.01 APK**, which contains `assets/hl2quest_steam_overlay.zip` and compressed resource blobs. **It is already included in the Full archive.** Only users of the script-only/source ZIP need to obtain it separately from [release 1.01](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.01). Do not use the historical 0.989 overlay or an unrelated APK. The APK's SHA-256 is recorded in the build report; compare it with the release's checksum file.

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

For an unattended build, open PowerShell in the extracted `HL2Quest-Cache-Builder-1.01-Full` directory and run (adjust paths):

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

Open a terminal in the extracted `HL2Quest-Cache-Builder-1.01-Full` directory. For prompts: `bash BUILD_GAME_CACHE.sh`. For a command-line build:

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

## Transfer to the headset

Use [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) or your sideloading tool. Enable Developer Mode, connect the Quest by USB and accept USB debugging. Run these commands from the extracted Full folder with `adb` available in PATH (substitute the output path if you changed it):

```bash
adb devices
adb pull /sdcard/srceng ./HL2Quest-backup-before-cache
adb install -r hl2quest-vr.apk
adb push ./game_cache/srceng /sdcard/
```

Skip the backup command only for a first installation with no existing `/sdcard/srceng`. Use a new backup destination each time. With multiple devices, add `-s DEVICE_SERIAL` after `adb`.

Copy into `/sdcard/`, so the result is `/sdcard/srceng/hl2`, `/sdcard/srceng/portal`, etc. Do not create `/sdcard/srceng/srceng` or copy the enclosing `game_cache` folder. The push merges files without first deleting the existing tree; it can overwrite same-name game files and generated `gameinfo.txt`. Back up first. The builder excludes PC saves and personal configs, but existing headset mods/configs may still affect the game.

Open **Half-Life 2 VR Standalone** in Unknown Sources, grant storage access, select the campaign and let the 1.01 launcher prepare its VR resources. Local content does not require Steam sign-in. Keep `cache-files.sha256` and `hl2q3vr-cache.json` on the PC for troubleshooting; they do not need to be copied to the headset.

The included APK is the **regular GitHub edition**. If you use [SideQuest Edition 1.01](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.01-sidequest), keep that edition installed and skip the regular APK installation above: the same cache works with it. Open **HL2Quest (SideQuest)** to prepare resources. Its package is separate, so installing the included regular APK would add a second app rather than update the SideQuest app. Do not run both editions or their installers at the same time.

## Полный архив: пошагово

**Для релиза 1.02:** Full-архив по-прежнему содержит APK 1.01. После распаковки замените его новым [hl2quest-vr.apk 1.02](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.02/hl2quest-vr.apk) с исправлением Steam-загрузки. Скрипты и ресурсы совместимы; уже готовый кеш пересобирать не нужно. Для SideQuest устанавливайте отдельный [APK SideQuest 1.02](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.02-sidequest).

1. Скачайте **[HL2Quest-Cache-Builder-1.01-Full.zip — 752 МБ](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.01/HL2Quest-Cache-Builder-1.01-Full.zip)** и распакуйте **весь** архив. Откройте полученную папку `HL2Quest-Cache-Builder-1.01-Full`. Не запускайте BAT из окна архиватора и не переносите его отдельно от `tools`.
2. Установите **Python 3.10+**. В Windows включите Python Launcher/добавление в PATH при установке и заново откройте терминал. Пакеты pip не нужны. Python в Full-архив не входит.
3. APK **уже лежит рядом со скриптами** и содержит все нужные VR-ресурсы. Не распаковывайте его и не скачивайте старый `vr_game_resources`. Файлы самих игр берутся из ваших установок Steam; установите нужные игры и русский язык озвучки заранее. Закройте игры и приостановите обновления Steam на время сборки.
4. Запустите `BUILD_GAME_CACHE.bat` двойным щелчком. В Linux выполните `bash BUILD_GAME_CACHE.sh` из этой папки. В каждом запросе корня игры нажмите Enter для предложенного пути, введите свой путь или `-`, чтобы пропустить игру. Например:

   | Игра | Пример корневой папки |
   |---|---|
   | Half-Life 2, эпизоды и Lost Coast | `C:\Program Files (x86)\Steam\steamapps\common\Half-Life 2` |
   | Portal | `C:\Program Files (x86)\Steam\steamapps\common\Portal` |
   | Portal 2 | `D:\SteamLibrary\steamapps\common\Portal 2` |

5. В запросе **Release APK** нажмите Enter: будет выбран включённый `hl2quest-vr.apk`. В **NEW output folder** оставьте предложенный `game_cache` или задайте другую **ещё не существующую** папку. Не создавайте её заранее. В **Voice language** введите `russian` для русской озвучки либо `english`. Названия языков вводятся по-английски.
6. Дождитесь успешного окончания копирования и проверки SHA-256. Готовый кеш появится в `game_cache/srceng`; рядом будут отчёт `hl2q3vr-cache.json` и контрольные суммы `cache-files.sha256`. Папка `.game_cache.building-*` после ошибки — незавершённая сборка, её нельзя переносить как готовый кеш.
7. Закройте игру на шлеме. Сделайте резервную копию его `/sdcard/srceng`, затем выполните команды из раздела [Transfer to the headset](#transfer-to-the-headset): установка APK поверх текущего через `adb install -r` и перенос `adb push ./game_cache/srceng /sdcard/`. ADB устанавливается отдельно. При первом запуске подтвердите USB-отладку на шлеме. Для уже установленной **SideQuest Edition 1.01** пропустите установку обычного APK: кеш общий, а приложения имеют разные пакеты.
8. Откройте лаунчер 1.01 из «Неизвестных источников», разрешите доступ к файлам, выберите игру и дождитесь подготовки VR-ресурсов. Для этого локального кеша вход в Steam не нужен.

Для повторной сборки выберите новую папку, например `game_cache_2`. Исходные игры и их сохранения сборщик не меняет. На шлеме правильный путь — `/sdcard/srceng/<кампания>`, без дополнительного уровня `srceng`.

### Если сборка не запускается

| Сообщение / проблема | Что сделать |
|---|---|
| Python 3.10+ required | Установите Python 3.10+ с модулем `lzma`, заново откройте терминал и повторите запуск. |
| Не найден APK или папка `tools` | Распакуйте весь Full-архив, сохраните структуру; APK должен лежать рядом с `BUILD_GAME_CACHE.bat`. |
| Выходная папка уже существует | Укажите новый путь; даже пустая существующая папка не принимается. |
| Ошибка VPK / отсутствует часть архива | Проверьте целостность игры в Steam и завершите загрузки, затем повторите сборку в новую папку. |
| Нет русской озвучки | Установите русский язык соответствующей игры в Steam, дождитесь загрузки и пересоберите с `russian`. |
| Недостаточно места | Освободите место для отдельного кеша выбранных игр; объём 752 МБ относится только к Full-архиву. |
| Кампания не видна на шлеме | Проверьте путь `/sdcard/srceng/<кампания>` и доступ лаунчера к файлам. |

При ошибке сохраните текст сообщения и приложите `hl2q3vr-cache.json`, если он уже создан, к [сообщению о проблеме](https://github.com/alferiko/half-life-2-stanalone-quest-releases/issues). Для проблем запуска на шлеме используйте [инструкцию по логам](../README.ru.md#как-отправить-логи-и-сообщить-об-ошибке).

## Важное для русскоязычных пользователей

- Это вспомогательная офлайн-сборка из ваших ПК-игр; основной способ установки остаётся в лаунчере на шлеме.
- Укажите корни Steam-игр, а не папки `save` или `custom`. Для Portal 2 нужны также установленные `portal2_dlc1`, `portal2_dlc2` и `update` — сборщик переносит их автоматически, если они есть.
- Для русской озвучки сначала установите русский язык игры в Steam и передайте `-Language russian` / `--language russian`. Если озвучки нет, в отчёте будет указан английский вариант.
- Нужен Python 3.10+; релизный APK 1.01 со встроенными VR-ресурсами уже включён в Full-архив. Старый `vr_game_resources` из 0.989 больше не используется.
- Выходная папка должна быть новой. Игры, сохранения на ПК, существующие кеши и эталон не изменяются.
- На шлем копируется только папка `srceng`. После копирования откройте лаунчер и дождитесь подготовки VR-ресурсов. Исходные сохранения шлема предварительно сохраните отдельно.

## Developer checks

```bash
python3 -B -m unittest discover -s tests -v
```

The test fixtures contain no commercial game data. They exercise independent Portal installs, DLC ordering, localization, unsafe paths, VPK truncation, excluded user data, compressed APK resources, existing-cache protection and the Linux wrapper.
