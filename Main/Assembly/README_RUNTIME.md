# ChordLang Assembly Runtime Library

**Week 7 Deliverable: Modular, tested assembly functions for audio generation**

## Overview

This is a complete x86-64 assembly runtime library for generating audio in ChordLang. The library provides modular, reusable functions that can be independently tested and used to build audio applications.

## Library Structure

```
audio_runtime.asm          - Main runtime library (9 functions)
test_envelope.asm          - Test for envelope calculation
test_sine_sample.asm       - Test for sine wave generation
test_runtime_complete.asm  - Integration test (generates WAV file)
Makefile                   - Build system
```

## Functions Provided

### 1. **init_audio_runtime**
Initialize the audio runtime library with default values.

```assembly
; Inputs:  None
; Outputs: None
```

Sets default amplitude (16000), tempo (120 BPM), and resets buffer position.

---

### 2. **set_amplitude**
Set global audio amplitude/volume.

```assembly
; Inputs:  xmm0 = amplitude (float, 0.0 to 32767.0)
; Outputs: None
```

Automatically clamps to valid 16-bit range.

---

### 3. **calculate_samples_for_duration**
Convert duration in milliseconds to number of PCM samples.

```assembly
; Inputs:  rdi = duration in milliseconds
; Outputs: rax = number of samples
```

Formula: `samples = (44100 * duration_ms) / 1000`

---

### 4. **generate_sine_sample**
Generate a single 16-bit PCM sample for a sine wave.

```assembly
; Inputs:  xmm0 = frequency (Hz, double precision)
;          xmm1 = time t (seconds, double precision)
;          xmm2 = amplitude (double precision)
; Outputs: rax = 16-bit PCM sample value
```

Formula: `sample = amplitude × sin(2π × frequency × t)`

Uses x87 FPU FSIN instruction for accurate sine calculation.

---

### 5. **calculate_envelope**
Calculate envelope multiplier for smooth fade-in/fade-out.

```assembly
; Inputs:  rdi = current sample index
;          rsi = total number of samples
; Outputs: xmm0 = envelope value (0.0 to 1.0)
```

- First 10%: Linear fade-in (0→1)
- Middle 80%: Full volume (1.0)
- Last 10%: Linear fade-out (1→0)

---

### 6. **generate_note**
Generate complete note with envelope and append to buffer.

```assembly
; Inputs:  xmm0 = frequency (Hz, single precision)
;          rdi = duration in milliseconds
; Outputs: rax = number of bytes written
```

Main high-level function that orchestrates:
- Duration → sample count conversion
- Envelope calculation
- Sine wave generation
- Buffer management

---

### 7. **generate_rest**
Generate silence for a given duration.

```assembly
; Inputs:  rdi = duration in milliseconds
; Outputs: rax = number of bytes written
```

Fills buffer with zeros (silence).

---

### 8. **get_buffer_data**
Get pointer and size of generated audio data.

```assembly
; Inputs:  None
; Outputs: rax = pointer to audio buffer
;          rdx = size in bytes
```

Used before writing to file or further processing.

---

### 9. **write_wav_header**
Generate WAV file header for 16-bit mono PCM at 44.1kHz.

```assembly
; Inputs:  rdi = output buffer pointer
;          rsi = total audio data size in bytes
; Outputs: rax = header size (44 bytes)
```

Creates proper RIFF/WAVE header with correct chunk sizes.

---

### 10. **reset_buffer**
Reset buffer position to start.

```assembly
; Inputs:  None
; Outputs: None
```

Use when starting a new composition.

---

### 11. **clamp_sample**
Clamp value to 16-bit signed range.

```assembly
; Inputs:  rdi = value to clamp
; Outputs: rax = clamped value ([-32768, 32767])
```

Utility function for preventing overflow.

---

## Building

### Requirements
- NASM (Netwide Assembler)
- ld (GNU linker)
- Linux x86-64 system

### Build Commands

```bash
# Build everything
make all

# Build only the library
make library

# Build and run all tests
make test

# Clean build artifacts
make clean
```

## Testing

### Test 1: Envelope Function
```bash
make test_envelope
./test_envelope
```

Tests fade-in, sustain, and fade-out calculations.

Expected output:
```
TEST: calculate_envelope
Fade-in (sample 50/1000): OK
Sustain (sample 500/1000): OK
Fade-out (sample 950/1000): OK
```

---

### Test 2: Sine Sample Generation
```bash
make test_sine_sample
./test_sine_sample
```

Generates samples for A4 (440 Hz) and validates output.

Expected output:
```
TEST: generate_sine_sample (A4 = 440Hz)
Sample 0
PASS
```

---

### Test 3: Complete Integration Test
```bash
make test_runtime_complete
./test_runtime_complete
```

Generates a 4-note melody (C4-E4-G4-C5) with rests.

Expected output:
```
Initializing audio runtime...
Generating notes...
Writing WAV file...
Done! Output: test_output.wav
```

Verify output:
```bash
# Check file created
ls -lh test_output.wav

# Validate WAV format
file test_output.wav
# Should show: RIFF (little-endian) data, WAVE audio, mono 44100 Hz

# Play audio
aplay test_output.wav
```

## Example Usage

```assembly
extern init_audio_runtime
extern set_amplitude
extern generate_note
extern get_buffer_data
extern write_wav_header

section .data
    note_c4 dd 261.63

section .text
global _start

_start:
    ; Initialize
    call init_audio_runtime
    
    ; Set volume
    mov eax, 15000
    cvtsi2ss xmm0, eax
    call set_amplitude
    
    ; Generate C4 for 500ms
    movss xmm0, [note_c4]
    mov rdi, 500
    call generate_note
    
    ; Get buffer data
    call get_buffer_data
    ; rax = buffer pointer
    ; rdx = data size
    
    ; ... write to file ...
```

## Technical Details

### Register Usage
- **r15**: Global buffer position (persistent)
- **r12-r14**: Function-local counters/temps
- **xmm0-xmm7**: Floating-point calculations
- **ST(0)**: x87 FPU stack for FSIN

### Memory Layout
- **audio_buffer**: 882,000 bytes (10 seconds max)
- **temp_buffer**: 88,200 bytes (1 second scratch)

### Audio Format
- **Sample Rate**: 44,100 Hz
- **Bit Depth**: 16-bit signed PCM
- **Channels**: 1 (mono)
- **Byte Order**: Little-endian

## Function Dependencies

```
init_audio_runtime
    └─ (standalone)

set_amplitude
    └─ (standalone)

calculate_samples_for_duration
    └─ (standalone)

generate_sine_sample
    └─ (standalone, uses x87 FPU)

calculate_envelope
    └─ (standalone)

generate_note
    ├─ calculate_samples_for_duration
    ├─ calculate_envelope
    └─ generate_sine_sample

generate_rest
    └─ calculate_samples_for_duration

get_buffer_data
    └─ (standalone)

write_wav_header
    └─ (standalone)

reset_buffer
    └─ (standalone)

clamp_sample
    └─ (standalone)
```

## Performance

Approximate timings on 3 GHz x86-64:
- `generate_sine_sample`: ~100 cycles (~33 ns)
- `calculate_envelope`: ~50 cycles (~17 ns)
- `generate_note` (500ms): ~2.2M cycles (~0.7 ms)

## Limitations

1. **Maximum Duration**: 10 seconds of audio (882,000 bytes buffer)
2. **Sample Rate**: Fixed at 44,100 Hz
3. **Channels**: Mono only
4. **Bit Depth**: 16-bit only
5. **No Chord Support**: Currently only single notes

## Future Enhancements

- [ ] Chord generation (simultaneous notes)
- [ ] Variable sample rates
- [ ] Stereo output
- [ ] Different waveforms (square, triangle, sawtooth)
- [ ] ADSR envelope with configurable parameters
- [ ] Vibrato and tremolo effects

## License

This is educational code for the ChordLang compiler project.

## Authors

Team: Aryan Chauhan, Tejas Karthik, Anvay Joshi
Course: Compiler Design Laboratory

---

**Week 7 Status**: ✅ Complete - All functions implemented and tested
