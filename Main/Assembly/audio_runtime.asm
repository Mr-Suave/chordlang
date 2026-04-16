; Enhanced ChordLang Audio Runtime Library
; Supports multiple instruments with different waveforms

section .data
    ; Audio parameters
    sample_rate dd 44100
    two_pi dq 6.28318530718
    default_amplitude dd 16000.0
    
    ; Instrument IDs
    INSTR_PIANO     equ 0
    INSTR_GUITAR    equ 1
    INSTR_BASS      equ 2
    INSTR_SAW       equ 3
    INSTR_SQUARE    equ 4
    INSTR_KICK      equ 5
    INSTR_SNARE     equ 6
    INSTR_HIHAT     equ 7

section .bss
    ; Global buffers
    audio_buffer resb 8820000       ; 100 seconds max
    temp_buffer resb 882000         ; 10 seconds temp
    
    ; Runtime state
    current_amplitude resd 1
    current_tempo resd 1
    current_instrument resd 1       ; Current instrument ID
    buffer_position resd 1

section .text

; ============================================================================
; FUNCTION: init_audio_runtime
; ============================================================================
global init_audio_runtime
init_audio_runtime:
    push rbp
    mov rbp, rsp
    
    mov eax, [default_amplitude]
    mov [current_amplitude], eax
    mov dword [current_tempo], 120
    mov dword [current_instrument], INSTR_PIANO  ; Default to piano
    mov dword [buffer_position], 0
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: set_instrument
; Set the current instrument
; Inputs: rdi = instrument ID (0-7)
; ============================================================================
global set_instrument
set_instrument:
    push rbp
    mov rbp, rsp
    
    ; Validate instrument ID (0-7)
    cmp rdi, 7
    jg .invalid
    cmp rdi, 0
    jl .invalid
    
    mov [current_instrument], edi
    jmp .done
    
.invalid:
    ; Default to piano if invalid
    mov dword [current_instrument], INSTR_PIANO
    
.done:
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_piano_sample
; Piano: Combination of harmonics (1.0 * sin + 0.5 * sin(2f) + 0.25 * sin(4f))
; Inputs: xmm0 = frequency, xmm1 = time t, xmm2 = amplitude
; Outputs: rax = PCM sample
; ============================================================================
global generate_piano_sample
generate_piano_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    
    ; Save inputs
    movsd [rsp], xmm0       ; freq
    movsd [rsp+8], xmm1     ; t
    movsd [rsp+16], xmm2    ; amplitude
    
    ; Fundamental (1.0 * sin(2πft))
    movsd xmm3, xmm0
    mulsd xmm3, xmm1
    mulsd xmm3, [two_pi]
    
    movsd [rsp+24], xmm3
    fld qword [rsp+24]
    fsin
    fstp qword [rsp+24]
    movsd xmm4, [rsp+24]    ; xmm4 = sin(2πft)
    
    ; Second harmonic (0.5 * sin(4πft))
    movsd xmm0, [rsp]
    movsd xmm1, [rsp+8]
    movsd xmm3, xmm0
    addsd xmm3, xmm3        ; 2f
    mulsd xmm3, xmm1
    mulsd xmm3, [two_pi]
    
    movsd [rsp+24], xmm3
    fld qword [rsp+24]
    fsin
    fstp qword [rsp+24]
    movsd xmm5, [rsp+24]
    
    mov rax, 0x3FE0000000000000  ; 0.5 in double
    movq xmm6, rax
    mulsd xmm5, xmm6        ; xmm5 = 0.5 * sin(4πft)
    
    ; Third harmonic (0.25 * sin(8πft))
    movsd xmm0, [rsp]
    movsd xmm1, [rsp+8]
    movsd xmm3, xmm0
    addsd xmm3, xmm3
    addsd xmm3, xmm3        ; 4f
    mulsd xmm3, xmm1
    mulsd xmm3, [two_pi]
    
    movsd [rsp+24], xmm3
    fld qword [rsp+24]
    fsin
    fstp qword [rsp+24]
    movsd xmm6, [rsp+24]
    
    mov rax, 0x3FD0000000000000  ; 0.25 in double
    movq xmm7, rax
    mulsd xmm6, xmm7        ; xmm6 = 0.25 * sin(8πft)
    
    ; Combine: fundamental + second + third
    addsd xmm4, xmm5
    addsd xmm4, xmm6
    
    ; Apply amplitude
    movsd xmm2, [rsp+16]
    mulsd xmm4, xmm2
    
    ; Convert to int
    cvttsd2si rax, xmm4
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 32
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_guitar_sample
; Guitar: Sawtooth wave with distortion and decay
; y = tanh(4 * (saw(f) + 0.7 * saw(1.5f))) * exp(-3t)
; ============================================================================
global generate_guitar_sample
generate_guitar_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    
    movsd [rsp], xmm0       ; freq
    movsd [rsp+8], xmm1     ; t
    movsd [rsp+16], xmm2    ; amplitude
    
    ; Sawtooth: 2 * (t*f - floor(0.5 + t*f))
    movsd xmm3, xmm0
    mulsd xmm3, xmm1        ; t*f
    
    movsd xmm4, xmm3
    mov rax, 0x3FE0000000000000  ; 0.5
    movq xmm5, rax
    addsd xmm4, xmm5        ; 0.5 + t*f
    
    ; Floor function (using cvttsd2si and back)
    cvttsd2si r8, xmm4
    cvtsi2sd xmm6, r8
    
    subsd xmm3, xmm6        ; t*f - floor(0.5 + t*f)
    addsd xmm3, xmm3        ; 2 * (...)
    
    ; Save root sawtooth
    movsd xmm7, xmm3
    
    ; Fifth harmonic: 1.5f
    movsd xmm0, [rsp]
    movsd xmm1, [rsp+8]
    mov rax, 0x3FF8000000000000  ; 1.5
    movq xmm4, rax
    mulsd xmm0, xmm4        ; 1.5 * freq
    
    ; Generate sawtooth for fifth
    mulsd xmm0, xmm1
    movsd xmm4, xmm0
    mov rax, 0x3FE0000000000000
    movq xmm5, rax
    addsd xmm4, xmm5
    cvttsd2si r8, xmm4
    cvtsi2sd xmm6, r8
    subsd xmm0, xmm6
    addsd xmm0, xmm0
    
    ; Combine: root + 0.7 * fifth
    mov rax, 0x3FE6666666666666  ; 0.7
    movq xmm5, rax
    mulsd xmm0, xmm5
    addsd xmm7, xmm0        ; combined
    
    ; Apply distortion: tanh(4 * x) ≈ clamp(4*x, -1, 1)
    mov rax, 0x4010000000000000  ; 4.0
    movq xmm4, rax
    mulsd xmm7, xmm4
    
    ; Clamp to [-1, 1]
    mov rax, 0x3FF0000000000000  ; 1.0
    movq xmm5, rax
    minsd xmm7, xmm5
    mov rax, 0xBFF0000000000000  ; -1.0
    movq xmm5, rax
    maxsd xmm7, xmm5
    
    ; Apply decay: exp(-3t)
    movsd xmm1, [rsp+8]
    mov rax, 0xC008000000000000  ; -3.0
    movq xmm4, rax
    mulsd xmm1, xmm4        ; -3t
    
    ; Approximate exp(x) using: 1 + x + x²/2 (for small x)
    movsd xmm5, xmm1
    mulsd xmm5, xmm1        ; x²
    mov rax, 0x3FE0000000000000  ; 0.5
    movq xmm6, rax
    mulsd xmm5, xmm6        ; x²/2
    addsd xmm5, xmm1        ; x + x²/2
    mov rax, 0x3FF0000000000000  ; 1.0
    movq xmm6, rax
    addsd xmm5, xmm6        ; decay = 1 + x + x²/2
    
    ; Apply decay and amplitude
    mulsd xmm7, xmm5
    movsd xmm2, [rsp+16]
    mulsd xmm7, xmm2
    
    ; Convert to int
    cvttsd2si rax, xmm7
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 32
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_bass_sample
; Bass: Pure sine wave with strong fundamental
; ============================================================================
global generate_bass_sample
generate_bass_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    
    ; Calculate 2π * freq * t
    movsd xmm3, xmm0
    mulsd xmm3, xmm1
    mulsd xmm3, [two_pi]
    
    ; sin(2πft)
    movsd [rsp], xmm3
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm4, [rsp]
    
    ; Apply amplitude * 0.9 (bass is strong)
    mov rax, 0x3FECCCCCCCCCCCCD  ; 0.9
    movq xmm5, rax
    mulsd xmm2, xmm5
    mulsd xmm4, xmm2
    
    ; Convert to int
    cvttsd2si rax, xmm4
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 16
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_sawtooth_sample
; Sawtooth wave: 2 * (t*f - floor(0.5 + t*f))
; ============================================================================
global generate_sawtooth_sample
generate_sawtooth_sample:
    push rbp
    mov rbp, rsp
    
    ; saw = 2 * (t*f - floor(0.5 + t*f))
    movsd xmm3, xmm0
    mulsd xmm3, xmm1
    
    movsd xmm4, xmm3
    mov rax, 0x3FE0000000000000  ; 0.5
    movq xmm5, rax
    addsd xmm4, xmm5
    
    cvttsd2si r8, xmm4
    cvtsi2sd xmm6, r8
    
    subsd xmm3, xmm6
    addsd xmm3, xmm3
    
    ; Apply amplitude
    mulsd xmm3, xmm2
    
    cvttsd2si rax, xmm3
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_square_sample
; Square wave: sign(sin(2πft))
; ============================================================================
global generate_square_sample
generate_square_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    
    ; Calculate 2π * freq * t
    movsd xmm3, xmm0
    mulsd xmm3, xmm1
    mulsd xmm3, [two_pi]
    
    ; sin(2πft)
    movsd [rsp], xmm3
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm4, [rsp]
    
    ; Get sign (-1 or +1)
    xorpd xmm5, xmm5
    comisd xmm4, xmm5
    jb .negative
    
    mov rax, 0x3FF0000000000000  ; 1.0
    movq xmm4, rax
    jmp .apply_amp
    
.negative:
    mov rax, 0xBFF0000000000000  ; -1.0
    movq xmm4, rax
    
.apply_amp:
    mulsd xmm4, xmm2
    cvttsd2si rax, xmm4
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 16
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_kick_sample  
; Kick drum: sin(2π * 80Hz * t) * exp(-30t)
; Short duration, low frequency with fast decay
; ============================================================================
global generate_kick_sample
generate_kick_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    
    ; Kick frequency = 80 Hz
    mov rax, 0x4054000000000000  ; 80.0
    movq xmm0, rax
    
    ; sin(2π * 80 * t)
    mulsd xmm0, xmm1
    mulsd xmm0, [two_pi]
    
    movsd [rsp], xmm0
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm4, [rsp]
    
    ; exp(-30t) approximation
    mov rax, 0xC03E000000000000  ; -30.0
    movq xmm5, rax
    mulsd xmm5, xmm1
    
    ; 1 + x + x²/2 approximation
    movsd xmm6, xmm5
    mulsd xmm6, xmm6
    mov rax, 0x3FE0000000000000
    movq xmm7, rax
    mulsd xmm6, xmm7
    addsd xmm6, xmm5
    mov rax, 0x3FF0000000000000
    movq xmm7, rax
    addsd xmm6, xmm7
    
    ; Apply decay and amplitude
    mulsd xmm4, xmm6
    mulsd xmm4, xmm2
    
    cvttsd2si rax, xmm4
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 16
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_snare_sample
; Snare: White noise * exp(-40t)
; Uses simple PRNG for noise
; ============================================================================
global generate_snare_sample
generate_snare_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    
    ; Simple PRNG for noise: (seed * 1103515245 + 12345) & 0x7FFFFFFF
    ; Use time-based seed
    movsd [rsp], xmm1
    fld qword [rsp]
    fistp dword [rsp]
    mov eax, [rsp]
    
    imul eax, 1103515245
    add eax, 12345
    and eax, 0x7FFFFFFF
    
    ; Convert to [-1, 1]
    cvtsi2sd xmm4, eax
    mov rax, 0x41E0000000000000  ; 2^31
    movq xmm5, rax
    divsd xmm4, xmm5
    mov rax, 0x3FF0000000000000
    movq xmm5, rax
    subsd xmm4, xmm5
    
    ; exp(-40t) decay
    mov rax, 0xC044000000000000  ; -40.0
    movq xmm5, rax
    mulsd xmm5, xmm1
    
    ; Approximation
    movsd xmm6, xmm5
    mulsd xmm6, xmm6
    mov rax, 0x3FE0000000000000
    movq xmm7, rax
    mulsd xmm6, xmm7
    addsd xmm6, xmm5
    mov rax, 0x3FF0000000000000
    movq xmm7, rax
    addsd xmm6, xmm7
    
    ; Apply decay and amplitude
    mulsd xmm4, xmm6
    mulsd xmm4, xmm2
    
    cvttsd2si rax, xmm4
    
    ; Clamp
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 16
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_hihat_sample
; Hi-hat: White noise * exp(-80t) (faster decay than snare)
; ============================================================================
global generate_hihat_sample
generate_hihat_sample:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    
    ; PRNG
    movsd [rsp], xmm1
    fld qword [rsp]
    fistp dword [rsp]
    mov eax, [rsp]
    
    imul eax, 1103515245
    add eax, 12345
    and eax, 0x7FFFFFFF
    
    cvtsi2sd xmm4, eax
    mov rax, 0x41E0000000000000
    movq xmm5, rax
    divsd xmm4, xmm5
    mov rax, 0x3FF0000000000000
    movq xmm5, rax
    subsd xmm4, xmm5
    
    ; exp(-80t) very fast decay
    mov rax, 0xC054000000000000  ; -80.0
    movq xmm5, rax
    mulsd xmm5, xmm1
    
    movsd xmm6, xmm5
    mulsd xmm6, xmm6
    mov rax, 0x3FE0000000000000
    movq xmm7, rax
    mulsd xmm6, xmm7
    addsd xmm6, xmm5
    mov rax, 0x3FF0000000000000
    movq xmm7, rax
    addsd xmm6, xmm7
    
    mulsd xmm4, xmm6
    mulsd xmm4, xmm2
    
    cvttsd2si rax, xmm4
    
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    add rsp, 16
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_sample_by_instrument
; Dispatcher: calls appropriate waveform generator based on current instrument
; Inputs: xmm0 = freq, xmm1 = time, xmm2 = amplitude
; Outputs: rax = PCM sample
; ============================================================================
global generate_sample_by_instrument
generate_sample_by_instrument:
    push rbp
    mov rbp, rsp
    
    mov eax, [current_instrument]
    
    cmp eax, INSTR_PIANO
    je .piano
    cmp eax, INSTR_GUITAR
    je .guitar
    cmp eax, INSTR_BASS
    je .bass
    cmp eax, INSTR_SAW
    je .saw
    cmp eax, INSTR_SQUARE
    je .square
    cmp eax, INSTR_KICK
    je .kick
    cmp eax, INSTR_SNARE
    je .snare
    cmp eax, INSTR_HIHAT
    je .hihat
    
.piano:
    call generate_piano_sample
    jmp .done
    
.guitar:
    call generate_guitar_sample
    jmp .done
    
.bass:
    call generate_bass_sample
    jmp .done
    
.saw:
    call generate_sawtooth_sample
    jmp .done
    
.square:
    call generate_square_sample
    jmp .done
    
.kick:
    call generate_kick_sample
    jmp .done
    
.snare:
    call generate_snare_sample
    jmp .done
    
.hihat:
    call generate_hihat_sample
    
.done:
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_note
; Modified to be robust against register clobbering
; ============================================================================
global generate_note
generate_note:
    push rbp
    mov rbp, rsp
    sub rsp, 32             ; Space for local variables
    push r12
    push r13
    push r14
    push r15
    
    ; Save frequency and max amplitude to stack (persist across calls)
    cvtss2sd xmm7, xmm0
    movsd [rbp-8], xmm7     ; [rbp-8]  = frequency (double)
    cvtss2sd xmm6, [current_amplitude]
    movsd [rbp-16], xmm6    ; [rbp-16] = max amplitude (double)
    
    push rdi                ; duration ms
    call calculate_samples_for_duration
    mov r12, rax            ; r12 = total samples
    pop rdi
    
    mov r15d, [buffer_position]
    xor r13, r13            ; r13 = current sample index
    
.loop:
    cmp r13, r12
    jge .done
    
    ; Calculate envelope
    mov rdi, r13
    mov rsi, r12
    call calculate_envelope ; returns multiplier in xmm0
    
    ; Apply envelope to max amplitude
    movsd xmm2, [rbp-16]    ; reload max amplitude
    mulsd xmm2, xmm0        ; xmm2 = current amplitude
    
    ; Setup frequency and time for instrument
    movsd xmm0, [rbp-8]     ; reload frequency
    
    cvtsi2sd xmm1, r13
    cvtsi2sd xmm3, dword [sample_rate]
    divsd xmm1, xmm3        ; xmm1 = t (seconds)
    
    call generate_sample_by_instrument
    
    ; Store 16-bit sample
    mov word [audio_buffer + r15], ax
    add r15, 2
    
    inc r13
    jmp .loop
    
.done:
    mov [buffer_position], r15d
    
    pop r15
    pop r14
    pop r13
    pop r12
    add rsp, 32
    pop rbp
    ret


; (Keep all other functions from original: generate_rest, get_buffer_data, 
;  write_wav_header, calculate_samples_for_duration, calculate_envelope, etc.)

; ============================================================================
; FUNCTION: set_amplitude
; Set the global amplitude/volume
; 
; Inputs:  xmm0 = amplitude (float, 0.0 to 32767.0)
; Outputs: None
; Modifies: [current_amplitude]
; ============================================================================
global set_amplitude
set_amplitude:
    push rbp
    mov rbp, rsp
    
    ; Clamp to valid range [0, 32767]
    cvttss2si eax, xmm0
    cmp eax, 0
    jge .not_negative
    xor eax, eax
.not_negative:
    cmp eax, 32767
    jle .not_too_high
    mov eax, 32767
.not_too_high:
    
    ; Convert back to float and store
    cvtsi2ss xmm0, eax
    movss [current_amplitude], xmm0
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: calculate_samples_for_duration
; Calculate number of samples for a given duration in milliseconds
; 
; Inputs:  rdi = duration in milliseconds
; Outputs: rax = number of samples
; Modifies: rax, rdx
; 
; Formula: samples = (sample_rate * duration_ms) / 1000
; ============================================================================
global calculate_samples_for_duration
calculate_samples_for_duration:
    push rbp
    mov rbp, rsp
    
    ; Load sample rate
    mov eax, [sample_rate]
    
    ; Multiply by duration
    mul rdi                     ; rax = sample_rate * duration_ms
    
    ; Divide by 1000
    mov rcx, 1000
    xor rdx, rdx
    div rcx                     ; rax = samples
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: generate_sine_sample
; Generate a single PCM sample for a sine wave at time t
; 
; Inputs:  xmm0 = frequency (Hz, double precision)
;          xmm1 = time t (seconds, double precision)
;          xmm2 = amplitude (double precision)
; Outputs: rax = 16-bit PCM sample value
; Modifies: rax, xmm3, xmm4, ST(0)
; 
; Formula: sample = amplitude * sin(2π * frequency * t)
; ============================================================================
global generate_sine_sample
generate_sine_sample:
    push rbp
    mov rbp, rsp
    
    ; Calculate phase: 2π * freq * t
    movsd xmm3, xmm0            ; xmm3 = frequency
    mulsd xmm3, xmm1            ; xmm3 = freq * t
    mulsd xmm3, [two_pi]        ; xmm3 = 2π * freq * t
    
    ; Calculate sine using x87 FPU
    sub rsp, 8
    movsd [rsp], xmm3
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm4, [rsp]
    add rsp, 8
    
    ; Apply amplitude
    mulsd xmm4, xmm2            ; xmm4 = amplitude * sin(...)
    
    ; Convert to 16-bit integer
    cvttsd2si rax, xmm4
    
    ; Clamp to 16-bit range
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: calculate_envelope
; Calculate envelope multiplier for a given sample position
; Uses linear fade-in/fade-out (10% of total duration each)
; 
; Inputs:  rdi = current sample index (i)
;          rsi = total number of samples
; Outputs: xmm0 = envelope value (0.0 to 1.0, double precision)
; Modifies: rax, rdx, xmm0, xmm1
; ============================================================================
global calculate_envelope
calculate_envelope:
    push rbp
    mov rbp, rsp
    
    ; Calculate fade_samples = total_samples / 10
    mov rax, rsi
    mov rcx, 10
    xor rdx, rdx
    div rcx                     ; rax = fade_samples
    
    ; Check if in fade-in region (i < fade_samples)
    cmp rdi, rax
    jge .check_fadeout
    
    ; Fade in: envelope = i / fade_samples
    cvtsi2sd xmm0, rdi
    cvtsi2sd xmm1, rax
    divsd xmm0, xmm1
    jmp .done
    
.check_fadeout:
    ; Calculate fade boundary
    mov rcx, rsi
    sub rcx, rax                ; rcx = total - fade_samples
    
    ; Check if in fade-out region
    cmp rdi, rcx
    jl .sustain
    
    ; Fade out: envelope = (total - i) / fade_samples
    mov rcx, rsi
    sub rcx, rdi                ; rcx = total - i
    cvtsi2sd xmm0, rcx
    cvtsi2sd xmm1, rax
    divsd xmm0, xmm1
    jmp .done
    
.sustain:
    ; Full volume
    mov rax, 1
    cvtsi2sd xmm0, rax
    
.done:
    pop rbp
    ret



; ============================================================================
; FUNCTION: generate_rest
; Generate silence (rest) for a given duration
; 
; Inputs:  rdi = duration in milliseconds
; Outputs: rax = number of bytes written
; Modifies: rax, rcx, updates buffer_position
; ============================================================================
global generate_rest
generate_rest:
    push rbp
    mov rbp, rsp
    
    ; Calculate number of samples
    call calculate_samples_for_duration
    mov rcx, rax                ; rcx = num_samples
    
    ; Load current buffer position
    mov r8d, [buffer_position]
    
    ; Fill with zeros
.loop:
    test rcx, rcx
    jz .done
    
    mov word [audio_buffer + r8], 0
    add r8, 2
    dec rcx
    jmp .loop
    
.done:
    ; Update buffer position
    mov [buffer_position], r8d
    
    ; Return bytes written
    mov rax, r8
    sub eax, [buffer_position]
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: get_buffer_data
; Get pointer and size of current audio buffer
; 
; Inputs:  None
; Outputs: rax = pointer to audio buffer
;          rdx = size in bytes
; Modifies: rax, rdx
; ============================================================================
global get_buffer_data
get_buffer_data:
    push rbp
    mov rbp, rsp
    
    mov rax, audio_buffer
    mov edx, [buffer_position]
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: reset_buffer
; Reset audio buffer position to start
; 
; Inputs:  None
; Outputs: None
; Modifies: [buffer_position]
; ============================================================================
global reset_buffer
reset_buffer:
    push rbp
    mov rbp, rsp
    
    mov dword [buffer_position], 0
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: write_wav_header
; Write WAV file header to buffer
; 
; Inputs:  rdi = output buffer pointer
;          rsi = total audio data size in bytes
; Outputs: rax = number of bytes written (44)
; Modifies: rax, rcx, rdi
; ============================================================================
global write_wav_header
write_wav_header:
    push rbp
    mov rbp, rsp
    
    mov rcx, rdi                ; Save buffer pointer
    
    ; RIFF header
    mov byte [rcx], 'R'
    mov byte [rcx+1], 'I'
    mov byte [rcx+2], 'F'
    mov byte [rcx+3], 'F'
    add rcx, 4
    
    ; ChunkSize = 36 + data_size
    mov eax, esi
    add eax, 36
    mov [rcx], eax
    add rcx, 4
    
    ; WAVE format
    mov byte [rcx], 'W'
    mov byte [rcx+1], 'A'
    mov byte [rcx+2], 'V'
    mov byte [rcx+3], 'E'
    add rcx, 4
    
    ; fmt subchunk
    mov byte [rcx], 'f'
    mov byte [rcx+1], 'm'
    mov byte [rcx+2], 't'
    mov byte [rcx+3], ' '
    add rcx, 4
    
    mov dword [rcx], 16         ; Subchunk1Size
    add rcx, 4
    
    mov word [rcx], 1           ; AudioFormat (PCM)
    add rcx, 2
    
    mov word [rcx], 1           ; NumChannels (mono)
    add rcx, 2
    
    mov dword [rcx], 44100      ; SampleRate
    add rcx, 4
    
    mov dword [rcx], 88200      ; ByteRate
    add rcx, 4
    
    mov word [rcx], 2           ; BlockAlign
    add rcx, 2
    
    mov word [rcx], 16          ; BitsPerSample
    add rcx, 2
    
    ; data subchunk
    mov byte [rcx], 'd'
    mov byte [rcx+1], 'a'
    mov byte [rcx+2], 't'
    mov byte [rcx+3], 'a'
    add rcx, 4
    
    mov [rcx], esi              ; Subchunk2Size
    add rcx, 4
    
    mov rax, 44                 ; Return header size
    
    pop rbp
    ret


; ============================================================================
; FUNCTION: clamp_sample
; Clamp a value to 16-bit signed integer range
; 
; Inputs:  rdi = value to clamp
; Outputs: rax = clamped value
; Modifies: rax
; ============================================================================
global clamp_sample
clamp_sample:
    push rbp
    mov rbp, rsp
    
    mov rax, rdi
    
    cmp rax, 32767
    jle .not_high
    mov rax, 32767
.not_high:
    
    cmp rax, -32768
    jge .not_low
    mov rax, -32768
.not_low:
    
    pop rbp
    ret