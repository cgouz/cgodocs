#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_asr.py — give it a path, get back a clean dataset.

Two jobs only:
  1. delete audio longer than 35 seconds
  2. clean characters that don't belong to the language

Output goes to  clean/<lang>/<dataset_name>/

    python clean_asr.py /workspace/datasets/uzbekvoice --lang uz
    python clean_asr.py /workspace/datasets --lang uz          # whole folder
    python clean_asr.py /workspace/datasets/golos --lang ru --max-dur 30

Install:  pip install datasets soundfile numpy librosa
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    import numpy as np
    import soundfile as sf
except ImportError:
    sys.exit("pip install soundfile numpy")


# ===========================================================================
# ALPHABETS — what each language is allowed to contain
# ===========================================================================

OQ, TUT = "\u02BB", "\u02BC"          # ʻ  and  ʼ
LATIN = "abcdefghijklmnopqrstuvwxyz"
CYR = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

ALPHABET = {
    "uz":  LATIN + OQ + TUT,
    "kaa": LATIN + "áóúıńśǵ" + OQ + TUT,
    "ru":  CYR,
    "en":  LATIN,
    "de":  LATIN + "äöüß",
    "fr":  LATIN + "àâæçéèêëîïôœùûüÿ",
    "ar":  "",
    "ko":  "",
    "ja":  "",
    "zh":  "",
}

# Big scripts are checked by codepoint range instead of a character set.
RANGES = {
    "ar": [(0x0600, 0x06FF), (0x0750, 0x077F)],
    "ko": [(0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F)],
    "ja": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF)],
    "zh": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
}

PUNCT = set(" 0123456789.,!?;:'\"()-—–…%")

INVIS = re.compile("[\u00ad\u200b-\u200f\u2060-\u2064\ufeff]")
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f]")
SPACES = str.maketrans({c: " " for c in
                        "\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
                        "\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000"})
QUOTES = str.maketrans({"\u201c": '"', "\u201d": '"', "\u00ab": '"',
                        "\u00bb": '"', "\u2010": "-", "\u2011": "-",
                        "\u2012": "-", "\u2212": "-"})
TAGS = re.compile(r"[<\[(](?:unk|noise|laugh|music|sil|silence|inaudible|\*+)"
                  r"[>\])]", re.IGNORECASE)
APOS = "'`\u00b4\u02b9\u02bd\u2018\u2019\u201b\u2032"
TASHKEEL = re.compile("[\u064b-\u065f\u0670]")
WS = re.compile(r"\s{2,}")
RU_HOMO = str.maketrans({"a": "а", "e": "е", "o": "о", "p": "р", "c": "с",
                         "x": "х", "y": "у", "A": "А", "E": "Е", "O": "О",
                         "P": "Р", "C": "С", "X": "Х"})


def allowed(lang):
    base = set(ALPHABET.get(lang, LATIN))
    return base | {c.upper() for c in base} | PUNCT


def in_script(ch, lang):
    return any(lo <= ord(ch) <= hi for lo, hi in RANGES.get(lang, []))


def clean_text(text, lang, seen_bad):
    """Normalize, then delete every character the language doesn't use."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = INVIS.sub("", text)
    text = CTRL.sub("", text)
    text = text.replace("\ufffd", "")
    text = text.translate(SPACES).translate(QUOTES)
    text = TAGS.sub(" ", text)

    if lang in ("uz", "kaa"):
        out = []
        for ch in text:
            if ch in APOS:
                out.append(OQ if (out and out[-1] in "oOgG") else TUT)
            else:
                out.append(ch)
        text = "".join(out)
    elif lang == "ru":
        text = "".join(c for c in text if c not in APOS)
        # Fix Latin letters standing in for Cyrillic lookalikes, but only
        # inside words that are ALREADY part Cyrillic. A pure-Latin word is
        # a real foreign word, not a typo: mangling "hello" into "ео" is
        # worse than letting the charset filter drop it cleanly.
        def _fix(m):
            w = m.group()
            has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", w))
            return w.translate(RU_HOMO) if has_cyr else w
        text = re.sub(r"\S+", _fix, text)
    elif lang == "ar":
        text = TASHKEEL.sub("", text)
        text = re.sub("[أإآ]", "ا", text).replace("ى", "ي")

    ok = allowed(lang)
    kept = []
    for ch in text:
        if ch in ok or ch.isspace() or in_script(ch, lang):
            kept.append(ch)
        else:
            seen_bad[ch] += 1          # dropped, but recorded for the report
    return WS.sub(" ", "".join(kept)).strip()


# ===========================================================================
# AUDIO
# ===========================================================================

_INDEX_CACHE = {}


def audio_index(base: Path) -> dict:
    """
    basename -> full path, for every audio file under the dataset dir.

    Parquet often stores a RELATIVE path whose root is ambiguous (sometimes
    the dataset dir, sometimes its parent). Looking up by filename is the
    only thing that reliably works across datasets.
    """
    key = str(base)
    if key in _INDEX_CACHE:
        return _INDEX_CACHE[key]
    idx = {}
    for ext in ("wav", "mp3", "flac", "ogg", "opus", "m4a"):
        for f in base.rglob(f"*.{ext}"):
            idx.setdefault(f.name, f)
    _INDEX_CACHE[key] = idx
    return idx


def resolve_audio_path(p: str, base: Path):
    fp = Path(p)
    if fp.is_absolute() and fp.exists():
        return fp
    for cand in (base / p, base.parent / p, Path.cwd() / p):
        if cand.exists():
            return cand
    return audio_index(base).get(fp.name)        # last resort: by filename


def decode(cell, base: Path):
    """Read an audio cell without needing torchcodec."""
    if cell is None:
        return None, None
    if isinstance(cell, str):
        cell = {"path": cell}
    if not isinstance(cell, dict):
        return None, None
    if cell.get("array") is not None and len(cell["array"]):
        return np.asarray(cell["array"], np.float32), cell.get("sampling_rate", 16000)
    if cell.get("bytes"):
        try:
            return sf.read(io.BytesIO(cell["bytes"]), dtype="float32")
        except Exception:
            return None, None
    p = cell.get("path")
    if not p:
        return None, None
    fp = resolve_audio_path(p, base)
    if fp is None:
        return None, None
    try:
        return sf.read(str(fp), dtype="float32")
    except Exception:
        return None, None


def to16k(arr, sr, target=16000):
    arr = np.asarray(arr, np.float32)
    if arr.ndim > 1:
        arr = arr.mean(axis=1)
    if sr and sr != target:
        try:
            import librosa
            arr = librosa.resample(arr, orig_sr=sr, target_sr=target)
        except ImportError:
            idx = np.linspace(0, len(arr) - 1, int(len(arr) * target / sr))
            arr = np.interp(idx, np.arange(len(arr)), arr).astype(np.float32)
    return arr



# ===========================================================================
# IMPORT GUARD
# ===========================================================================

def require_datasets():
    """
    Import the Hugging Face `datasets` library, with a useful error.

    Trap: if you run this from a directory that contains a folder named
    `datasets` (very likely - that's where the data lives) AND the library
    isn't installed, Python treats your data folder as an empty namespace
    package. The error then reads "cannot import name 'load_dataset' from
    'datasets' (unknown location)" instead of "No module named datasets",
    which sends people hunting for the wrong bug.
    """
    import importlib

    # Don't let the current directory win over an installed package.
    here = str(Path.cwd())
    shadow = Path(here) / "datasets"
    removed = []
    if shadow.is_dir() and not (shadow / "__init__.py").exists():
        for entry in ("", ".", here, str(Path(__file__).resolve().parent)):
            while entry in sys.path:
                sys.path.remove(entry)
                removed.append(entry)
        sys.modules.pop("datasets", None)
        importlib.invalidate_caches()

    try:
        mod = importlib.import_module("datasets")
    except ImportError:
        mod = None

    if mod is None or getattr(mod, "__file__", None) is None \
            or not hasattr(mod, "load_dataset"):
        found = list(getattr(mod, "__path__", [])) if mod else []
        print("\n  ERROR: the Hugging Face 'datasets' library is not installed "
              "in this environment.\n", file=sys.stderr)
        if found:
            print(f"  Python instead found your data folder:\n"
                  f"    {found[0]}\n"
                  f"  A directory named 'datasets' with no __init__.py looks "
                  f"like an empty\n  package, which is why the error mentions "
                  f"'unknown location'.\n", file=sys.stderr)
        print("  Fix:\n"
              "    pip install datasets soundfile librosa numpy\n"
              "    # or, inside a uv venv:\n"
              "    uv pip install datasets soundfile librosa numpy\n",
              file=sys.stderr)
        print("  Then rerun. Running from outside /workspace also avoids the\n"
              "  name clash entirely:\n"
              "    cd /workspace/Speech && python /workspace/clean_asr.py "
              "--lang uz\n", file=sys.stderr)
        sys.exit(2)

    for entry in removed:                 # restore sys.path for other imports
        sys.path.append(entry)
    return mod.load_dataset, mod.Audio


# ===========================================================================
# FIND DATASETS
# ===========================================================================

MARKERS = ("*.parquet", "dataset_info.json", "*.arrow", "*.jsonl")


def looks_like_dataset(d: Path, depth: int = 3) -> bool:
    """Data files within `depth` levels. Layouts vary: *.parquet at the
    root, data/*.parquet, or data/train/*.parquet are all common."""
    if not d.is_dir():
        return False
    for lvl in range(depth):
        pat = "*/" * lvl
        for m in MARKERS:
            if next(d.glob(pat + m), None):
                return True
    return False


def find_datasets(root: Path) -> list:
    """One dataset, or a folder containing several."""
    if not root.is_dir():
        return [root]
    subs = [d for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith((".", "_"))
            and looks_like_dataset(d)]
    # Children that are datasets => this is a collection folder. Checking
    # children FIRST stops a parent of N datasets being read as one big one.
    if len(subs) > 1:
        return subs
    if looks_like_dataset(root, depth=1) or (
            len(subs) == 1 and subs[0].name in ("data", "train", "default")):
        return [root]
    return subs or [root]


TEXT_COLS = ("text", "sentence", "transcription", "transcript",
             "normalized_text", "raw_transcription", "answer", "label")



def duration_stats(durs) -> dict:
    """Percentiles plus how many clips each candidate threshold would cut."""
    if not durs:
        return {}
    a = np.sort(np.asarray(durs, dtype=np.float64))
    n = len(a)
    pct = {f"p{q}": round(float(np.percentile(a, q)), 2)
           for q in (1, 5, 25, 50, 75, 95, 99)}
    below = {str(t): int((a < t).sum()) for t in (0.3, 0.5, 1.0, 1.5, 2.0)}
    above = {str(t): int((a > t).sum()) for t in (10, 15, 20, 25, 30, 35)}
    return {"count": n, "total_hours": round(float(a.sum()) / 3600, 3),
            "min": round(float(a[0]), 2), "max": round(float(a[-1]), 2),
            "mean": round(float(a.mean()), 2), "percentiles": pct,
            "n_below": below, "n_above": above}


def print_duration_advice(d: dict, cfg):
    n = d["count"]
    p = d["percentiles"]
    print(f"           durations: min {d['min']}s  p5 {p['p5']}s  "
          f"median {p['p50']}s  p95 {p['p95']}s  max {d['max']}s")
    lo = "  ".join(f"<{t}s: {v:,} ({100*v/n:.1f}%)"
                   for t, v in d["n_below"].items() if v)
    hi = "  ".join(f">{t}s: {v:,} ({100*v/n:.1f}%)"
                   for t, v in d["n_above"].items() if v)
    if lo:
        print(f"           short:  {lo}")
    if hi:
        print(f"           long:   {hi}")




# ===========================================================================
# DIRECT PARQUET READER  (no datasets cache, no disk duplication)
# ===========================================================================

SPLIT_WORDS = ("train", "validation", "valid", "dev", "test")


def find_parquet(src: Path, config, split: str):
    """
    Locate the parquet shards for one config+split.

    This exists because load_dataset() rebuilds a local parquet dataset into
    an Arrow cache under ~/.cache/huggingface, needing as much free space
    again as the data already occupies. Reading the parquet directly avoids
    that entirely.
    """
    files = sorted(src.rglob("*.parquet"))
    if not files:
        return []

    if config and config != "default":
        scoped = [f for f in files
                  if config in f.parts or f.name.startswith(config)]
        if scoped:
            files = scoped

    def split_of(f):
        for part in list(f.parts[:-1]) + [f.name]:
            for w in SPLIT_WORDS:
                if part == w or part.startswith(w + "-") or part.startswith(w + "_"):
                    return w
        return None

    tagged = [(f, split_of(f)) for f in files]
    want = [f for f, sp in tagged if sp == split]
    if want:
        return want
    # requested split absent: fall back to whatever single split exists
    present = {sp for _, sp in tagged if sp}
    if len(present) == 1:
        only = present.pop()
        print(f"           split '{split}' not found, using '{only}'")
        return [f for f, sp in tagged if sp == only]
    if not present:
        return files                      # untagged files: take them all
    for alt in ("train", "test", "validation"):
        if alt in present:
            print(f"           split '{split}' not found, using '{alt}' "
                  f"(available: {', '.join(sorted(present))})")
            return [f for f, sp in tagged if sp == alt]
    return files


def parquet_rows(files, batch_size=32):
    """Stream rows without materializing a whole file in memory."""
    import pyarrow.parquet as pq
    for f in files:
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=batch_size):
            for row in batch.to_pylist():
                yield row


def parquet_info(files):
    """(total_rows, column_names) read from footers only - cheap."""
    import pyarrow.parquet as pq
    total, cols = 0, []
    for f in files:
        pf = pq.ParquetFile(f)
        total += pf.metadata.num_rows
        if not cols:
            cols = list(pf.schema_arrow.names)
    return total, cols


# ===========================================================================
# CONFIG / SPLIT RESOLUTION
# ===========================================================================

# Datasets like FLEURS, Common Voice and Granary hold every language in one
# repo as separate configs. Each project names them differently, so map our
# short code onto the forms actually used in the wild.
CONFIG_ALIASES = {
    "ar":  ["ar_eg", "ar", "ar_sa", "arabic"],
    "en":  ["en_us", "en", "en_gb", "english"],
    "ru":  ["ru_ru", "ru", "russian"],
    "uz":  ["uz_uz", "uz", "uzbek"],
    "kaa": ["kaa", "karakalpak"],
    "ja":  ["ja_jp", "ja", "japanese"],
    "ko":  ["ko_kr", "ko", "korean"],
    "zh":  ["cmn_hans_cn", "zh-CN", "zh_cn", "zh", "yue_hant_hk", "chinese",
            "mandarin"],
    "fr":  ["fr_fr", "fr", "french"],
    "de":  ["de_de", "de", "german"],
}


def pick_config(src: Path, lang: str, explicit):
    """Choose a config for a multi-config dataset, or None if it has one."""
    if explicit:
        return explicit
    try:
        from datasets import get_dataset_config_names
        names = get_dataset_config_names(str(src))
    except Exception:
        return None
    if not names:
        return None
    if len(names) == 1:
        return names[0]

    low = {n.lower(): n for n in names}
    for alias in CONFIG_ALIASES.get(lang, [lang]):
        if alias.lower() in low:
            return low[alias.lower()]
    # prefix match: "ar_eg" for lang "ar"
    for n in names:
        if n.lower().startswith(lang.lower() + "_") or \
           n.lower().startswith(lang.lower() + "-"):
            return n
    raise ValueError(
        f"this dataset has {len(names)} configs and none obviously matches "
        f"'{lang}'.\n           available: {', '.join(names[:12])}"
        f"{' ...' if len(names) > 12 else ''}\n"
        f"           rerun with: EXTRA=\"--config <name>\" ./clean.sh {lang}")


def pick_split(src: Path, config, wanted: str):
    """Fall back sensibly when the requested split doesn't exist."""
    try:
        from datasets import get_dataset_split_names
        splits = get_dataset_split_names(str(src), config)
    except Exception:
        return wanted
    if not splits or wanted in splits:
        return wanted
    for alt in ("train", "training", "validation", "test"):
        if alt in splits:
            print(f"           split '{wanted}' not found, using '{alt}' "
                  f"(available: {', '.join(splits)})")
            return alt
    return splits[0]


# ===========================================================================
# MAIN
# ===========================================================================

def clean_one(src: Path, out: Path, cfg, load_dataset, Audio) -> dict:
    name = src.name
    dst = out / cfg.lang / name
    manifest = dst / "manifest.jsonl"
    if manifest.exists() and not cfg.force:
        n = sum(1 for _ in manifest.open(encoding="utf-8"))
        print(f"  [{name}] already clean ({n:,} lines). --force to redo.")
        return {"name": name, "skipped": True}

    (dst / "audio").mkdir(parents=True, exist_ok=True)

    try:
        config = pick_config(src, cfg.lang, cfg.config)
    except ValueError as e:
        print(f"  [{name}] {e}")
        return {"name": name, "error": True}
    if config:
        print(f"  [{name}] config: {config}")
    # Preferred path: read the parquet straight off disk. No Arrow cache,
    # no second copy, works when the drive is nearly full.
    pq_files = [] if cfg.no_parquet_fast else find_parquet(src, config, cfg.split)
    ds = None
    if pq_files:
        try:
            n_rows, cols = parquet_info(pq_files)
            rows_iter = parquet_rows(pq_files)
            print(f"  [{name}] {len(pq_files)} parquet file(s), "
                  f"{n_rows:,} rows (direct read, no cache)")
        except Exception as e:
            print(f"  [{name}] parquet read failed ({type(e).__name__}), "
                  f"falling back to datasets")
            pq_files = []

    if not pq_files:
        split = pick_split(src, config, cfg.split)
        try:
            ds = load_dataset(str(src), config, split=split,
                              trust_remote_code=cfg.trust_remote_code)
        except Exception as e:
            msg = str(e).splitlines()[0][:150]
            print(f"  [{name}] cannot load: {type(e).__name__}: {msg}")
            if "disk space" in msg.lower():
                print("           load_dataset() copies the data into "
                      "~/.cache/huggingface.")
                print("           Free space, or clear it: "
                      "rm -rf ~/.cache/huggingface/datasets")
            return {"name": name, "error": True}
        cols = ds.column_names
        n_rows = len(ds)
        rows_iter = ds
    tcol = next((c for c in TEXT_COLS if c in cols), None)
    acol = next((c for c in ("audio", "wav", "speech") if c in cols), None)
    if not tcol or not acol:
        print(f"  [{name}] need a text and an audio column, found {cols}")
        return {"name": name, "error": True}

    if ds is not None:
        try:
            ds = ds.cast_column(acol, Audio(decode=False))
            rows_iter = ds
        except Exception:
            pass

    bad = Counter()
    n_keep = n_long = n_short = n_noaudio = n_notext = n_empty = 0
    kept_s = long_s = 0.0
    all_durs = []          # every decodable clip, before duration filtering

    with manifest.open("w", encoding="utf-8") as fh:
        for i, row in enumerate(rows_iter):
            if i and i % 5000 == 0:
                print(f"    [{name}] {i:,}/{n_rows:,} ...", flush=True)

            raw = row.get(tcol)
            if not isinstance(raw, str) or not raw.strip():
                n_notext += 1
                continue

            arr, sr = decode(row.get(acol), src)
            if arr is None or len(arr) == 0:
                n_noaudio += 1
                continue

            arr = to16k(arr, sr or 16000, cfg.sr)
            dur = len(arr) / cfg.sr
            all_durs.append(dur)

            # ---- job 1: kill anything over the limit ----------------------
            if dur > cfg.max_dur:
                n_long += 1
                long_s += dur
                continue
            if dur < cfg.min_dur:
                n_short += 1
                continue

            # ---- job 2: clean the characters ------------------------------
            text = clean_text(raw, cfg.lang, bad)
            if not text:
                n_empty += 1
                continue

            p = dst / "audio" / f"{name}_{n_keep:08d}.{cfg.fmt}"
            sf.write(p, arr, cfg.sr,
                     subtype="PCM_16" if cfg.fmt == "wav" else None)
            fh.write(json.dumps({"audio_filepath": str(p),
                                 "duration": round(dur, 3),
                                 "text": text}, ensure_ascii=False) + "\n")
            n_keep += 1
            kept_s += dur

    dstats = duration_stats(all_durs)
    stats = {"name": name, "kept": n_keep, "durations": dstats,
             "dropped_too_long": n_long, "dropped_too_short": n_short,
             "dropped_no_audio": n_noaudio,
             "dropped_no_text": n_notext, "dropped_empty_text": n_empty,
             "kept_hours": round(kept_s / 3600, 3),
             "removed_hours": round(long_s / 3600, 3),
             "chars_removed": sum(bad.values()),
             "bad_chars": [{"char": c, "codepoint": f"U+{ord(c):04X}",
                            "count": n} for c, n in bad.most_common(50)],
             "manifest": str(manifest)}
    (dst / "report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  [{name}] kept {n_keep:,} ({kept_s/3600:.2f} h) | "
          f">{cfg.max_dur:g}s: {n_long:,} | short: {n_short:,} | "
          f"no audio: {n_noaudio:,} | no text: {n_notext + n_empty:,} | "
          f"chars removed: {sum(bad.values()):,}")
    if bad:
        top = ", ".join(f"{c!r}({n})" for c, n in bad.most_common(6))
        print(f"           removed chars: {top}")
    if dstats and cfg.show_durations:
        print_duration_advice(dstats, cfg)
    return stats


def main():
    ap = argparse.ArgumentParser(
        description="Remove long audio and unsupported characters.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  clean_asr.py /workspace/datasets/uzbekvoice --lang uz
  clean_asr.py /workspace/datasets --lang uz        # every dataset in folder
  clean_asr.py /workspace/datasets/golos --lang ru --max-dur 30

output: clean/<lang>/<dataset>/audio/*.wav + manifest.jsonl
""")
    ap.add_argument("path", nargs="?", default=None,
                    help="dataset folder, or a folder of them. "
                         "Omit to use <ASR_ROOT>/<lang> (default "
                         "/workspace/datasets/<lang>)")
    ap.add_argument("--lang", required=True, choices=sorted(ALPHABET))
    ap.add_argument("--out", default=None,
                    help="root output dir (default: <ASR_ROOT>/../clean)")
    ap.add_argument("--max-dur", type=float, default=35.0)
    ap.add_argument("--min-dur", type=float, default=0.5,
                    help="drop anything shorter (default 0.5 s). Below ~0.5 s "
                         "clips are usually truncated words, and very short "
                         "audio can make CTC loss diverge.")
    ap.add_argument("--no-duration-stats", dest="show_durations",
                    action="store_false", default=True,
                    help="skip the duration distribution printout")
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--fmt", default="wav", choices=["wav", "flac"])
    ap.add_argument("--split", default="train")
    ap.add_argument("--config", default=None,
                    help="config name for multi-language repos (fleurs, "
                         "common voice). Auto-detected from --lang if omitted.")
    ap.add_argument("--trust-remote-code", action="store_true")
    ap.add_argument("--no-parquet-fast", action="store_true",
                    help="disable direct parquet reading and use "
                         "load_dataset() (needs lots of free disk)")
    ap.add_argument("--force", action="store_true")
    cfg = ap.parse_args()

    # `clean_asr.py --lang uz` with no path: look where the downloader puts
    # things. Override the base with ASR_ROOT=/some/other/dir.
    load_dataset, Audio = require_datasets()

    asr_root = Path(os.environ.get("ASR_ROOT", "/workspace/datasets"))
    if cfg.path is None:
        root = (asr_root / cfg.lang).expanduser().resolve()
        if not root.exists():
            sys.exit(f"not found: {root}\n"
                     f"pass a path explicitly, or set ASR_ROOT=<dir> so that "
                     f"<dir>/{cfg.lang} exists.")
    else:
        root = Path(cfg.path).expanduser().resolve()
        if not root.exists():
            sys.exit(f"not found: {root}")

    if cfg.out is None:
        # /workspace/datasets/uz  ->  /workspace/clean/uz
        base = asr_root if cfg.path is None else root.parent
        out = (base.parent / "clean").expanduser().resolve()
    else:
        out = Path(cfg.out).expanduser().resolve()

    sets = find_datasets(root)
    print(f"\n  lang={cfg.lang}  max-dur={cfg.max_dur}s  "
          f"datasets={len(sets)}  ->  {out / cfg.lang}\n")

    all_stats, total_keep, total_h = [], 0, 0.0
    for s in sets:
        st = clean_one(s, out, cfg, load_dataset, Audio)
        all_stats.append(st)
        total_keep += st.get("kept", 0)
        total_h += st.get("kept_hours", 0.0)

    (out / cfg.lang / "summary.json").write_text(
        json.dumps(all_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  TOTAL kept: {total_keep:,} utterances, {total_h:.2f} hours")
    print(f"  clean data: {out / cfg.lang}")

    # one manifest covering everything cleaned for this language
    merged = out / cfg.lang / "all_manifest.jsonl"
    with merged.open("w", encoding="utf-8") as fh:
        for m in sorted((out / cfg.lang).glob("*/manifest.jsonl")):
            fh.writelines(m.open(encoding="utf-8"))
    print(f"  manifest:   {merged}\n")


if __name__ == "__main__":
    main()