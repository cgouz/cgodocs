"""
qadam7.py — O'RGATISH (YANGILANGAN VERSIYA).

BIRGA TOPGAN VA TUZATGAN XATOLARIMIZ TARIXI:
  1-xato: jami_loss har epoch'da nollanmasdi -> loss "o'sib" ko'rinardi
  2-xato: jami_loss += ... batch sikli TASHQARISIDA edi -> faqat oxirgi
          batch loss'i hisoblanardi (yolg'on "yaxshi" 0.47 ko'rsatardi)
  3-xato: print'da train loss'ni TEST soniga (18) bo'lardik -> 4x katta
          son chiqardi. Yechim: train_loss ni nollashdan OLDIN saqlash.
SABOQ: o'lchov asbobi buzuq bo'lsa, diagnostika ham yolg'on!

YANGI SOZLAMALAR (davolash tajribasi):
  LR:     0.001 -> 0.003  (kattaroq o'rganish qadami)
  EPOCHS: 30    -> 100    (ko'proq vaqt)
"""

import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from qadam5 import SozDataset
from qadam6 import KichikKWS

# ---------- Sozlamalar ----------
EPOCHS = 150      # 30 -> 100: modelga ko'proq vaqt beramiz
BATCH = 16
LR = 0.003        # 0.001 -> 0.003: kattaroq tuzatish qadami

# ---------- 1) Dataset va bo'linish ----------
dataset = SozDataset("../dataset")
print("So'zlar:", dataset.sozlar, "| Jami:", len(dataset))

test_n = int(0.2 * len(dataset))
train_n = len(dataset) - test_n

generator = torch.Generator().manual_seed(42)
train_set, test_set = random_split(dataset, [train_n, test_n], generator=generator)
print(f"Train: {len(train_set)} ta | Test: {len(test_set)} ta")

# ---------- 2) DataLoader ----------
train_loader = DataLoader(train_set, batch_size=BATCH, shuffle=True)
test_loader = DataLoader(test_set, batch_size=BATCH)

# ---------- 3) Model, hakam, murabbiy ----------
model = KichikKWS(son_klasslar=len(dataset.sozlar))
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

# ---------- 4) Asosiy sikl ----------
eng_yaxshi = 0.0

for epoch in range(1, EPOCHS + 1):

    # ========== O'RGATISH QISMI ==========
    model.train()
    togri, jami, jami_loss = 0, 0, 0.0        # har epoch boshida nollanadi!

    for spek, label in train_loader:
        optimizer.zero_grad()
        ballar = model(spek)                  # 1) bashorat
        loss = loss_fn(ballar, label)         # 2) xatoni o'lchash
        loss.backward()                       # 3) gradientlar
        optimizer.step()                      # 4) tuzatish

        # MUHIM: bu uch qator SIKL ICHIDA — har batch'da ishlaydi!
        jami_loss += loss.item() * label.size(0)
        togri += (ballar.argmax(1) == label).sum().item()
        jami += label.size(0)

    # Train natijalarini nollashdan OLDIN saqlab qo'yamiz (3-xato davosi):
    train_acc = togri / jami
    train_loss = jami_loss / jami

    # ========== IMTIHON QISMI ==========
    model.eval()
    togri, jami = 0, 0                        # endi bemalol nollasa bo'ladi
    with torch.no_grad():
        for spek, label in test_loader:
            ballar = model(spek)
            togri += (ballar.argmax(1) == label).sum().item()
            jami += label.size(0)
    test_acc = togri / jami

    # ========== Eng yaxshisini saqlash ==========
    belgi = ""
    if test_acc > eng_yaxshi:
        eng_yaxshi = test_acc
        torch.save(model.state_dict(), "../models/model_eng_yaxshi.pt")
        belgi = "  <- saqlandi!"

    # Har 5-epoch'da chiqaramiz (100 qator o'rniga 20 qator — o'qish oson).
    # Saqlangan epochlarni ham doim ko'rsatamiz.
    if epoch % 5 == 0 or belgi:
        print(f"Epoch {epoch:3d}/{EPOCHS} | loss: {train_loss:.3f} | "
              f"train: {train_acc:.1%} | test: {test_acc:.1%}{belgi}")

# ---------- 5) So'zlar ro'yxatini saqlash ----------
with open("../models/sozlar.json", "w", encoding="utf-8") as f:
    json.dump(dataset.sozlar, f, ensure_ascii=False)

print(f"\nTayyor! Eng yaxshi test aniqligi: {eng_yaxshi:.1%}")
print("Saqlandi: models/model_eng_yaxshi.pt va models/sozlar.json")