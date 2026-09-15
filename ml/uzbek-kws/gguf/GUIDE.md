# KichikKWS'ni llama.cpp / whisper.cpp-oilasi bilan mos GGUF qilish — qo'llanma

## 0. Xulosa (avval o'qing)

**To'g'ridan-to'g'ri "convert" qiladigan yo'l yo'q.** Faqat ikkita real yo'l bor
(3-bo'limga qarang), va ikkalasi ham hozirgi 3-so'zlik, 90-namunali loyihangiz
uchun mehnat/foyda nisbati juda yomon. Pastda nima uchun ekani va baribir
qilmoqchi bo'lsangiz nima qilish kerakligi yozilgan.

---

## 1. Bu vositalar ICHIDA qanday ishlaydi

`llama.cpp`, `whisper.cpp` va ulardan "ilhomlanib" yozilgan boshqa `*.cpp`
loyihalar (masalan `parakeet.cpp`) barchasi bitta umumiy naqshga amal qiladi:

1. GGUF fayl ochiladi, undan `general.architecture` (yoki shunga o'xshash)
   maydoni o'qiladi — masalan `"llama"`, `"whisper"`, `"parakeet"`.
2. Dastur ICHIDA, C++ manba kodida, O'SHA nom uchun QATTIQ YOZILGAN
   (compile vaqtida tayyor) forward-pass funksiyalari chaqiriladi.
3. GGUF'dagi tensorlar aniq, oldindan kelishilgan NOMLAR bo'yicha qidiriladi
   (masalan `blk.0.attn_q.weight`, `encoder.conv1.weight` va h.k.) — nom yoki
   shakl mos kelmasa, dastur xato beradi yoki ishga tushmaydi.

Ya'ni: **GGUF format o'zi "universal" emas — universal bo'lgani konteyner
(saqlash usuli), lekin uni O'QIYDIGAN dastur har doim arxitekturaga qattiq
bog'langan.** Plagin yoki "har qanday grafikni qabul qil" degan umumiy
mexanizm yo'q.

## 2. Nomlangan loyihalar haqida nimani ishonch bilan, nimani ishonchsiz bilaman

| Loyiha | Ishonch darajam | Izoh |
|---|---|---|
| `llama.cpp` | Yuqori | Matnli LLM (transformer) inference kutubxonasi, ggml asosida. Arxitektura ro'yxati (`llama`, `gemma`, `qwen2`, ...) manba kodida qattiq yozilgan. |
| `whisper.cpp` | Yuqori | OpenAI Whisper (nutq→matn, encoder-decoder, conv frontend + transformer) uchun ggml porti. |
| `parakeet.cpp` | O'rta | NVIDIA Parakeet (FastConformer + CTC/RNNT) uchun shunga o'xshash ggml-port loyiha borligini bilaman, lekin aniq tensor-nomlash konventsiyasi va joriy holatini tasdiqlay olmayman — repo'ni o'zingiz tekshirishingiz kerak. |
| `magpie.cpp` | Past / noaniq | Bu nom haqida ishonchli, tekshirilgan ma'lumotim yo'q. Balki men bilmaydigan yangi/tor doiradagi loyiha, balki nom boshqacha yozilishi kerak. **Bu haqidagi har qanday texnik da'voni tasdiqlanmagan deb hisoblang** — avval GitHub'dan repo mavjudligini, faolligini va README'sini tekshiring.

**Muhim:** mening bilim chekim 2026-yil yanvar bilan cheklangan, va hatto shu
sanagacha ham men niche/kam tanilgan loyihalarning barchasini bilmayman.
Nomlangan loyihalardan har birini ishlatishdan oldin ularning **o'z
GitHub repo'sidagi README va `convert_*.py` skriptlarini** albatta o'qib
chiqing — bu qo'llanmadagi umumiy tamoyillar to'g'ri, lekin har loyihaning
aniq tensor-nom sxemasi farq qiladi va vaqt o'tishi bilan o'zgarishi mumkin.

## 3. Nega KichikKWS hech biriga "to'g'ridan-to'g'ri" sig'maydi

Bu uchala loyiha ham quyidagi ikki toifadan biriga mo'ljallangan:

- **Katta til modellari** (token ketma-ketlik, embedding, self-attention
  qatlamlari) — `llama.cpp`
- **Nutq-encoder modellari** (mel-spektrogramma kirish, conv frontend +
  transformer/conformer bloklar, CTC yoki attention-decoder chiqish,
  odatda o'nlab-yuzlab million parametr) — `whisper.cpp`, `parakeet.cpp`

Sizning `KichikKWS` (2 ta Conv2d + 1 ta Linear, ~4,900 parametr, 3 klassli
oddiy klassifikator) bu ikkala qolipga ham mos emas — na token/attention
qatlamlari bor, na ularning kutayotgan qatlam-nomlash konventsiyasi
(`blk.N.*`, `encoder.layers.N.*` kabi) bilan mos keladi.

## 4. Real ikkita yo'l

### YO'L A — Modelni ULARNING arxitekturasiga moslab QAYTA o'rgatish

G'oya: whisper.cpp/parakeet.cpp'ning encoder qismini (yoki shunga o'xshash,
ular qo'llab-quvvatlaydigan tuzilishni) olib, ustiga oddiy classifier head
qo'shib, o'z datasetingizda o'rgatish. Shunda O'SHA loyihaning RASMIY
`convert_*.py` skripti ishlaydi, chunki tensor nomlari allaqachon mos.

Kamchiligi: bu modellar millionlab parametrli — 90 ta namunalik datasetingiz
uchun massasi ham, murakkabligi ham asossiz katta. Real foyda deyarli yo'q.

### YO'L B — cpp-loyihaning O'ZIGA yangi arxitektura qo'shish (fork + C++)

G'oya: loyihani fork qilib, ichiga "kichik_kws" nomli yangi arxitektura
yo'lini qo'lda yozish.

Umumiy qadamlar tartibi (checklist, kod emas — bu haqiqatda kichik bo'lmagan
C++ ishi):

1. Fork qiling, arxitektura ro'yxati qayerda ekanini toping (masalan
   `llama.cpp`da `src/llama-model.cpp`/`src/llama-arch.cpp`, `whisper.cpp`da
   asosiy `.cpp` fayl ichidagi model-yuklash funksiyasi).
2. GGUF'dan `general.architecture` o'qiladigan va shunga qarab tarmoqlanadigan
   joyni toping (odatda katta `if/switch` yoki enum orqali).
3. Yangi enum qiymati (`ARCH_KICHIK_KWS`) qo'shing.
4. `ggml_conv_2d`, `ggml_relu`, `ggml_pool_2d`, `ggml_mul_mat` kabi ggml C
   funksiyalari bilan aynan `qadam6.py`dagi grafikni (Conv→ReLU→Pool→Conv→
   ReLU→Pool→AvgPool→Linear) qo'lda quring.
5. `export_gguf.py`dagi tensor nomlarini shu yangi C++ kodning kutgan
   nomlariga moslang (yoki aksincha).
6. Butun loyihani qayta build qiling (`cmake`/`make`), keyin sinab ko'ring.

Bu — mavjud modelni "konvert qilish" emas, balki **llama.cpp/whisper.cpp
oilasiga yangi kichik model-turi qo'shish** darajasidagi hissa (C/C++
bilimi, ggml grafik API'siga oshnalik, va build tizimini tushunish talab
qiladi).

## 5. Tavsiya

Loyihangiz hajmi (3 so'z, 90 namuna, ~5 ming parametr) uchun `llama.cpp`/
`whisper.cpp`/`parakeet.cpp` oilasi noto'g'ri maqsad — ular og'ir nutq/LLM
modellari uchun optimallashtirilgan (SIMD, kvantlash, katta kontekst).
Agar maqsad "boshqa til/muhitda, tezkor va yengil ishlash" bo'lsa:

- **ONNX Runtime** — `torch.onnx.export` bilan bevosita eksport qilinadi,
  hech qanday qo'lda-forward-pass yozish shart emas, C++/C#/Java/JS/Python/
  mobil (Android/iOS) da tayyor ishlaydi.
- Yoki **sof `ggml` kutubxonasi** (llama.cpp'ning o'zi emas, faqat undagi
  tensor-hisoblash kutubxonasi) bilan o'zingiz mustaqil, mitti C dastur
  yozish — bu "mavjud dastur bilan ishlash" emas, "o'z dasturingizni
  yozish", lekin YO'L B'dan ancha kichikroq va real bajariladigan ish.

Ikkalasi ham hozirgi `gguf/infer_gguf.py`dagi (numpy'dagi) yondashuvdan
prinsipial farq qilmaydi — faqat tilni (Python→C++/C#) almashtiradi.
