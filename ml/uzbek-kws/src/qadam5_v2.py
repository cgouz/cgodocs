"""
qadam5.py — SozDataset (YANGILANGAN: endi AUGMENTATSIYA bilan!)

AUGMENTATSIYA NIMA?
Har o'qishda yozuvni OZGINA tasodifiy o'zgartirish: siljitish, shovqin,
balandlik. Natijada model bir yozuvni har epoch'da BOSHQACHA ko'radi —
90 ta yozuv "minglab" bo'lib tuyuladi. Kichik datasetning eng kuchli dorisi!

MUHIM QOIDA: augmentatsiya FAQAT train uchun! Test — imtihon, uni
o'zgartirmaymiz (imtihon savolini har safar o'zgartirib bo'lmaydi-ku).
Shuning uchun klassga augment=True/False bayrog'i qo'shildi.
"""

import os
import random                  # tasodifiy sonlar uchun

import soundfile as sf
import numpy as np
import torch
import torchaudio.transforms as T
from torch.utils.data import Dataset

MAQSAD = 16000


def standartla(data: np.ndarray) -> np.ndarray:
    """Mono + aqlli kesish (eng baland nuqta markazda) + 16000 nuqta."""
    if data.ndim == 2:
        data = data.mean(axis=1)

    if len(data) > MAQSAD:
        markaz = np.abs(data).argmax()
        bosh = markaz - MAQSAD // 2
        bosh = max(0, min(bosh, len(data) - MAQSAD))
        data = data[bosh : bosh + MAQSAD]
    elif len(data) < MAQSAD:
        data = np.pad(data, (0, MAQSAD - len(data)))

    return data


def augmentla(data: np.ndarray) -> np.ndarray:
    """Yozuvni tasodifiy ozgina o'zgartirish — har chaqirishda boshqacha!

    Uchta texnika (har biri haqiqiy hayotdagi o'zgaruvchanlikni taqlid qiladi):
    """

    # ---- 1) VAQT SILJISHI (±0.1 sekund) ----
    # Haqiqatda: so'zni sal ertaroq/kechroq aytish.
    # np.roll -> massivni "aylantirib" siljitadi (chetdan chiqqani
    # ikkinchi chetdan kiradi). ±1600 nuqta = ±0.1 sekund.
    siljish = random.randint(-1600, 1600)
    data = np.roll(data, siljish)

    # ---- 2) SHOVQIN QO'SHISH (50% ehtimol bilan) ----
    # Haqiqatda: fon shovqini, mikrofon sifati.
    # randn -> normal taqsimotli tasodifiy sonlar; 0.005 -> juda past
    # daraja (so'zdan ~100x past — zirillashingiz darajasida!)
    if random.random() < 0.5:
        data = data + 0.005 * np.random.randn(len(data))

    # ---- 3) BALANDLIK O'ZGARISHI (0.7x .. 1.3x) ----
    # Haqiqatda: mikrofonga yaqin/uzoq gapirish.
    # Eslatma: normalizatsiya buni qisman "tekislaydi", lekin spektrogramma
    # dB bosqichida nozik farqlar baribir qoladi — model chiniqadi.
    data = data * random.uniform(0.7, 1.3)

    return data


class SozDataset(Dataset):
    def __init__(self, dataset_papka: str, augment: bool = False):
        # YANGI: augment bayrog'i. True -> har o'qishda tasodifiy o'zgartirish.
        self.augment = augment

        self.sozlar = sorted(
            d for d in os.listdir(dataset_papka)
            if os.path.isdir(os.path.join(dataset_papka, d))
        )

        self.namunalar = []
        for label, soz in enumerate(self.sozlar):
            soz_papka = os.path.join(dataset_papka, soz)
            for fayl in sorted(os.listdir(soz_papka)):
                if fayl.endswith(".wav"):
                    self.namunalar.append(
                        (os.path.join(soz_papka, fayl), label)
                    )

        self.melspek = T.MelSpectrogram(
            sample_rate=16000, n_fft=400, hop_length=160, n_mels=64
        )
        self.db = T.AmplitudeToDB()

    def __len__(self) -> int:
        return len(self.namunalar)

    def __getitem__(self, idx: int):
        fayl_yoli, label = self.namunalar[idx]

        data, sr = sf.read(fayl_yoli)
        data = standartla(data)

        # YANGI: augmentatsiya — standartlashdan KEYIN, spektrogrammadan OLDIN.
        # Har __getitem__ chaqirilganda YANGI tasodifiy variant chiqadi!
        if self.augment:
            data = augmentla(data)

        waveform = torch.from_numpy(data).float()
        spek = self.db(self.melspek(waveform))
        spek = (spek - spek.mean()) / (spek.std() + 1e-6)
        spek = spek.unsqueeze(0)

        return spek, label


# ================== SINOV QISMI ==================
if __name__ == "__main__":
    # Augmentatsiya ishlayotganini isbotlaymiz: BIR XIL namunani
    # ikki marta o'qib solishtiramiz.

    print("=== Augmentatsiyasiz (augment=False) ===")
    dataset = SozDataset("../dataset", augment=False)
    a, _ = dataset[0]
    b, _ = dataset[0]
    # allclose -> ikki tensor deyarli tengmi?
    print("Ikki o'qish bir xilmi?", torch.allclose(a, b))   # True kutamiz

    print("\n=== Augmentatsiya bilan (augment=True) ===")
    dataset_aug = SozDataset("../dataset", augment=True)
    a, _ = dataset_aug[0]
    b, _ = dataset_aug[0]
    print("Ikki o'qish bir xilmi?", torch.allclose(a, b))   # False kutamiz!
    print("O'rtacha farq:", (a - b).abs().mean().item())
    # False + sezilarli farq = har o'qishda yangi variant. Model har
    # epoch'da 90 ta emas, go'yo cheksiz turli namuna ko'radi!