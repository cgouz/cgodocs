"""
qadam3.py — Ovozni MEL-SPEKTROGRAMMAGA aylantirish va uni RASM qilib ko'rish.

NIMA UCHUN?
16000 ta yalang'och raqamdan "qaysi so'z aytildi"ni topish modelga qiyin.
Ovozni chastota tiliga o'tkazsak, har so'zning o'ziga xos "barmoq izi"
paydo bo'ladi. Spektrogramma:
    gorizontal o'q = VAQT
    vertikal o'q   = CHASTOTA (pastda past tovushlar, tepada baland)
    rang           = shu chastota shu paytda QANCHALIK BALAND eshitilgani

"MEL" nima? Inson qulog'i chastotalarni notekis eshitadi: 100 Hz va 200 Hz
farqini yaqqol sezamiz, lekin 7100 Hz va 7200 Hz deyarli bir xil tuyuladi.
Mel shkalasi — chastotalarni "quloq qanday eshitsa shunday" joylashtirish.
Nutq uchun aynan shu shkala eng yaxshi ishlaydi.
"""

import soundfile as sf
import torch                          # PyTorch — asosiy ML kutubxonamiz
import torchaudio.transforms as T     # tayyor audio o'zgartirishlar to'plami
import matplotlib.pyplot as plt       # grafik/rasm chizish kutubxonasi

# ---------- 1) Audio'ni o'qish (2-qadamdan tanish) ----------
data, sr = sf.read("../sinov/bir_standart.wav")
print("Audio nuqtalar:", len(data), "| sample rate:", sr)

# ---------- 2) NumPy -> PyTorch TENSOR ----------
# Tensor — PyTorch'ning massivi. NumPy massivga juda o'xshaydi, lekin
# tensor GPU'da ishlay oladi va gradient (o'rganish uchun kerak) saqlaydi.
# torchaudio faqat tensor bilan ishlaydi, shuning uchun aylantiramiz.
# .float() -> 32-bitli kasr son turiga o'tkazadi (PyTorch standarti).
waveform = torch.from_numpy(data).float()
print("Tensor shakli:", waveform.shape)   # torch.Size([16000])

# ---------- 3) Mel-spektrogramma YASOVCHI obyekt ----------
# T.MelSpectrogram — bu "fabrika": bir marta sozlab olamiz,
# keyin istalgan audio'ga qo'llayveramiz.
melspek = T.MelSpectrogram(
    sample_rate=16000,
    n_fft=400,        # tahlil OYNASI: bir martada 400 nuqta (=25 ms) tahlil
                      # qilinadi. Qisqa oyna -> vaqt aniq, chastota xira;
                      # uzun oyna -> aksincha. 25 ms — nutq uchun standart.
    hop_length=160,   # oynaning QADAMI: har safar 160 nuqta (=10 ms) siljiydi.
                      # Ya'ni sekundiga ~100 ta "surat" olinadi.
    n_mels=64,        # chastota QATORLARI soni — rasmning balandligi.
                      # 64 ta mel-filtr past chastotadan balandgacha qamraydi.
)

# ---------- 4) Qo'llash: audio -> spektrogramma ----------
spek = melspek(waveform)
print("Spektrogramma shakli:", spek.shape)
# Kutilgan natija: torch.Size([64, 101])
#   64  -> n_mels (chastota qatorlari)
#   101 -> vaqt ustunlari: 16000 / 160 = 100 ta qadam + 1 chetki oyna = 101
# Ya'ni ovozimiz endi 64x101 o'lchamli "rasm" bo'ldi!

# ---------- 5) dB (desibel) shkalaga o'tkazish ----------
# Xom spektrogrammada qiymatlar juda notekis: bitta nuqta 50000, boshqasi 0.001.
# Quloq ham ovozni logarifmik eshitadi (2 barobar quvvat != 2 barobar balandlik).
# AmplitudeToDB hammasini logarifmik, qulay diapazonga (~-100..0) keltiradi.
spek_db = T.AmplitudeToDB()(spek)
print("dB dan keyin: min =", round(spek_db.min().item(), 1),
      "| max =", round(spek_db.max().item(), 1))

# ---------- 6) RASM qilib ko'rsatish ----------
plt.figure(figsize=(10, 4))                      # rasm o'lchami (dyuymda)
plt.imshow(
    spek_db,             # 64x101 matritsani rasm sifatida chizadi
    origin="lower",      # 0-qator PASTDA bo'lsin (past chastota pastda —
                         # xuddi musiqadagi kabi tabiiy joylashuv)
    aspect="auto",       # rasm oynaga moslashib cho'zilsin
    cmap="magma",        # rang palitrasi: qora=jim, sariq/oq=baland
)
plt.colorbar(label="dB")                         # yon tomonda rang shkalasi
plt.xlabel("Vaqt (ustunlar, har biri 10 ms)")
plt.ylabel("Mel chastota qatorlari")
plt.title("'bir' so'zining mel-spektrogrammasi")
plt.tight_layout()
plt.savefig("../sinov/bir_spektrogramma.png")    # rasmni faylga ham saqlaymiz
plt.show()                                       # ekranga chiqaradi
print("Rasm saqlandi: sinov/bir_spektrogramma.png")