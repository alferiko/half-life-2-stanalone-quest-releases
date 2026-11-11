# HL2Quest 1.02 — Steam download hotfix

## English

- Fixed Steam downloads stopping on a temporary Android DNS failure, including failures after the headset wakes or its network reconnects. The downloader now recognizes `UnknownHostException` even when Android wraps the underlying DNS error, and uses the existing retry/backoff path.
- Existing partial downloads remain reusable. If installation has already stopped, open **Check cache**, sign in again if prompted and retry; do not delete the downloaded game files.
- Version increased to **1.02 / 1020** so 1.01 installations can update normally. Game engines and bundled VR resources are unchanged from 1.01.

Install `hl2quest-vr.apk` over the regular GitHub edition with `adb install -r hl2quest-vr.apk`, or use its in-app update check. Keep the installed app and `/sdcard/srceng`; no cache rebuild is required. Back up saves before updating.

The [SideQuest edition](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/tag/1.02-sidequest) has the same fix, its existing package `com.alferiko.hl2quest.sidequest`, and in-app APK updates remain disabled. Update that edition through SideQuest or install its matching APK over it. The two editions have different package IDs.

The [1.01 Full cache-builder archive](https://github.com/alferiko/half-life-2-stanalone-quest-releases/releases/download/1.01/HL2Quest-Cache-Builder-1.01-Full.zip) remains compatible: it contains the previous 1.01 APK, so use the new 1.02 APK on the headset. For a fresh PC setup, replace the archive's `hl2quest-vr.apk` with this release's same-named file. [Cache-builder guide](docs/CACHE_BUILDER.md).

Validation: 580 synthetic production-loader checks passed on Quest/Android, including the wrapped-DNS regression, retries, resume, integrity, cancellation and language/depot selection. Signatures match 1.01; native libraries and assets were checked byte for byte against 1.01. These are not a new live Steam login/download test or a full campaign playthrough.

## Русский

- Исправлено прекращение загрузки из Steam при временной ошибке DNS на Android, в том числе после пробуждения шлема или восстановления сети. Загрузчик теперь распознаёт вложенный `UnknownHostException` и повторяет запрос с предусмотренной задержкой.
- Уже скачанные части файлов можно использовать повторно. Если установка уже остановилась, откройте **«Проверить кеш»**, при необходимости снова войдите в Steam и повторите загрузку. Удалять скачанные файлы не нужно.
- Версия повышена до **1.02 / 1020** для обновления поверх 1.01. Игровые движки и встроенные VR-ресурсы не изменены.

Установите обычный `hl2quest-vr.apk` поверх GitHub-версии командой `adb install -r hl2quest-vr.apk` либо через обновление лаунчера. Не удаляйте приложение и `/sdcard/srceng`; пересборка кеша не требуется. Перед обновлением сохраните резервную копию сохранений.

Для **SideQuest Edition** используйте её отдельный APK 1.02 или обновление через SideQuest. Имя пакета прежнее, обновление APK внутри приложения по-прежнему отключено.

Полный сборщик кеша 1.01 остаётся совместимым, но содержит старый APK 1.01. На шлем устанавливайте новый APK 1.02; при новой распаковке сборщика замените вложенный `hl2quest-vr.apk` новым одноимённым файлом. Кеш заново собирать не нужно.

Проверка: на Quest/Android прошли 580 синтетических проверок загрузчика, включая повтор запроса после вложенной ошибки DNS. Полная загрузка из реального Steam-аккаунта и повторное прохождение кампаний в эту проверку не входили.
