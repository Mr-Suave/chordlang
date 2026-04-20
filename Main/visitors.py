"""
ChordLang AST Visitors

1. ASTVisitor        – abstract base; override visit_* methods
2. ASTPrinter        – pretty-prints the tree for debugging
3. SymbolTableBuilder – walks the AST and populates a SymbolTable
"""

import textwrap
from typing import Any
from ast_nodes import (
    ProgramNode, AssignmentNode, SequenceNode, ChordNode,
    PlayNode, RepeatNode, IfNode, BinaryOpNode,
    IntegerLiteralNode, NoteLiteralNode, RestNode, IdentifierNode,
)
from symbol_table import SymbolTable, SymbolKind


# ─── Base Visitor ────────────────────────────────────────────────────────────

class ASTVisitor:
    """
    Abstract base visitor.

    Override visit_<NodeClassName> methods in subclasses.
    Call node.accept(visitor) to dispatch.
    """

    def generic_visit(self, node):
        raise NotImplementedError(
            f"{type(self).__name__} has no handler for {type(node).__name__}"
        )

    def visit_children(self, nodes):
        """Helper: visit a list of nodes and return results."""
        return [node.accept(self) for node in nodes]


# ─── Pretty-Printer ──────────────────────────────────────────────────────────

class ASTPrinter(ASTVisitor):
    """
    Produces a human-readable indented tree of the AST.

    Usage
    -----
        printer = ASTPrinter()
        print(printer.print(ast_root))
    """

    def __init__(self):
        self._indent = 0

    def _line(self, text: str) -> str:
        return "  " * self._indent + text

    def _block(self, nodes) -> str:
        self._indent += 1
        out = "\n".join(n.accept(self) for n in nodes)
        self._indent -= 1
        return out

    def print(self, node) -> str:
        return node.accept(self)

    # ── Visitors ──────────────────────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode) -> str:
        body = self._block(node.statements) if node.statements else self._line("(empty)")
        return f"Program\n{body}"

    def visit_AssignmentNode(self, node: AssignmentNode) -> str:
        self._indent += 1
        val = node.value.accept(self)
        self._indent -= 1
        return self._line(f"Assign [{node.name}]\n{val}")

    def visit_SequenceNode(self, node: SequenceNode) -> str:
        self._indent += 1
        notes = "\n".join(n.accept(self) for n in node.notes)
        self._indent -= 1
        return self._line(f"Sequence [{node.name}]\n{notes}")

    def visit_ChordNode(self, node: ChordNode) -> str:
        self._indent += 1
        notes = "\n".join(n.accept(self) for n in node.notes)
        self._indent -= 1
        return self._line(f"Chord [{node.name}]\n{notes}")

    def visit_PlayNode(self, node: PlayNode) -> str:
        self._indent += 1
        targets = "\n".join(t.accept(self) for t in node.targets)
        self._indent -= 1
        return self._line(f"Play\n{targets}")

    def visit_RepeatNode(self, node: RepeatNode) -> str:
        self._indent += 1
        count = node.count.accept(self)
        body  = self._block(node.body)
        self._indent -= 1
        return self._line(f"Repeat\n{count}\n{body}")

    def visit_IfNode(self, node: IfNode) -> str:
        self._indent += 1
        cond      = node.condition.accept(self)
        then_body = self._block(node.then_body)
        else_body = self._block(node.else_body) if node.else_body else self._line("(no else)")
        self._indent -= 1
        return self._line(f"If\n{cond}\nThen:\n{then_body}\nElse:\n{else_body}")

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        self._indent += 1
        left  = node.left.accept(self)
        right = node.right.accept(self)
        self._indent -= 1
        return self._line(f"BinaryOp [{node.operator}]\n{left}\n{right}")

    def visit_IntegerLiteralNode(self, node: IntegerLiteralNode) -> str:
        return self._line(f"Integer [{node.value}]")

    def visit_NoteLiteralNode(self, node: NoteLiteralNode) -> str:
        dur = f":{node.duration}" if node.duration else ""
        return self._line(f"Note [{node.full_name}{dur}]")

    def visit_RestNode(self, node: RestNode) -> str:
        dur = f":{node.duration}" if node.duration else ""
        return self._line(f"Rest{dur}")

    def visit_IdentifierNode(self, node: IdentifierNode) -> str:
        return self._line(f"Identifier [{node.name}]")


# ─── Symbol Table Builder ────────────────────────────────────────────────────

class SymbolTableBuilder(ASTVisitor):
    """
    Walks the AST and builds a SymbolTable.

    Usage
    -----
        builder = SymbolTableBuilder()
        sym_table = builder.build(ast_root)
        print(sym_table.dump())
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: list[str] = []

    def build(self, node: ProgramNode) -> SymbolTable:
        node.accept(self)
        return self.symbol_table

    def _error(self, msg: str, lineno: int = 0):
        self.errors.append(f"[Line {lineno}] {msg}")

    # ── Visitors ──────────────────────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_AssignmentNode(self, node: AssignmentNode):
        # Evaluate RHS enough to store a compile-time value if it's a literal
        value = self._eval_literal(node.value)
        existing = self.symbol_table.lookup(node.name)
        if existing:
            self.symbol_table.update(node.name, value)
        else:
            self.symbol_table.define_variable(node.name, value, lineno=node.lineno)

    def visit_SequenceNode(self, node: SequenceNode):
        existing = self.symbol_table.lookup(node.name)
        if existing and existing.kind != SymbolKind.SEQUENCE:
            self._error(
                f"'{node.name}' already defined as {existing.kind.name}; "
                f"cannot redefine as SEQUENCE.",
                node.lineno,
            )
            return
        self.symbol_table.define_sequence(node.name, node.notes, lineno=node.lineno)

    def visit_ChordNode(self, node: ChordNode):
        existing = self.symbol_table.lookup(node.name)
        if existing and existing.kind != SymbolKind.CHORD:
            self._error(
                f"'{node.name}' already defined as {existing.kind.name}; "
                f"cannot redefine as CHORD.",
                node.lineno,
            )
            return
        self.symbol_table.define_chord(node.name, node.notes, lineno=node.lineno)

    def visit_PlayNode(self, node: PlayNode):
        # Validate that identifier targets are defined
        for target in node.targets:
            if isinstance(target, IdentifierNode):
                name = target.name
                if not self.symbol_table.lookup(name):
                    self._error(f"Undefined symbol '{name}' used in play statement.", node.lineno)

    # In SymbolTableBuilder class only!

    def visit_RepeatNode(self, node: RepeatNode):
        # Visit the count expression
        node.count.accept(self)
        
        # Process body in the same scope
        for stmt in node.body:
            stmt.accept(self)

    def visit_IfNode(self, node: IfNode):
        # Check condition identifiers
        node.condition.accept(self)

        # Process then-body in the same scope
        for stmt in node.then_body:
            stmt.accept(self)

        # Process else-body in the same scope
        if node.else_body:
            for stmt in node.else_body:
                stmt.accept(self)

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        node.left.accept(self)
        node.right.accept(self)

    def visit_IdentifierNode(self, node: IdentifierNode):
        if not self.symbol_table.lookup(node.name):
            self._error(f"Undefined symbol '{node.name}'.", node.lineno)

    # Leaf nodes — nothing to register
    def visit_IntegerLiteralNode(self, node):  pass
    def visit_NoteLiteralNode(self, node):     pass
    def visit_RestNode(self, node):            pass

    # ── Helpers ───────────────────────────────────────────────────────────

    def _eval_literal(self, node) -> Any:
        """Return the compile-time value of a node if it is a literal, else None."""
        if isinstance(node, IntegerLiteralNode):
            return node.value
        return None   # complex expressions resolved at runtime