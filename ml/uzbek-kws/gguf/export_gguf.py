"""
export_gguf.py — models/model_eng_yaxshi.pt (PyTorch) ni model.gguf faylga
eksport qiladi.

MUHIM: GGUF — llama.cpp/ggml ekotizimi uchun yaratilgan format. U hech qanday
CNN arxitekturasini "tanimaydi" — faqat tensorlar + metadata saqlaydigan
umumiy konteyner. Shu sababli bu yerda faqat OG'IRLIKLAR GGUF ga yoziladi;
forward pass mantig'ini o'qiydigan alohida infer_gguf.py yozilgan (llama.cpp
bilan mos emas, faqat shu loyihaning o'z ehtiyoji uchun).

ISHLATISH (uzbek-kws/gguf papkasidan, venv faol holda):
    python export_gguf.py
"""

import json
import os

import gguf
import torch

MODEL_PT = "../models/model_eng_yaxshi.pt"
SOZLAR_JSON = "../models/sozlar.json"
CHIQISH = "model.gguf"

writer = gguf.GGUFWriter(CHIQISH, arch="kichik_kws")

# ---------- Metadata: modelni qayta qurish uchun kerakli sozlamalar ----------
with open(SOZLAR_JSON, encoding="utf-8") as f:
    sozlar = json.load(f)

writer.add_string("kichik_kws.arxitektura", "Conv(1->16,k3,p1)-ReLU-MaxPool2"
                                             "-Conv(16->32,k3,p1)-ReLU-MaxPool2"
                                             "-AdaptiveAvgPool1-Linear(32->N)")
writer.add_array("kichik_kws.sozlar", sozlar)
writer.add_uint32("kichik_kws.son_klasslar", len(sozlar))
writer.add_uint32("kichik_kws.n_mels", 64)
writer.add_uint32("kichik_kws.sample_rate", 16000)
writer.add_uint32("kichik_kws.n_fft", 400)
writer.add_uint32("kichik_kws.hop_length", 160)

# ---------- Og'irliklar ----------
state_dict = torch.load(MODEL_PT, map_location="cpu")

nomlar_moslashtirish = {
    "features.0.weight": "conv1.weight",
    "features.0.bias": "conv1.bias",
    "features.3.weight": "conv2.weight",
    "features.3.bias": "conv2.bias",
    "classifier.2.weight": "fc.weight",
    "classifier.2.bias": "fc.bias",
}

for pt_nom, gguf_nom in nomlar_moslashtirish.items():
    tensor = state_dict[pt_nom].numpy().astype("float32")
    writer.add_tensor(gguf_nom, tensor)
    print(f"{pt_nom} -> {gguf_nom}  shakl={tuple(tensor.shape)}")

writer.write_header_to_file()
writer.write_kv_data_to_file()
writer.write_tensors_to_file()
writer.close()

hajm = os.path.getsize(CHIQISH)
print(f"\nTayyor: {CHIQISH} ({hajm} bayt)")
print("Diqqat: bu GGUF faylni llama.cpp/Ollama kabi dasturlar ISHGA "
      "TUSHIRA OLMAYDI — ular faqat tanish arxitekturalarni biladi. "
      "Faylni o'qish uchun shu papkadagi infer_gguf.py yozilgan.")
