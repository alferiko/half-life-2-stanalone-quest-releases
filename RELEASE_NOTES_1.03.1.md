# HL2Quest 1.03.1 — Portal collision hotfix

## English

- Fixed client-side collision traces through portals using the wrong entity list.
- Version raised to **1.03.1 / 1031** so the regular GitHub launcher detects this hotfix as an update from 1.03.

Use the launcher's **Check for updates**, or install `HL2VR-Standalone-1.03.1.apk` over the regular GitHub edition. Keep the app, game cache and saves; do not uninstall or clear app data.

This contains the same game code and resources as the earlier `e5e18bf9` hotfix APK under 1.03; only Android version metadata and signing output changed. Native builds and 40 collision-filter checks passed for that hotfix. The repack passed signature, alignment, CRC and complete non-manifest payload comparison. The production updater code accepts the 1.03 → 1.03.1 transition and versionCode 1030 → 1031. No new headset test was performed.

[Full 1.03 changelog](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.03) · [SideQuest edition](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.03.1-sidequest) · [Setup guide](https://github.com/alferiko/half-life-2-stanalone-quest-releases/blob/main/README.md)

## Русский

- Исправлен выбор списка сущностей при клиентских проверках столкновений через порталы.
- Версия повышена до **1.03.1 / 1031**, чтобы лаунчер обычной GitHub-версии обнаруживал хотфикс поверх 1.03.

Нажмите **«Проверить обновления»** в лаунчере или установите `HL2VR-Standalone-1.03.1.apk` поверх обычной GitHub-версии. Не удаляйте приложение, кеш и сохранения.

Код и ресурсы совпадают с хотфиксом `e5e18bf9`, ранее опубликованным под номером 1.03. Изменены только метаданные версии и подпись APK. Проверены подпись, выравнивание, CRC, побайтовое соответствие содержимого и переход обновления 1.03 → 1.03.1. Повторного теста на шлеме не было.

Thanks to **nom**, **matmanreturns** and **sniperPug115** for the bug reports!
