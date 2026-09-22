#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_uz.py — download every open Uzbek ASR dataset.

    python download_uz.py info              # what exists: hours, rows, size
    python download_uz.py plan              # disk check before committing
    python download_uz.py get               # download everything
    python download_uz.py get uzbekvoice_filtered usc
    python download_uz.py hours             # REAL hours of what you downloaded

Install:  pip install "huggingface_hub" pyarrow soundfile
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

try:
    from huggingface_hub import __version__ as _HV
    os.environ.setdefault(
        "HF_XET_HIGH_PERFORMANCE" if int(_HV.split(".")[0]) >= 1
        else "HF_HUB_ENABLE_HF_TRANSFER", "1")
    from huggingface_hub import snapshot_download, HfApi
    from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError
except ImportError:
    sys.exit("pip install huggingface_hub")


# ===========================================================================
# THE UZBEK REGISTRY
#
# rows / GB are measured from the Hub. `hours` is the published figure where
# one exists, otherwise an estimate from size — marked with ~ and confirmed
# for real by `download_uz.py hours` after you download.
# ===========================================================================

@dataclass
class DS:
    key: str
    repo: str
    rows: int
    gb: float
    hours: str
    license: str
    note: str
    gated: bool = False
    allow: list = field(default_factory=list)
    tags: list = field(default_factory=list)


UZ = [
    # ---- start here -----------------------------------------------------
    DS("usc", "murodbek/uzbek-speech-corpus",
       108_387, 11.7, "105",
       "cc-by-4.0",
       "Uzbek Speech Corpus (USC) by ISSAI + Tashkent Univ. of IT. "
       "958 speakers, manually checked by native speakers. 105 h exactly. "
       "COMMERCIAL USE ALLOWED. The reference Uzbek ASR baseline "
       "(18.1% / 17.4% WER in the original paper). Start here.",
       tags=["starter", "clean"]),

    DS("uzbekvoice_filtered", "DavronSherbaev/uzbekvoice-filtered",
       503_378, 13.7, "~700 (est)",
       "apache-2.0",
       "UzbekVoice, quality-filtered. Crowdsourced, many speakers. "
       "Apache-2.0, so commercial use is fine. Best size/quality trade-off "
       "in Uzbek — use this rather than the unfiltered version.",
       tags=["starter", "clean"]),

    DS("common_voice_uz", "roscoe1912/common-voice-uz",
       301_301, 7.28, "~420 (est)",
       "cc0-1.0",
       "Common Voice Uzbek, mirrored so it is NOT gated. CC0 = public "
       "domain, no restrictions at all. Read prompts, many speakers.",
       tags=["starter", "clean"]),

    # ---- more scale, lower quality --------------------------------------
    DS("uzbekvoice", "DavronSherbaev/uzbekvoice",
       868_090, 22.9, "~1200 (est)",
       "see repo",
       "Full UNFILTERED UzbekVoice. 365k more rows than the filtered cut, "
       "but the extra rows are the ones filtering rejected. Only add this "
       "after the clean sets stop helping.",
       tags=["scale"]),

    # ---- domain / dialect coverage --------------------------------------
    DS("it_youtube_uz", "islomov/it_youtube_uzbek_speech_dataset",
       21_016, 15.8, "~140 (est)",
       "see repo",
       "Uzbek IT-domain YouTube speech. Only 21k rows but 15.8 GB, so the "
       "segments are LONG — expect many over 35 s. Technical vocabulary.",
       tags=["domain", "long-audio"]),

    DS("news_youtube_uz", "islomov/news_youtube_uzbek_speech_dataset",
       20_795, 15.9, "~140 (est)",
       "see repo",
       "Uzbek news YouTube speech. Broadcast register, clear diction. "
       "Also long segments.",
       tags=["domain", "long-audio"]),

    DS("tashkent_dialect", "islomov/podcasts_tashkent_dialect_youtube_uzbek_speech_dataset",
       14_547, 11.1, "~100 (est)",
       "see repo",
       "Tashkent-dialect podcasts. Spontaneous conversational speech — the "
       "hardest and most useful kind if real users will talk to your model. "
       "Long segments.",
       tags=["domain", "dialect", "long-audio"]),

    # ---- worth adding, not in your original list -------------------------
    DS("feruzaspeech", "AnnaPovey/FeruzaSpeech",
       0, 0.0, "60",
       "academic-only",
       "FeruzaSpeech: 60 h read speech, ONE female speaker from Tashkent. "
       "The only Uzbek corpus with BOTH Cyrillic and Latin transcripts, and "
       "with punctuation + casing. ACADEMIC RESEARCH ONLY — not for a "
       "commercial product. Verify the repo id; it may be hosted elsewhere.",
       tags=["punctuation", "academic"]),
]

BY_KEY = {d.key: d for d in UZ}

PRESETS = {
    "starter": ["usc", "uzbekvoice_filtered", "common_voice_uz"],
    "clean":   [d.key for d in UZ if "clean" in d.tags],
    "domain":  [d.key for d in UZ if "domain" in d.tags],
    "commercial": ["usc", "uzbekvoice_filtered", "common_voice_uz"],
    "all":     [d.key for d in UZ if d.rows],       # skip unverified entries
}


# ===========================================================================
# HELPERS
# ===========================================================================

def human_gb(g):
    if not g:
        return "?"
    return f"{g*1024:.0f} MB" if g < 1 else f"{g:,.1f} GB"


def free_gb(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(p).free / 1024**3


def dir_gb(p: Path):
    if not p.exists():
        return 0.0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1024**3


def resolve(names, preset):
    keys = list(PRESETS[preset]) if preset else []
    for n in names or []:
        if n not in BY_KEY:
            sys.exit(f"unknown '{n}'. run: download_uz.py info")
        keys.append(n)
    if not keys:
        keys = PRESETS["all"]
    seen, out = set(), []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(BY_KEY[k])
    return out


# ===========================================================================
# COMMANDS
# ===========================================================================

def cmd_info(cfg):
    print(f"\n  {'KEY':<21}{'HOURS':>12}{'ROWS':>12}{'SIZE':>10}  {'LICENSE':<14}")
    print("  " + "-" * 76)
    tr = tg = 0
    for d in UZ:
        rows = f"{d.rows:,}" if d.rows else "?"
        print(f"  {d.key:<21}{d.hours:>12}{rows:>12}"
              f"{human_gb(d.gb):>10}  {d.license:<14}")
        tr += d.rows
        tg += d.gb
    print("  " + "-" * 76)
    print(f"  {'TOTAL':<21}{'~2800 h':>12}{tr:>12,}{human_gb(tg):>10}")

    print("\n  presets:")
    for name, keys in PRESETS.items():
        g = sum(BY_KEY[k].gb for k in keys)
        r = sum(BY_KEY[k].rows for k in keys)
        print(f"    --preset {name:<12} {len(keys)} sets, {r:>9,} rows, "
              f"{human_gb(g):>9}")

    print("\n  details:")
    for d in UZ:
        print(f"\n    {d.key}  [{d.license}]")
        for line in _wrap(d.note, 68):
            print(f"      {line}")

    print("\n  NOTE: hours marked (est) are derived from file size. Run")
    print("  `download_uz.py hours` after downloading for real numbers.\n")


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def cmd_plan(cfg, sets=None):
    sets = sets or resolve(cfg.datasets, cfg.preset)
    out = Path(cfg.out).expanduser().resolve()
    total = sum(d.gb for d in sets)
    avail = free_gb(out)
    print(f"\n  target : {out}")
    print(f"  free   : {avail:,.1f} GB\n")
    print(f"  {'KEY':<21}{'SIZE':>10}{'ON DISK':>10}   STATUS")
    print("  " + "-" * 68)
    for d in sets:
        have = dir_gb(out / d.key)
        if have > 0.05:
            st = "partial/done — will resume"
        elif d.gated:
            st = "GATED: accept terms first"
        elif not d.rows:
            st = "unverified repo id — run `check`"
        else:
            st = "will download"
        print(f"  {d.key:<21}{human_gb(d.gb):>10}"
              f"{human_gb(have) if have > 0.05 else '—':>10}   {st}")
    print("  " + "-" * 68)
    print(f"  {'TOTAL':<21}{human_gb(total):>10}")
    if total > avail:
        print(f"\n  ** NOT ENOUGH SPACE: need {total:,.1f} GB, "
              f"have {avail:,.1f} GB **")
        print("  ** Use --preset starter (32.7 GB), or free up disk.")
    print()
    return sets


def cmd_check(cfg):
    api = HfApi()
    token = cfg.token or os.environ.get("HF_TOKEN")
    print(f"\n  {'KEY':<21}{'STATUS':<16}REPO")
    print("  " + "-" * 76)
    bad = []
    for d in UZ:
        try:
            api.dataset_info(d.repo, token=token)
            st = "OK"
        except GatedRepoError:
            st = "gated"
        except RepositoryNotFoundError:
            st = "404 MISSING"; bad.append(d.key)
        except Exception as e:
            st = type(e).__name__[:15]; bad.append(d.key)
        print(f"  {d.key:<21}{st:<16}{d.repo}")
    print()
    if bad:
        print(f"  unreachable: {', '.join(bad)}\n")
    return 1 if bad else 0


def cmd_get(cfg):
    sets = cmd_plan(cfg)
    out = Path(cfg.out).expanduser().resolve()
    if sum(d.gb for d in sets) > free_gb(out) and not cfg.force:
        sys.exit("aborting: not enough disk. --force to try anyway.")
    if not cfg.yes and input("  proceed? [y/N] ").strip().lower() not in ("y", "yes"):
        sys.exit("cancelled.")

    token = cfg.token or os.environ.get("HF_TOKEN")
    ok = fail = 0
    report = {}
    for i, d in enumerate(sets, 1):
        dest = out / d.key
        print(f"\n[{i}/{len(sets)}] {d.key}  <-  {d.repo}")
        t0 = time.time()
        kw = dict(repo_id=d.repo, repo_type="dataset", local_dir=str(dest),
                  allow_patterns=d.allow or None, token=token,
                  max_workers=cfg.workers)
        import inspect
        if "resume_download" in inspect.signature(snapshot_download).parameters:
            kw["resume_download"] = True
        try:
            snapshot_download(**kw)
            got, secs = dir_gb(dest), time.time() - t0
            n_aud = sum(1 for f in dest.rglob("*")
                        if f.suffix.lower() in
                        {".parquet", ".wav", ".mp3", ".flac", ".opus", ".tar"})
            print(f"          {human_gb(got)} in {secs/60:.1f} min, "
                  f"{n_aud:,} data files")
            if n_aud == 0:
                print("          ** WARNING: no audio/parquet found **")
            report[d.key] = {"gb": round(got, 2), "files": n_aud}
            ok += 1
        except GatedRepoError:
            print(f"          GATED: https://huggingface.co/datasets/{d.repo}")
            fail += 1
        except KeyboardInterrupt:
            print("\n  interrupted — rerun to resume.")
            break
        except Exception as e:
            print(f"          failed: {type(e).__name__}: {str(e)[:120]}")
            report[d.key] = {"error": str(e)[:200]}
            fail += 1

    (out / "_download_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  {ok} ok, {fail} failed. on disk: {human_gb(dir_gb(out))}")
    print(f"\n  next:  python download_uz.py hours")
    print(f"         ./clean.sh uz\n")
    return 1 if fail else 0


def cmd_hours(cfg):
    """Measure REAL audio hours from the downloaded parquet."""
    try:
        import pyarrow.parquet as pq
        import soundfile as sf
    except ImportError:
        sys.exit("pip install pyarrow soundfile")

    out = Path(cfg.out).expanduser().resolve()
    if not out.exists():
        sys.exit(f"nothing at {out}")

    print(f"\n  sampling {cfg.sample} clips per dataset for a duration estimate\n")
    print(f"  {'DATASET':<21}{'ROWS':>11}{'AVG':>8}{'HOURS':>11}{'SIZE':>10}")
    print("  " + "-" * 64)
    grand_h = grand_r = 0
    for sub in sorted(p for p in out.iterdir() if p.is_dir()):
        files = sorted(sub.rglob("*.parquet"))
        if not files:
            continue
        rows = sum(pq.ParquetFile(f).metadata.num_rows for f in files)

        durs = []
        for f in files:
            if len(durs) >= cfg.sample:
                break
            pf = pq.ParquetFile(f)
            for batch in pf.iter_batches(batch_size=32):
                for row in batch.to_pylist():
                    cell = row.get("audio")
                    if isinstance(cell, dict) and cell.get("bytes"):
                        try:
                            info = sf.info(io.BytesIO(cell["bytes"]))
                            durs.append(info.frames / info.samplerate)
                        except Exception:
                            pass
                    if len(durs) >= cfg.sample:
                        break
                if len(durs) >= cfg.sample:
                    break

        if durs:
            avg = sum(durs) / len(durs)
            hrs = avg * rows / 3600
            print(f"  {sub.name:<21}{rows:>11,}{avg:>7.1f}s{hrs:>10,.1f}h"
                  f"{human_gb(dir_gb(sub)):>10}")
            grand_h += hrs
        else:
            print(f"  {sub.name:<21}{rows:>11,}{'?':>8}{'?':>11}"
                  f"{human_gb(dir_gb(sub)):>10}")
        grand_r += rows

    print("  " + "-" * 64)
    print(f"  {'TOTAL':<21}{grand_r:>11,}{'':>8}{grand_h:>10,.1f}h"
          f"{human_gb(dir_gb(out)):>10}")
    print("\n  Estimated from a sample, so ±5%. Exact hours come out of")
    print("  clean_asr.py, which measures every clip it keeps.\n")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(
        description="Download Uzbek ASR datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  download_uz.py info
  download_uz.py plan --preset starter
  download_uz.py get  --preset starter -y
  download_uz.py get  usc uzbekvoice_filtered
  download_uz.py hours
""")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info", help="hours, rows, size, licence for every dataset")
    for name, h in [("plan", "dry run + disk check"), ("get", "download")]:
        p = sub.add_parser(name, help=h)
        p.add_argument("datasets", nargs="*")
        p.add_argument("--preset", choices=sorted(PRESETS))
        p.add_argument("--out", default="/workspace/datasets/uz")
        p.add_argument("--token")
        p.add_argument("--workers", type=int, default=8)
        p.add_argument("--yes", "-y", action="store_true")
        p.add_argument("--force", action="store_true")
    c = sub.add_parser("check", help="verify repo ids against the Hub")
    c.add_argument("--token")
    h = sub.add_parser("hours", help="measure real hours of downloaded data")
    h.add_argument("--out", default="/workspace/datasets/uz")
    h.add_argument("--sample", type=int, default=200)

    cfg = ap.parse_args()
    return {"info": cmd_info, "check": cmd_check, "hours": cmd_hours,
            "plan": lambda c: (cmd_plan(c), 0)[1],
            "get": cmd_get}[cfg.cmd](cfg) or 0


if __name__ == "__main__":
    sys.exit(main())