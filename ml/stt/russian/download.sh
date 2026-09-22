#!/usr/bin/env bash
# download_ru.sh — download Russian ASR datasets.
#
#   ./download_ru.sh              # same as "all"
#   ./download_ru.sh info         # table only, download nothing
#   ./download_ru.sh starter      # the 4 clean bond005 sets  (~25 GB)
#   ./download_ru.sh all          # starter + fleurs eval     (~28 GB)
#   ./download_ru.sh eval         # benchmark only            (~3 GB)
#   ./download_ru.sh scale        # YO-CPT-ru                 (~100 GB!)
#   ./download_ru.sh golos_crowd rulibrispeech
#
#   OUT=/workspace/datasets/ru   JOBS=3   YES=1   MIN_GB=0
set -uo pipefail

OUT=${OUT:-/workspace/datasets/ru}
LOGS=${LOGS:-/workspace/logs/ru}
JOBS=${JOBS:-3}

# key | repo | hours | rows | GB | licence | include-pattern
DATA=(
"golos_crowd|bond005/sberdevices_golos_10h_crowd|10|18780|2.27|cc-by-4.0|"
"golos_farfield|bond005/sberdevices_golos_100h_farfield|~9 (see note)|12419|1.08|cc-by-4.0|"
"rulibrispeech|bond005/rulibrispeech|92|57224|11.1|cc-by-4.0|"
"sova_rudevices|bond005/sova_rudevices|75|54586|10.7|cc-by-4.0|"
"fleurs_ru|google/fleurs|10|?|3|cc-by-4.0|data/ru_ru/*"
"common_voice_ru|mozilla-foundation/common_voice_17_0|~230|?|30|cc0-1.0|audio/ru/*"
"golos_full|SberDevices/Golos|1240|?|180|cc-by-4.0|"
"yo_cpt_ru|NCSpeech/YO-CPT-ru|?|100K-1M|~100|CUSTOM - read it|"
)

STARTER=(golos_crowd golos_farfield rulibrispeech sova_rudevices)
ALLSETS=(golos_crowd golos_farfield rulibrispeech sova_rudevices fleurs_ru)
EVALSET=(fleurs_ru)
SCALE=(yo_cpt_ru)

field() { echo "$1" | cut -d'|' -f"$2"; }
fadd()  { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.1f", a+b}'; }
fgt()   { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>b)}'; }
commas(){ echo "$1" | sed -E ':a;s/([0-9])([0-9]{3})($|,)/\1,\2\3/;ta'; }

show_info() {
    printf "\n  %-17s %14s %11s %7s   %-16s %s\n" \
        "KEY" "HOURS" "ROWS" "SIZE" "LICENSE" "FILTER"
    printf "  %s\n" "-------------------------------------------------------------------------------------"
    for e in "${DATA[@]}"; do
        local gb; gb=$(field "$e" 5)
        case "$gb" in ""|"?") gb="?" ;; *) gb="${gb}G" ;; esac
        printf "  %-17s %14s %11s %7s   %-16s %s\n" \
            "$(field "$e" 1)" "$(field "$e" 3)" \
            "$(commas "$(field "$e" 4)")" "$gb" \
            "$(field "$e" 6)" "$(field "$e" 7)"
    done
    printf "  %s\n" "-------------------------------------------------------------------------------------"
    cat <<'EOF'

  PRESETS
    starter   golos_crowd golos_farfield rulibrispeech sova_rudevices  ~25 GB
    all       starter + fleurs_ru                                      ~28 GB
    eval      fleurs_ru                                                 ~3 GB
    scale     yo_cpt_ru                                                ~100 GB

  NOTE ON golos_farfield
    The repo is named "100h_farfield" but holds 12,419 rows in 1.08 GB,
    which works out near 9 hours, not 100. It is a slice, not the full set.
    Confirm after download:  python download_uz.py hours --out /workspace/datasets/ru

  LICENCE
    yo_cpt_ru uses a CUSTOM licence ("yo-cpt-ru"), not CC-BY or CC0.
    Read it before shipping anything. It is also ~100 GB - three times
    everything else here combined - and "CPT" means continued pre-training,
    so its labels may be machine-generated. Check samples before trusting.

  All four bond005 sets are CC-BY-4.0: commercial use is fine.
  fleurs_ru is EVAL ONLY - never put it in your training manifest.
EOF
}

# ---------------------------------------------------------------- selection
SELECTED=()
case "${1:-all}" in
    info)    show_info; exit 0 ;;
    starter) SELECTED=("${STARTER[@]}") ;;
    all)     SELECTED=("${ALLSETS[@]}") ;;
    eval)    SELECTED=("${EVALSET[@]}") ;;
    scale)   SELECTED=("${SCALE[@]}") ;;
    *)       SELECTED=("$@") ;;
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
            g=$(field "$e" 5); g=${g#\~}
            case "$g" in ""|"?") unknown=1 ;; *) need=$(fadd "$need" "$g") ;; esac
        fi
    done
done

echo "  downloading : ${SELECTED[*]}"
echo "  destination : $OUT"
echo "  needs       : ${need} GB$( ((unknown)) && echo "  (+ unknown sizes)")"
echo "  free        : ${free_gb} GB"
echo

if fgt "$need" "$free_gb"; then
    echo "  ** NOT ENOUGH SPACE. Try: ./download_ru.sh starter" >&2
    [ "${MIN_GB:-1}" != "0" ] && exit 1
fi

if [ "${YES:-0}" != "1" ]; then
    read -r -p "  proceed? [y/N] " a
    [[ "$a" =~ ^[Yy] ]] || { echo "cancelled."; exit 0; }
fi

# ------------------------------------------------------------- the downloads
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DOWNLOAD_TIMEOUT=60
[ -n "${HF_TOKEN:-}" ] || echo "  note: no HF_TOKEN - slower, and gated sets will fail."
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
printf "  %-17s %10s %10s\n" "DATASET" "FILES" "SIZE"
printf "  %s\n" "---------------------------------------"
for key in "${SELECTED[@]}"; do
    [ -d "$OUT/$key" ] || continue
    n=$(find "$OUT/$key" -type f \( -iname '*.parquet' -o -iname '*.wav' \
        -o -iname '*.mp3' -o -iname '*.flac' -o -iname '*.opus' \
        -o -iname '*.tar*' -o -iname '*.arrow' \) 2>/dev/null | wc -l)
    sz=$(du -sh "$OUT/$key" 2>/dev/null | cut -f1)
    warn=""; (( n == 0 )) && warn="   <-- NO DATA FILES"
    printf "  %-17s %10s %10s%s\n" "$key" "$n" "$sz" "$warn"
done
printf "  %s\n" "---------------------------------------"
printf "  %-17s %10s %10s\n" "TOTAL" "" "$(du -sh "$OUT" 2>/dev/null | cut -f1)"

echo
(( ${#GATED[@]} )) && {
    echo "  GATED (accept terms, then rerun):"
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
echo
echo "  next:  ./clean.sh ru"
echo "         python diagnose.py /workspace/clean/ru"