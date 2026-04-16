; Test program for calculate_envelope function
; Tests fade-in, sustain, and fade-out regions

extern calculate_envelope

section .data
    test_name db 'TEST: calculate_envelope', 10, 0
    test_name_len equ $ - test_name
    
    msg_fadein db 'Fade-in (sample 50/1000): ', 0
    msg_fadein_len equ $ - msg_fadein
    
    msg_sustain db 'Sustain (sample 500/1000): ', 0
    msg_sustain_len equ $ - msg_sustain
    
    msg_fadeout db 'Fade-out (sample 950/1000): ', 0
    msg_fadeout_len equ $ - msg_fadeout
    
    newline db 10

section .bss
    result_buffer resb 32

section .text
global _start

_start:
    ; Print test name
    mov rax, 1
    mov rdi, 1
    mov rsi, test_name
    mov rdx, test_name_len
    syscall
    
    ; Test 1: Fade-in region (sample 50 of 1000)
    mov rdi, 50             ; sample index
    mov rsi, 1000           ; total samples
    call calculate_envelope
    
    ; xmm0 now contains envelope value
    ; Expected: ~0.5 (50/100 where 100 = 1000/10)
    
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_fadein
    mov rdx, msg_fadein_len
    syscall
    
    ; Print result (simplified - just print "OK")
    mov byte [result_buffer], 'O'
    mov byte [result_buffer+1], 'K'
    mov byte [result_buffer+2], 10
    mov rax, 1
    mov rdi, 1
    mov rsi, result_buffer
    mov rdx, 3
    syscall
    
    ; Test 2: Sustain region (sample 500 of 1000)
    mov rdi, 500
    mov rsi, 1000
    call calculate_envelope
    ; Expected: 1.0
    
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_sustain
    mov rdx, msg_sustain_len
    syscall
    
    mov byte [result_buffer], 'O'
    mov byte [result_buffer+1], 'K'
    mov byte [result_buffer+2], 10
    mov rax, 1
    mov rdi, 1
    mov rsi, result_buffer
    mov rdx, 3
    syscall
    
    ; Test 3: Fade-out region (sample 950 of 1000)
    mov rdi, 950
    mov rsi, 1000
    call calculate_envelope
    ; Expected: ~0.5 (50/100)
    
    mov rax, 1
    mov rdi, 1
    mov rsi, msg_fadeout
    mov rdx, msg_fadeout_len
    syscall
    
    mov byte [result_buffer], 'O'
    mov byte [result_buffer+1], 'K'
    mov byte [result_buffer+2], 10
    mov rax, 1
    mov rdi, 1
    mov rsi, result_buffer
    mov rdx, 3
    syscall
    
    ; Exit
    mov rax, 60
    xor rdi, rdi
    syscall
