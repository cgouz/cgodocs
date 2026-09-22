
# uv
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Подхватить uv в текущую shell-сессию
if [ -f "$HOME/.local/bin/env" ]; then
    source "$HOME/.local/bin/env"
fi

# NeMo Speech repo
if [ ! -d "Speech" ]; then
    git clone https://github.com/NVIDIA-NeMo/Speech.git
fi

cd /workspace/Speech

# venv
if [ ! -d ".venv" ]; then
    uv venv --python 3.11
fi

source .venv/bin/activate

if ! python -c "import nemo" >/dev/null 2>&1; then
    uv pip install -e ".[asr]"
fi

mkdir -p /workspace/datasets

hf download DavronSherbaev/uzbekvoice-filtered \
  --repo-type dataset \
  --local-dir /workspace/datasets/uzbekvoice-filtered &

hf download DavronSherbaev/uzbekvoice \
  --repo-type dataset \
  --local-dir /workspace/datasets/uzbekvoice &

hf download islomov/it_youtube_uzbek_speech_dataset \
  --repo-type dataset \
  --local-dir /workspace/datasets/it_youtube_uzbek &

hf download islomov/news_youtube_uzbek_speech_dataset \
  --repo-type dataset \
  --local-dir /workspace/datasets/news_youtube_uzbek &

hf download murodbek/uzbek-speech-corpus \
  --repo-type dataset \
  --local-dir /workspace/datasets/uzbek-speech-corpus &

hf download islomov/podcasts_tashkent_dialect_youtube_uzbek_speech_dataset \
  --repo-type dataset \
  --local-dir /workspace/datasets/tashkent_dialect_youtube &

hf download roscoe1912/common-voice-uz \
  --repo-type dataset \
  --local-dir /workspace/datasets/common-voice-uz &

wait
echo "ALL DOWNLOADS DONE"root@jupyterlite-0-0:/workspace# 