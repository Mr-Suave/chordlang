"""
ChordLang – Unit Tests
Covers: parser, AST structure, symbol table, visitor pattern.
Run with:  python -m pytest tests.py -v
"""

import pytest
from ast_nodes import (
    ProgramNode, AssignmentNode, SequenceNode, ChordNode,
    PlayNode, RepeatNode, IfNode, BinaryOpNode,
    IntegerLiteralNode, NoteLiteralNode, RestNode, IdentifierNode,
)
from symbol_table import SymbolTable, SymbolKind
from visitors import ASTPrinter, SymbolTableBuilder
from parser import parse


# ─── Helpers ─────────────────────────────────────────────────────────────────

def first_stmt(src: str):
    """Parse source and return the first statement."""
    tree = parse(src)
    assert tree is not None, "Parser returned None"
    assert len(tree.statements) >= 1, "No statements parsed"
    return tree.statements[0]


# ─── Assignment ──────────────────────────────────────────────────────────────

class TestAssignment:

    def test_tempo_assignment(self):
        node = first_stmt("tempo = 120")
        assert isinstance(node, AssignmentNode)
        assert node.name == "tempo"
        assert isinstance(node.value, IntegerLiteralNode)
        assert node.value.value == 120

    def test_volume_assignment(self):
        node = first_stmt("volume = 75")
        assert isinstance(node, AssignmentNode)
        assert node.name == "volume"
        assert node.value.value == 75

    def test_custom_variable(self):
        node = first_stmt("myVar = 42")
        assert isinstance(node, AssignmentNode)
        assert node.name == "myVar"
        assert node.value.value == 42


# ─── Sequence ────────────────────────────────────────────────────────────────

class TestSequence:

    def test_simple_sequence(self):
        node = first_stmt("sequence melody { C4, D4, E4 }")
        assert isinstance(node, SequenceNode)
        assert node.name == "melody"
        assert len(node.notes) == 3
        assert all(isinstance(n, NoteLiteralNode) for n in node.notes)

    def test_sequence_with_duration(self):
        node = first_stmt("sequence r { C4:2, D4:4 }")
        assert node.notes[0].duration == 2
        assert node.notes[1].duration == 4

    def test_sequence_with_rest(self):
        node = first_stmt("sequence r { C4, rest, D4 }")
        assert isinstance(node.notes[1], RestNode)

    def test_sequence_rest_with_duration(self):
        node = first_stmt("sequence r { C4, rest:2 }")
        assert node.notes[1].duration == 2

    def test_empty_sequence(self):
        node = first_stmt("sequence empty {  }")
        assert isinstance(node, SequenceNode)
        assert node.notes == []


# ─── Chord ───────────────────────────────────────────────────────────────────

class TestChord:

    def test_simple_chord(self):
        node = first_stmt("chord Cmaj { C4, E4, G4 }")
        assert isinstance(node, ChordNode)
        assert node.name == "Cmaj"
        assert len(node.notes) == 3

    def test_chord_with_sharp(self):
        node = first_stmt("chord Fsharp { F#4, A#4, C#5 }")
        assert node.notes[0].pitch == "F#"
        assert node.notes[0].octave == 4

    def test_chord_with_flat(self):
        node = first_stmt("chord Bbmin { Bb3, Db4, F4 }")
        assert node.notes[0].pitch == "Bb"


# ─── Play ────────────────────────────────────────────────────────────────────

class TestPlay:

    def test_play_note(self):
        node = first_stmt("play C4")
        assert isinstance(node, PlayNode)
        assert isinstance(node.target, NoteLiteralNode)
        assert node.target.pitch == "C"
        assert node.target.octave == 4

    def test_play_identifier(self):
        node = first_stmt("play melody")
        assert isinstance(node, PlayNode)
        assert isinstance(node.target, IdentifierNode)
        assert node.target.name == "melody"

    def test_play_rest(self):
        node = first_stmt("play rest")
        assert isinstance(node, PlayNode)
        assert isinstance(node.target, RestNode)


# ─── Repeat ──────────────────────────────────────────────────────────────────

class TestRepeat:

    def test_repeat_integer(self):
        node = first_stmt("repeat 4 times { play C4 }")
        assert isinstance(node, RepeatNode)
        assert isinstance(node.count, IntegerLiteralNode)
        assert node.count.value == 4
        assert len(node.body) == 1

    def test_repeat_identifier(self):
        node = first_stmt("repeat n times { play C4 }")
        assert isinstance(node.count, IdentifierNode)
        assert node.count.name == "n"

    def test_repeat_nested(self):
        src = "repeat 2 times { repeat 3 times { play C4 } }"
        node = first_stmt(src)
        inner = node.body[0]
        assert isinstance(inner, RepeatNode)
        assert inner.count.value == 3


# ─── If / Else ───────────────────────────────────────────────────────────────

class TestIf:

    def test_if_with_else(self):
        src = "if tempo > 100 then { play fast } else { play slow }"
        node = first_stmt(src)
        assert isinstance(node, IfNode)
        assert node.else_body is not None

    def test_if_no_else(self):
        src = "if tempo > 100 then { play fast }"
        node = first_stmt(src)
        assert isinstance(node, IfNode)
        assert node.else_body is None

    def test_condition_is_binop(self):
        src = "if tempo >= 120 then { play C4 }"
        node = first_stmt(src)
        assert isinstance(node.condition, BinaryOpNode)
        assert node.condition.operator == ">="

    def test_equality_condition(self):
        src = "if volume == 100 then { play C4 }"
        node = first_stmt(src)
        assert node.condition.operator == "=="

    def test_neq_condition(self):
        src = "if volume != 0 then { play C4 }"
        node = first_stmt(src)
        assert node.condition.operator == "!="


# ─── Expressions ─────────────────────────────────────────────────────────────

class TestExpressions:

    def test_addition(self):
        node = first_stmt("myVar = 10 + 5")
        assert isinstance(node.value, BinaryOpNode)
        assert node.value.operator == "+"
        assert node.value.left.value == 10
        assert node.value.right.value == 5

    def test_modulo(self):
        node = first_stmt("myVar = 10 % 3")
        assert node.value.operator == "%"

    def test_subtraction(self):
        node = first_stmt("myVar = 20 - 7")
        assert node.value.operator == "-"

    def test_precedence_plus_before_compare(self):
        # "tempo + 10 > 100" should be "(tempo + 10) > 100"
        src = "if tempo + 10 > 100 then { play C4 }"
        node = first_stmt(src)
        cond = node.condition
        assert cond.operator == ">"
        assert isinstance(cond.left, BinaryOpNode)
        assert cond.left.operator == "+"


# ─── Note Literal Parsing ─────────────────────────────────────────────────────

class TestNoteLiteral:

    def test_simple_note(self):
        node = first_stmt("play C4")
        n = node.target
        assert n.pitch == "C"
        assert n.octave == 4
        assert n.duration is None

    def test_sharp_note(self):
        node = first_stmt("play F#3")
        assert node.target.pitch == "F#"
        assert node.target.octave == 3

    def test_flat_note(self):
        node = first_stmt("play Bb2")
        assert node.target.pitch == "Bb"
        assert node.target.octave == 2

    def test_note_with_duration(self):
        node = first_stmt("play G4:8")
        assert node.target.duration == 8


# ─── Symbol Table ─────────────────────────────────────────────────────────────

class TestSymbolTable:

    def test_builtin_tempo(self):
        st = SymbolTable()
        sym = st.lookup("tempo")
        assert sym is not None
        assert sym.kind == SymbolKind.VARIABLE
        assert sym.value == 120

    def test_builtin_volume(self):
        st = SymbolTable()
        sym = st.lookup("volume")
        assert sym.value == 100

    def test_define_variable(self):
        st = SymbolTable()
        st.define_variable("x", 5)
        assert st.lookup("x").value == 5

    def test_update_variable(self):
        st = SymbolTable()
        st.define_variable("x", 5)
        st.update("x", 10)
        assert st.lookup("x").value == 10

    def test_define_sequence(self):
        st = SymbolTable()
        st.define_sequence("melody", ["C4", "D4"])
        sym = st.lookup_sequence("melody")
        assert sym is not None
        assert sym.kind == SymbolKind.SEQUENCE

    def test_define_chord(self):
        st = SymbolTable()
        st.define_chord("Cmaj", ["C4", "E4", "G4"])
        sym = st.lookup_chord("Cmaj")
        assert sym.kind == SymbolKind.CHORD

    def test_scope_chain(self):
        st = SymbolTable()
        st.define_variable("outer", 1)
        st.enter_scope("inner")
        assert st.lookup("outer") is not None, "Should find outer from inner scope"
        st.define_variable("inner_var", 2)
        st.exit_scope()
        assert st.lookup("inner_var") is None, "inner_var should not be visible after exit"

    def test_exit_global_raises(self):
        st = SymbolTable()
        with pytest.raises(RuntimeError):
            st.exit_scope()

    def test_dump_is_string(self):
        st = SymbolTable()
        st.define_variable("x", 1)
        dump = st.dump()
        assert isinstance(dump, str)
        assert "x" in dump


# ─── Symbol Table Builder ─────────────────────────────────────────────────────

class TestSymbolTableBuilder:

    def _build(self, src: str):
        tree = parse(src)
        builder = SymbolTableBuilder()
        st = builder.build(tree)
        return st, builder.errors

    def test_builds_variable(self):
        st, errors = self._build("tempo = 140")
        assert st.lookup("tempo").value == 140
        assert errors == []

    def test_builds_sequence(self):
        st, errors = self._build("sequence mel { C4, D4 }")
        assert st.lookup_sequence("mel") is not None
        assert errors == []

    def test_builds_chord(self):
        st, errors = self._build("chord Cmaj { C4, E4, G4 }")
        assert st.lookup_chord("Cmaj") is not None

    def test_undefined_play_triggers_error(self):
        _, errors = self._build("play undefinedSeq")
        assert any("undefinedSeq" in e for e in errors)

    def test_repeat_creates_scope(self):
        # Variables defined inside repeat are NOT visible outside
        src = "repeat 2 times { myInner = 5 }"
        st, _ = self._build(src)
        # After building, scope has exited; inner var not in global
        assert st.lookup("myInner") is None


# ─── AST Printer ─────────────────────────────────────────────────────────────

class TestASTPrinter:

    def test_printer_returns_string(self):
        tree = parse("tempo = 120\nsequence mel { C4, D4 }")
        printer = ASTPrinter()
        output = printer.print(tree)
        assert isinstance(output, str)
        assert "Assign" in output
        assert "Sequence" in output

    def test_printer_shows_note(self):
        tree = parse("play C4")
        output = ASTPrinter().print(tree)
        assert "Note [C4]" in output

    def test_printer_shows_rest(self):
        tree = parse("play rest")
        output = ASTPrinter().print(tree)
        assert "Rest" in output


# ─── Integration ─────────────────────────────────────────────────────────────

class TestIntegration:

    def test_full_program(self):
        src = """
# Set global parameters
tempo = 140
volume = 90

sequence verse { C4, E4, G4:2, rest:1, A4 }
chord Cmaj { C4, E4, G4 }

repeat 2 times {
    play verse
    play Cmaj
}

if tempo > 100 then {
    play G4
} else {
    play C3
}
"""
        tree = parse(src)
        assert tree is not None
        assert len(tree.statements) == 6

        builder = SymbolTableBuilder()
        st = builder.build(tree)
        assert builder.errors == []
        assert st.lookup("tempo").value == 140
        assert st.lookup_sequence("verse") is not None
        assert st.lookup_chord("Cmaj") is not None

        output = ASTPrinter().print(tree)
        assert "Sequence [verse]" in output
        assert "Chord [Cmaj]" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])