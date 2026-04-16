import numpy as np
import wave
import struct

sample_rate = 44100
duration = 10
bpm = 130
beat_duration = 60 / bpm

t = np.linspace(0, duration, int(sample_rate * duration), False)

# -------------------------
# NOTES
# -------------------------
notes = {
    "E2": 82.41, "G2": 98.00, "A2": 110.00, "C3": 130.81
}

# -------------------------
# FUNCTIONS
# -------------------------
def sine(freq, time):
    return np.sin(2 * np.pi * freq * time)

def saw(freq, time):
    return 2 * (time * freq - np.floor(0.5 + time * freq))

def distortion(x):
    return np.tanh(4 * x)

def guitar(freq, start, length):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + length)
    
    root = saw(freq, t[mask])
    fifth = saw(freq * 1.5, t[mask])
    
    combined = distortion(root + 0.7 * fifth)
    
    decay = np.exp(-3 * (t[mask] - start))
    signal[mask] = combined * decay
    return signal

def bass(freq, start, length):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + length)
    signal[mask] = sine(freq, t[mask]) * 0.9
    return signal

def kick(start):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + 0.12)
    decay = np.exp(-30 * (t[mask] - start))
    signal[mask] = np.sin(2 * np.pi * 80 * t[mask]) * decay
    return signal

def snare(start):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + 0.1)
    noise = np.random.randn(np.sum(mask))
    decay = np.exp(-40 * (t[mask] - start))
    signal[mask] = noise * decay
    return signal

def hihat(start):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + 0.03)
    noise = np.random.randn(np.sum(mask))
    decay = np.exp(-80 * (t[mask] - start))
    signal[mask] = noise * decay
    return signal

# -------------------------
# BUILD TRACK
# -------------------------
final = np.zeros_like(t)

progression = ["E2", "G2", "A2", "C3"]

# 🎸 Guitar (fast strumming feel)
for i in range(int(duration / beat_duration)):
    beat_time = i * beat_duration
    freq = notes[progression[(i // 4) % 4]]
    
    # play short chugs every beat
    final += 0.5 * guitar(freq, beat_time, 0.2)

# 🎸 Bass (locked with beat)
for i in range(int(duration / beat_duration)):
    beat_time = i * beat_duration
    freq = notes[progression[(i // 4) % 4]]
    final += 0.6 * bass(freq, beat_time, 0.3)

# 🥁 Drums (proper groove)
for i in range(int(duration / beat_duration)):
    beat_time = i * beat_duration
    
    # Kick on 1 and 3
    if i % 4 == 0 or i % 4 == 2:
        final += 1.0 * kick(beat_time)
    
    # Snare on 2 and 4
    if i % 4 == 1 or i % 4 == 3:
        final += 0.8 * snare(beat_time)
    
    # Hi-hat every beat
    final += 0.2 * hihat(beat_time)

# -------------------------
# NORMALIZE
# -------------------------
final = final / np.max(np.abs(final))

# -------------------------
# WRITE WAV
# -------------------------
with wave.open("Beat.wav", "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sample_rate)

    for s in final:
        f.writeframes(struct.pack('<h', int(s * 30000)))

print("Generated: Beat.wav")