"""
ChordLang Intermediate Representation (IR)
Three-address code style instructions for code generation.
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Union
from enum import Enum, auto


class IROpcode(Enum):
    """IR instruction opcodes."""
    # Configuration
    SET_TEMPO = auto()           # SET_TEMPO <value>
    SET_VOLUME = auto()          # SET_VOLUME <value>
    SET_INSTRUMENT = auto()      # SET_INSTRUMENT <id>
    
    # Variable operations
    ASSIGN = auto()              # ASSIGN <var> <value>
    ADD = auto()                 # ADD <dest> <left> <right>
    SUB = auto()                 # SUB <dest> <left> <right>
    MOD = auto()                 # MOD <dest> <left> <right>
    
    # Comparisons (for conditionals)
    CMP_GT = auto()              # CMP_GT <dest> <left> <right>
    CMP_LT = auto()              # CMP_LT <dest> <left> <right>
    CMP_GTE = auto()             # CMP_GTE <dest> <left> <right>
    CMP_LTE = auto()             # CMP_LTE <dest> <left> <right>
    CMP_EQ = auto()              # CMP_EQ <dest> <left> <right>
    CMP_NEQ = auto()             # CMP_NEQ <dest> <left> <right>
    
    # Musical data definitions
    DEFINE_SEQUENCE = auto()     # DEFINE_SEQUENCE <name> <notes>
    DEFINE_CHORD = auto()        # DEFINE_CHORD <name> <notes>
    
    # Playback operations
    PLAY_NOTE = auto()           # PLAY_NOTE <pitch> <octave> <duration>
    PLAY_REST = auto()           # PLAY_REST <duration>
    PLAY_SEQUENCE = auto()       # PLAY_SEQUENCE <name>
    PLAY_CHORD = auto()          # PLAY_CHORD <name>
    
    # Control flow
    LABEL = auto()               # LABEL <name>
    JUMP = auto()                # JUMP <label>
    JUMP_IF_ZERO = auto()        # JUMP_IF_ZERO <var> <label>
    JUMP_IF_NOT_ZERO = auto()    # JUMP_IF_NOT_ZERO <var> <label>
    
    # Comments (for debugging)
    COMMENT = auto()             # COMMENT <text>
    NOP = auto()                 # NOP (no operation)


@dataclass
class IRInstruction:
    """
    A single IR instruction.
    
    Format: opcode [arg1] [arg2] [arg3]
    """
    opcode: IROpcode
    args: List[Any]
    lineno: int = 0
    comment: str = ""  # Optional comment for debugging
    
    def __str__(self):
        args_str = " ".join(str(arg) for arg in self.args)
        base = f"{self.opcode.name:20s} {args_str}"
        if self.comment:
            return f"{base:50s} # {self.comment}"
        return base
    
    def __repr__(self):
        return f"IR({self.opcode.name}, {self.args})"


@dataclass
class NoteData:
    """Represents a musical note in IR."""
    pitch: str        # e.g., "C", "D#", "Bb"
    octave: int       # 0-8
    duration: int     # milliseconds
    
    def __str__(self):
        return f"{self.pitch}{self.octave}:{self.duration}"
    
    def __repr__(self):
        return f"Note({self.pitch}{self.octave}:{self.duration})"


@dataclass
class RestData:
    """Represents a rest (silence) in IR."""
    duration: int     # milliseconds
    
    def __str__(self):
        return f"rest:{self.duration}"
    
    def __repr__(self):
        return f"Rest({self.duration})"


class IRProgram:
    """
    Container for an IR program.
    Holds all instructions and provides utilities.
    """
    
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self._label_counter = 0
        self._temp_counter = 0
    
    def emit(self, opcode: IROpcode, *args, lineno: int = 0, comment: str = ""):
        """Add an instruction to the program."""
        instr = IRInstruction(opcode, list(args), lineno, comment)
        self.instructions.append(instr)
        return instr
    
    def new_label(self, prefix: str = "L") -> str:
        """Generate a unique label name."""
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label
    
    def new_temp(self) -> str:
        """Generate a unique temporary variable name."""
        temp = f"_t{self._temp_counter}"
        self._temp_counter += 1
        return temp
    
    def __str__(self):
        """Pretty-print the entire IR program."""
        lines = []
        lines.append("=" * 70)
        lines.append("CHORDLANG INTERMEDIATE REPRESENTATION (IR)")
        lines.append("=" * 70)
        
        for i, instr in enumerate(self.instructions):
            lines.append(f"{i:4d}: {instr}")
        
        lines.append("=" * 70)
        lines.append(f"Total instructions: {len(self.instructions)}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def __repr__(self):
        return f"IRProgram({len(self.instructions)} instructions)"
    
    def optimize(self):
        """Apply basic optimizations to the IR."""
        # Constant folding
        self._constant_folding()
        
        # Dead code elimination
        self._dead_code_elimination()
        
        # Remove consecutive labels
        self._merge_labels()
    
    def _constant_folding(self):
        """Fold constant arithmetic operations."""
        optimized = []
        
        for instr in self.instructions:
            if instr.opcode in (IROpcode.ADD, IROpcode.SUB, IROpcode.MOD):
                # Check if both operands are constants
                if isinstance(instr.args[1], int) and isinstance(instr.args[2], int):
                    left, right = instr.args[1], instr.args[2]
                    
                    if instr.opcode == IROpcode.ADD:
                        result = left + right
                    elif instr.opcode == IROpcode.SUB:
                        result = left - right
                    else:  # MOD
                        result = left % right
                    
                    # Replace with direct assignment
                    optimized.append(IRInstruction(
                        IROpcode.ASSIGN,
                        [instr.args[0], result],
                        instr.lineno,
                        f"constant folded: {left} {instr.opcode.name} {right}"
                    ))
                    continue
            
            optimized.append(instr)
        
        self.instructions = optimized
    
    def _dead_code_elimination(self):
        """Remove unreachable code after unconditional jumps."""
        optimized = []
        skip_until_label = False
        
        for instr in self.instructions:
            # After unconditional JUMP, skip until next LABEL
            if skip_until_label:
                if instr.opcode == IROpcode.LABEL:
                    skip_until_label = False
                    optimized.append(instr)
                continue
            
            optimized.append(instr)
            
            if instr.opcode == IROpcode.JUMP:
                skip_until_label = True
        
        self.instructions = optimized
    
    def _merge_labels(self):
        """Remove consecutive duplicate labels."""
        optimized = []
        last_was_label = False
        
        for instr in self.instructions:
            if instr.opcode == IROpcode.LABEL:
                if last_was_label:
                    continue  # Skip consecutive labels
                last_was_label = True
            else:
                last_was_label = False
            
            optimized.append(instr)
        
        self.instructions = optimized


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def format_ir_program(program: IRProgram, show_line_numbers: bool = True) -> str:
    """Format IR program for display."""
    return str(program)


def ir_to_dict(program: IRProgram) -> dict:
    """Convert IR program to dictionary for serialization."""
    return {
        'instructions': [
            {
                'opcode': instr.opcode.name,
                'args': instr.args,
                'lineno': instr.lineno,
                'comment': instr.comment
            }
            for instr in program.instructions
        ],
        'instruction_count': len(program.instructions)
    }