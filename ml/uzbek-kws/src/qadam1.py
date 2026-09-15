import soundfile as sf

data, sr = sf.read("../sinov/bir_sinov.wav")

print("Sample rate:", sr)
print("Len data", len(data))
print("Data max", data.max())
print("Data min", data.min())


