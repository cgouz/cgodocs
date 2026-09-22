#!/usr/bin/env bash
# download_uz.sh — download all 7 open Uzbek ASR datasets.
#
#   ./download_uz.sh              # info table, then download everything
#   ./download_uz.sh info         # just show the table, download nothing
#   ./download_uz.sh starter      # only the 3 clean, commercially-usable sets
#   ./download_uz.sh usc common_voice_uz      # pick individual sets
#
# Options (environment variables):
#   OUT=/workspace/datasets/uz    where to put it
#   JOBS=3                        concurrent downloads (>3 gets HTTP 429)
#   MIN_GB=100                    refuse to start below this much free space
#   YES=1                         skip the confirmation prompt
set -uo pipefail

OUT=${OUT:-/workspace/datasets/uz}
LOGS=${LOGS:-/workspace/logs/uz}
JOBS=${JOBS:-3}
MIN_GB=${MIN_GB:-100}

# key | repo | hours | rows | GB | licence
DATA=(
"usc|murodbek/uzbek-speech-corpus|105|108387|11.7|cc-by-4.0"
"uzbekvoice_filtered|DavronSherbaev/uzbekvoice-filtered|~700|503378|13.7|apache-2.0"
"common_voice_uz|roscoe1912/common-voice-uz|~420|301301|7.3|cc0-1.0"
"uzbekvoice|DavronSherbaev/uzbekvoice|~1200|868090|22.9|see repo"
"it_youtube_uz|islomov/it_youtube_uzbek_speech_dataset|~140|21016|15.8|see repo"
"news_youtube_uz|islomov/news_youtube_uzbek_speech_dataset|~140|20795|15.9|see repo"
"tashkent_dialect|islomov/podcasts_tashkent_dialect_youtube_uzbek_speech_dataset|~100|14547|11.1|see repo"
)

STARTER=(usc uzbekvoice_filtered common_voice_uz)

field() { echo "$1" | cut -d'|' -f"$2"; }

# awk, not bc: bc is not installed on many minimal images.
fadd() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.1f", a+b}'; }
fgt()  { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>b)}'; }
# thousands separators without depending on a grouping locale
commas() { echo "$1" | sed -E ':a;s/([0-9])([0-9]{3})($|,)/\1,\2\3/;ta'; }

show_info() {
    printf "\n  %-21s %8s %11s %8s   %s\n" "KEY" "HOURS" "ROWS" "SIZE" "LICENSE"
    printf "  %s\n" "---------------------------------------------------------------------"
    local tr=0 tg=0
    for e in "${DATA[@]}"; do
        printf "  %-21s %8s %11s %7sG   %s\n" \
            "$(field "$e" 1)" "$(field "$e" 3)" \
            "$(commas "$(field "$e" 4)")" "$(field "$e" 5)" "$(field "$e" 6)"
        tr=$(( tr + $(field "$e" 4) ))
        tg=$(fadd "$tg" "$(field "$e" 5)")
    done
    printf "  %s\n" "---------------------------------------------------------------------"
    printf "  %-21s %8s %11s %7sG\n" "TOTAL" "~2800" "$(commas $tr)" "$tg"
    echo
    echo "  usc / uzbekvoice_filtered / common_voice_uz allow COMMERCIAL use."
    echo "  The 3 youtube sets have LONG segments - expect drops at 35s."
    echo "  Hours marked ~ are estimated from size, not published figures."
    echo
}

# ---------------------------------------------------------------- selection
SELECTED=()
case "${1:-all}" in
    info)    show_info; exit 0 ;;
    all|"")  for e in "${DATA[@]}"; do SELECTED+=("$(field "$e" 1)"); done ;;
    starter) SELECTED=("${STARTER[@]}") ;;
    *)       SELECTED=("$@") ;;
esac

show_info

# ------------------------------------------------------------- sanity check
if ! command -v hf >/dev/null 2>&1; then
    echo "ERROR: 'hf' not found. Run: uv pip install huggingface_hub" >&2
    exit 1
fi

mkdir -p "$OUT" "$LOGS"
free_gb=$(df -BG --output=avail "$OUT" | tail -1 | tr -dc '0-9')
need=0
for key in "${SELECTED[@]}"; do
    for e in "${DATA[@]}"; do
        [ "$(field "$e" 1)" = "$key" ] && need=$(fadd "$need" "$(field "$e" 5)")
    done
done

echo "  downloading : ${SELECTED[*]}"
echo "  destination : $OUT"
echo "  needs       : ${need} GB      free: ${free_gb} GB"
echo

if fgt "$need" "$free_gb"; then
    echo "  ** NOT ENOUGH SPACE. Try: ./download_uz.sh starter" >&2
    echo "  ** or override: MIN_GB=0 ./download_uz.sh" >&2
    [ "${MIN_GB}" != "0" ] && exit 1
fi

if [ "${YES:-0}" != "1" ]; then
    read -r -p "  proceed? [y/N] " a
    [[ "$a" =~ ^[Yy] ]] || { echo "cancelled."; exit 0; }
fi

# ------------------------------------------------------------- the downloads
# Each `hf download` already opens ~8 connections internally. Running all 7
# at once means ~56 sockets, which triggers HTTP 429 and thrashes the disk.
# So cap concurrency, log separately, and CHECK EVERY EXIT CODE - plain
# `wait` ignores them and would report success on a failed download.
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DOWNLOAD_TIMEOUT=60

declare -A PID2KEY
FAILED=()
START=$(date +%s)

for key in "${SELECTED[@]}"; do
    repo=""
    for e in "${DATA[@]}"; do
        [ "$(field "$e" 1)" = "$key" ] && repo=$(field "$e" 2)
    done
    if [ -z "$repo" ]; then
        echo "  ! unknown dataset '$key', skipping"
        continue
    fi

    while (( $(jobs -rp | wc -l) >= JOBS )); do wait -n || true; done

    echo "  -> $key  ($repo)"
    hf download "$repo" --repo-type dataset --local-dir "$OUT/$key" \
        > "$LOGS/$key.log" 2>&1 &
    PID2KEY[$!]=$key
done

for pid in "${!PID2KEY[@]}"; do
    key=${PID2KEY[$pid]}
    if wait "$pid"; then
        sz=$(du -sh "$OUT/$key" 2>/dev/null | cut -f1)
        echo "  OK    $key  ($sz)"
    else
        echo "  FAIL  $key  -- tail -20 $LOGS/$key.log"
        FAILED+=("$key")
    fi
done

# ------------------------------------------------------------- verification
echo
printf "  %-21s %10s %10s\n" "DATASET" "FILES" "SIZE"
printf "  %s\n" "-------------------------------------------------"
for key in "${SELECTED[@]}"; do
    [ -d "$OUT/$key" ] || continue
    n=$(find "$OUT/$key" -type f \( -iname '*.parquet' -o -iname '*.wav' \
        -o -iname '*.mp3' -o -iname '*.flac' -o -iname '*.opus' \
        -o -iname '*.tar' -o -iname '*.arrow' \) 2>/dev/null | wc -l)
    sz=$(du -sh "$OUT/$key" 2>/dev/null | cut -f1)
    warn=""; (( n == 0 )) && warn="   <-- NO DATA FILES"
    printf "  %-21s %10s %10s%s\n" "$key" "$n" "$sz" "$warn"
done
printf "  %s\n" "-------------------------------------------------"
printf "  %-21s %10s %10s\n" "TOTAL" "" "$(du -sh "$OUT" 2>/dev/null | cut -f1)"

MINS=$(( ($(date +%s) - START) / 60 ))
echo
if (( ${#FAILED[@]} )); then
    echo "  FAILED: ${FAILED[*]}"
    echo "  Rerun the same command - finished files are skipped."
    exit 1
fi
echo "  ALL ${#SELECTED[@]} DATASETS DONE in ${MINS} min"
echo
echo "  next:  ./clean.sh uz"