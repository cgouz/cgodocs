"""
qadam8.py — BASHORAT: o'rgatilgan model bilan gaplashamiz!

NIMA QILADI?
Saqlangan modelni yuklab, unga YANGI wav fayl beramiz va u qaysi so'z
ekanini aytadi — har so'z bo'yicha ishonch foizlari bilan.

ISHLATISH:
    python qadam8.py ../sinov/test_bir_1.wav

MUHIM YANGI TUSHUNCHA — SOFTMAX:
Model xom "ball"lar (logits) beradi: masalan [2.1, -0.3, 0.8].
Odamga foiz tushunarli: "77% bir, 8% ikki, 15% uch".
Softmax — ballarni foizlarga aylantiruvchi formula:
har ballning e^ball ini hisoblab, yig'indiga bo'ladi.
Natija: hammasi 0..1 oralig'ida va yig'indisi aynan 1.0 (=100%).
"""

import json
import sys                     # terminal argumentlarini o'qish uchun

import soundfile as sf
import torch

# Avvalgi mehnatimiz yana kutubxona bo'lib xizmatda:
from qadam5 import SozDataset, standartla, MAQSAD
from qadam6 import KichikKWS
import torchaudio.transforms as T


def model_yukla():
    """Saqlangan model va so'zlar ro'yxatini yuklaydi."""

    # So'zlar ro'yxati — "0 = bir" tarjimoni:
    with open("../models/sozlar.json", encoding="utf-8") as f:
        sozlar = json.load(f)

    # Avval BO'SH model yasaymiz (xuddi o'rgatishdagi kabi tuzilishda),
    # keyin ichiga saqlangan og'irliklarni QUYAMIZ.
    # Nima uchun ikki bosqich? .pt faylda faqat OG'IRLIKLAR bor (lug'at),
    # tuzilishning o'zi yo'q — tuzilish kodda (qadam6.py) yashaydi.
    model = KichikKWS(son_klasslar=len(sozlar))
    model.load_state_dict(torch.load("../models/model_eng_yaxshi.pt"))

    # eval() ni UNUTMANG: Dropout o'chadi. Usiz har chaqirishda
    # tasodifiy neyronlar o'chib, javob har safar o'zgarib turadi!
    model.eval()

    return model, sozlar


def bashorat(model, sozlar, fayl_yoli):
    """Bitta wav fayl uchun to'liq quvur: fayl -> so'z + foizlar."""

    # ---------- Tanish quvur (5-qadamdagi bilan AYNAN bir xil!) ----------
    # Muhim qoida: bashoratda audio TAYYORLASH o'rgatishdagi bilan
    # zarracha ham farq qilmasligi kerak. Farq bo'lsa — model adashadi.
    data, sr = sf.read(fayl_yoli)
    data = standartla(data)

    waveform = torch.from_numpy(data).float()
    melspek = T.MelSpectrogram(sample_rate=16000, n_fft=400,
                               hop_length=160, n_mels=64)
    spek = T.AmplitudeToDB()(melspek(waveform))
    spek = (spek - spek.mean()) / (spek.std() + 1e-6)

    # Model batch kutadi: (64,101) -> (1,1,64,101)
    # Birinchi unsqueeze -> kanal, ikkinchisi -> batch o'lchami.
    spek = spek.unsqueeze(0).unsqueeze(0)

    # ---------- Bashorat ----------
    with torch.no_grad():              # o'rganmayapmiz — gradient kerak emas
        ballar = model(spek)           # xom logits: masalan [[2.1, -0.3, 0.8]]

    # SOFTMAX: ballar -> foizlar. dim=1 -> klasslar o'qi bo'ylab
    # (har namuna ichida foizlar yig'indisi 1.0 bo'lsin).
    # [0] -> batch'dagi yagona namunani olamiz.
    foizlar = torch.softmax(ballar, dim=1)[0]

    # argmax -> eng katta foiz indeksi; .item() -> tensor'dan oddiy songa
    top = foizlar.argmax().item()

    return sozlar[top], foizlar


# ================== ASOSIY QISM ==================
if __name__ == "__main__":
    # sys.argv -> terminal argumentlari ro'yxati:
    # "python qadam8.py fayl.wav" da argv[0]='qadam8.py', argv[1]='fayl.wav'
    if len(sys.argv) < 2:
        print("Ishlatish: python qadam8.py <wav fayl yo'li>")
        print("Masalan:   python qadam8.py ../sinov/test_bir_1.wav")
        sys.exit(1)   # dasturdan chiqish (1 = xato kodi)

    fayl = sys.argv[1]

    model, sozlar = model_yukla()
    soz, foizlar = bashorat(model, sozlar, fayl)

    print(f"\nFayl: {fayl}")
    print(f"Model javobi: '{soz}'  (ishonch: {foizlar.max():.1%})\n")

    # Barcha foizlarni "diagramma" bilan ko'rsatamiz — model nima bilan
    # ikkilanayotgani ko'rinadi. zip -> ikki ro'yxatni juftlab beradi.
    for s, f in zip(sozlar, foizlar.tolist()):
        chiziq = "#" * int(f * 40)          # foizga mos uzunlikdagi chiziq
        print(f"  {s:6s} {chiziq:40s} {f:.1%}")