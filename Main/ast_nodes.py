"""
ChordLang AST Node Definitions
Each node represents a construct in the ChordLang language.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Any


# ─── Base ───────────────────────────────────────────────────────────────────

class ASTNode:
    """Base class for all AST nodes."""

    def accept(self, visitor):
        """Accept a visitor (Visitor Pattern)."""
        method_name = f"visit_{type(self).__name__}"
        method = getattr(visitor, method_name, visitor.generic_visit)
        return method(self)

    def __repr__(self):
        fields = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items()
        )
        return f"{type(self).__name__}({fields})"


# ─── Literals & Primitives ──────────────────────────────────────────────────

@dataclass
class IntegerLiteralNode(ASTNode):
    """Integer literal, e.g. 120"""
    value: int
    lineno: int = 0


@dataclass
class NoteLiteralNode(ASTNode):
    """
    A single note, e.g. C4, G#3, Bb2:8
    pitch    : e.g. 'C', 'G#', 'Bb'
    octave   : int
    duration : optional int (beat subdivisions)
    """
    pitch: str
    octave: int
    duration: Optional[int]
    lineno: int = 0

    @property
    def full_name(self) -> str:
        return f"{self.pitch}{self.octave}"



@dataclass
class RestNode(ASTNode):
    """A rest (silence), optionally with duration."""
    duration: Optional[int]
    lineno: int = 0


@dataclass
class IdentifierNode(ASTNode):
    """Variable / sequence / chord reference by name."""
    name: str
    lineno: int = 0


# ─── Expressions ────────────────────────────────────────────────────────────

@dataclass
class BinaryOpNode(ASTNode):
    """Binary operation: left OP right.  OP ∈ {+, -, %, >, <, >=, <=, ==, !=}"""
    operator: str
    left: ASTNode
    right: ASTNode
    lineno: int = 0


# ─── Statements ─────────────────────────────────────────────────────────────

@dataclass
class AssignmentNode(ASTNode):
    """
    Variable assignment.
    e.g.  tempo = 120
          volume = 80
          myVar = 42
    """
    name: str
    value: ASTNode
    lineno: int = 0


@dataclass
class SequenceNode(ASTNode):
    """
    Named sequence of notes / rests.
    e.g.  sequence myMelody { C4, D4, E4:2, rest:1 }
    """
    name: str
    notes: List[ASTNode]   # NoteLiteralNode | RestNode | IdentifierNode
    lineno: int = 0


@dataclass
class ChordNode(ASTNode):
    """
    Named chord (simultaneous notes).
    e.g.  chord Cmaj { C4, E4, G4 }
    """
    name: str
    notes: List[NoteLiteralNode]
    lineno: int = 0


@dataclass
class PlayNode(ASTNode):
    """
    Play a note, rest, sequence, or chord.
    e.g.  play myMelody
          play C4
          play C4, E4, G4
    """
    targets: List[ASTNode]    # List of IdentifierNode | NoteLiteralNode | RestNode
    lineno: int = 0


@dataclass
class RepeatNode(ASTNode):
    """
    Repeat a block N times.
    e.g.  repeat 4 times { play C4, play D4 }
    """
    count: ASTNode           # IntegerLiteralNode | IdentifierNode
    body: List[ASTNode]
    lineno: int = 0


@dataclass
class IfNode(ASTNode):
    """
    Conditional statement.
    e.g.  if tempo > 100 then { play fast } else { play slow }
    """
    condition: ASTNode
    then_body: List[ASTNode]
    else_body: Optional[List[ASTNode]]
    lineno: int = 0


@dataclass
class ProgramNode(ASTNode):
    """Root node — list of top-level statements."""
    statements: List[ASTNode] = field(default_factory=list)
    lineno: int = 0