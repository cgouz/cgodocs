"""
qadam6.py — CNN MODEL: loyihamizning "miyasi".

VAZIFASI:
    Kirish:  (1, 64, 101)  — bitta spektrogramma "rasmi"
    Chiqish: 3 ta raqam    — har so'z uchun "ball" (logits)
    Eng katta ball qaysi so'zda -> model o'sha so'z aytilgan deb hisoblaydi.

ARXITEKTURA (konveyer):
    rasm -> [Conv+ReLU+Pool] -> [Conv+ReLU+Pool] -> o'rtacha -> Linear -> 3 ball
Qatlamdan qatlamga: rasm kichrayadi, "chuqurlik" (kanallar) ortadi —
mayda detallardan umumiy xulosa tomon.
"""

import torch
import torch.nn as nn   # nn = neural network. Barcha qatlamlar shu yerda.


class KichikKWS(nn.Module):
    """nn.Module — PyTorch'dagi BARCHA modellarning "ota" klassi.

    Xuddi Dataset'dagi kabi meros: PyTorch'ning o'rganish mexanizmlari
    (gradientlar, saqlash/yuklash...) tayyor keladi, biz faqat ikkita
    narsani yozamiz:
        __init__  -> modelning QISMLARINI e'lon qilamiz
        forward   -> ma'lumot qismlardan QANDAY OQIB O'TISHINI yozamiz
    """

    def __init__(self, son_klasslar: int):
        # super().__init__() -> ota klassni ishga tushirish. MAJBURIY birinchi
        # qator, usiz PyTorch qatlamlarni "ko'rmaydi" va o'rgata olmaydi.
        super().__init__()

        # nn.Sequential -> qatlamlarni "konveyer lentasi"ga teradi:
        # ma'lumot birinchisidan kirib, tartib bilan oxirgisidan chiqadi.
        self.features = nn.Sequential(
            # ---------- 1-BLOK: mayda naqshlarni topish ----------
            # Conv2d(kirish_kanallar, chiqish_kanallar, lupa_o'lchami, ...)
            # 1 -> 16: bitta "kulrang" rasmdan 16 ta naqsh-xarita yasaydi.
            # kernel_size=3 -> 3x3 lupa; padding=1 -> chetlarga 1 qator nol
            # qo'shiladi, shunda rasm o'lchami Conv'dan keyin O'ZGARMAYDI
            # (faqat Pool kichraytiradi — hisoblash oson bo'ladi).
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),                # manfiylarni 0 ga -> egiluvchanlik
            nn.MaxPool2d(2),          # (16, 64, 101) -> (16, 32, 50)

            # ---------- 2-BLOK: naqshlarning naqshlarini topish ----------
            # 16 -> 32: birinchi blok topgan oddiy naqshlardan
            # murakkabroq birikmalar yasaydi.
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),          # (32, 32, 50) -> (32, 16, 25)
        )

        # ---------- XULOSA QISMI ----------
        # AdaptiveAvgPool2d(1) -> har kanalning BUTUN xaritasini bitta
        # o'rtacha raqamga siqadi: (32, 16, 25) -> (32, 1, 1).
        # Ma'nosi: "32-naqsh rasmda o'rtacha qanchalik kuchli uchradi?"
        self.pool = nn.AdaptiveAvgPool2d(1)

        self.classifier = nn.Sequential(
            # Flatten -> (32,1,1) ni tekis (32,) qatorga yozadi,
            # chunki Linear qatlam faqat tekis vektor qabul qiladi.
            nn.Flatten(),

            # Dropout(0.3) -> FAQAT o'rgatish paytida har safar tasodifiy
            # 30% neyronni o'chiradi. Nima uchun?! Model yodlab olmasligi
            # uchun: hech bir neyronga to'liq suyanolmaydi, bilim hammaga
            # taqsimlanadi. Bu overfitting'ga qarshi asosiy qurolimiz.
            nn.Dropout(0.3),

            # Linear(32 -> 3): yakuniy hakam. 32 ta naqsh-xulosani
            # tortib-taroziga solib, har so'zga ball beradi.
            nn.Linear(32, son_klasslar),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Ma'lumotning modeldan OQIB O'TISH yo'li.

        model(x) deb chaqirilganda PyTorch avtomatik shu metodni ishlatadi
        (xuddi dataset[i] -> __getitem__ kabi sehrli mexanizm).
        """
        x = self.features(x)      # (batch, 1,64,101) -> (batch, 32,16,25)
        x = self.pool(x)          # -> (batch, 32, 1, 1)
        x = self.classifier(x)    # -> (batch, 3)
        return x


# ================== SINOV QISMI ==================
if __name__ == "__main__":
    model = KichikKWS(son_klasslar=3)

    # Modelning ichki tuzilishini chiroyli ko'rsatadi:
    print(model)

    # --- Soxta kirish bilan tekshiruv ---
    # torch.randn -> tasodifiy raqamlar. Haqiqiy ovoz shart emas:
    # hozir faqat SHAKLLAR to'g'ri oqishini tekshiryapmiz.
    # 4 -> batch (bir yo'la 4 ta namuna). Model doim batch kutadi,
    # shuning uchun bitta rasm ham (1, 1, 64, 101) shaklda beriladi.
    soxta = torch.randn(4, 1, 64, 101)
    chiqish = model(soxta)                  # forward avtomatik chaqirildi
    print("\nKirish shakli :", tuple(soxta.shape))
    print("Chiqish shakli:", tuple(chiqish.shape))   # (4, 3) kutamiz!

    # --- Bitta namunaning ballarini ko'ramiz ---
    print("\n0-namuna ballari (logits):", chiqish[0].detach())
    print("Eng katta ball indeksi:", chiqish[0].argmax().item())
    # Hozir ballar ma'nosiz — model hali O'RGATILMAGAN, filtrlar tasodifiy.
    # O'rgatishdan keyin (7-qadam!) bu ballar haqiqiy ma'no kasb etadi.

    # --- Model hajmi ---
    params = sum(p.numel() for p in model.parameters())
    print(f"\nO'rganiladigan parametrlar soni: {params:,}")
    # ~10 mingga yaqin son chiqadi. Taqqoslang: GPT kabi modellarda
    # MILLIARDLAB parametr bor. Bizniki mitti — lekin vazifamizga yetadi!