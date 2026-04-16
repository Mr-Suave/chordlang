; Compile: nasm -f elf64 melody.asm -o melody.o
; Link:    gcc -nostdlib -static melody.o -o melody
; Run:     ./melody && aplay melody.wav

section .data
    filename db 'melody.wav', 0
    
    ; WAV file header - will be updated with correct size
    wav_header:
        db 'RIFF'           ; ChunkID
        dd 0                ; ChunkSize (will calculate later)
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
        dd 0                ; Subchunk2Size (will calculate later)
    
    sample_rate dd 44100
    note_duration dd 22050      ; 0.5 seconds per note (44100 * 0.5)
    two_pi dq 6.28318530718     ; 2 * PI
    amplitude dd 16000.0        ; Volume
    
    ; Note frequencies (in Hz)
    note_c4 dd 261.63           ; C4 (middle C)
    note_e4 dd 329.63           ; E4
    note_g4 dd 392.00           ; G4
    note_c5 dd 523.25           ; C5 (one octave higher)
    
    ; Messages
    msg db 'Generated melody.wav with 4 notes: C4 -> E4 -> G4 -> C5', 10
    msg_len equ $ - msg

section .bss
    audio_buffer resb 352800    ; Buffer for 4 notes * 0.5 sec each = 2 seconds
    fd resd 1                   ; File descriptor
    buffer_pos resd 1           ; Current position in buffer (in samples)

section .text
    global _start

_start:
    xor r15, r15                ; r15 = buffer_pos in bytes (starts at 0)
    
    ; Generate C4 note
    movss xmm7, [note_c4]
    call generate_note
    
    ; Generate E4 note
    movss xmm7, [note_e4]
    call generate_note
    
    ; Generate G4 note
    movss xmm7, [note_g4]
    call generate_note
    
    ; Generate C5 note
    movss xmm7, [note_c5]
    call generate_note
    
    ; Now r15 contains total bytes written
    ; Update WAV header with correct sizes
    mov eax, r15d
    mov [wav_header + 40], eax  ; data chunk size
    add eax, 36
    mov [wav_header + 4], eax   ; file size - 8
    
    ; Open file for writing
    mov rax, 2                  ; sys_open
    mov rdi, filename
    mov rsi, 0x241              ; O_WRONLY | O_CREAT | O_TRUNC
    mov rdx, 0644o              ; Permissions
    syscall
    mov [fd], eax
    
    cmp eax, 0
    jl error_exit
    
    ; Write WAV header (44 bytes)
    mov rax, 1                  ; sys_write
    mov edi, [fd]
    mov rsi, wav_header
    mov rdx, 44
    syscall
    
    ; Write audio data
    mov rax, 1                  ; sys_write
    mov edi, [fd]
    mov rsi, audio_buffer
    mov edx, r15d               ; Total bytes written
    syscall
    
    ; Close file
    mov rax, 3                  ; sys_close
    mov edi, [fd]
    syscall
    
    ; Print success message
    mov rax, 1                  ; sys_write
    mov rdi, 1                  ; stdout
    mov rsi, msg
    mov rdx, msg_len
    syscall
    
    ; Exit successfully
    mov rax, 60                 ; sys_exit
    xor rdi, rdi
    syscall

error_exit:
    mov rax, 60
    mov rdi, 1
    syscall


; generate_note: Generate one note and append to audio buffer
; Input: xmm7 = frequency (as float)
;        r15 = current buffer position in bytes
; Output: r15 = updated buffer position

generate_note:
    push rbp
    mov rbp, rsp
    
    ; Convert frequency to double precision
    cvtss2sd xmm7, xmm7         ; xmm7 = frequency (double)
    
    ; Get note duration
    mov r12d, [note_duration]   ; r12 = number of samples for this note
    xor r13, r13                ; r13 = sample counter (i)
    
.generate_loop:
    cmp r13d, r12d
    jge .done
    
    ; Calculate t = i / sample_rate
    cvtsi2sd xmm0, r13d         ; xmm0 = i (as double)
    cvtsi2sd xmm1, dword [sample_rate]
    divsd xmm0, xmm1            ; xmm0 = t
    
    ; Calculate 2 * PI * frequency * t
    movsd xmm2, xmm7            ; xmm2 = frequency
    mulsd xmm2, xmm0            ; xmm2 = frequency * t
    mulsd xmm2, [two_pi]        ; xmm2 = 2 * PI * frequency * t
    
    ; Calculate sine
    sub rsp, 8
    movsd [rsp], xmm2
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm2, [rsp]
    add rsp, 8
    
    ; Apply envelope (simple fade in/out)
    ; Fade in: first 10% of samples
    ; Fade out: last 10% of samples
    movsd xmm6, xmm2            ; Save sine value
    
    ; Check if in fade-in region
    mov eax, r12d
    mov ebx, 10
    xor edx, edx
    div ebx                     ; eax = num_samples / 10 (fade samples)
    
    cmp r13d, eax
    jge .check_fadeout
    
    ; Fade in: envelope = i / fade_samples
    cvtsi2sd xmm5, r13d
    cvtsi2sd xmm4, eax
    divsd xmm5, xmm4
    mulsd xmm6, xmm5
    jmp .apply_amplitude
    
.check_fadeout:
    ; Check if in fade-out region
    mov ebx, r12d
    sub ebx, eax                ; ebx = num_samples - fade_samples
    cmp r13d, ebx
    jl .apply_amplitude
    
    ; Fade out: envelope = (num_samples - i) / fade_samples
    mov ecx, r12d
    sub ecx, r13d               ; ecx = num_samples - i
    cvtsi2sd xmm5, ecx
    cvtsi2sd xmm4, eax
    divsd xmm5, xmm4
    mulsd xmm6, xmm5
    
.apply_amplitude:
    ; Multiply by amplitude
    cvtss2sd xmm3, dword [amplitude]
    mulsd xmm6, xmm3
    
    ; Convert to 16-bit integer
    cvttsd2si eax, xmm6
    
    ; Clamp to 16-bit range
    cmp eax, 32767
    jle .not_too_high
    mov eax, 32767
.not_too_high:
    cmp eax, -32768
    jge .not_too_low
    mov eax, -32768
.not_too_low:
    
    ; Store sample in buffer at current position
    mov word [audio_buffer + r15], ax
    add r15, 2                  ; Move to next sample position (2 bytes)
    
    ; Increment sample counter
    inc r13
    jmp .generate_loop

.done:
    pop rbp
    ret
