import soundfile as sf
import numpy as np

# Har klassdan bitta faylni tekshiramiz
for soz in ["bir", "ikki", "uch"]:
    data, sr = sf.read(f"../dataset/{soz}/001.wav")

    # Faylning eng "jim" chorak qismini topamiz — u yerda faqat shovqin bor
    chorak = len(data) // 4
    bolaklar = [data[i:i+chorak] for i in range(0, len(data)-chorak, chorak)]
    shovqin = min(np.abs(b).mean() for b in bolaklar)   # eng jim bo'lak

    # Eng baland qism — so'zning o'zi
    signal = np.abs(data).max()

    print(f"{soz}: signal={signal:.3f} | shovqin={shovqin:.4f} | "
          f"nisbat={signal/shovqin:.0f}x")