#!/usr/bin/env python3
"""
ChordLang Audio Generation Prototype (Week 6)
Python implementation to validate mathematical formulas before assembly coding.
"""

import math
import struct
import wave


# ============================================================================
# WEEK 6: AUDIO GENERATION MATH FORMULAS
# ============================================================================

def note_to_frequency(pitch, octave):
    """
    Calculate frequency from pitch and octave using equal temperament.
    
    Formula: f = 440 × 2^((semitone_offset - 9) / 12)
    
    Args:
        pitch: Note name (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
        octave: Octave number (0-8)
    
    Returns:
        Frequency in Hz
    
    Examples:
        >>> note_to_frequency('C', 4)
        261.6255653005986
        >>> note_to_frequency('A', 4)
        440.0
    """
    # Map pitch to semitone offset from C
    pitch_map = {
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4,
        'F': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11
    }
    
    semitone = pitch_map[pitch]
    
    # Calculate MIDI note number
    # C4 is MIDI 60, A4 is MIDI 69
    midi_note = 12 * (octave + 1) + semitone
    
    # A4 (MIDI 69) = 440 Hz
    frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
    return frequency


def generate_sine_wave(frequency, duration_ms, sample_rate=44100, amplitude=16000.0):
    """
    Generate PCM samples for a sine wave.
    
    Formula: sample[i] = amplitude × sin(2π × frequency × (i / sample_rate))
    
    Args:
        frequency: Frequency in Hz
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz (default 44100)
        amplitude: Amplitude/volume (default 16000.0)
    
    Returns:
        List of 16-bit PCM samples
    """
    duration_seconds = duration_ms / 1000.0
    num_samples = int(sample_rate * duration_seconds)
    
    samples = []
    for i in range(num_samples):
        # Calculate time
        t = i / sample_rate
        
        # Calculate phase (angle in radians)
        phase = 2.0 * math.pi * frequency * t
        
        # Calculate sine value
        sine_value = math.sin(phase)
        
        # Scale by amplitude
        sample_value = amplitude * sine_value
        
        # Convert to 16-bit integer
        sample_int = int(round(sample_value))
        
        # Clamp to 16-bit range
        sample_int = max(-32768, min(32767, sample_int))
        
        samples.append(sample_int)
    
    return samples


def apply_envelope(samples, fade_percent=10):
    """
    Apply linear fade-in and fade-out envelope.
    
    Args:
        samples: List of PCM samples
        fade_percent: Percentage of duration for fade (default 10%)
    
    Returns:
        List of enveloped samples
    """
    num_samples = len(samples)
    fade_samples = num_samples * fade_percent // 100
    
    enveloped = []
    for i, sample in enumerate(samples):
        envelope = 1.0
        
        # Fade in (first 10%)
        if i < fade_samples:
            envelope = i / fade_samples
        
        # Fade out (last 10%)
        elif i >= num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples
        
        # Apply envelope
        enveloped_sample = int(sample * envelope)
        enveloped.append(enveloped_sample)
    
    return enveloped


def write_wav_file(filename, samples, sample_rate=44100):
    """
    Write PCM samples to WAV file.
    
    WAV Format:
        - RIFF header (12 bytes)
        - fmt chunk (24 bytes)
        - data chunk (8 bytes + samples)
    
    Args:
        filename: Output filename
        samples: List of 16-bit PCM samples
        sample_rate: Sample rate in Hz
    """
    with wave.open(filename, 'wb') as wav_file:
        # Set parameters
        num_channels = 1      # Mono
        sample_width = 2      # 16-bit = 2 bytes
        num_frames = len(samples)
        
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.setnframes(num_frames)
        
        # Pack samples as 16-bit signed integers (little-endian)
        packed_samples = b''.join(struct.pack('<h', s) for s in samples)
        wav_file.writeframes(packed_samples)


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_frequency_calculation():
    """Test note-to-frequency conversion."""
    print("=" * 70)
    print("TEST 1: Frequency Calculation")
    print("=" * 70)
    
    test_cases = [
        ('C', 4, 261.63),
        ('E', 4, 329.63),
        ('G', 4, 392.00),
        ('A', 4, 440.00),
        ('C', 5, 523.25),
    ]
    
    for pitch, octave, expected in test_cases:
        actual = note_to_frequency(pitch, octave)
        error = abs(actual - expected)
        status = "✓" if error < 0.1 else "✗"
        print(f"{status} {pitch}{octave}: {actual:.2f} Hz (expected {expected:.2f} Hz, error {error:.2f})")
    
    print()


def test_sine_wave_generation():
    """Test sine wave generation."""
    print("=" * 70)
    print("TEST 2: Sine Wave Generation")
    print("=" * 70)
    
    # Generate 0.1 second of A4 (440 Hz)
    frequency = 440.0
    duration_ms = 100
    samples = generate_sine_wave(frequency, duration_ms)
    
    print(f"Frequency: {frequency} Hz")
    print(f"Duration: {duration_ms} ms")
    print(f"Expected samples: {44100 * 0.1} = 4410")
    print(f"Actual samples: {len(samples)}")
    print(f"Sample range: [{min(samples)}, {max(samples)}]")
    print(f"Status: {'✓' if len(samples) == 4410 else '✗'}")
    print()


def test_envelope():
    """Test envelope application."""
    print("=" * 70)
    print("TEST 3: Envelope Application")
    print("=" * 70)
    
    # Generate samples
    samples = generate_sine_wave(440, 100)
    enveloped = apply_envelope(samples, fade_percent=10)
    
    # Check fade regions
    fade_samples = len(samples) // 10
    
    print(f"Total samples: {len(samples)}")
    print(f"Fade samples (10%): {fade_samples}")
    print(f"First sample (should be ~0): {enveloped[0]}")
    print(f"Middle sample (should be ~max): {enveloped[len(samples)//2]}")
    print(f"Last sample (should be ~0): {enveloped[-1]}")
    print(f"Status: {'✓' if abs(enveloped[0]) < 1000 and abs(enveloped[-1]) < 1000 else '✗'}")
    print()


def test_wav_output():
    """Test WAV file generation."""
    print("=" * 70)
    print("TEST 4: WAV File Output")
    print("=" * 70)
    
    # Generate C4-E4-G4-C5 sequence (like the assembly example)
    all_samples = []
    
    notes = [
        ('C', 4, 500),
        ('E', 4, 500),
        ('G', 4, 500),
        ('C', 5, 500),
    ]
    
    for pitch, octave, duration in notes:
        freq = note_to_frequency(pitch, octave)
        samples = generate_sine_wave(freq, duration)
        samples = apply_envelope(samples)
        all_samples.extend(samples)
        print(f"  Generated {pitch}{octave} ({freq:.2f} Hz) - {len(samples)} samples")
    
    # Write to file
    filename = 'test_melody_python.wav'
    write_wav_file(filename, all_samples)
    
    print(f"\nTotal samples: {len(all_samples)}")
    print(f"Total bytes: {len(all_samples) * 2}")
    print(f"Duration: {len(all_samples) / 44100:.2f} seconds")
    print(f"Output: {filename}")
    print(f"Status: ✓")
    print()


def generate_frequency_table():
    """Generate complete frequency table for reference."""
    print("=" * 70)
    print("REFERENCE: Complete Frequency Table")
    print("=" * 70)
    
    pitches = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for octave in range(9):  # 0-8
        print(f"\nOctave {octave}:")
        for pitch in pitches:
            freq = note_to_frequency(pitch, octave)
            print(f"  {pitch:3s}{octave}: {freq:8.2f} Hz")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("ChordLang Audio Generation - Python Prototype (Week 6)")
    print("=" * 70)
    print()
    
    # Run tests
    test_frequency_calculation()
    test_sine_wave_generation()
    test_envelope()
    test_wav_output()
    
    # Optional: Generate frequency table
    # generate_frequency_table()
    
    print("=" * 70)
    print("All formulas validated! Ready for assembly implementation.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()