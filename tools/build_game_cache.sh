#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys,lzma,zipfile; sys.exit(sys.version_info < (3,10))'; then
    printf '%s\n' 'ERROR: Python 3.10+ with standard-library LZMA is required. No pip packages are needed.' >&2
    exit 2
fi
exec python3 -B -X utf8 "$ROOT/build_game_cache.py" "$@"
