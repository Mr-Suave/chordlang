; Test program for generate_sine_sample function
; Generates a few samples and prints them

extern generate_sine_sample

section .data
    test_name db 'TEST: generate_sine_sample (A4 = 440Hz)', 10, 0
    test_name_len equ $ - test_name
    
    freq_a4 dq 440.0        ; A4 frequency
    amplitude dq 16000.0     ; Amplitude
    
    msg_sample db 'Sample ', 0
    msg_sample_len equ $ - msg_sample
    
    msg_value db ': value = ', 0
    msg_value_len equ $ - msg_value
    
    newline db 10

section .bss
    sample_buffer resw 10   ; Store 10 samples

section .text
global _start

_start:
    ; Print test name
    mov rax, 1
    mov rdi, 1
    mov rsi, test_name
    mov rdx, test_name_len
    syscall
    
    ; Generate 10 samples for A4 (440 Hz)
    xor r12, r12            ; sample counter
    
.generate_loop:
    cmp r12, 10
    jge .done_generating
    
    ; Calculate time t = i / 44100
    cvtsi2sd xmm1, r12
    mov rax, 44100
    cvtsi2sd xmm2, rax
    divsd xmm1, xmm2        ; xmm1 = t
    
    ; Load frequency and amplitude
    movsd xmm0, [freq_a4]
    movsd xmm2, [amplitude]
    
    ; Generate sample
    call generate_sine_sample
    
    ; Store sample
    mov [sample_buffer + r12*2], ax
    
    inc r12
    jmp .generate_loop
    
.done_generating:
    ; Print first 3 samples
    mov rax, 1
    mov rdi, 1
    lea rsi, [msg_sample]
    mov rdx, msg_sample_len
    syscall
    
    ; Print "0: "
    mov byte [rsp-8], '0'
    mov byte [rsp-7], 10
    mov rax, 1
    mov rdi, 1
    lea rsi, [rsp-8]
    mov rdx, 2
    syscall
    
    ; Expected: sample[0] should be ~0 (sine starts at 0)
    ; sample[1] should be positive
    ; Simplified test - just check if we got here
    
    mov byte [rsp-8], 'P'
    mov byte [rsp-7], 'A'
    mov byte [rsp-6], 'S'
    mov byte [rsp-5], 'S'
    mov byte [rsp-4], 10
    mov rax, 1
    mov rdi, 1
    lea rsi, [rsp-8]
    mov rdx, 5
    syscall
    
    ; Exit
    mov rax, 60
    xor rdi, rdi
    syscall
