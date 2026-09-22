# Running it, language by language

Your layout is already what the script expects:

```
/workspace/datasets/uz/
  _download_report.json      <- ignored
  common_voice_uz/
  uzbek_speech_corpus/
  uzbekvoice_filtered/
```

## Easiest

```bash
cd /workspace
python clean_asr.py --lang uz
```

No path needed. It reads `/workspace/datasets/uz` and writes `/workspace/clean/uz`.

## Several languages at once

```bash
chmod +x clean.sh

./clean.sh uz            # one
./clean.sh uz ru en      # several, in order
./clean.sh all           # every language folder you've downloaded
./clean.sh               # just list what's there
```

Ends with a summary:

```
==================================================
  uz             9 utterances      0.01 hours
  ru         41,203 utterances    112.40 hours
==================================================
```

## Output

```
/workspace/clean/uz/
  common_voice_uz/audio/*.wav      16 kHz mono
  common_voice_uz/manifest.jsonl
  common_voice_uz/report.json
  uzbek_speech_corpus/...
  uzbekvoice_filtered/...
  all_manifest.jsonl               <- feed this to NeMo
  summary.json
```

## Changing settings

```bash
MAX_DUR=30 ./clean.sh uz               # different duration limit
EXTRA="--fmt flac" ./clean.sh uz       # flac, roughly half the size
EXTRA="--force" ./clean.sh uz          # redo everything
ASR_ROOT=/data/sets ./clean.sh uz      # different input location
```

## Resume

Rerunning skips datasets already finished:

```
[common_voice_uz] already clean (3 lines). --force to redo.
```

Safe to interrupt at any point. Your downloads are never modified.

## If a dataset reports 0 kept

Almost always the wrong `--lang` — the charset filter then strips the entire
transcript and every line is dropped as empty. Check `report.json` in that
dataset's folder: the `bad_chars` list will show the alphabet it was actually
written in.