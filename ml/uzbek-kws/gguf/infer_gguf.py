"""
infer_gguf.py — model.gguf faylidan OG'IRLIKLARNI o'qib, forward pass'ni
TOZA NUMPY bilan (PyTorch nn.Module'siz) qayta quradi va bitta wav fayl
uchun bashorat qiladi.

NIMA UCHUN NUMPY BILAN QAYTA QURISH KERAK?
GGUF fayl faqat sonlarni (tensorlarni) saqlaydi — u "Conv2d qanday
hisoblanadi" degan mantiqni bilmaydi. llama.cpp bu mantiqni ggml C++
kodida taniydi, lekin faqat O'ZI TANIYDIGAN arxitekturalar (Llama,
Whisper, ...) uchun. Bizning mitti CNN ggml'da yo'q, shuning uchun
forward pass'ni shu yerda qo'lda (numpy bilan) yozamiz — bu GGUF
faylning haqiqiy og'irliklarni to'g'ri saqlaganini isbotlaydi.

ISHLATISH:
    python infer_gguf.py ../sinov/test_bir_1.wav
"""

import sys

import gguf
import numpy as np
import soundfile as sf
import torch
import torchaudio.transforms as T

MAQSAD = 16000


# ---------- qadam5.py'dagi standartla() bilan AYNAN bir xil bo'lishi shart ----------
def standartla(data: np.ndarray) -> np.ndarray:
    if data.ndim == 2:
        data = data.mean(axis=1)
    if len(data) > MAQSAD:
        markaz = np.abs(data).argmax()
        bosh = markaz - MAQSAD // 2
        bosh = max(0, min(bosh, len(data) - MAQSAD))
        data = data[bosh: bosh + MAQSAD]
    elif len(data) < MAQSAD:
        data = np.pad(data, (0, MAQSAD - len(data)))
    return data


def gguf_dan_yukla(fayl_yoli: str):
    reader = gguf.GGUFReader(fayl_yoli)

    def kv(nom):
        return reader.get_field(nom).contents()

    def tensor(nom):
        for t in reader.tensors:
            if t.name == nom:
                return np.array(t.data, dtype=np.float32).reshape(t.shape[::-1])
        raise KeyError(nom)

    sozlar = list(kv("kichik_kws.sozlar"))
    ogirliklar = {
        "conv1.weight": tensor("conv1.weight"),
        "conv1.bias": tensor("conv1.bias"),
        "conv2.weight": tensor("conv2.weight"),
        "conv2.bias": tensor("conv2.bias"),
        "fc.weight": tensor("fc.weight"),
        "fc.bias": tensor("fc.bias"),
    }
    return ogirliklar, sozlar


# ---------- Numpy bilan qo'lda forward pass ----------
def conv2d(x, weight, bias, padding=1):
    """x: (Cin,H,W), weight: (Cout,Cin,kh,kw) -> (Cout,H,W) (stride=1)."""
    cin, h, w = x.shape
    kh, kw = weight.shape[2], weight.shape[3]
    xp = np.pad(x, ((0, 0), (padding, padding), (padding, padding)))
    windows = np.lib.stride_tricks.sliding_window_view(xp, (kh, kw), axis=(1, 2))
    out = np.einsum("oikl,ihwkl->ohw", weight, windows) + bias[:, None, None]
    return out


def relu(x):
    return np.maximum(x, 0)


def maxpool2d(x, k=2):
    c, h, w = x.shape
    hout, wout = h // k, w // k
    x = x[:, : hout * k, : wout * k]
    x = x.reshape(c, hout, k, wout, k)
    return x.max(axis=(2, 4))


def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def forward(spek: np.ndarray, w: dict) -> np.ndarray:
    """spek: (1,64,101) -> logits (son_klasslar,). Dropout yo'q (eval rejimi)."""
    x = conv2d(spek, w["conv1.weight"], w["conv1.bias"], padding=1)
    x = relu(x)
    x = maxpool2d(x, 2)

    x = conv2d(x, w["conv2.weight"], w["conv2.bias"], padding=1)
    x = relu(x)
    x = maxpool2d(x, 2)

    x = x.mean(axis=(1, 2))                     # AdaptiveAvgPool2d(1) + Flatten
    logits = w["fc.weight"] @ x + w["fc.bias"]   # Linear
    return logits


def spektrogramma_yasash(fayl_yoli: str) -> np.ndarray:
    data, sr = sf.read(fayl_yoli)
    data = standartla(data)

    waveform = torch.from_numpy(data).float()
    melspek = T.MelSpectrogram(sample_rate=16000, n_fft=400, hop_length=160, n_mels=64)
    spek = T.AmplitudeToDB()(melspek(waveform))
    spek = (spek - spek.mean()) / (spek.std() + 1e-6)
    return spek.unsqueeze(0).numpy()   # (1,64,101)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ishlatish: python infer_gguf.py <wav fayl yo'li>")
        sys.exit(1)

    ogirliklar, sozlar = gguf_dan_yukla("model.gguf")
    spek = spektrogramma_yasash(sys.argv[1])
    logits = forward(spek, ogirliklar)
    foizlar = softmax(logits)
    top = int(foizlar.argmax())

    print(f"\nFayl: {sys.argv[1]}")
    print(f"Model javobi (GGUF orqali): '{sozlar[top]}'  (ishonch: {foizlar[top]:.1%})\n")
    for s, f in zip(sozlar, foizlar.tolist()):
        chiziq = "#" * int(f * 40)
        print(f"  {s:6s} {chiziq:40s} {f:.1%}")
