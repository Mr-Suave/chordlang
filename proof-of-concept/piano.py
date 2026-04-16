import numpy as np
import wave
import struct

sample_rate = 44100
duration = 10
bpm = 120
beat = 60 / bpm

t = np.linspace(0, duration, int(sample_rate * duration), False)

# -------------------------
# NOTES
# -------------------------
notes = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63,
    "G4": 392.00, "A3": 220.00, "F4": 349.23,
    "G3": 196.00, "C3": 130.81
}

# -------------------------
# PIANO TONE 
# -------------------------
def piano(freq, start, length):
    signal = np.zeros_like(t)
    mask = (t >= start) & (t < start + length)
    
    # richer tone (harmonics)
    wave = (
        np.sin(2*np.pi*freq*t[mask]) +
        0.5*np.sin(2*np.pi*2*freq*t[mask]) +
        0.25*np.sin(2*np.pi*3*freq*t[mask])
    )
    
    # fast attack + decay
    decay = np.exp(-4 * (t[mask] - start))
    signal[mask] = wave * decay
    return signal

# -------------------------
# BUILD TRACK
# -------------------------
final = np.zeros_like(t)

progression = [
    ["C4","E4","G4"],   # C
    ["A3","C4","E4"],   # Am
    ["F4","A3","C4"],   # F
    ["G3","D4","G4"]    # G
]

#  Left hand (bass + chord hits)
time = 0
for i in range(int(duration / beat)):
    chord = progression[(i // 4) % 4]
    
    # bass note on strong beats
    if i % 2 == 0:
        final += 0.6 * piano(notes[chord[0]]/2, time, 0.3)
    
    # chord stab
    for note in chord:
        final += 0.2 * piano(notes[note], time, 0.25)
    
    time += beat

#  Right hand (arpeggio = groove)
time = 0
for i in range(int(duration / (beat/2))):
    chord = progression[(i // 8) % 4]
    note = chord[i % 3]
    
    final += 0.4 * piano(notes[note], time, 0.2)
    time += beat/2

#  Melody (simple hook)
melody = ["E4","G4","E4","D4","C4","D4","E4","G4"]

time = 0
for note in melody * 2:
    final += 0.5 * piano(notes[note], time, 0.3)
    time += beat

# -------------------------
# NORMALIZE
# -------------------------
final = final / np.max(np.abs(final))

# -------------------------
# WRITE WAV
# -------------------------
with wave.open("piano_groove.wav", "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sample_rate)

    for s in final:
        f.writeframes(struct.pack('<h', int(s * 30000)))

print("Generated: piano_groove.wav")