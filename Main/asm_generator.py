import math
from ir_instructions import IRProgram, IROpcode, IRInstruction, NoteData, RestData

class AsmGenerator:
    """
    Translates an IRProgram into x86-64 NASM assembly code
    that utilizes the audio_runtime.asm library.
    """

    def __init__(self, filename="output.wav"):
        self.filename = filename
        self.data_section = []
        self.bss_section = []
        self.text_section = []
        
        self.frequencies = {} # float -> label mapping
        self.freq_counter = 0
        self.variables = set()
        
        self.sequences = {}
        self.chords = {}

    def get_frequency_label(self, pitch: str, octave: int) -> str:
        """Calculates frequency and returns its data label."""
        pitch_map = {
            'C': -9, 'C#': -8, 'Db': -8,
            'D': -7, 'D#': -6, 'Eb': -6,
            'E': -5,
            'F': -4, 'F#': -3, 'Gb': -3,
            'G': -2, 'G#': -1, 'Ab': -1,
            'A': 0, 'A#': 1, 'Bb': 1,
            'B': 2
        }
        
        semitone = pitch_map.get(pitch.upper(), 0)
        n = semitone + (octave - 4) * 12
        freq = 440.0 * (2.0 ** (n / 12.0))
        
        if freq not in self.frequencies:
            label = f"freq_{self.freq_counter}"
            self.frequencies[freq] = label
            self.freq_counter += 1
            self.data_section.append(f"    {label} dd {freq:.2f}")
        
        return self.frequencies[freq]

    def _load_operand(self, op, reg="rax"):
        """Loads an operand (constant or variable) into a register."""
        
        # Determine register size
        is_32bit = reg.startswith('e') or reg.endswith('d')
        size = "dword" if is_32bit else "qword"
        
        if isinstance(op, int):
            self.text_section.append(f"    mov {reg}, {op}")
        elif isinstance(op, str):
            # Check if it's a temp variable or user variable
            if op.startswith('_t'):
                # Temp variable - likely from IR
                self.text_section.append(f"    mov {reg}, {size} [var_{op}]")
            else:
                # User variable
                self.text_section.append(f"    mov {reg}, {size} [var_{op}]")
        else:
            self.text_section.append(f"    ; Warning: Unknown operand type {type(op)} for {op}")
            self.text_section.append(f"    xor {reg}, {reg}  ; Default to 0")

    def generate(self, ir_program: IRProgram) -> str:
        # First pass: collect variables to declare in .bss
        for instr in ir_program.instructions:
            if instr.opcode in (IROpcode.ASSIGN, IROpcode.ADD, IROpcode.SUB, IROpcode.MOD, 
                                IROpcode.CMP_EQ, IROpcode.CMP_NEQ, IROpcode.CMP_GT, IROpcode.CMP_LT,
                                IROpcode.CMP_GTE, IROpcode.CMP_LTE):
                var_name = instr.args[0]
                if isinstance(var_name, str):
                    self.variables.add(var_name)
                    
        # Boilerplate data
        self.data_section.append(f"    filename db '{self.filename}', 0")
        self.data_section.append("    msg_done db 'Done generating WAV!', 10")
        self.data_section.append("    msg_done_len equ $ - msg_done")
        
        # Boilerplate bss
        self.bss_section.append("    wav_header resb 44")
        self.bss_section.append("    fd resd 1")
        for var in self.variables:
            self.bss_section.append(f"    var_{var} resq 1")
            
        # Boilerplate text
        self.text_section.append("global _start")
        self.text_section.append("_start:")
        self.text_section.append("    ; Initialize runtime")
        self.text_section.append("    call init_audio_runtime")
        
        # Iterate over IR
        for instr in ir_program.instructions:
            self._translate_instruction(instr)
            
        # End boilerplate: write to file
        self.text_section.extend([
            "    ; Get buffer data",
            "    call get_buffer_data",
            "    mov r14, rax            ; Save buffer pointer",
            "    mov r15d, edx           ; Save data size",
            "",
            "    ; Write WAV header",
            "    mov rdi, wav_header",
            "    mov rsi, r15            ; Data size",
            "    call write_wav_header",
            "",
            "    ; Open file",
            "    mov rax, 2              ; sys_open",
            "    mov rdi, filename",
            "    mov rsi, 0x241          ; O_WRONLY | O_CREAT | O_TRUNC",
            "    mov rdx, 0644o",
            "    syscall",
            "    mov [fd], eax",
            "",
            "    cmp eax, 0",
            "    jl error_exit",
            "",
            "    ; Write WAV header to file",
            "    mov rax, 1              ; sys_write",
            "    mov edi, [fd]",
            "    mov rsi, wav_header",
            "    mov rdx, 44",
            "    syscall",
            "",
            "    ; Write audio data to file",
            "    mov rax, 1",
            "    mov edi, [fd]",
            "    mov rsi, r14            ; Buffer pointer",
            "    mov edx, r15d           ; Data size",
            "    syscall",
            "",
            "    ; Close file",
            "    mov rax, 3",
            "    mov edi, [fd]",
            "    syscall",
            "",
            "    ; Print done message",
            "    mov rax, 1",
            "    mov rdi, 1",
            "    mov rsi, msg_done",
            "    mov rdx, msg_done_len",
            "    syscall",
            "",
            "    ; Exit successfully",
            "    mov rax, 60",
            "    xor rdi, rdi",
            "    syscall",
            "",
            "error_exit:",
            "    mov rax, 60",
            "    mov rdi, 1",
            "    syscall"
        ])
        
        # Assemble file content
        lines = [
            "; Generated by ChordLang AsmGenerator",
            "extern init_audio_runtime",
            "extern set_amplitude",
            "extern set_instrument",
            "extern generate_note",
            "extern generate_rest",
            "extern get_buffer_data",
            "extern write_wav_header",
            "extern reset_buffer",
            "",
            "section .data"
        ]
        lines.extend(self.data_section)
        
        lines.append("")
        lines.append("section .bss")
        lines.extend(self.bss_section)
        
        lines.append("")
        lines.append("section .text")
        lines.extend(self.text_section)
        
        return "\n".join(lines)
        
    def _translate_instruction(self, instr: IRInstruction):
        if instr.comment:
            self.text_section.append(f"    ; {instr.comment}")
            
        if instr.opcode == IROpcode.COMMENT:
            return
            
        elif instr.opcode == IROpcode.NOP:
            self.text_section.append("    nop")
            
        elif instr.opcode == IROpcode.SET_TEMPO:
            # Tempo is informational only since duration is in ms
            self.text_section.append(f"    ; Tempo set to {instr.args[0]} (Informational only)")
            
        elif instr.opcode == IROpcode.SET_VOLUME:
            val = instr.args[0]
            
            # Handle variable references
            if isinstance(val, str):
                self.text_section.append(f"    mov eax, dword [var_{val}]")
                # Scale if needed (assume 0-127 MIDI range or 0-100 percentage)
                self.text_section.append("    imul eax, 257")  # Scale 0-127 to 0-32639
            elif isinstance(val, int):
                # Assume MIDI range (0-127) or percentage (0-100)
                if val <= 127:
                    val = int((val / 127.0) * 32767)
                else:
                    val = min(val, 32767)  # Clamp
                self.text_section.append(f"    mov eax, {val}")
            
            self.text_section.append("    cvtsi2ss xmm0, eax")
            self.text_section.append("    call set_amplitude")
            
        elif instr.opcode == IROpcode.SET_INSTRUMENT:
            # instr.args[0] might be an integer ID or string name
            instr_id = instr.args[0]
            if isinstance(instr_id, str):
                # Map name to ID
                instr_map = {
                    'piano': 0, 'guitar': 1, 'bass': 2,
                    'sawtooth': 3, 'square': 4,
                    'drums_kick': 5, 'drums_snare': 6, 'drums_hihat': 7
                }
                instr_id = instr_map.get(instr_id, 0)
            
            self._load_operand(instr_id, "rdi")
            self.text_section.append("    call set_instrument")
            
        elif instr.opcode == IROpcode.ASSIGN:
            var_name, val = instr.args[0], instr.args[1]
            self._load_operand(val, "rax")
            self.text_section.append(f"    mov qword [var_{var_name}], rax")
            
        elif instr.opcode == IROpcode.ADD:
            dest, left, right = instr.args[0], instr.args[1], instr.args[2]
            self._load_operand(left, "rax")
            self._load_operand(right, "rcx")
            self.text_section.append("    add rax, rcx")
            self.text_section.append(f"    mov qword [var_{dest}], rax")
            
        elif instr.opcode == IROpcode.SUB:
            dest, left, right = instr.args[0], instr.args[1], instr.args[2]
            self._load_operand(left, "rax")
            self._load_operand(right, "rcx")
            self.text_section.append("    sub rax, rcx")
            self.text_section.append(f"    mov qword [var_{dest}], rax")
            
        elif instr.opcode == IROpcode.MOD:
            dest, left, right = instr.args[0], instr.args[1], instr.args[2]
            self._load_operand(left, "rax")
            self._load_operand(right, "rcx")
            self.text_section.append("    cqo")
            self.text_section.append("    idiv rcx")
            self.text_section.append(f"    mov qword [var_{dest}], rdx")
            
        elif instr.opcode in (IROpcode.CMP_EQ, IROpcode.CMP_NEQ, IROpcode.CMP_GT, 
                              IROpcode.CMP_LT, IROpcode.CMP_GTE, IROpcode.CMP_LTE):
            dest, left, right = instr.args[0], instr.args[1], instr.args[2]
            self._load_operand(left, "rax")
            self._load_operand(right, "rcx")
            self.text_section.append("    cmp rax, rcx")
            
            cond_map = {
                IROpcode.CMP_GT: "setg",
                IROpcode.CMP_LT: "setl",
                IROpcode.CMP_GTE: "setge",
                IROpcode.CMP_LTE: "setle",
                IROpcode.CMP_EQ: "sete",
                IROpcode.CMP_NEQ: "setne",
            }
            self.text_section.append(f"    {cond_map[instr.opcode]} al")
            self.text_section.append("    movzx rax, al")
            self.text_section.append(f"    mov qword [var_{dest}], rax")
            
        elif instr.opcode == IROpcode.LABEL:
            self.text_section.append(f"{instr.args[0]}:")
            
        elif instr.opcode == IROpcode.JUMP:
            self.text_section.append(f"    jmp {instr.args[0]}")
            
        elif instr.opcode == IROpcode.JUMP_IF_ZERO:
            var_name, label = instr.args[0], instr.args[1]
            self._load_operand(var_name, "rax")
            self.text_section.append("    test rax, rax")
            self.text_section.append(f"    jz {label}")
            
        elif instr.opcode == IROpcode.JUMP_IF_NOT_ZERO:
            var_name, label = instr.args[0], instr.args[1]
            self._load_operand(var_name, "rax")
            self.text_section.append("    test rax, rax")
            self.text_section.append(f"    jnz {label}")
            
        elif instr.opcode == IROpcode.PLAY_NOTE:
            pitch, octave, duration = instr.args[0], instr.args[1], instr.args[2]
            freq_label = self.get_frequency_label(pitch, octave)
            self.text_section.append(f"    movss xmm0, dword [{freq_label}]")
            self._load_operand(duration, "rdi")
            self.text_section.append("    call generate_note")
            
        elif instr.opcode == IROpcode.PLAY_REST:
            duration = instr.args[0]
            self._load_operand(duration, "rdi")
            self.text_section.append("    call generate_rest")
            
        elif instr.opcode == IROpcode.DEFINE_SEQUENCE:
            name, notes = instr.args[0], instr.args[1]
            self.sequences[name] = notes
            
        elif instr.opcode == IROpcode.DEFINE_CHORD:
            name, notes = instr.args[0], instr.args[1]
            self.chords[name] = notes
            
        elif instr.opcode == IROpcode.PLAY_SEQUENCE:
            name = instr.args[0]
            self._expand_sequence(name)
            
        elif instr.opcode == IROpcode.PLAY_CHORD:
            name = instr.args[0]
            self._expand_chord(name)
            
        else:
            self.text_section.append(f"    ; Unhandled opcode: {instr.opcode.name}")

    def _expand_sequence(self, name: str):
        notes = self.sequences.get(name, [])
        for note in notes:
            if isinstance(note, NoteData):
                freq_label = self.get_frequency_label(note.pitch, note.octave)
                self.text_section.append(f"    movss xmm0, dword [{freq_label}]")
                self._load_operand(note.duration, "rdi")
                self.text_section.append("    call generate_note")
            elif isinstance(note, RestData):
                self._load_operand(note.duration, "rdi")
                self.text_section.append("    call generate_rest")
            elif isinstance(note, str):
                if note in self.sequences:
                    self._expand_sequence(note)
                elif note in self.chords:
                    self._expand_chord(note)

    def _expand_chord(self, name: str):
        notes = self.chords.get(name, [])
        self.text_section.append("    ; Limitation: Real chords should play all notes at the same time, not sequentially.")
        self.text_section.append("    ; However, this runtime only supports single frequency output per note.")
        for note in notes:
            if isinstance(note, NoteData):
                freq_label = self.get_frequency_label(note.pitch, note.octave)
                self.text_section.append(f"    movss xmm0, dword [{freq_label}]")
                self._load_operand(note.duration, "rdi")
                self.text_section.append("    call generate_note")
            elif isinstance(note, str):
                if note in self.chords:
                    self._expand_chord(note)
                elif note in self.sequences:
                    self._expand_sequence(note)