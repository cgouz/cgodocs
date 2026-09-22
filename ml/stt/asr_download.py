#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ru_download.py — download Russian ASR datasets from Hugging Face.

Built for NeMo / Nemotron fine-tuning. Resumable, disk-aware, and it tells you
what it is going to do before it eats 200 GB of your drive.

    python ru_download.py list                         # what's available
    python ru_download.py plan  --preset starter       # dry run, show sizes
    python ru_download.py get   --preset starter       # actually download
    python ru_download.py get   golos_crowd rulibrispeech
    python ru_download.py manifest --out train.jsonl   # build NeMo manifest

Install:
    pip install "huggingface_hub[hf_transfer]" datasets soundfile librosa tqdm
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Faster transfers. The variable was renamed in huggingface_hub 1.0, so set
# whichever one this install actually understands.
try:
    from huggingface_hub import __version__ as _HUB_V
    if int(_HUB_V.split(".")[0]) >= 1:
        os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
    else:
        os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
except Exception:
    pass

try:
    from huggingface_hub import snapshot_download, HfApi
    from huggingface_hub.utils import (
        GatedRepoError, RepositoryNotFoundError, HfHubHTTPError,
    )
except ImportError:
    sys.exit("pip install huggingface_hub")


# ===========================================================================
# REGISTRY
# ===========================================================================

@dataclass
class DS:
    key: str
    repo: str                       # HF repo id
    hours: str
    license: str
    note: str
    audio: bool = True              # False = transcripts/manifests only, no sound
    labels: bool = True             # False = raw audio, no transcripts
    gated: bool = False             # needs you to accept terms on the website
    size_gb: float = 0.0            # rough on-disk estimate
    configs: list = field(default_factory=list)
    allow: list = field(default_factory=list)   # glob filter, [] = everything
    tags: list = field(default_factory=list)


RU = [
    # 18,780 rows | 2.27 GB
    DS("golos_crowd", "bond005/sberdevices_golos_10h_crowd", "10", "cc-by-4.0",
       "Small Golos crowd slice. Start here to test your pipeline.",
       size_gb=1.5, tags=["starter"]),

    # 12,419 rows | 1.08 GB
    DS("golos_farfield", "bond005/sberdevices_golos_100h_farfield", "100", "cc-by-4.0",
       "Far-field / smart-speaker audio. Robustness to room noise.",
       size_gb=11, tags=["starter"]),

    # 57,224 rows | 11.1 GB
    DS("rulibrispeech", "bond005/rulibrispeech", "92", "cc-by-4.0",
       "Russian LibriSpeech. Clean read speech.", size_gb=9, tags=["starter"]),

    # 54,586 rows | 10.7 GB
    DS("sova_rudevices", "bond005/sova_rudevices", "75", "cc-by-4.0",
       "SOVA device recordings. Spontaneous speech.", size_gb=8, tags=["starter"]),
] # All Russian: ~143k rows, ~35 GB

EN = [
    # 584,734 rows
    DS("librispeech", "openslr/librispeech_asr", "960", "cc-by-4.0",
       "THE English baseline. Read audiobooks, clean labels. Every paper "
       "reports on it. Subsets: clean.100 / clean.360 / other.500.",
       size_gb=60, tags=["starter"]),

    # 14,654,760 rows
    DS("loquacious", "speechbrain/LoquaciousSet", "25000", "mixed-permissive",
       "25k hours of diverse English, curated for research AND commercial "
       "use. Blends LibriSpeech, CommonVoice, VoxPopuli, People's Speech, "
       "YODAS. Subsets: small / medium / large / clean. Best default if you "
       "need scale without a license headache.",
       size_gb=0, configs=["small", "medium", "large", "clean"], tags=["scale"]),

    # 8,051,212 rows | certified CC-BY-SA-4.0
    DS("peoples_speech", "MLCommons/peoples_speech", "30000", "cc-by-sa-4.0",
       "30k hours scraped from the open internet. Labels are noisy - use the "
       "'clean' config, not 'dirty'.",
       size_gb=0, configs=["clean", "clean_sa", "dirty", "dirty_sa"], tags=["scale"]),

    # 768,120 | 878 GB
    # DS("fleurs_en", "google/fleurs", "12", "cc-by-4.0",
    #    "FLEURS English. EVAL ONLY.", size_gb=3,
    #    configs=["en_us"], tags=["eval"]),
] # All English without fleurs: ~23M rows, ~1.2 TB

UZ = [
    # 503,378 rows | 13.7 GB
    DS("uzbekvoice_filtered", "DavronSherbaev/uzbekvoice-filtered", "?", "see repo",
       "Filtered UzbekVoice. Best starting point for Uzbek.",
       size_gb=0, tags=["starter"]),

    # 868,090 rows | 22.9 GB
    DS("uzbekvoice", "DavronSherbaev/uzbekvoice", "?", "see repo",
       "Full unfiltered UzbekVoice.", size_gb=0),

    # 108,387 rows | 11.7 GB
    DS("uzbek_speech_corpus", "murodbek/uzbek-speech-corpus", "?", "see repo",
       "General Uzbek speech corpus.", size_gb=0, tags=["starter"]),

    # 301,301 rows | 7.28 GB
    DS("common_voice_uz", "roscoe1912/common-voice-uz", "?", "cc0-1.0",
       "Common Voice Uzbek mirror (not gated).", size_gb=0, tags=["starter"]),

    # 21,016 rows | 15.8 GB
    DS("it_youtube_uz", "islomov/it_youtube_uzbek_speech_dataset", "?", "see repo",
       "Uzbek IT-domain YouTube speech.", size_gb=0),

    # 20,795 rows | 15.9 GB
    DS("news_youtube_uz", "islomov/news_youtube_uzbek_speech_dataset", "?", "see repo",
       "Uzbek news YouTube speech.", size_gb=0),

    # 14,547 rows | 11.1 GB
    DS("tashkent_dialect", "islomov/podcasts_tashkent_dialect_youtube_uzbek_speech_dataset",
       "?", "see repo", "Tashkent-dialect podcasts. Dialect coverage.", size_gb=0),
] # All: ~1.8M rows, ~88 GB


KO = [
    # 22,720 rows | 2.88 GB
    DS("zeroth_korean", "kresnik/zeroth_korean", "51.6", "cc-by-4.0",
       "Zeroth-Korean. The main freely-licensed Korean ASR set: 22k "
       "utterances, 105 speakers. Parquet, no loading script.",
       size_gb=6, tags=["starter"]),

    # 22,720 rows | 2.87 GB
    DS("zeroth_korean_alt", "Bingsu/zeroth-korean", "51.6", "cc-by-4.0",
       "Mirror of Zeroth-Korean. Use if kresnik's copy misbehaves.",
       size_gb=6),

    # DS("fleurs_ko", "google/fleurs", "12", "cc-by-4.0",
    #    "FLEURS Korean. EVAL ONLY.", size_gb=3,
    #    configs=["ko_kr"], tags=["starter", "eval"]),
    # DS("yodas_ko", "espnet/yodas", "large", "cc-by-3.0",
    #    "Raw YouTube Korean. Noisy auto-captions.",
    #    size_gb=0, allow=["data/ko000/**"]),
] # All Korean: ~45k rows, ~5.7 GB

ZH = [
    DS("aishell1", "AISHELL/AISHELL-1", "178", "apache-2.0",
       "AISHELL-1. The standard Mandarin baseline, 400 speakers. "
       "Verify the repo id with `check` - several mirrors exist.",
       size_gb=18, tags=["starter"]),
    DS("wenetspeech", "wenet-e2e/wenetspeech", "10000", "cc-by-4.0",
       "WenetSpeech. 10k hours Mandarin from YouTube + podcasts. "
       "Subsets S(100h) / M(1000h) / L(10000h).",
       size_gb=0, configs=["S", "M", "L"], tags=["scale"]),
    DS("common_voice_zh", "mozilla-foundation/common_voice_17_0", "~200", "cc0-1.0",
       "Common Voice Mandarin (zh-CN). GATED.",
       gated=True, size_gb=15, configs=["zh-CN"], tags=["starter"]),
    DS("fleurs_zh", "google/fleurs", "12", "cc-by-4.0",
       "FLEURS Mandarin. EVAL ONLY.", size_gb=3,
       configs=["cmn_hans_cn"], tags=["starter", "eval"]),
    DS("yodas_zh", "espnet/yodas", "large", "cc-by-3.0",
       "Raw YouTube Mandarin.", size_gb=0, allow=["data/zh000/**"]),
]

JA = [
    DS("reazonspeech", "reazon-research/reazonspeech", "35000", "see-terms",
       "ReazonSpeech - by far the largest Japanese corpus, from TV audio. "
       "LEGAL: you must agree to use it solely under Japanese Copyright Act "
       "Article 30-4. Needs trust_remote_code=True. Sizes: tiny/small/"
       "medium/large/all. Start with 'small'.",
       size_gb=0, configs=["tiny", "small", "medium", "large", "all"],
       tags=["starter", "scale"]),
    DS("common_voice_ja", "mozilla-foundation/common_voice_17_0", "~50", "cc0-1.0",
       "Common Voice Japanese. GATED.",
       gated=True, size_gb=5, configs=["ja"], tags=["starter"]),
    DS("fleurs_ja", "google/fleurs", "12", "cc-by-4.0",
       "FLEURS Japanese. EVAL ONLY.", size_gb=3,
       configs=["ja_jp"], tags=["starter", "eval"]),
    DS("yodas_ja", "espnet/yodas", "large", "cc-by-3.0",
       "Raw YouTube Japanese.", size_gb=0, allow=["data/ja000/**"]),
]

KAA = [
    DS("karakalpak_corpus", "atikuwu/karakalpak-speech-corpus", "107", "see repo",
       "THE Karakalpak ASR dataset - first open community-crowdsourced corpus "
       "for kaa, 200+ contributors from Karakalpakstan. Basically your only "
       "real option, and it is a good one.",
       size_gb=0, tags=["starter"]),
]

FR = [
    DS("mls_fr", "facebook/multilingual_librispeech", "1076", "cc-by-4.0",
       "Multilingual LibriSpeech French. Largest clean French read speech.",
       size_gb=90, configs=["french"], tags=["starter", "scale"]),
    DS("common_voice_fr", "mozilla-foundation/common_voice_17_0", "~1000", "cc0-1.0",
       "Common Voice French. Big and accent-diverse. GATED.",
       gated=True, size_gb=70, configs=["fr"], tags=["starter"]),
    DS("voxpopuli_fr", "facebook/voxpopuli", "211", "cc0-1.0",
       "European Parliament French. Public domain.",
       size_gb=15, configs=["fr"], tags=["starter"]),
    DS("fleurs_fr", "google/fleurs", "12", "cc-by-4.0",
       "FLEURS French. EVAL ONLY.", size_gb=3,
       configs=["fr_fr"], tags=["starter", "eval"]),
    DS("granary_fr", "nvidia/Granary", "large", "cc-by-4.0",
       "NO AUDIO - manifests only.", audio=False, size_gb=4,
       allow=["fr/**", "*.md"]),
    DS("yodas_granary_fr", "espnet/yodas-granary", "thousands", "cc-by-3.0",
       "Granary French labels WITH audio embedded.",
       size_gb=0, configs=["French"], allow=["data/fr*/**", "*.md"], tags=["scale"]),
]

DE = [
    DS("mls_de", "facebook/multilingual_librispeech", "1966", "cc-by-4.0",
       "Multilingual LibriSpeech German. The biggest clean German set.",
       size_gb=160, configs=["german"], tags=["starter", "scale"]),
    DS("common_voice_de", "mozilla-foundation/common_voice_17_0", "~1400", "cc0-1.0",
       "Common Voice German - one of the largest CV languages. GATED.",
       gated=True, size_gb=95, configs=["de"], tags=["starter"]),
    DS("voxpopuli_de", "facebook/voxpopuli", "282", "cc0-1.0",
       "European Parliament German. Public domain.",
       size_gb=18, configs=["de"], tags=["starter"]),
    DS("fleurs_de", "google/fleurs", "12", "cc-by-4.0",
       "FLEURS German. EVAL ONLY.", size_gb=3,
       configs=["de_de"], tags=["starter", "eval"]),
    DS("granary_de", "nvidia/Granary", "large", "cc-by-4.0",
       "NO AUDIO - manifests only.", audio=False, size_gb=4,
       allow=["de/**", "*.md"]),
    DS("yodas_granary_de", "espnet/yodas-granary", "thousands", "cc-by-3.0",
       "Granary German labels WITH audio. German is one of the best-covered.",
       size_gb=0, configs=["German"], allow=["data/de*/**", "*.md"], tags=["scale"]),
]

AR = [
    DS("common_voice_ar", "mozilla-foundation/common_voice_17_0", "~150", "cc0-1.0",
       "Common Voice Arabic. Mostly MSA. GATED.",
       gated=True, size_gb=12, configs=["ar"], tags=["starter"]),
    DS("fleurs_ar", "google/fleurs", "12", "cc-by-4.0",
       "FLEURS Arabic (Egyptian). EVAL ONLY.", size_gb=3,
       configs=["ar_eg"], tags=["starter", "eval"]),
    DS("masc", "pain/MASC", "1000", "cc-by-4.0",
       "Massive Arabic Speech Corpus, ~1000h from YouTube across dialects. "
       "Verify the repo id with `check`.",
       size_gb=0, tags=["scale"]),
    DS("yodas_ar", "espnet/yodas", "large", "cc-by-3.0",
       "Raw YouTube Arabic. Heavy dialect mixing.",
       size_gb=0, allow=["data/ar000/**"]),
]

LANGS = {"en": EN, "ru": RU, "uz": UZ, "kaa": KAA,
         "ko": KO, "zh": ZH, "ja": JA,
         "fr": FR, "de": DE, "ar": AR}
REGISTRY: list = []
BY_KEY: dict = {}
PRESETS: dict = {}


def set_lang(lang: str):
    """Point the module at one language's registry and build its presets."""
    global REGISTRY, BY_KEY, PRESETS
    if lang not in LANGS:
        sys.exit(f"unknown language '{lang}'. have: {', '.join(LANGS)}")
    REGISTRY = LANGS[lang]
    BY_KEY = {d.key: d for d in REGISTRY}

    usable = [d for d in REGISTRY if d.audio and d.labels]
    PRESETS = {
        "starter": [d.key for d in REGISTRY if "starter" in d.tags] or
                   [d.key for d in usable[:3]],
        "eval":    [d.key for d in REGISTRY if "eval" in d.tags],
        "scale":   [d.key for d in REGISTRY if "scale" in d.tags],
        "all":     [d.key for d in usable],
    }
    PRESETS = {k: v for k, v in PRESETS.items() if v}


def resolve(names, preset, with_manifests=False) -> list:
    keys = []
    if preset:
        if preset not in PRESETS:
            sys.exit(f"unknown preset '{preset}'. have: {', '.join(PRESETS)}")
        keys += PRESETS[preset]
    for n in names or []:
        if n not in BY_KEY:
            sys.exit(f"unknown dataset '{n}'. run: asr_download.py list --lang <l>")
        keys.append(n)
    if not keys:
        sys.exit("nothing selected. use --preset starter, or name datasets.")

    seen, out = set(), []
    for k in keys:                       # dedupe, keep order
        if k in seen:
            continue
        seen.add(k)
        d = BY_KEY[k]
        named = k in (names or [])
        # Supervised STT needs BOTH sound and transcripts. Never silently hand
        # someone a repo that is missing one half.
        if not d.audio and not with_manifests:
            if named:
                print(f"  ! skipping '{k}': no AUDIO in this repo. "
                      f"--with-manifests to force.")
            continue
        if not d.labels and not with_manifests:
            if named:
                print(f"  ! skipping '{k}': no TRANSCRIPTS in this repo "
                      f"(pretraining only). --with-manifests to force.")
            continue
        out.append(d)
    if not out:
        sys.exit("nothing left: every selected repo is missing audio or labels.")
    return out


# ===========================================================================
# HELPERS
# ===========================================================================

def human(gb: float, zero: str = "unknown") -> str:
    if gb <= 0:
        return zero
    return f"{gb*1024:.0f} MB" if gb < 1 else f"{gb:.0f} GB"


def free_gb(path: Path) -> float:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free / 1024**3


def dir_gb(path: Path) -> float:
    if not path.exists():
        return 0.0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024**3


AUDIO_EXT = {".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a", ".parquet", ".tar"}


def dur_str(hours: float) -> str:
    """Hours are useless for tiny sets — fall back to minutes or seconds."""
    if hours >= 1:
        return f"{hours:,.1f} h"
    if hours * 60 >= 1:
        return f"{hours*60:.1f} min"
    return f"{hours*3600:.0f} s"


# ===========================================================================
# COMMANDS
# ===========================================================================

def cmd_list(cfg):
    print(f"\n  language: {cfg.lang}   "
          f"(others: {', '.join(k for k in LANGS if k != cfg.lang)})")
    print(f"\n  {'KEY':<21}{'AUDIO':<7}{'TEXT':<7}{'HOURS':<11}{'SIZE':<9}REPO")
    print("  " + "-" * 95)
    for d in REGISTRY:
        flag = " [GATED]" if d.gated else ""
        print(f"  {d.key:<21}{('yes' if d.audio else 'NO'):<7}"
              f"{('yes' if d.labels else 'NO'):<7}{d.hours:<11}"
              f"{human(d.size_gb):<9}{d.repo}{flag}")
    print("\n  presets:")
    for name, keys in PRESETS.items():
        total = sum(BY_KEY[k].size_gb for k in keys)
        print(f"    --preset {name:<13} {len(keys)} sets, ~{human(total)}")
    print("\n  details:")
    for d in REGISTRY:
        print(f"    {d.key}: {d.note}")
    print("\n  Rows with AUDIO=NO or TEXT=NO are skipped by default: supervised")
    print("  STT needs both halves. Override with --with-manifests.\n")


def cmd_plan(cfg, sets=None):
    sets = sets or resolve(cfg.datasets, cfg.preset,
                       getattr(cfg, 'with_manifests', False))
    out = Path(cfg.out).expanduser().resolve()
    total = sum(d.size_gb for d in sets)
    avail = free_gb(out)

    print(f"\n  target : {out}")
    print(f"  free   : {avail:.0f} GB\n")
    print(f"  {'KEY':<22}{'EST. SIZE':<12}{'ON DISK':<11}STATUS")
    print("  " + "-" * 78)
    for d in sets:
        have = dir_gb(out / d.key)
        if have > 0.05:
            status = "partial/done — will resume"
        elif d.gated:
            status = "GATED: accept terms on the HF page first"
        elif d.size_gb == 0:
            status = "size unknown — filtered download"
        else:
            status = "will download"
        print(f"  {d.key:<22}{human(d.size_gb):<12}{human(have, chr(8212)):<11}{status}")

    print("  " + "-" * 78)
    print(f"  {'TOTAL':<22}{human(total):<12}{human(dir_gb(out), chr(8212)):<11}")
    if total > avail:
        print(f"\n  ** NOT ENOUGH SPACE: need ~{total:.0f} GB, have {avail:.0f} GB **")
    print()
    return sets


def cmd_get(cfg):
    sets = cmd_plan(cfg)
    out = Path(cfg.out).expanduser().resolve()

    if sum(d.size_gb for d in sets) > free_gb(out) and not cfg.force:
        sys.exit("aborting: not enough disk. use --force to try anyway.")
    if not cfg.yes:
        if input("  proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            sys.exit("cancelled.")

    token = cfg.token or os.environ.get("HF_TOKEN") or os.environ.get("HF_HUB_TOKEN")
    if any(d.gated for d in sets) and not token:
        print("\n  warning: gated datasets selected but no token found.")
        print("  run `hf auth login`, or pass --token / set HF_TOKEN.\n")

    report, ok, failed = {}, 0, 0
    for i, d in enumerate(sets, 1):
        dest = out / d.key
        print(f"\n[{i}/{len(sets)}] {d.key}  <-  {d.repo}")
        if d.configs:
            print(f"          configs: {', '.join(d.configs)}")
        if d.allow:
            print(f"          filter : {', '.join(d.allow)}")

        t0 = time.time()
        kwargs = dict(
            repo_id=d.repo,
            repo_type="dataset",
            local_dir=str(dest),
            allow_patterns=d.allow or None,
            token=token,
            max_workers=cfg.workers,
        )
        # hub < 1.0 needed this flag; in 1.x resume is automatic and the
        # argument was removed, so only pass it when it exists.
        import inspect as _insp
        if "resume_download" in _insp.signature(snapshot_download).parameters:
            kwargs["resume_download"] = True
        try:
            path = snapshot_download(**kwargs)
            secs, got = time.time() - t0, dir_gb(dest)
            n_audio = sum(1 for f in dest.rglob("*")
                          if f.is_file() and f.suffix.lower() in AUDIO_EXT)
            print(f"          done: {human(got)} in {secs/60:.1f} min, "
                  f"{n_audio:,} audio/shard files")
            if d.audio and n_audio == 0:
                print("          ** WARNING: no audio files found. The repo may")
                print("          ** store audio elsewhere — check it before training.")
            report[d.key] = {"repo": d.repo, "path": str(path), "audio": d.audio,
                             "gb": round(got, 2), "audio_files": n_audio,
                             "seconds": round(secs)}
            ok += 1

        except GatedRepoError:
            print(f"          GATED. Open https://huggingface.co/datasets/{d.repo}")
            print("          accept the terms, then `hf auth login` and rerun.")
            report[d.key] = {"repo": d.repo, "error": "gated"}
            failed += 1
        except RepositoryNotFoundError:
            print("          repo not found — it may have been renamed or removed.")
            report[d.key] = {"repo": d.repo, "error": "not_found"}
            failed += 1
        except KeyboardInterrupt:
            print("\n  interrupted. rerun the same command to resume.")
            break
        except (HfHubHTTPError, OSError) as e:
            print(f"          failed: {type(e).__name__}: {e}")
            report[d.key] = {"repo": d.repo, "error": str(e)[:300]}
            failed += 1

    rp = out / "_download_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  {ok} ok, {failed} failed. total on disk: {human(dir_gb(out))}")
    print(f"  report: {rp}\n")
    if any(not d.audio for d in sets):
        print("  note: you downloaded a transcript-only repo. It contains no")
        print("  sound — you must source the audio separately.\n")
    print("  next: python ru_download.py verify --out " + str(out))
    print("        python ru_download.py manifest <keys> --out train.jsonl\n")
    return 1 if failed else 0


def cmd_manifest(cfg):
    """Turn downloaded HF datasets into NeMo JSONL manifests."""
    try:
        from datasets import load_dataset, Audio
    except ImportError:
        sys.exit("pip install datasets soundfile librosa")

    out = Path(cfg.out).expanduser().resolve()
    audio_dir = Path(cfg.audio_dir).expanduser().resolve()
    audio_dir.mkdir(parents=True, exist_ok=True)
    src = Path(cfg.root).expanduser().resolve()

    import soundfile as sf
    written = skipped = 0
    with out.open("w", encoding="utf-8") as fh:
        for key in cfg.datasets:
            d = BY_KEY.get(key)
            local = src / key
            if not local.exists():
                print(f"  ! {key}: not downloaded, skipping")
                continue
            print(f"  reading {key} ...")
            try:
                ds = load_dataset(str(local), split=cfg.split)
            except Exception as e:
                print(f"  ! {key}: {type(e).__name__}: {e}")
                continue

            ds = ds.cast_column("audio", Audio(sampling_rate=16000))
            text_col = next((c for c in ("text", "sentence", "transcription",
                                         "transcript") if c in ds.column_names), None)
            if text_col is None:
                print(f"  ! {key}: no text column in {ds.column_names}")
                continue

            sub = audio_dir / key
            sub.mkdir(parents=True, exist_ok=True)
            for i, row in enumerate(ds):
                text = (row[text_col] or "").strip()
                arr = row["audio"]["array"]
                dur = len(arr) / 16000.0
                if not text or not (cfg.min_dur <= dur <= cfg.max_dur):
                    skipped += 1
                    continue
                wav = sub / f"{key}_{i:08d}.wav"
                sf.write(wav, arr, 16000, subtype="PCM_16")
                fh.write(json.dumps({
                    "audio_filepath": str(wav),
                    "duration": round(dur, 3),
                    "text": text,
                }, ensure_ascii=False) + "\n")
                written += 1
                if written % 2000 == 0:
                    print(f"    {written:,} written ...", flush=True)

    print(f"\n  manifest: {out}")
    print(f"  {written:,} utterances written, {skipped:,} skipped "
          f"(empty text or outside {cfg.min_dur}-{cfg.max_dur}s)\n")


def cmd_verify(cfg):
    """Prove the audio is really there: count files, measure real duration."""
    out = Path(cfg.out).expanduser().resolve()
    if not out.exists():
        sys.exit(f"nothing at {out}")

    try:
        import soundfile as sf
    except ImportError:
        sf = None
        print("  (pip install soundfile for exact durations)\n")

    print(f"\n  {'DATASET':<19}{'FILES':>10}{'SIZE':>11}   HOURS")
    print("  " + "-" * 60)
    grand_files = grand_hours = 0.0
    for sub in sorted(p for p in out.iterdir() if p.is_dir()):
        files = [f for f in sub.rglob("*")
                 if f.is_file() and f.suffix.lower() in AUDIO_EXT]
        if not files:
            print(f"  {sub.name:<19}{0:>10}{human(dir_gb(sub), '0'):>11}   "
                  f"no audio found")
            continue

        # Sample real files for duration; parquet/tar are containers, skip them.
        playable = [f for f in files if f.suffix.lower() not in (".parquet", ".tar")]
        hours = "?"
        if sf and playable:
            sample = playable[:cfg.sample]
            secs = 0.0
            for f in sample:
                try:
                    info = sf.info(str(f))
                    secs += info.frames / info.samplerate
                except Exception:
                    pass
            if secs > 0:
                est = secs / len(sample) * len(playable) / 3600
                hours = dur_str(est) + ("" if len(playable) <= cfg.sample else " (est)")
                grand_hours += est
        grand_files += len(files)
        print(f"  {sub.name:<19}{len(files):>10,}{human(dir_gb(sub), '0'):>11}   {hours}")

    print("  " + "-" * 60)
    print(f"  {'TOTAL':<19}{int(grand_files):>10,}{human(dir_gb(out), '0'):>11}   "
          f"{dur_str(grand_hours)}\n")
    if grand_files == 0:
        print("  No audio anywhere. You likely downloaded a manifest-only repo.\n")


def cmd_check(cfg):
    """Ask the Hub whether each repo in this registry really exists."""
    api = HfApi()
    token = cfg.token or os.environ.get("HF_TOKEN")
    print(f"\n  checking {len(REGISTRY)} repos for lang '{cfg.lang}'...\n")
    print(f"  {'KEY':<22}{'STATUS':<14}REPO")
    print("  " + "-" * 82)
    bad = []
    for d in REGISTRY:
        try:
            info = api.dataset_info(d.repo, token=token)
            status = "OK"
            if getattr(info, "gated", False) and not d.gated:
                status = "OK (gated!)"
        except GatedRepoError:
            status = "gated" if d.gated else "GATED (unflagged)"
        except RepositoryNotFoundError:
            status = "404 MISSING"; bad.append(d.key)
        except Exception as e:
            status = type(e).__name__[:13]; bad.append(d.key)
        print(f"  {d.key:<22}{status:<14}{d.repo}")
    print()
    if bad:
        print(f"  {len(bad)} unreachable: {', '.join(bad)}")
        print("  These may be renamed, private, or need a token. Search the Hub")
        print("  for a working mirror and edit the registry at the top of this file.\n")
    else:
        print("  all repos reachable.\n")
    return 1 if bad else 0


# ===========================================================================
# CLI
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(
        description="Download Russian ASR datasets from Hugging Face.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  ru_download.py list
  ru_download.py plan --preset starter
  ru_download.py get  --preset starter --out ./datasets/ru
  ru_download.py get  golos_full common_voice_ru --workers 16
  ru_download.py manifest golos_crowd rulibrispeech --out train.jsonl
""")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_lang(p):
        p.add_argument("--lang", default="en", choices=sorted(LANGS),
                       help="which language registry to use (default: en)")
        return p

    add_lang(sub.add_parser("list", help="show the dataset registry"))

    for name, helptext in [("plan", "dry run: show sizes and disk usage"),
                           ("get", "download")]:
        p = sub.add_parser(name, help=helptext)
        add_lang(p)
        p.add_argument("datasets", nargs="*", help="dataset keys")
        p.add_argument("--preset", help=f"one of: {', '.join(PRESETS)}")
        p.add_argument("--out", default=None, help="default: ./datasets/<lang>")
        p.add_argument("--token", help="HF token (or set HF_TOKEN)")
        p.add_argument("--workers", type=int, default=8)
        p.add_argument("--with-manifests", action="store_true",
                       help="also fetch transcript-only repos (no audio)")
        p.add_argument("--yes", "-y", action="store_true", help="skip confirmation")
        p.add_argument("--force", action="store_true", help="ignore disk warning")

    c = sub.add_parser("check", help="verify every repo id against the Hub")
    add_lang(c)
    c.add_argument("--token", help="HF token (or set HF_TOKEN)")

    v = sub.add_parser("verify", help="count audio files and measure hours")
    add_lang(v)
    v.add_argument("--out", default="./datasets")
    v.add_argument("--sample", type=int, default=300,
                   help="files to probe per dataset when estimating hours")

    m = sub.add_parser("manifest", help="build a NeMo JSONL manifest")
    add_lang(m)
    m.add_argument("datasets", nargs="+")
    m.add_argument("--root", default=None)
    m.add_argument("--out", default="train_manifest.jsonl")
    m.add_argument("--audio-dir", default=None)
    m.add_argument("--split", default="train")
    m.add_argument("--min-dur", type=float, default=0.3)
    m.add_argument("--max-dur", type=float, default=30.0)

    cfg = ap.parse_args()
    set_lang(cfg.lang)
    if getattr(cfg, "out", None) is None:
        cfg.out = f"./datasets/{cfg.lang}"
    if getattr(cfg, "root", None) is None:
        cfg.root = f"./datasets/{cfg.lang}"
    if getattr(cfg, "audio_dir", None) is None:
        cfg.audio_dir = f"./datasets/{cfg.lang}_wav16k"
    return {"list": cmd_list, "plan": lambda c: (cmd_plan(c), 0)[1],
            "get": cmd_get, "verify": cmd_verify, "check": cmd_check,
            "manifest": cmd_manifest}[cfg.cmd](cfg) or 0


if __name__ == "__main__":
    sys.exit(main())