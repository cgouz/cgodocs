"""
qadam2.py — Audio'ni STANDART shaklga keltirish.

NIMA UCHUN KERAK?
Model — bu matematik funksiya. U har doim BIR XIL o'lchamdagi kirishni kutadi.
Lekin yozuvlarimiz har xil: biri 1.6 sekund, biri 0.7, biri stereo...
Shuning uchun har audio'ni bitta qolipga solamiz:
    MONO + 16000 Hz + aynan 1 sekund (16000 nuqta)

Bu jarayon ML'da "preprocessing" (oldindan qayta ishlash) deyiladi.
"""

import soundfile as sf   # audio o'qish/yozish uchun
import numpy as np       # massivlar ustida matematik amallar uchun

# O'zgarmas qiymatlarni KATTA harf bilan yozish — Python odati.
# Bitta joyda o'zgartirsak, hamma joyda o'zgaradi.
MAQSAD = 16000           # maqsad uzunlik: 16000 nuqta = 16kHz da 1 sekund


def standartla(data: np.ndarray, sr: int) -> np.ndarray:
    """Har qanday audio massivni mono, aynan 16000 nuqtali shaklga keltiradi.

    data -> ovoz raqamlari (NumPy massiv)
    sr   -> sample rate (hozircha 16000 deb kutamiz)
    """

    # ---------- 2.1: STEREO bo'lsa -> MONO ----------
    # Mono massiv shakli:   (25600,)    -> ndim == 1 (bir o'lchamli)
    # Stereo massiv shakli: (25600, 2)  -> ndim == 2 (ikki o'lchamli: nuqta x kanal)
    if data.ndim == 2:
        # axis=1 -> har QATOR bo'yicha o'rtacha, ya'ni har nuqtada
        # chap va o'ng kanal qiymatlarining o'rtachasi olinadi.
        # Natija yana bir o'lchamli (mono) massiv bo'ladi.
        data = data.mean(axis=1)

    # ---------- 2.2: UZUNLIKNI aynan MAQSAD ga tenglashtirish ----------
    if len(data) > MAQSAD:
        # UZUN bo'lsa: boshidagi 16000 tasini KESIB olamiz.
        # data[:16000] -> "0-indeksdan 16000-gacha" degan kesim (slicing).
        data = data[:MAQSAD]

    elif len(data) < MAQSAD:
        # QISQA bo'lsa: oxiriga NOL qo'shamiz. Nol = to'liq jimlik,
        # ya'ni ovozga hech narsa qo'shmayapmiz, faqat "sukut" bilan to'ldiryapmiz.
        yetishmaydi = MAQSAD - len(data)
        # np.pad(massiv, (boshiga_nechta, oxiriga_nechta)):
        # boshiga 0 ta, oxiriga 'yetishmaydi' ta nol qo'shadi.
        data = np.pad(data, (0, yetishmaydi))

    # Aynan teng bo'lsa (len == MAQSAD) hech narsa qilmaymiz — shundoq ham tayyor.

    return data


# ================== SINOV QISMI ==================
# Bu qism faqat faylni to'g'ridan-to'g'ri ishga tushirganda ishlaydi.
# Keyinchalik boshqa fayl 'from qadam2 import standartla' qilsa, bu qism ishlamaydi.
if __name__ == "__main__":

    # 1) Asl faylni o'qiymiz
    data, sr = sf.read("../sinov/bir_sinov.wav")
    print("OLDIN:")
    print("  Shakl (shape):", data.shape)       # (25600,) -> mono, 25600 nuqta
    print("  Nuqtalar:", len(data))
    print("  Sekund:", len(data) / sr)          # 25600/16000 = 1.6

    # 2) Standartlaymiz
    yangi = standartla(data, sr)
    print("KEYIN:")
    print("  Nuqtalar:", len(yangi))            # aynan 16000 bo'lishi SHART
    print("  Sekund:", len(yangi) / sr)         # aynan 1.0 bo'lishi SHART

    # 3) Natijani faylga saqlaymiz — quloq bilan tekshirish uchun!
    #    Kod "ishladi" deyish yetarli emas, natijani ESHITISH kerak.
    sf.write("../sinov/bir_standart.wav", yangi, sr)
    print("Saqlandi: sinov/bir_standart.wav — endi eshitib ko'ring!")