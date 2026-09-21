#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
[[ -f "$ROOT/vr_game_resources/MANIFEST.sha256" ]] || {
    printf 'ERROR: This distribution is incomplete: vr_game_resources/MANIFEST.sha256 is missing.\n' >&2
    printf 'Extract the complete archive again before running the cache builder.\n' >&2
    exit 2
}
exec "$ROOT/tools/build_game_cache.sh" "$@"
