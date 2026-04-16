"""
ChordLang IR Generator
Translates AST to IR (Intermediate Representation).
"""

from typing import Any, List, Optional
from ast_nodes import *
from symbol_table import SymbolTable, SymbolKind
from visitors import ASTVisitor
from ir_instructions import (
    IRProgram, IROpcode, IRInstruction, NoteData, RestData
)


class IRGenerator(ASTVisitor):
    """
    Generates IR from an AST.
    
    Usage:
        generator = IRGenerator(symbol_table)
        ir_program = generator.generate(ast_root)
        print(ir_program)
    """
    
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.program = IRProgram()
        self.sequence_data = {}  # name -> list of notes
        self.chord_data = {}     # name -> list of notes
    
    def generate(self, ast_root: ProgramNode) -> IRProgram:
        """Generate IR from AST root."""
        # Add initial comment
        self.program.emit(
            IROpcode.COMMENT,
            "ChordLang IR - Generated Code",
            comment="Program start"
        )
        
        # Visit the AST
        ast_root.accept(self)
        
        # Add final comment
        self.program.emit(
            IROpcode.COMMENT,
            "End of program",
            comment="Program end"
        )
        
        return self.program
    
    # ═══════════════════════════════════════════════════════════════════════
    # Visitor Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    def visit_ProgramNode(self, node: ProgramNode):
        """Generate IR for entire program."""
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_AssignmentNode(self, node: AssignmentNode):
        """Generate IR for variable assignment."""
        # Special handling for tempo and volume
        if node.name == "tempo":
            value = self._eval_expression(node.value)
            self.program.emit(
                IROpcode.SET_TEMPO,
                value,
                lineno=node.lineno,
                comment=f"Set tempo to {value}"
            )
            return
        
        if node.name == "volume":
            value = self._eval_expression(node.value)
            self.program.emit(
                IROpcode.SET_VOLUME,
                value,
                lineno=node.lineno,
                comment=f"Set volume to {value}"
            )
            return
        
        if node.name == "instrument":
            instr_map = {
                'piano': 0,
                'guitar': 1,
                'bass': 2,
                'sawtooth': 3,
                'square': 4,
                'drums_kick': 5,
                'drums_snare': 6,
                'drums_hihat': 7
            }
            
            if isinstance(node.value, IdentifierNode):
                instr_name = node.value.name
                instr_id = instr_map.get(instr_name, 0)
                self.program.emit(
                    IROpcode.SET_INSTRUMENT,
                    instr_id,
                    lineno=node.lineno,
                    comment=f"Set instrument to {instr_name}"
                )
            return
        
        # Regular variable assignment
        value = self._eval_expression(node.value)
        self.program.emit(
            IROpcode.ASSIGN,
            node.name,
            value,
            lineno=node.lineno,
            comment=f"{node.name} = {value}"
        )
    
    def visit_SequenceNode(self, node: SequenceNode):
        """Generate IR for sequence definition."""
        # Convert notes to IR-friendly format
        notes = []
        for note in node.notes:
            if isinstance(note, NoteLiteralNode):
                notes.append(NoteData(note.pitch, note.octave, note.duration if note.duration is not None else 500))
            elif isinstance(note, RestNode):
                notes.append(RestData(note.duration if note.duration is not None else 500))
            elif isinstance(note, IdentifierNode):
                # Reference to another sequence
                notes.append(note.name)
        
        # Store sequence data
        self.sequence_data[node.name] = notes
        
        # Emit define instruction
        self.program.emit(
            IROpcode.DEFINE_SEQUENCE,
            node.name,
            notes,
            lineno=node.lineno,
            comment=f"Define sequence '{node.name}' with {len(notes)} items"
        )
    
    def visit_ChordNode(self, node: ChordNode):
        """Generate IR for chord definition."""
        # Convert notes to IR-friendly format
        notes = []
        for note in node.notes:
            if isinstance(note, NoteLiteralNode):
                notes.append(NoteData(note.pitch, note.octave, note.duration if note.duration is not None else 1000))
            elif isinstance(note, IdentifierNode):                notes.append(note.name)
        
        # Store chord data
        self.chord_data[node.name] = notes
        
        # Emit define instruction
        self.program.emit(
            IROpcode.DEFINE_CHORD,
            node.name,
            notes,
            lineno=node.lineno,
            comment=f"Define chord '{node.name}' with {len(notes)} notes"
        )
    
    def visit_PlayNode(self, node: PlayNode):
        """Generate IR for play statement."""
        for target in node.targets:
            if isinstance(target, NoteLiteralNode):
                # Play single note
                dur = target.duration if target.duration is not None else 500
                self.program.emit(
                    IROpcode.PLAY_NOTE,
                    target.pitch,
                    target.octave,
                    dur,
                    lineno=node.lineno,
                    comment=f"Play note {target.pitch}{target.octave}"
                )
            
            elif isinstance(target, RestNode):
                # Play rest
                dur = target.duration if target.duration is not None else 500
                self.program.emit(
                    IROpcode.PLAY_REST,
                    dur,
                    lineno=node.lineno,
                    comment=f"Rest for {dur}ms"
                )
            
            elif isinstance(target, IdentifierNode):
                # Play sequence or chord
                sym = self.symbol_table.lookup(target.name)
                
                if sym and sym.kind == SymbolKind.SEQUENCE:
                    self.program.emit(
                        IROpcode.PLAY_SEQUENCE,
                        target.name,
                        lineno=node.lineno,
                        comment=f"Play sequence '{target.name}'"
                    )
                elif sym and sym.kind == SymbolKind.CHORD:
                    self.program.emit(
                        IROpcode.PLAY_CHORD,
                        target.name,
                        lineno=node.lineno,
                        comment=f"Play chord '{target.name}'"
                    )
    
    def visit_RepeatNode(self, node: RepeatNode):
        """Generate IR for repeat loop."""
        # Labels for loop
        loop_start = self.program.new_label("repeat_start")
        loop_end = self.program.new_label("repeat_end")
        
        # Initialize counter
        counter_var = self.program.new_temp()
        count_value = self._eval_expression(node.count)
        
        self.program.emit(
            IROpcode.ASSIGN,
            counter_var,
            count_value,
            lineno=node.lineno,
            comment=f"Initialize repeat counter to {count_value}"
        )
        
        # Loop start label
        self.program.emit(
            IROpcode.LABEL,
            loop_start,
            comment="Repeat loop start"
        )
        
        # Check if counter is zero
        self.program.emit(
            IROpcode.JUMP_IF_ZERO,
            counter_var,
            loop_end,
            comment="Exit loop if counter is zero"
        )
        
        # Loop body
        for stmt in node.body:
            stmt.accept(self)
        
        # Decrement counter
        temp = self.program.new_temp()
        self.program.emit(IROpcode.SUB, temp, counter_var, 1, comment="Decrement counter")
        self.program.emit(IROpcode.ASSIGN, counter_var, temp)
        
        # Jump back to start
        self.program.emit(
            IROpcode.JUMP,
            loop_start,
            comment="Jump back to loop start"
        )
        
        # Loop end label
        self.program.emit(
            IROpcode.LABEL,
            loop_end,
            comment="Repeat loop end"
        )
    
    def visit_IfNode(self, node: IfNode):
        """Generate IR for if statement."""
        else_label = self.program.new_label("else")
        end_label = self.program.new_label("endif")
        
        # Evaluate condition
        condition_var = self._eval_condition(node.condition)
        
        # Jump to else if condition is false (zero)
        if node.else_body:
            self.program.emit(
                IROpcode.JUMP_IF_ZERO,
                condition_var,
                else_label,
                comment="Jump to else if condition is false"
            )
        else:
            self.program.emit(
                IROpcode.JUMP_IF_ZERO,
                condition_var,
                end_label,
                comment="Jump to end if condition is false"
            )
        
        # Then body
        for stmt in node.then_body:
            stmt.accept(self)
        
        # Jump over else
        if node.else_body:
            self.program.emit(IROpcode.JUMP, end_label, comment="Skip else block")
            
            # Else label
            self.program.emit(IROpcode.LABEL, else_label, comment="Else block")
            
            # Else body
            for stmt in node.else_body:
                stmt.accept(self)
        
        # End label
        self.program.emit(IROpcode.LABEL, end_label, comment="End of if statement")
    
    def visit_BinaryOpNode(self, node: BinaryOpNode):
        """This is handled by _eval_expression."""
        pass
    
    def visit_IntegerLiteralNode(self, node: IntegerLiteralNode):
        """Leaf node - handled by _eval_expression."""
        pass
    
    def visit_IdentifierNode(self, node: IdentifierNode):
        """Leaf node - handled by _eval_expression."""
        pass
    
    def visit_NoteLiteralNode(self, node: NoteLiteralNode):
        """Leaf node - handled elsewhere."""
        pass
    
    def visit_RestNode(self, node: RestNode):
        """Leaf node - handled elsewhere."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    def _eval_expression(self, node: ASTNode) -> Any:
        """
        Evaluate an expression and return result.
        For simple literals, return the value.
        For complex expressions, emit IR and return temp variable.
        """
        if isinstance(node, IntegerLiteralNode):
            return node.value
        
        if isinstance(node, IdentifierNode):
            return node.name
        
        if isinstance(node, BinaryOpNode):
            left = self._eval_expression(node.left)
            right = self._eval_expression(node.right)
            result = self.program.new_temp()
            
            opcode_map = {
                '+': IROpcode.ADD,
                '-': IROpcode.SUB,
                '%': IROpcode.MOD,
            }
            
            if node.operator in opcode_map:
                self.program.emit(
                    opcode_map[node.operator],
                    result,
                    left,
                    right,
                    lineno=node.lineno,
                    comment=f"{result} = {left} {node.operator} {right}"
                )
                return result
        
        return 0  # Fallback
    
    def _eval_condition(self, node: ASTNode) -> str:
        """
        Evaluate a conditional expression.
        Returns the name of the variable holding the result (0 or 1).
        """
        if isinstance(node, BinaryOpNode):
            left = self._eval_expression(node.left)
            right = self._eval_expression(node.right)
            result = self.program.new_temp()
            
            opcode_map = {
                '>': IROpcode.CMP_GT,
                '<': IROpcode.CMP_LT,
                '>=': IROpcode.CMP_GTE,
                '<=': IROpcode.CMP_LTE,
                '==': IROpcode.CMP_EQ,
                '!=': IROpcode.CMP_NEQ,
            }
            
            if node.operator in opcode_map:
                self.program.emit(
                    opcode_map[node.operator],
                    result,
                    left,
                    right,
                    lineno=node.lineno,
                    comment=f"{result} = ({left} {node.operator} {right})"
                )
                return result
        
        # For simple values, create a comparison with non-zero
        if isinstance(node, IntegerLiteralNode):
            result = self.program.new_temp()
            self.program.emit(
                IROpcode.CMP_NEQ,
                result,
                node.value,
                0,
                comment=f"{result} = ({node.value} != 0)"
            )
            return result
        
        # For identifiers
        if isinstance(node, IdentifierNode):
            return node.name
        
        return "_false"  # Fallback