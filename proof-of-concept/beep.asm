; Simple WAV file generator in x86-64 assembly
; Generates a 440Hz sine wave (A4 note) for 1 second
; Compile: nasm -f elf64 beep.asm -o beep.o
; Link:    ld beep.o -o beep
; Run:     ./beep && aplay output.wav

section .data
    ; File name
    filename db 'output.wav', 0
    
    ; WAV file header (44 bytes)
    wav_header:
        db 'RIFF'           ; ChunkID
        dd 88244            ; ChunkSize (file size - 8) = 36 + data_size
        db 'WAVE'           ; Format
        db 'fmt '           ; Subchunk1ID
        dd 16               ; Subchunk1Size (16 for PCM)
        dw 1                ; AudioFormat (1 = PCM)
        dw 1                ; NumChannels (1 = mono)
        dd 44100            ; SampleRate
        dd 88200            ; ByteRate (SampleRate * NumChannels * BitsPerSample/8)
        dw 2                ; BlockAlign (NumChannels * BitsPerSample/8)
        dw 16               ; BitsPerSample
        db 'data'           ; Subchunk2ID
        dd 88200            ; Subchunk2Size (NumSamples * NumChannels * BitsPerSample/8)
    
    ; Constants for sine wave generation
    sample_rate dd 44100
    frequency dd 440        ; A4 note
    duration dd 1           ; 1 second
    two_pi dq 6.28318530718 ; 2 * PI
    amplitude dd 16000.0    ; Volume (max is ~32767)
    
    ; Success message
    msg db 'Generated output.wav - play with: aplay output.wav', 10
    msg_len equ $ - msg

section .bss
    audio_buffer resb 88200  ; Buffer for 1 second of 16-bit mono audio at 44.1kHz
    fd resd 1                ; File descriptor

section .text
    global _start

_start:
    ; Calculate number of samples: sample_rate * duration
    mov eax, [sample_rate]
    imul eax, [duration]
    mov r12d, eax           ; r12 = num_samples (44100)
    
    ; Generate audio samples
    xor r13, r13            ; r13 = sample counter (i)
    
generate_samples:
    cmp r13d, r12d
    jge done_generating
    
    ; Calculate t = i / sample_rate
    cvtsi2sd xmm0, r13d     ; xmm0 = i (as double)
    cvtsi2sd xmm1, dword [sample_rate]  ; xmm1 = sample_rate
    divsd xmm0, xmm1        ; xmm0 = t = i / sample_rate
    
    ; Calculate 2 * PI * frequency * t
    cvtsi2sd xmm2, dword [frequency]    ; xmm2 = frequency
    mulsd xmm2, xmm0                    ; xmm2 = frequency * t
    mulsd xmm2, [two_pi]                ; xmm2 = 2 * PI * frequency * t
    
    ; Calculate sine using approximation (Taylor series, limited accuracy)
    ; For better accuracy, you'd use FSIN or a lookup table
    ; Here's a simple approximation: sin(x) ≈ x - x³/6 + x⁵/120 (for small x)
    ; For simplicity, we'll just use a basic sine approximation
    
    ; Use x87 FPU for sine calculation
    sub rsp, 8
    movsd [rsp], xmm2
    fld qword [rsp]
    fsin                    ; ST(0) = sin(ST(0))
    fstp qword [rsp]
    movsd xmm2, [rsp]
    add rsp, 8
    
    ; Multiply by amplitude
    cvtss2sd xmm3, dword [amplitude]
    mulsd xmm2, xmm3
    
    ; Convert to 16-bit integer
    cvttsd2si eax, xmm2     ; eax = (int)sample
    
    ; Clamp to 16-bit range (-32768 to 32767)
    cmp eax, 32767
    jle not_too_high
    mov eax, 32767
not_too_high:
    cmp eax, -32768
    jge not_too_low
    mov eax, -32768
not_too_low:
    
    ; Store sample in buffer (16-bit little-endian)
    mov rbx, r13
    shl rbx, 1              ; rbx = i * 2 (byte offset)
    mov word [audio_buffer + rbx], ax
    
    ; Increment counter
    inc r13
    jmp generate_samples

done_generating:
    ; Open file for writing
    mov rax, 2              ; sys_open
    mov rdi, filename
    mov rsi, 0x241          ; O_WRONLY | O_CREAT | O_TRUNC (0x01 | 0x40 | 0x200)
    mov rdx, 0644o          ; Permissions (rw-r--r--)
    syscall
    mov [fd], eax
    
    ; Check if file opened successfully
    cmp eax, 0
    jl error_exit
    
    ; Write WAV header (44 bytes)
    mov rax, 1              ; sys_write
    mov edi, [fd]
    mov rsi, wav_header
    mov rdx, 44
    syscall
    
    ; Write audio data (88200 bytes)
    mov rax, 1              ; sys_write
    mov edi, [fd]
    mov rsi, audio_buffer
    mov rdx, 88200
    syscall
    
    ; Close file
    mov rax, 3              ; sys_close
    mov edi, [fd]
    syscall
    
    ; Print success message
    mov rax, 1              ; sys_write
    mov rdi, 1              ; stdout
    mov rsi, msg
    mov rdx, msg_len
    syscall
    
    ; Exit successfully
    mov rax, 60             ; sys_exit
    xor rdi, rdi            ; exit code 0
    syscall

error_exit:
    ; Exit with error
    mov rax, 60
    mov rdi, 1              ; exit code 1
    syscall
