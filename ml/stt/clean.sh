#!/usr/bin/env bash
# clean.sh — clean downloaded ASR datasets, language by language.
#
#   ./clean.sh uz            one language
#   ./clean.sh uz ru en      several, in order
#   ./clean.sh all           every language folder found
#
# Reads  /workspace/datasets/<lang>   ->  writes  /workspace/clean/<lang>
# Override with:  ASR_ROOT=/other/datasets ./clean.sh uz
set -uo pipefail

ASR_ROOT=${ASR_ROOT:-/workspace/datasets}
OUT=${OUT:-$(dirname "$ASR_ROOT")/clean}
MAX_DUR=${MAX_DUR:-35}
SCRIPT=${SCRIPT:-$(dirname "$0")/clean_asr.py}
PY=${PY:-python}

if [ $# -eq 0 ]; then
    echo "usage: ./clean.sh <lang> [lang...]   |   ./clean.sh all"
    echo
    echo "found in $ASR_ROOT:"
    for d in "$ASR_ROOT"/*/; do
        [ -d "$d" ] || continue
        n=$(find "$d" -maxdepth 1 -mindepth 1 -type d | wc -l)
        printf "  %-6s %s dataset(s)\n" "$(basename "$d")" "$n"
    done
    exit 1
fi

# "all" -> every subfolder of ASR_ROOT that is a known language code
LANGS=("$@")
if [ "${1:-}" = "all" ]; then
    LANGS=()
    for d in "$ASR_ROOT"/*/; do
        [ -d "$d" ] || continue
        l=$(basename "$d")
        case "$l" in
            uz|kaa|ru|en|de|fr|ar|ko|ja|zh) LANGS+=("$l") ;;
            *) echo "  (skipping '$l' - not a language code)" ;;
        esac
    done
fi

[ ${#LANGS[@]} -eq 0 ] && { echo "nothing to do under $ASR_ROOT"; exit 1; }

echo "languages : ${LANGS[*]}"
echo "input     : $ASR_ROOT/<lang>"
echo "output    : $OUT/<lang>"
echo "max-dur   : ${MAX_DUR}s"
echo

FAILED=()
for lang in "${LANGS[@]}"; do
    src="$ASR_ROOT/$lang"
    if [ ! -d "$src" ]; then
        echo "=== $lang: no folder at $src, skipping ==="
        continue
    fi
    echo "=================================================="
    echo "  $lang"
    echo "=================================================="
    # EXTRA is optional; word-split it so an empty value adds no argument
    # (passing "" would reach argparse as a bogus empty positional).
    read -r -a extra_args <<< "${EXTRA:-}"
    if ! "$PY" "$SCRIPT" "$src" --lang "$lang" --out "$OUT" \
            --max-dur "$MAX_DUR" "${extra_args[@]}"; then
        FAILED+=("$lang")
    fi
    echo
done

echo "=================================================="
for lang in "${LANGS[@]}"; do
    m="$OUT/$lang/all_manifest.jsonl"
    if [ -f "$m" ]; then
        lines=$(wc -l < "$m")
        hrs=$("$PY" - "$m" <<'PY'
import json, sys
t = 0.0
for line in open(sys.argv[1], encoding="utf-8"):
    try: t += json.loads(line)["duration"]
    except Exception: pass
print(f"{t/3600:.2f}")
PY
)
        printf "  %-6s %9s utterances  %8s hours\n" "$lang" "$lines" "$hrs"
    fi
done
echo "=================================================="

if [ ${#FAILED[@]} -gt 0 ]; then
    echo "failed: ${FAILED[*]}"
    exit 1
fi
echo "done. manifests: $OUT/<lang>/all_manifest.jsonl"