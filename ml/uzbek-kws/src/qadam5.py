"""
qadam5.py — SozDataset: 90 ta faylni PyTorch tushunadigan shaklga keltirish.

NIMA UCHUN KLASS KERAK?
PyTorch'ga "mana mening datasetim" deyishning standart usuli — Dataset klassi.
Keyin PyTorch'ning DataLoader'i shu klassdan namunalarni o'zi olib,
aralashtirib, guruhlarga (batch) bo'lib modelga uzatadi.

KLASSDA 3 TA METOD BO'LISHI SHART (PyTorch talabi):
    __init__      -> bir marta: fayllar ro'yxatini tuzadi
    __len__       -> nechta namuna bor? (bizda 90)
    __getitem__   -> idx-nchi namunani tayyorlab beradi: (spektrogramma, label)

Bu fayl avvalgi qadamlarni birlashtiradi:
    fayl -> o'qish(1-qadam) -> standartla(2-qadam) -> spektrogramma(3-qadam)
"""

import os

import soundfile as sf
import numpy as np
import torch
import torchaudio.transforms as T
from torch.utils.data import Dataset   # PyTorch'ning tayyor "ota" klassi

MAQSAD = 16000   # 2-qadamdan tanish: 1 sekund = 16000 nuqta


def standartla(data: np.ndarray) -> np.ndarray:
    if data.ndim == 2:
        data = data.mean(axis=1)

    if len(data) > MAQSAD:
        # AQLLI KESISH: eng baland nuqta atrofidan 1 sekund olamiz
        markaz = np.abs(data).argmax()        # eng baland nuqta indeksi
        bosh = markaz - MAQSAD // 2           # undan yarim sekund oldin
        # Chegaralardan chiqib ketmaslik:
        bosh = max(0, min(bosh, len(data) - MAQSAD))
        data = data[bosh : bosh + MAQSAD]
    elif len(data) < MAQSAD:
        data = np.pad(data, (0, MAQSAD - len(data)))

    return data


class SozDataset(Dataset):
    """(Dataset) — PyTorch'ning Dataset klassidan "meros" olamiz.

    Meros degani: PyTorch'ning tayyor imkoniyatlarini olamiz va
    faqat o'zimizga keraklilarini (__init__, __len__, __getitem__) yozamiz.
    """

    def __init__(self, dataset_papka: str):
        # ---------- So'zlarni topish ----------
        # dataset/ ichidagi papka nomlari = so'zlarimiz (label'lar).
        # sorted() MUHIM: har ishga tushirishda bir xil tartib bo'lishi uchun.
        # Aks holda bugun bir=0, ertaga bir=2 bo'lib, model adashadi!
        self.sozlar = sorted(
            d for d in os.listdir(dataset_papka)
            if os.path.isdir(os.path.join(dataset_papka, d))
        )
        # Natija: ['bir', 'ikki', 'uch'] -> bir=0, ikki=1, uch=2

        # ---------- (fayl, label) juftliklarini yig'ish ----------
        # enumerate -> ro'yxatni raqami bilan beradi: (0,'bir'), (1,'ikki')...
        self.namunalar = []
        for label, soz in enumerate(self.sozlar):
            soz_papka = os.path.join(dataset_papka, soz)
            for fayl in sorted(os.listdir(soz_papka)):
                if fayl.endswith(".wav"):
                    self.namunalar.append(
                        (os.path.join(soz_papka, fayl), label)
                    )
        # Endi self.namunalar = [('dataset/bir/001.wav', 0), ..., 
        #                        ('dataset/uch/030.wav', 2)] — jami 90 juftlik

        # ---------- Spektrogramma yasovchi (3-qadamdan tanish) ----------
        # Bir marta yasab olamiz — har __getitem__ da qayta yasamaymiz (tejash)
        self.melspek = T.MelSpectrogram(
            sample_rate=16000, n_fft=400, hop_length=160, n_mels=64
        )
        self.db = T.AmplitudeToDB()

    def __len__(self) -> int:
        """len(dataset) deyilganda nechta namuna borligini aytadi."""
        return len(self.namunalar)

    def __getitem__(self, idx: int):
        """dataset[idx] deyilganda idx-nchi namunani TAYYORLAB beradi.

        Aynan shu yerda butun quvur (pipeline) ishlaydi:
        fayl -> o'qish -> standartlash -> tensor -> spektrogramma -> dB
        """
        fayl_yoli, label = self.namunalar[idx]

        # 1-qadam: o'qish
        data, sr = sf.read(fayl_yoli)

        # 2-qadam: standart shakl (mono, 16000 nuqta)
        data = standartla(data)

        # 3-qadam: tensor -> spektrogramma -> dB
        waveform = torch.from_numpy(data).float()
        spek = self.db(self.melspek(waveform))      # shakl: (64, 101)

        # ---------- YANGI: normalizatsiya ----------
        # Har spektrogrammani "o'rtacha 0, tarqoqlik 1" holatga keltiramiz.
        # Nima uchun? Biri baland, biri past yozilgan — model balandlikka
        # emas, so'z SHAKLIGA qarashi kerak. Normalizatsiya shuni ta'minlaydi.
        # (+ 1e-6 -> nolga bo'linishdan himoya, agar butunlay jim fayl bo'lsa)
        spek = (spek - spek.mean()) / (spek.std() + 1e-6)

        # ---------- YANGI: kanal o'lchami ----------
        # CNN rasm kutadi va rasm formati: (kanallar, balandlik, kenglik).
        # Rangli rasmda 3 kanal (RGB), bizda 1 ta "rang" bor.
        # unsqueeze(0) -> boshiga 1 o'lcham qo'shadi: (64,101) -> (1,64,101)
        spek = spek.unsqueeze(0)

        return spek, label


# ================== SINOV QISMI ==================
if __name__ == "__main__":
    dataset = SozDataset("../dataset")

    print("So'zlar (tartibi = label raqami):", dataset.sozlar)
    print("Jami namunalar:", len(dataset))          # __len__ chaqirildi!

    # Bitta namunani olib tekshiramiz:                __getitem__ chaqirildi!
    spek, label = dataset[0]
    print("0-namuna shakli:", spek.shape)            # (1, 64, 101) kutamiz
    print("0-namuna labeli:", label, "->", dataset.sozlar[label])

    # Har klassdan bittadan tekshirib ko'ramiz (0, 30, 60-namunalar):
    for idx in [0, 30, 60]:
        spek, label = dataset[idx]
        print(f"{idx}-namuna: label={label} ({dataset.sozlar[label]}), "
              f"shakl={tuple(spek.shape)}, "
              f"o'rtacha={spek.mean():.3f}, tarqoqlik={spek.std():.3f}")
    # O'rtacha ~0.000 va tarqoqlik ~1.000 chiqsa — normalizatsiya ishlayapti!