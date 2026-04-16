"""
ChordLang Enhanced Semantic Analyzer
Comprehensive semantic validation beyond basic symbol table building.
"""

from typing import List, Set
from ast_nodes import *
from symbol_table import SymbolTable, SymbolKind
from visitors import ASTVisitor


VALID_INSTRUMENTS = [
    'piano', 'guitar', 'bass', 'sawtooth', 'square',
    'drums_kick', 'drums_snare', 'drums_hihat'
]


class SemanticAnalyzer(ASTVisitor):
    """
    Performs deep semantic analysis on the AST.
    
    Validates:
    - Type consistency (integers vs notes vs sequences)
    - Note format correctness
    - Value ranges (octaves, durations, tempo, volume)
    - Control flow validity
    - Duplicate definitions
    """
    
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.errors: List[str] = []
        self.warnings: List[str] = []
        # Current state for line-by-line validation
        self.current_instrument: Optional[str] = None
        self.current_tempo: int = 120
        self.current_volume: int = 100
        
    def analyze(self, ast_root: ProgramNode) -> bool:
        """
        Run semantic analysis on the AST.
        Returns True if no errors, False otherwise.
        """
        # Re-initialize state before analysis
        self.current_instrument = None
        self.current_tempo = 120
        self.current_volume = 100
        ast_root.accept(self)
        return len(self.errors) == 0
    
    def _error(self, msg: str, lineno: int = 0):
        self.errors.append(f"[Line {lineno}] ERROR: {msg}")
    
    def _warning(self, msg: str, lineno: int = 0):
        self.warnings.append(f"[Line {lineno}] WARNING: {msg}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Visitors
    # ═══════════════════════════════════════════════════════════════════════
    
    def visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            stmt.accept(self)


    
    def visit_AssignmentNode(self, node: AssignmentNode):
        # Validate RHS is an expression (not a note)
        if isinstance(node.value, NoteLiteralNode):
            self._error(
                f"Cannot assign note '{node.value.full_name}' to variable '{node.name}'. "
                f"Variables can only hold numeric values.",
                node.lineno
            )
        
        # Track and validate special variables
        if node.name == "tempo":
            val = self._validate_tempo(node.value, node.lineno)
            if val is not None:
                self.current_tempo = val
        elif node.name == "volume":
            val = self._validate_volume(node.value, node.lineno)
            if val is not None:
                self.current_volume = val
        elif node.name == "instrument":
            # Validate instrument name
            if isinstance(node.value, IdentifierNode):
                instr_name = node.value.name
                if instr_name not in VALID_INSTRUMENTS:
                    self._error(
                        f"Unknown instrument '{instr_name}'. "
                        f"Valid: {', '.join(VALID_INSTRUMENTS)}",
                        node.lineno
                    )
                else:
                    self.current_instrument = instr_name
            else:
                self._error(
                    "Instrument must be assigned an instrument name (e.g., piano, guitar)",
                    node.lineno
                )
    
    def visit_SequenceNode(self, node: SequenceNode):
        # Validate all notes in sequence
        for note in node.notes:
            if isinstance(note, NoteLiteralNode):
                self._validate_note(note)
            elif isinstance(note, RestNode):
                self._validate_rest(note)
            elif isinstance(note, IdentifierNode):
                # Check if identifier refers to a valid note/sequence
                sym = self.symbol_table.lookup(note.name)
                if not sym:
                    self._error(
                        f"Undefined symbol '{note.name}' in sequence '{node.name}'",
                        note.lineno
                    )
                elif sym.kind not in (SymbolKind.SEQUENCE, SymbolKind.CHORD):
                    self._error(
                        f"'{note.name}' is a {sym.kind.name}, cannot be used in sequence",
                        note.lineno
                    )
        
        # Warn if sequence is empty
        if not node.notes:
            self._warning(f"Sequence '{node.name}' is empty", node.lineno)
    
    def visit_ChordNode(self, node: ChordNode):
        # Validate all notes in chord
        for note in node.notes:
            if isinstance(note, NoteLiteralNode):
                self._validate_note(note)
            elif isinstance(note, IdentifierNode):
                sym = self.symbol_table.lookup(note.name)
                if not sym:
                    self._error(
                        f"Undefined symbol '{note.name}' in chord '{node.name}'",
                        note.lineno
                    )
        
        # Warn if chord has only one note
        if len(node.notes) == 1:
            self._warning(
                f"Chord '{node.name}' has only one note, consider using a sequence instead",
                node.lineno
            )
        
        # Warn if chord is empty
        if not node.notes:
            self._warning(f"Chord '{node.name}' is empty", node.lineno)
    
    def visit_PlayNode(self, node: PlayNode):
        for target in node.targets:
            if isinstance(target, IdentifierNode):
                sym = self.symbol_table.lookup(target.name)
                if not sym:
                    self._error(
                        f"Cannot play undefined symbol '{target.name}'",
                        node.lineno
                    )
                elif sym.kind == SymbolKind.VARIABLE:
                    self._error(
                        f"Cannot play variable '{target.name}'. "
                        f"Only notes, sequences, and chords can be played.",
                        node.lineno
                    )
            elif isinstance(target, NoteLiteralNode):
                self._validate_note(target)
            elif isinstance(target, RestNode):
                self._validate_rest(target)
    
    def visit_RepeatNode(self, node: RepeatNode):
        # Validate count is a positive integer expression
        if isinstance(node.count, IntegerLiteralNode):
            if node.count.value <= 0:
                self._error(
                    f"Repeat count must be positive, got {node.count.value}",
                    node.lineno
                )
            elif node.count.value > 1000:
                self._warning(
                    f"Very large repeat count ({node.count.value}), may cause performance issues",
                    node.lineno
                )
        elif isinstance(node.count, IdentifierNode):
            sym = self.symbol_table.lookup(node.count.name)
            if sym and sym.kind != SymbolKind.VARIABLE:
                self._error(
                    f"Repeat count must be a variable, not {sym.kind.name}",
                    node.lineno
                )
        
        # Visit body
        for stmt in node.body:
            stmt.accept(self)
    
    def visit_IfNode(self, node: IfNode):
        # Validate condition
        node.condition.accept(self)
        
        # Check that condition is actually a comparison
        if isinstance(node.condition, IntegerLiteralNode):
            self._warning(
                f"Condition is always {'true' if node.condition.value else 'false'}",
                node.lineno
            )
        
        # Visit branches
        for stmt in node.then_body:
            stmt.accept(self)
        
        if node.else_body:
            for stmt in node.else_body:
                stmt.accept(self)
    
    def visit_BinaryOpNode(self, node: BinaryOpNode):
        # Validate both sides
        node.left.accept(self)
        node.right.accept(self)
        
        # Type checking for operators
        if node.operator in ['%']:
            # Modulo requires integers
            if isinstance(node.left, NoteLiteralNode) or isinstance(node.right, NoteLiteralNode):
                self._error(
                    f"Modulo operator requires numeric operands, not notes",
                    node.lineno
                )
    
    def visit_IdentifierNode(self, node: IdentifierNode):
        # This is called for identifiers in expressions
        sym = self.symbol_table.lookup(node.name)
        if not sym:
            self._error(f"Undefined variable '{node.name}'", node.lineno)
    
    # Leaf nodes
    def visit_IntegerLiteralNode(self, node): pass
    def visit_NoteLiteralNode(self, node): 
        self._validate_note(node)
    def visit_RestNode(self, node): 
        self._validate_rest(node)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Validation Helpers
    # ═══════════════════════════════════════════════════════════════════════
    
    def _validate_note(self, note: NoteLiteralNode):
        """Validate note format and ranges."""
        # Validate pitch
        valid_pitches = ['C', 'D', 'E', 'F', 'G', 'A', 'B',
                        'C#', 'D#', 'F#', 'G#', 'A#',
                        'Db', 'Eb', 'Gb', 'Ab', 'Bb']
        
        if note.pitch not in valid_pitches:
            self._error(
                f"Invalid pitch '{note.pitch}'. Must be A-G with optional # or b",
                note.lineno
            )
        
        # Validate octave range (typically 0-8 for standard MIDI)
        if not (0 <= note.octave <= 8):
            self._error(
                f"Octave {note.octave} out of range. Must be 0-8",
                note.lineno
            )
        
        # Validate duration if present
        if note.duration is not None:
            if note.duration < 0:
                self._error(
                    f"Note duration cannot be negative, got {note.duration}",
                    note.lineno
                )
            elif note.duration > 10000:
                self._warning(
                    f"Very long note duration ({note.duration}ms), is this intentional?",
                    note.lineno
                )
    
    def _validate_rest(self, rest: RestNode):
        """Validate rest duration."""
        if rest.duration is not None:
            if rest.duration < 0:
                self._error(
                    f"Rest duration cannot be negative, got {rest.duration}",
                    rest.lineno
                )
            elif rest.duration == 0:
                # rest:0 is a special trigger for drum instruments
                if self.current_instrument:
                    instr_name = self.current_instrument
                    if not (instr_name.startswith("drums_") or instr_name in ["kick", "snare", "hihat"]):
                        self._warning(
                            f"rest:0 is typically used as a trigger for drum instruments. "
                            f"Current instrument is '{instr_name}'.",
                            rest.lineno
                        )
                else:
                    self._warning(
                        "rest:0 is typically used as a trigger for drum instruments. "
                        "No instrument currently set.",
                        rest.lineno
                    )
            elif rest.duration > 10000:
                self._warning(
                    f"Very long rest ({rest.duration}ms), is this intentional?",
                    rest.lineno
                )
    
    def _validate_tempo(self, value_node: ASTNode, lineno: int):
        """Validate tempo value."""
        if isinstance(value_node, IntegerLiteralNode):
            tempo = value_node.value
            if tempo < 20:
                self._warning(f"Tempo {tempo} is very slow (< 20 BPM)", lineno)
            elif tempo > 300:
                self._warning(f"Tempo {tempo} is very fast (> 300 BPM)", lineno)
            elif not (40 <= tempo <= 208):
                self._warning(
                    f"Tempo {tempo} is outside typical range (40-208 BPM)",
                    lineno
                )
            return tempo
        return None
    
    def _validate_volume(self, value_node: ASTNode, lineno: int):
        """Validate volume value."""
        if isinstance(value_node, IntegerLiteralNode):
            volume = value_node.value
            if volume < 0:
                self._error(f"Volume cannot be negative, got {volume}", lineno)
            elif volume > 127:
                self._warning(
                    f"Volume {volume} exceeds MIDI max (127), will be clamped",
                    lineno
                )
            return volume
        return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # Reporting
    # ═══════════════════════════════════════════════════════════════════════
    
    def report(self) -> str:
        """Generate a formatted report of all errors and warnings."""
        lines = []
        
        if self.errors:
            lines.append("=== SEMANTIC ERRORS ===")
            for err in self.errors:
                lines.append(err)
        
        if self.warnings:
            if lines:
                lines.append("")
            lines.append("=== WARNINGS ===")
            for warn in self.warnings:
                lines.append(warn)
        
        if not self.errors and not self.warnings:
            lines.append("✓ No semantic errors or warnings")
        
        return "\n".join(lines)