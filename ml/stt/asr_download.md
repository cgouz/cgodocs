# asr_download.py — 10 language registries

```bash
python asr_download.py list  --lang ko      # ko zh ja kaa fr de ar en ru uz
python asr_download.py check --lang zh      # verify repo ids BEFORE downloading
python asr_download.py get   --preset starter --lang ja
python asr_download.py verify --lang ja
```

## Run `check` first

New in this version. It queries the Hub and tells you which repo ids actually
resolve:

```
  KEY                   STATUS        REPO
  aishell1              OK            AISHELL/AISHELL-1
  wenetspeech           404 MISSING   wenet-e2e/wenetspeech
```

Dataset repos get renamed and moved constantly. Anything marked `404 MISSING`
just needs a corrected id — the registry is a plain list at the top of the
script, easy to edit.

## The headline dataset per language

| Lang | Best bet | Hours | Watch out for |
|---|---|---|---|
| Korean | `zeroth_korean` | 51.6 | Small. The big Korean sets are locked |
| Chinese | `wenetspeech` | 10,000 | `aishell1` (178h) is the standard baseline |
| Japanese | `reazonspeech` | 35,000 | **Legal restriction, see below** |
| Karakalpak | `karakalpak_corpus` | 107 | Essentially your only option |
| French | `mls_fr` | 1,076 | Plus `yodas_granary_fr` for scale |
| German | `mls_de` | 1,966 | Best-resourced after English |
| Arabic | `common_voice_ar` | ~150 | **Dialect problem, see below** |

## Three language-specific traps

**Japanese — ReazonSpeech has a legal condition.** 35,000 hours, by far the
largest Japanese corpus, sourced from TV broadcasts. Accessing it requires
agreeing to use it *solely* under Japanese Copyright Act Article 30-4. That is
a real legal constraint, not boilerplate, and it may not cover a commercial
product outside Japan. Read it before you build on it. It also needs
`trust_remote_code=True`. Start with the `small` config, not `all`.

**Arabic — "Arabic" is not one language.** Common Voice Arabic is mostly Modern
Standard Arabic, which almost nobody speaks conversationally. A model trained
only on MSA will fail badly on Egyptian, Gulf or Levantine speech. If your users
speak a dialect, MSA data alone will not save you. `masc` (~1000h from YouTube)
has broader dialect coverage.

**Korean — the good data is behind a wall.** KsponSpeech (1,000h) and the AI Hub
corpora need Korean national registration to access. Zeroth's 51.6 hours is what
is genuinely open. Plan to fine-tune a strong multilingual checkpoint rather
than train from scratch.

## Karakalpak

`atikuwu/karakalpak-speech-corpus` — 107 hours, the first open crowdsourced
corpus for kaa, built by a student team at the Muhammad al-Khwarizmi Specialized
School in Nukus with 200+ community contributors.

There is also a published baseline, `atikuwu/whisper-medium-karakalpak`,
reporting 9.59% test WER. Beat that number and you have a genuine contribution —
this is a language where one person can still move the state of the art.

Karakalpak Latin uses `á ó ú ı ń ś ǵ`. Your text normalizer must preserve these
and not strip them as "unsupported":

```bash
python uz_clean.py scan datasets/kaa --allow "áóúıńśǵÁÓÚINŚǴ"
```

## Low-resource strategy

For Karakalpak, Korean and Uzbek, you do not have enough data to train from
scratch. Fine-tune a multilingual checkpoint instead — `nemotron-3.5-asr-
streaming-0.6b` covers 40 languages, and Whisper or MMS are alternatives.

Related-language transfer is real: Karakalpak is Turkic and close to Kazakh and
Uzbek. Pretraining on Uzbek before fine-tuning on Karakalpak usually beats
training on 107 hours of Karakalpak alone. You already have the Uzbek registry.