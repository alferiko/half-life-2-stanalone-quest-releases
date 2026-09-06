# Half-Life 2 VR Standalone for Meta Quest

[Русская версия](README.ru.md)

An unofficial, free and non-commercial standalone VR port of Half-Life 2 for Meta Quest 3 and Quest 3S. The initial release of this repository is 0.982 and supports Half-Life 2, Lost Coast, Episode One and Episode Two. The original games are not included: you must own and install them legally on Steam.

The repository includes `HL2VR-Standalone-0.983.apk`, the Windows and Linux cache builders in `BUILD_GAME_CACHE.bat`, `BUILD_GAME_CACHE.sh` and `tools/`, plus the complete VR compatibility overlay in `vr_game_resources/`. A clone is therefore sufficient to build the cache. The release archive contains only the APK, builders, documentation and VR resources.

## Original VR implementation

All code responsible for interaction with the VR world was written from scratch for this project. No code, VR logic or other resources from the PC VR version are used. The only exception is maps and models, which the cache builder takes from the user's legally installed copy of the game; they are not included in this repository or its releases.

## What you need

- Meta Quest 3 or Quest 3S with Developer Mode enabled;
- a Windows 10/11 or Linux PC;
- a USB data cable and authorized USB debugging;
- Android SDK Platform Tools (`adb`), or another sideloading tool;
- a legal Steam installation of Half-Life 2; install Episode One and Episode Two too if you want those campaigns;
- the 0.983 APK from the repository root or release attachments; either clone this repository or download the standalone distribution archive.

## Installation

### 1. Build the legal game cache

1. Clone/download this repository to a writable folder, or extract `HL2VR-Standalone-0.983.7z`. Keep `BUILD_GAME_CACHE.*`, `tools/` and `vr_game_resources/` beside one another.
2. From the repository/distribution root, run `BUILD_GAME_CACHE.bat` on Windows. On Linux run:

   ```bash
   bash BUILD_GAME_CACHE.sh
   ```

3. When asked, select the Half-Life 2 Steam Legacy root folder containing `hl2` and `platform`, for example:

   ```text
   D:\SteamLibrary\steamapps\common\Half-Life 2
   ```

4. If `lostcoast`, `episodic` and `ep2` are installed beside `hl2`, the builder includes them automatically. The result is `game_cache/srceng`.

The builder excludes executables, DLLs, saves, logs, personal configuration and every campaign's `custom` folder. It combines your legal game installation with the supplied VR compatibility resources. Python is not required. Linux needs Bash 4+ and GNU coreutils.

### 2. Install the APK

Connect the headset, accept its USB debugging prompt and check the connection:

```bash
adb devices
adb install -r HL2VR-Standalone-0.983.apk
```

The `-r` option updates an existing installation without deleting its application data. If Android reports an incompatible signature, back up anything important, uninstall the older package, then install again.

### 3. Copy the game cache

Keep the complete `srceng` folder and copy it to shared storage:

```bash
adb push game_cache/srceng /sdcard/
```

The final headset layout must be:

```text
/sdcard/srceng/hl2/
/sdcard/srceng/platform/
/sdcard/srceng/lostcoast/  (only when Lost Coast is installed)
/sdcard/srceng/episodic/   (only when Episode One is installed)
/sdcard/srceng/ep2/        (only when Episode Two is installed)
```

Start **Half-Life 2 VR Standalone** from the headset's Unknown Sources section. Select the campaign in the launcher and start the game.

## Controls

The table shows the default right-handed layout. Enable left-handed mode in the launcher to mirror weapon-hand actions.

| Touch controller input | Action |
|---|---|
| Left thumbstick | Move; forward direction follows horizontal head direction |
| Right thumbstick | Turn/look; smooth or snap turning is selectable in the launcher |
| Dominant-hand trigger (right by default) | Fire; point and select in menus |
| Support-hand trigger | Context action: mounted-gun fire or buggy boost with alternative vehicle controls |
| Either grip | Grab/use with that hand; the dominant grip also provides weapon-specific alternate actions |
| A | Jump; confirm in menus |
| B | Tap/hold weapon selection; back in menus |
| X | Reload; eject magazine/ammunition during physical reload |
| Y | Flashlight |
| Left thumbstick click | Toggle sprint |
| Right thumbstick click | Toggle crouch |
| Menu button on the left controller | Open or close the pause menu |

### VR interactions

- **Weapon selection:** tap B to switch quickly; hold B, point at a weapon in the radial/grid selector, then release. In left-handed mode this role moves to Y.
- **Physical reload (default):** eject the current magazine/ammunition with X for a right-handed profile (A when left-handed), reach behind the shoulder with the free hand to take fresh ammunition, insert it and operate the slide/pump where required. Reload mode can be changed in launcher settings.
- **Two-handed weapons:** hold the free-hand grip near the fore-end to attach the second hand; release it to detach.
- **Alternate fire:** for an armed weapon, double-squeeze the dominant grip within 350 ms. The gravity gun uses its dominant grip to attract/release and its trigger to punt.
- **Objects and controls:** grip starts and maintains use with the hand that touched the object. This also works for continuously operated levers and wheels.
- **Physical ladders:** when enabled, place either hand near a rung, hold that hand's grip and pull down. Either hand can remain attached; release both grips to dismount.
- **Crowbar:** physical-contact damage is optional. When enabled, swing the crowbar; trigger attack remains available when the option is disabled.
- **Mounted guns:** grab the handles, fire with either trigger and release either grip to let go.
- **Vehicles:** the optional alternative layout uses the physical left stick for throttle/brake, the right stick for steering and the non-dominant trigger for buggy boost.
- **Room-scale movement:** optional and disabled by default; enable it in the launcher if you want real horizontal body motion to add locomotion.

## Updating

Install a newer APK with `adb install -r`. Version 0.982 performs a one-time reset of launcher, game, graphics and VR settings to the new defaults; saves, installed game data and user mods are preserved. Rebuild and recopy the cache when the release notes say VR resources changed. The launcher's update check may also download the fixed-name APK and hand it to Android's package installer; confirm the system installation prompt to complete the update.

## Troubleshooting

- **`unauthorized` in `adb devices`:** put on the headset, accept the computer fingerprint, then reconnect USB.
- **More than one device:** use `adb -s DEVICE_SERIAL ...` with the serial shown by `adb devices`.
- **Game returns to the launcher or cannot find content:** verify that the path is exactly `/sdcard/srceng/hl2`, not `/sdcard/srceng/srceng/hl2`.
- **A campaign is missing:** install it in Steam, run the cache builder again and verify that `lostcoast/gameinfo.txt`, `episodic/gameinfo.txt` or `ep2/gameinfo.txt` exists in the generated cache.
- **Old files cause visual or startup issues:** rebuild a clean cache and replace `/sdcard/srceng` rather than merging directories by hand.

## Legal notice

This project does not include commercial Half-Life 2 maps, VPKs, voices, saves or other game data. It is distributed free of charge for non-commercial use. Half-Life, Steam, Source and Meta Quest trademarks belong to their respective owners.
