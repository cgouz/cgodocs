"""
yozuvchi.py — Dataset yozish uchun QUROL.

NIMA QILADI?
Har Enter bosganingizda mikrofondan 1.5 sekund yozib oladi va
avtomatik raqamlangan fayl qilib saqlaydi:
    dataset/bir/001.wav, 002.wav, 003.wav ...

QANDAY ISHLATILADI?
1) Pastdagi SOZ o'zgaruvchisiga qaysi so'zni yozmoqchi bo'lsangiz shuni yozing
2) Terminalda: python yozuvchi.py
3) Har Enter -> bitta yozuv. To'xtatish: Ctrl+C
4) 30 ta yozib bo'lgach, SOZ ni keyingi so'zga o'zgartirib qaytadan ishga tushiring

YOZISH QOIDALARI (sifatli dataset siri!):
- So'zni Enter bosgan ZAHOTI ayting (kechiksangiz — kesilib qoladi)
- Har xil ohangda ayting: tez, sekin, baland, past
- Jim xonada yozing
"""

import os

import sounddevice as sd   # mikrofondan yozib olish kutubxonasi
import soundfile as sf     # wav faylga saqlash (1-qadamdan tanish)

# ---------- Sozlamalar ----------
SR = 16000            # sample rate — loyihamiz standarti
DAVOMIYLIK = 1.5      # sekund. Ataylab 1.0 dan uzunroq — zaxira bilan yozamiz,
                      # keyinroq standartla() funksiyamiz 1.0 sekundga keltiradi.
SOZ = "3"           # <<< QAYSI SO'ZNI YOZAYAPMIZ — har so'zdan oldin o'zgartiring!

# ---------- Papkani tayyorlash ----------
papka = f"../sinov/{SOZ}"
# exist_ok=True -> papka allaqachon bo'lsa, xato bermaydi (bo'lmasa yaratadi)
os.makedirs(papka, exist_ok=True)

# ---------- Raqamlashni davom ettirish ----------
# Agar papkada oldindan yozuvlar bo'lsa (masalan kecha 10 ta yozgansiz),
# 001 dan qayta boshlab USTIGA YOZIB YUBORMASLIK uchun mavjud fayllarni sanaymiz
# va keyingi raqamdan davom etamiz.
mavjud = [f for f in os.listdir(papka) if f.endswith(".wav")]
raqam = len(mavjud) + 1

print(f"So'z: '{SOZ}' | Papka: {papka} | Mavjud yozuvlar: {len(mavjud)}")
print("Har Enter = 1 yozuv. To'xtatish: Ctrl+C\n")

# ---------- Asosiy sikl ----------
try:
    while True:   # cheksiz sikl — Ctrl+C bosilguncha aylanadi
        input(f">> Enter bosing va ayting: '{SOZ}'  (keyingi: {raqam:03d}.wav)")

        # --- Yozib olish ---
        # sd.rec(nechta_nuqta, samplerate, channels):
        #   nechta_nuqta = SR * DAVOMIYLIK = 16000 * 1.5 = 24000 nuqta
        #   int(...) kerak, chunki 16000*1.5 kasr son chiqarishi mumkin
        #   channels=1 -> mono yozamiz (bizga stereo kerak emas)
        audio = sd.rec(int(SR * DAVOMIYLIK), samplerate=SR, channels=1)

        # sd.rec DARHOL qaytadi (yozish fonda davom etadi),
        # sd.wait() esa yozish TUGASHINI kutib turadi. Usiz yarim yozuv saqlanadi!
        sd.wait()

        # --- Shaklni tozalash ---
        # sd.rec natijasi 2 o'lchamli: (24000, 1) — "24000 qator, 1 ustun".
        # Bizga oddiy mono kerak: (24000,). [:, 0] -> "hamma qator, 0-ustun".
        audio = audio[:, 0]

        # --- Faylga saqlash ---
        # {raqam:03d} -> raqamni 3 xonali qiladi: 1 -> '001', 27 -> '027'.
        # Bu tartiblashda chiroyli: 001, 002 ... 010 (aks holda 1, 10, 2 bo'lardi)
        fayl = f"{papka}/{raqam:03d}.wav"
        sf.write(fayl, audio, SR)

        # Ovoz balandligini darhol ko'rsatamiz — o'z-o'zini tekshirish:
        # max qiymat 0.05 dan past bo'lsa, ovoz juda past yozilgan!
        eng_baland = abs(audio).max()
        ogohlantirish = "  <- JUDA PAST! Qaytadan yozing" if eng_baland < 0.05 else ""
        print(f"   Saqlandi: {fayl} | eng baland nuqta: {eng_baland:.2f}{ogohlantirish}\n")

        raqam += 1

except KeyboardInterrupt:
    # Ctrl+C bosilganda dastur "yiqilib" emas, chiroyli xayrlashib tugaydi
    print(f"\n\nTugadi! '{SOZ}' papkasida endi {raqam - 1} ta yozuv bor.")
    print("Keyingi so'z uchun: SOZ o'zgaruvchisini o'zgartirib qayta ishga tushiring.")