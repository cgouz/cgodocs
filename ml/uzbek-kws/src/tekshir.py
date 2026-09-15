import matplotlib.pyplot as plt
from qadam5 import SozDataset

dataset = SozDataset("../dataset")

# 3 qator (so'zlar) x 3 ustun (namunalar) panjara
fig, oqlar = plt.subplots(3, 3, figsize=(12, 8))

# har klassning boshidan 3 tadan: bir=0,1,2  ikki=30,31,32  uch=60,61,62
indekslar = [0, 1, 2, 30, 31, 32, 60, 61, 62]

for oq, idx in zip(oqlar.flat, indekslar):
    spek, label = dataset[idx]
    oq.imshow(spek[0], origin="lower", aspect="auto", cmap="magma")
    oq.set_title(f"{dataset.sozlar[label]} (#{idx})")
    oq.axis("off")

plt.tight_layout()
plt.savefig("../sinov/dataset_tekshiruv.png")
plt.show()