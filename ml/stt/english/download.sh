#!/usr/bin/env bash
# download_en.sh — download English ASR datasets.
#
#   ./download_en.sh info         # table only, download nothing
#   ./download_en.sh starter      # librispeech + voxpopuli + eval  (~115 GB)
#   ./download_en.sh commercial   # only sets you may ship a product with
#   ./download_en.sh eval         # benchmarks only (~28 GB)
#   ./download_en.sh librispeech tedlium
#
# There is no "all" here on purpose: English at full scale is TERABYTES,
# not the 98 GB Uzbek costs. You must name what you want.
#
#   OUT=/workspace/datasets/en   JOBS=3   YES=1   MIN_GB=150
set -uo pipefail

OUT=${OUT:-/workspace/datasets/en}
LOGS=${LOGS:-/workspace/logs/en}
JOBS=${JOBS:-3}

# key | repo | hours | rows | GB | licence | include-pattern (empty = all)
DATA=(
"librispeech|openslr/librispeech_asr|960|584734|60|cc-by-4.0|"
"voxpopuli_en|facebook/voxpopuli|543|?|30|cc0-1.0|data/en/*"
"esb_test|hf-audio/esb-datasets-test-only-sorted|eval|?|25|mixed|"
"fleurs_en|google/fleurs|10|?|3|cc-by-4.0|data/en_us/*"
"common_voice_en|mozilla-foundation/common_voice_17_0|1774|?|90|cc0-1.0|audio/en/*"
"tedlium|LIUM/tedlium|452|?|35|cc-by-nc-nd-3.0|"
"loquacious_small|speechbrain/LoquaciousSet|~1000|?|?|mixed-permissive|*small*"
"loquacious|speechbrain/LoquaciousSet|25000|14654760|?|mixed-permissive|"
"peoples_speech|MLCommons/peoples_speech|30000|8051212|?|cc-by-sa-4.0|*clean*"
"gigaspeech|speechcolab/gigaspeech|10000|?|?|NON-COMMERCIAL|"
)

STARTER=(librispeech voxpopuli_en esb_test)
COMMERCIAL=(librispeech voxpopuli_en loquacious_small)   # all permissive
EVAL=(esb_test fleurs_en)
SCALE=(loquacious peoples_speech)

field() { echo "$1" | cut -d'|' -f"$2"; }
fadd()  { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.1f", a+b}'; }
fgt()   { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>b)}'; }
commas(){ echo "$1" | sed -E ':a;s/([0-9])([0-9]{3})($|,)/\1,\2\3/;ta'; }

show_info() {
    printf "\n  %-19s %8s %12s %7s   %-16s %s\n" \
        "KEY" "HOURS" "ROWS" "SIZE" "LICENSE" "FILTER"
    printf "  %s\n" "--------------------------------------------------------------------------------------"
    for e in "${DATA[@]}"; do
        local gb; gb=$(field "$e" 5)
        [ "$gb" = "?" ] && gb="?" || gb="${gb}G"
        printf "  %-19s %8s %12s %7s   %-16s %s\n" \
            "$(field "$e" 1)" "$(field "$e" 3)" \
            "$(commas "$(field "$e" 4)")" "$gb" \
            "$(field "$e" 6)" "$(field "$e" 7)"
    done
    printf "  %s\n" "--------------------------------------------------------------------------------------"
    cat <<'EOF'

  PRESETS
    starter      librispeech voxpopuli_en esb_test          ~115 GB
    commercial   librispeech voxpopuli_en loquacious_small  permissive only
    eval         esb_test fleurs_en                          ~28 GB
    scale        loquacious peoples_speech                   TERABYTES

  LICENCE WARNINGS
    tedlium     CC-BY-NC-ND : research only, no commercial product
    gigaspeech  NON-COMMERCIAL + gated. Its terms bind your employer too.
    peoples_speech  CC-BY-SA : share-alike. Derived models may inherit this.
    Safe to ship: librispeech, voxpopuli_en, loquacious, common_voice_en.

  FILTER column = files actually fetched. Without it, fleurs pulls ALL 102
  languages (878 GB instead of 3 GB) and common_voice pulls every language.

  esb_test is the Open ASR Leaderboard bundle. EVAL ONLY - never train on it.
EOF
}

# ---------------------------------------------------------------- selection
SELECTED=()
case "${1:-info}" in
    info)       show_info; exit 0 ;;
    starter)    SELECTED=("${STARTER[@]}") ;;
    commercial) SELECTED=("${COMMERCIAL[@]}") ;;
    eval)       SELECTED=("${EVAL[@]}") ;;
    scale)      SELECTED=("${SCALE[@]}") ;;
    all)        echo "No 'all' for English - it is terabytes." >&2
                echo "Use: starter | commercial | eval | scale" >&2; exit 1 ;;
    *)          SELECTED=("$@") ;;
esac

show_info

if ! command -v hf >/dev/null 2>&1; then
    echo "ERROR: 'hf' not found. Run: uv pip install huggingface_hub" >&2
    exit 1
fi

mkdir -p "$OUT" "$LOGS"
free_gb=$(df -BG --output=avail "$OUT" | tail -1 | tr -dc '0-9')
need=0; unknown=0
for key in "${SELECTED[@]}"; do
    for e in "${DATA[@]}"; do
        if [ "$(field "$e" 1)" = "$key" ]; then
            g=$(field "$e" 5)
            if [ "$g" = "?" ]; then unknown=1; else need=$(fadd "$need" "$g"); fi
        fi
    done
done

echo "  downloading : ${SELECTED[*]}"
echo "  destination : $OUT"
if (( unknown )); then
    echo "  needs       : >${need} GB  (some sizes UNKNOWN - could be TB)"
else
    echo "  needs       : ${need} GB"
fi
echo "  free        : ${free_gb} GB"
echo

if (( unknown )); then
    echo "  ** At least one selected dataset has no published size."
    echo "  ** Start it alone, watch 'du -sh $OUT', and Ctrl-C if it runs away."
    echo
fi
if fgt "$need" "$free_gb"; then
    echo "  ** NOT ENOUGH SPACE. Try: ./download_en.sh starter" >&2
    [ "${MIN_GB:-1}" != "0" ] && exit 1
fi

if [ "${YES:-0}" != "1" ]; then
    read -r -p "  proceed? [y/N] " a
    [[ "$a" =~ ^[Yy] ]] || { echo "cancelled."; exit 0; }
fi

# ------------------------------------------------------------- the downloads
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DOWNLOAD_TIMEOUT=60
[ -n "${HF_TOKEN:-}" ] || echo "  note: no HF_TOKEN set - slower, and gated sets will fail."
echo

declare -A PID2KEY
FAILED=(); GATED=()
START=$(date +%s)

for key in "${SELECTED[@]}"; do
    repo=""; inc=""
    for e in "${DATA[@]}"; do
        if [ "$(field "$e" 1)" = "$key" ]; then
            repo=$(field "$e" 2); inc=$(field "$e" 7)
        fi
    done
    [ -z "$repo" ] && { echo "  ! unknown dataset '$key', skipping"; continue; }

    while (( $(jobs -rp | wc -l) >= JOBS )); do wait -n || true; done

    if [ -n "$inc" ]; then
        echo "  -> $key  ($repo)  [only: $inc]"
        hf download "$repo" --repo-type dataset --local-dir "$OUT/$key" \
            --include "$inc" "*.md" "*.json" > "$LOGS/$key.log" 2>&1 &
    else
        echo "  -> $key  ($repo)"
        hf download "$repo" --repo-type dataset --local-dir "$OUT/$key" \
            > "$LOGS/$key.log" 2>&1 &
    fi
    PID2KEY[$!]=$key
done

for pid in "${!PID2KEY[@]}"; do
    key=${PID2KEY[$pid]}
    if wait "$pid"; then
        echo "  OK    $key  ($(du -sh "$OUT/$key" 2>/dev/null | cut -f1))"
    else
        if grep -qiE "gated|403|accept.*terms|authoriz" "$LOGS/$key.log" 2>/dev/null; then
            echo "  GATED $key  -- accept terms, then: hf auth login"
            GATED+=("$key")
        else
            echo "  FAIL  $key  -- tail -20 $LOGS/$key.log"
            FAILED+=("$key")
        fi
    fi
done

# ------------------------------------------------------------- verification
echo
printf "  %-19s %10s %10s\n" "DATASET" "FILES" "SIZE"
printf "  %s\n" "-----------------------------------------"
for key in "${SELECTED[@]}"; do
    [ -d "$OUT/$key" ] || continue
    n=$(find "$OUT/$key" -type f \( -iname '*.parquet' -o -iname '*.wav' \
        -o -iname '*.mp3' -o -iname '*.flac' -o -iname '*.opus' \
        -o -iname '*.tar*' -o -iname '*.arrow' \) 2>/dev/null | wc -l)
    sz=$(du -sh "$OUT/$key" 2>/dev/null | cut -f1)
    warn=""; (( n == 0 )) && warn="   <-- NO DATA FILES"
    printf "  %-19s %10s %10s%s\n" "$key" "$n" "$sz" "$warn"
done
printf "  %s\n" "-----------------------------------------"
printf "  %-19s %10s %10s\n" "TOTAL" "" "$(du -sh "$OUT" 2>/dev/null | cut -f1)"

echo
(( ${#GATED[@]} )) && {
    echo "  GATED (accept terms on huggingface.co, then rerun):"
    for k in "${GATED[@]}"; do
        for e in "${DATA[@]}"; do
            [ "$(field "$e" 1)" = "$k" ] && \
                echo "    https://huggingface.co/datasets/$(field "$e" 2)"
        done
    done
    echo
}
if (( ${#FAILED[@]} )); then
    echo "  FAILED: ${FAILED[*]}   (rerun - finished files are skipped)"
    exit 1
fi
echo "  DONE in $(( ($(date +%s) - START) / 60 )) min"
echo "  next:  ./clean.sh en"