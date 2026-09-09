#!/usr/bin/env bash
set -Eeuo pipefail

PORT_VERSION="0.985"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
RELEASE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
OVERLAY_ROOT="$RELEASE_ROOT/vr_game_resources"
OVERLAY_SRCENG="$OVERLAY_ROOT/srceng"
OVERLAY_MANIFEST="$OVERLAY_ROOT/MANIFEST.sha256"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command is missing: $1"
}

resolve_game_root() {
    local candidate="$1"
    candidate="${candidate%\"}"
    candidate="${candidate#\"}"
    [[ -n "$candidate" ]] || die "The Half-Life 2 path is empty."
    candidate="$(realpath -e -- "$candidate")" || die "Path does not exist: $candidate"

    if [[ -f "$candidate/hl2/gameinfo.txt" && -d "$candidate/platform" ]]; then
        printf '%s\n' "$candidate"
        return
    fi
    if [[ "$(basename -- "$candidate")" == "hl2" && -f "$candidate/gameinfo.txt" && -d "$candidate/../platform" ]]; then
        realpath -e -- "$candidate/.."
        return
    fi
    die "Not a Half-Life 2 root: $candidate (expected hl2/gameinfo.txt and platform/)"
}

resolve_portal_root() {
    local candidate="$1"
    candidate="${candidate%\"}"
    candidate="${candidate#\"}"
    candidate="$(realpath -e -- "$candidate")" || die "Path does not exist: $candidate"
    [[ -f "$candidate/portal/gameinfo.txt" && -d "$candidate/hl2" && -d "$candidate/platform" ]] ||
        die "Not a Portal root: $candidate (expected portal/gameinfo.txt, hl2 and platform)"
    printf '%s\n' "$candidate"
}

verify_overlay() {
    [[ -d "$OVERLAY_SRCENG" ]] || die "VR resource directory is missing: $OVERLAY_SRCENG"
    [[ -f "$OVERLAY_MANIFEST" ]] || die "VR resource checksum manifest is missing: $OVERLAY_MANIFEST"

    local expected relative actual verified=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ -z "$line" || "$line" == \#* ]] && continue
        [[ "$line" =~ ^([[:xdigit:]]{64})[[:space:]]{2}(.+)$ ]] || die "Invalid manifest line: $line"
        expected="${BASH_REMATCH[1],,}"
        relative="${BASH_REMATCH[2]}"
        [[ "$relative" != /* && "$relative" != *".."* ]] || die "Unsafe manifest path: $relative"
        [[ -f "$OVERLAY_ROOT/$relative" ]] || die "VR resource is missing: $relative"
        actual="$(sha256sum -- "$OVERLAY_ROOT/$relative")"
        actual="${actual%% *}"
        [[ "$actual" == "$expected" ]] || die "VR resource checksum mismatch: $relative"
        ((verified += 1))
    done < "$OVERLAY_MANIFEST"
    ((verified > 0)) || die "The VR resource manifest contains no files."
    printf 'Verified VR resources: %d files\n' "$verified"
}

skip_file() {
    local name="${1##*/}"
    name="${name,,}"
    case "$name" in
        *.dll|*.exe|*.pdb|*.dmp|*.mdmp|*.log|config.cfg|video.txt|videodefaults.txt|voice_ban.dt) return 0 ;;
        *) return 1 ;;
    esac
}

copy_game_tree() {
    local source="$1" destination="$2" package="$3"
    local path relative top target
    while IFS= read -r -d '' path; do
        relative="${path#"$source/"}"
        top="${relative%%/*}"
        case "${top,,}" in
            bin|download|downloads|logs|save|screenshots) continue ;;
            custom) [[ "$package" != "platform" ]] && continue ;;
        esac
        skip_file "$relative" && continue
        target="$destination/$relative"
        mkdir -p -- "$(dirname -- "$target")"
        cp -p -- "$path" "$target"
    done < <(find "$source" -type f -print0)
}

copy_overlay() {
    local path relative target
    while IFS= read -r -d '' path; do
        relative="${path#"$OVERLAY_SRCENG/"}"
        target="$SRCENG_ROOT/$relative"
        mkdir -p -- "$(dirname -- "$target")"
        cp -p -- "$path" "$target"
    done < <(find "$OVERLAY_SRCENG" -type f -print0)
}

enable_vr_support() {
    local gameinfo="$1" temporary
    temporary="$(mktemp)"
    if grep -Eqi '^[[:space:]]*supportsvr[[:space:]]+' "$gameinfo"; then
        sed -E 's/^([[:space:]]*supportsvr[[:space:]]+).*$/\11/I' "$gameinfo" > "$temporary"
    else
        awk '
            BEGIN { added = 0 }
            { print }
            !added && tolower($0) ~ /^[[:space:]]*type[[:space:]]+singleplayer_only[[:space:]]*$/ {
                match($0, /^[[:space:]]*/)
                print substr($0, RSTART, RLENGTH) "supportsVR\t1"
                added = 1
            }
            END { if (!added) exit 3 }
        ' "$gameinfo" > "$temporary" || { rm -f -- "$temporary"; die "Cannot add supportsVR to $gameinfo"; }
    fi
    mv -- "$temporary" "$gameinfo"
}

need_command realpath
need_command sha256sum
need_command find
need_command cp
need_command sed
need_command awk

printf 'Half-Life 2 VR Standalone %s\n' "$PORT_VERSION"
printf 'The sources must be legal Half-Life 2 and optional Portal installations.\n\n'

GAME_ROOT="${1:-}"
if [[ -z "$GAME_ROOT" ]]; then
    read -r -p 'Enter the Half-Life 2 root path (the folder containing hl2 and platform): ' GAME_ROOT
fi
GAME_ROOT="$(resolve_game_root "$GAME_ROOT")"

PORTAL_ROOT="${3:-}"
if [[ -z "$PORTAL_ROOT" && -f "$(dirname -- "$GAME_ROOT")/Portal/portal/gameinfo.txt" ]]; then
    PORTAL_ROOT="$(dirname -- "$GAME_ROOT")/Portal"
    printf 'Portal found automatically: %s\n' "$PORTAL_ROOT"
elif [[ -z "$PORTAL_ROOT" ]]; then
    read -r -p 'Enter the Portal root path, or leave blank to build without Portal 1: ' PORTAL_ROOT
fi
[[ -z "$PORTAL_ROOT" ]] || PORTAL_ROOT="$(resolve_portal_root "$PORTAL_ROOT")"

OUTPUT_ROOT="${2:-$RELEASE_ROOT/game_cache}"
OUTPUT_ROOT="$(realpath -m -- "$OUTPUT_ROOT")"
SRCENG_ROOT="$OUTPUT_ROOT/srceng"
case "$OUTPUT_ROOT/" in
    "$GAME_ROOT/"*) die "The output cache must not be inside the Half-Life 2 installation." ;;
esac
if [[ -n "$PORTAL_ROOT" ]]; then
    case "$OUTPUT_ROOT/" in
        "$PORTAL_ROOT/"*) die "The output cache must not be inside the Portal installation." ;;
    esac
fi
[[ "$(basename -- "$SRCENG_ROOT")" == "srceng" && "$(dirname -- "$SRCENG_ROOT")" == "$OUTPUT_ROOT" ]] || die "Unsafe generated-cache path: $SRCENG_ROOT"

verify_overlay

if [[ -e "$SRCENG_ROOT" ]]; then
    read -r -p "The existing cache will be replaced: $SRCENG_ROOT. Continue? [y/N] " answer
    [[ "$answer" =~ ^([yY]|[yY][eE][sS])$ ]] || { printf 'Cancelled.\n'; exit 1; }
    rm -rf -- "$SRCENG_ROOT"
fi

mkdir -p -- "$SRCENG_ROOT/hl2" "$SRCENG_ROOT/platform"
printf 'Source: %s\nOutput: %s\nCopying Half-Life 2 files...\n' "$GAME_ROOT" "$SRCENG_ROOT"
copy_game_tree "$GAME_ROOT/hl2" "$SRCENG_ROOT/hl2" hl2
copy_game_tree "$GAME_ROOT/platform" "$SRCENG_ROOT/platform" platform

CAMPAIGNS=(hl2)
for campaign in lostcoast episodic ep2; do
    if [[ -f "$GAME_ROOT/$campaign/gameinfo.txt" ]]; then
        printf 'Copying %s...\n' "$campaign"
        mkdir -p -- "$SRCENG_ROOT/$campaign"
        copy_game_tree "$GAME_ROOT/$campaign" "$SRCENG_ROOT/$campaign" "$campaign"
        CAMPAIGNS+=("$campaign")
    else
        printf 'Skipping %s: gameinfo.txt was not found.\n' "$campaign"
    fi
done

if [[ -n "$PORTAL_ROOT" ]]; then
    printf 'Copying Portal 1 into the shared cache...\n'
    for mapping in 'portal:portal' 'hl2:portal_hl2' 'platform:portal_platform'; do
        source_name="${mapping%%:*}"
        destination_name="${mapping#*:}"
        mkdir -p -- "$SRCENG_ROOT/$destination_name"
        copy_game_tree "$PORTAL_ROOT/$source_name" "$SRCENG_ROOT/$destination_name" "$source_name"
    done
    cat > "$SRCENG_ROOT/portal/gameinfo.txt" <<'EOF'
"GameInfo"
{
    game "Portal"
    title "Portal"
    type singleplayer_only
    nodifficulty 1
    hasportals 1
    supportsvr 1
    FileSystem
    {
        SteamAppId 400
        SearchPaths
        {
            game+mod "portal/custom/*"
            game "hl2/custom/*"
            game+mod "portal/portal_sound_vo_russian.vpk"
            game+mod "portal/portal_sound_vo_english.vpk"
            game+mod "portal/portal_pak.vpk"
            game "portal_hl2/hl2_textures.vpk"
            game "portal_hl2/hl2_sound_vo_russian.vpk"
            game "portal_hl2/hl2_sound_vo_english.vpk"
            game "portal_hl2/hl2_sound_misc.vpk"
            game "portal_hl2/hl2_misc.vpk"
            platform "portal_platform/platform_misc.vpk"
            mod+mod_write+default_write_path "|gameinfo_path|."
            game+game_write "portal"
            gamebin "portal/bin"
            game "portal_hl2"
            game "hl2"
            platform "portal_platform"
            platform "platform"
        }
    }
}
EOF
    CAMPAIGNS+=(portal)
fi

printf 'Applying HL2Q3VR resources...\n'
copy_overlay
for campaign in "${CAMPAIGNS[@]}"; do
    enable_vr_support "$SRCENG_ROOT/$campaign/gameinfo.txt"
done

FILE_COUNT="$(find "$SRCENG_ROOT" -type f -printf '.' | wc -c)"
SIZE_BYTES="$(find "$SRCENG_ROOT" -type f -printf '%s\n' | awk '{ total += $1 } END { printf "%.0f", total }')"
SOURCE_NAME="$(basename -- "$GAME_ROOT")"
SOURCE_NAME="${SOURCE_NAME//\\/\\\\}"
SOURCE_NAME="${SOURCE_NAME//\"/\\\"}"
mkdir -p -- "$OUTPUT_ROOT"
CAMPAIGNS_JSON="$(printf '"%s",' "${CAMPAIGNS[@]}")"
CAMPAIGNS_JSON="[${CAMPAIGNS_JSON%,}]"
printf '{\n  "format": 2,\n  "port": "HL2Q3VR",\n  "port_version": "%s",\n  "campaigns": %s,\n  "lost_coast_supported": true,\n  "episodes_supported": true,\n  "portal_supported": %s,\n  "generated_utc": "%s",\n  "source_folder_name": "%s",\n  "file_count": %s,\n  "size_bytes": %s,\n  "headset_destination": "/sdcard/srceng"\n}\n' \
    "$PORT_VERSION" "$CAMPAIGNS_JSON" "$([[ -n "$PORTAL_ROOT" ]] && printf true || printf false)" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$SOURCE_NAME" "$FILE_COUNT" "$SIZE_BYTES" \
    > "$OUTPUT_ROOT/hl2q3vr-cache.json"

printf '\nCache ready: %s\nQuest destination: /sdcard/srceng\n' "$SRCENG_ROOT"
