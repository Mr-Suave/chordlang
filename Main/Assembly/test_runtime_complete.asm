; Complete test program using the audio runtime library
; Generates a simple melody and writes to WAV file

extern init_audio_runtime
extern set_amplitude
extern set_instrument
extern generate_note
extern generate_rest
extern get_buffer_data
extern write_wav_header
extern reset_buffer

section .data
    filename db 'test_output.wav', 0
    
    ; Instrument IDs
    INSTR_PIANO     equ 0
    INSTR_GUITAR    equ 1
    INSTR_BASS      equ 2
    
    ; Note frequencies (single precision floats)
    note_c4 dd 261.63
    note_e4 dd 329.63
    note_g4 dd 392.00
    note_c5 dd 523.25
    
    ; Messages
    msg_init db 'Initializing audio runtime...', 10
    msg_init_len equ $ - msg_init
    
    msg_generate db 'Generating notes...', 10
    msg_generate_len equ $ - msg_generate
    
    msg_write db 'Writing WAV file...', 10
    msg_write_len equ $ - msg_write
    
    msg_done db 'Done! Output: test_output.wav', 10
    msg_done_len equ $ - msg_done

section .bss
    wav_header resb 44
    fd resd 1

section .text
global _start

_start:
    ; Print init message
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_init
    mov rdx, msg_init_len
    syscall
    
    ; Initialize runtime
    call init_audio_runtime
    
    ; Set instrument to PIANO
    mov rdi, INSTR_PIANO
    call set_instrument
    
    ; Set amplitude to 12000
    mov eax, 12000
    cvtsi2ss xmm0, eax
    call set_amplitude
    
    ; Print generate message
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_generate
    mov rdx, msg_generate_len
    syscall
    
    ; Generate C4 (500ms)
    movss xmm0, [note_c4]
    mov rdi, 500
    call generate_note
    
    ; Rest (100ms)
    mov rdi, 100
    call generate_rest
    
    ; Generate E4 (500ms)
    movss xmm0, [note_e4]
    mov rdi, 500
    call generate_note
    
    ; Rest (100ms)
    mov rdi, 100
    call generate_rest
    
    ; Generate G4 (500ms)
    movss xmm0, [note_g4]
    mov rdi, 500
    call generate_note
    
    ; Rest (100ms)
    mov rdi, 100
    call generate_rest
    
    ; Generate C5 (500ms)
    movss xmm0, [note_c5]
    mov rdi, 500
    call generate_note
    
    ; Switch to Guitar for a final chord
    mov rdi, INSTR_GUITAR
    call set_instrument
    
    ; Generate G4 (1000ms)
    movss xmm0, [note_g4]
    mov rdi, 1000
    call generate_note
    
    ; Get buffer data
    call get_buffer_data
    ; rax = buffer pointer, rdx = size in bytes
    mov r14, rax            ; Save buffer pointer
    mov r15d, edx           ; Save data size
    
    ; Write WAV header
    mov rdi, wav_header
    mov rsi, r15            ; Data size
    call write_wav_header
    
    ; Print write message
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_write
    mov rdx, msg_write_len
    syscall
    
    ; Open file
    mov rax, 2              ; sys_open
    mov rdi, filename
    mov rsi, 0x241          ; O_WRONLY | O_CREAT | O_TRUNC
    mov rdx, 0644o
    syscall
    mov [fd], eax
    
    cmp eax, 0
    jl error_exit
    
    ; Write WAV header
    mov rax, 1              ; sys_write
    mov edi, [fd]
    mov rsi, wav_header
    mov rdx, 44
    syscall
    
    ; Write audio data
    mov rax, 1
    mov edi, [fd]
    mov rsi, r14            ; Buffer pointer
    mov edx, r15d           ; Data size
    syscall
    
    ; Close file
    mov rax, 3
    mov edi, [fd]
    syscall
    
    ; Print done message
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_done
    mov rdx, msg_done_len
    syscall
    
    ; Exit successfully
    mov rax, 60
    xor rdi, rdi
    syscall

error_exit:
    mov rax, 60
    mov rdi, 1
    syscall
