# Half-Life 2 & Portal — Standalone VR 1.01

Meta Quest 3 / Quest 3S · Half-Life 2 · Episode One · Episode Two · Lost Coast · Portal · Portal 2

## Install / Установка

Download **hl2quest-vr.apk** below and install over your existing version. Sign in to Steam in the headset launcher to download the games you own. **Current Steam / Anniversary content is supported; pre-Anniversary / Legacy is no longer required.** The updated PC cache helper also supports Portal 2 and current local Steam installs (Python 3.10+ and this APK required); it remains an optional alternative to the launcher.

Скачайте **hl2quest-vr.apk** ниже и установите поверх текущей версии. Для установки принадлежащих вам игр войдите в Steam в лаунчере на шлеме. **Поддерживается актуальный контент Steam / Anniversary; версия до Anniversary / Legacy больше не нужна.** Обновлённый сборщик кеша на ПК также поддерживает Portal 2 и актуальные локальные Steam-установки (нужны Python 3.10+ и этот APK); он остаётся дополнительным вариантом установки.

[Updated PC cache helper / Обновлённый сборщик кеша](https://github.com/alferiko/half-life-2-stanalone-quest-releases/blob/main/docs/CACHE_BUILDER.md) · [Current scripts ZIP / Актуальные скрипты](https://github.com/alferiko/half-life-2-stanalone-quest-releases/archive/refs/heads/main.zip)

```bash
adb install -r hl2quest-vr.apk
```

[English setup, controls and logs](https://github.com/alferiko/half-life-2-stanalone-quest-releases/blob/main/README.md) · [Установка, управление и логи на русском](https://github.com/alferiko/half-life-2-stanalone-quest-releases/blob/main/README.ru.md)

## Changes since 0.989

- **Portal 2 joins the unified APK:** campaign systems, VR interactions and video support; fixes across portals, bridges, funnels, gels, lasers, turrets, story events, subtitles and audio.
- **Steam downloads on the headset:** choose owned games, resume downloads, verify files, select localized audio and prepare installed campaigns automatically.
- **Updated launcher and VR menus:** localized interface, button remapping, refreshed weapon icons and a smoother weapon selector.
- **Weapons and interactions:** adapted Juniez weapons and HD portal gun; improved aiming, grabbing, gravity gun, mounted weapons, hands/body and floor-height handling.
- **Rendering and stability:** Anniversary compatibility, shader/stereo fixes, Portal 2 optimizations, HL2/episode transition and save-related fixes, and multithreaded model-rendering fixes.
- **Resource packaging:** compressed, deduplicated payload with integrity checks and updated included-mod credits.

## Изменения после 0.989

- **Portal 2 в общем APK:** игровые системы, VR-взаимодействия и ролики; исправления порталов, мостов, воронок, гелей, лазеров, турелей, сюжетных событий, субтитров и звука.
- **Steam прямо на шлеме:** выбор принадлежащих вам игр, возобновление загрузки, проверка файлов, локализованная озвучка и автоматическая подготовка установленных кампаний.
- **Новые лаунчер и VR-меню:** локализация, переназначение кнопок, обновлённые иконки и более плавный селектор оружия.
- **Оружие и взаимодействия:** адаптированные модели Juniez и HD-портальная пушка; улучшены прицеливание, захват, гравипушка, стационарное оружие, руки/тело и высота пола.
- **Графика и стабильность:** совместимость Anniversary, исправления шейдеров и стерео, оптимизации Portal 2, переходы и ошибки сохранений HL2/эпизодов, многопоточная отрисовка моделей.
- **Упаковка ресурсов:** сжатие, дедупликация, проверка целостности и обновлённые сведения об авторах модов.

## Verification / Проверка

The exact APK passed **10/10 basic startup checks on Quest 3**: all six campaigns in Vulkan, plus HL2/Lost Coast/episodes in GLES. Start maps loaded, both-eye captures were reviewed and each game process remained alive for 30 seconds after loading. Installed as an update; all 911 original save files matched backups by SHA-256 and the 787 VPK/BSP cache files retained size and modification time. This does not certify full playthroughs, controller gameplay, old-save loading, audio or performance. Quest 3S and the Steam download/UI flow were not part of this device smoke test. Nonfatal resource-parser warnings remain in logs.

Этот APK прошёл **10/10 базовых проверок запуска на Quest 3**: шесть кампаний на Vulkan и HL2/Lost Coast/эпизоды на GLES. Загружены стартовые карты, просмотрены кадры обоих глаз, процесс каждой игры оставался активен 30 секунд после загрузки. Установка выполнена поверх старой версии; все 911 исходных файлов сохранений совпали с резервной копией по SHA-256, размеры и время изменения 787 файлов VPK/BSP сохранились. Это не полная проверка прохождения, управления, загрузки старых сохранений, звука и производительности. Quest 3S, Steam-загрузка и навигация по лаунчеру в этот тест на устройстве не входили. В логах остаются нефатальные предупреждения парсера ресурсов.

APK: `hl2quest-vr.apk` · 751,785,619 bytes · Android version `1.01` (`1010`).

SHA-256: `10ae00ad3e6de2c4e009d2c08f35dba4edcfa29de0c7528ecfcc9ff7becd5b4b`

Built from source main commit `1467fc2e01beb2aa85e332f2a02ef7d05fe1e42a`. Release-repository tags identify distribution documentation, not the engine source commit. APK signature matches public 0.989. Full native build, archive integrity, alignment, runtime ABI/resource checks and host regression checks passed.

## Credits / Авторы

- [Juniez Weapons Pack](https://gamebanana.com/mods/427632): Juniez, Crowbar_XL, Shadow_RUN. Дополнительные включённые модели гильз и гранаты ПП — Reduxtered/USAR; электродубинка — Yogensia. Из пакета используются модели и материалы оружия; его звуковые модификации и HD-ящики не включены.
- [PortalGun HD Remake 2024](https://gamebanana.com/mods/522354), [вариант для Portal 2](https://gamebanana.com/mods/522356): Igrium, Matsilagi, OskiWolf; материалы и дополнительный вклад — ShadowRUN, marv, Viper. Оригинальный дизайн — Valve.
- [Gordon Freeman из Half-Life: Alyx](https://steamcommunity.com/sharedfiles/filedetails/?id=2144692491): jQueary, Kuro, Red Menace, Smug Bastard; оригинальные модели и материалы — Valve.
- [The Enhanced HWM Chell](https://steamcommunity.com/sharedfiles/filedetails/?id=299076518): Maxxy, Velly; оригинальные ресурсы — Valve.
- [Enhanced Chell [PM]](https://steamcommunity.com/sharedfiles/filedetails/?id=3568118506): THG; HD-костюм — Sirgibsalot; оригинальные ресурсы — Valve.
- Иконки Half-Life 2 Premium — [VIVRE-MOTION](https://www.vivre-motion.com). Дополнительная иконка рук подготовлена для этого проекта.
- Основной интерфейсный шрифт HL2Arcade использует Play и Noto: Jonas Hecksher, Playtype / e-types, Google и Adobe. Дополнительные ресурсы шрифта Raju: YouWorkForThem, Nicolas Massi и Valve.

Благодарим nillerusr и участников, участников hl2mp/d3d9-vr, Volkolak, JersonGaming, Dynamic_, Just Jacob, LarrySBM, Khronos, Meta и тестировщиков сообщества. Оригинальные игровые ресурсы принадлежат Valve. Авторство включённых модов сохранено; их адаптация не означает авторства исходных моделей и материалов.

## Support / Поддержка

[Patreon — zer0k0](https://www.patreon.com/cw/zer0k0)

Ethereum: `0xefFcAc44B2dc16333745fAC2df39218BBE7e341F`
