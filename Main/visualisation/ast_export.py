"""
Run ChordLang parser on a sample program and export AST as JSON.
Usage: python3 ast_export.py > ast_output.json
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
from ast_nodes import (
    ProgramNode, AssignmentNode, SequenceNode, ChordNode,
    PlayNode, RepeatNode, IfNode, BinaryOpNode,
    IntegerLiteralNode, NoteLiteralNode, RestNode, IdentifierNode, ASTNode,
)
from parser import parse



# ── Sample ChordLang program ──────────────────────────────────────────────────

SAMPLE = """
# A mildly complex ChordLang program
tempo = 140
volume = 85

sequence intro { C4, E4, G4:2, rest:1, A4, G4 }
sequence bridge { F4, A4, C5:2, rest:1 }

chord Cmaj { C4, E4, G4 }
chord Amin { A3, C4, E4 }

repeat 2 times {
    play intro
    play Cmaj
}

if tempo > 120 then {
    play bridge
    play Amin
} else {
    play intro
}
"""


# ── AST → dict serialiser ─────────────────────────────────────────────────────

def node_to_dict(node) -> dict:
    """Recursively convert an AST node into a JSON-serialisable dict."""
    if node is None:
        return None

    kind = type(node).__name__

    if isinstance(node, ProgramNode):
        return {
            "type": "Program",
            "children": [node_to_dict(s) for s in node.statements],
        }

    if isinstance(node, AssignmentNode):
        return {
            "type": "Assignment",
            "label": f"{node.name} =",
            "name": node.name,
            "lineno": node.lineno,
            "children": [node_to_dict(node.value)],
        }

    if isinstance(node, SequenceNode):
        return {
            "type": "Sequence",
            "label": f"sequence {node.name}",
            "name": node.name,
            "lineno": node.lineno,
            "children": [node_to_dict(n) for n in node.notes],
        }

    if isinstance(node, ChordNode):
        return {
            "type": "Chord",
            "label": f"chord {node.name}",
            "name": node.name,
            "lineno": node.lineno,
            "children": [node_to_dict(n) for n in node.notes],
        }

    if isinstance(node, PlayNode):
        return {
            "type": "Play",
            "label": "play",
            "lineno": node.lineno,
            "children": [node_to_dict(node.target)],
        }

    if isinstance(node, RepeatNode):
        return {
            "type": "Repeat",
            "label": "repeat … times",
            "lineno": node.lineno,
            "children": [
                {"type": "RepeatCount", "label": "count", "children": [node_to_dict(node.count)]},
                {"type": "RepeatBody",  "label": "body",  "children": [node_to_dict(s) for s in node.body]},
            ],
        }

    if isinstance(node, IfNode):
        branches = [
            {"type": "IfCondition", "label": "condition", "children": [node_to_dict(node.condition)]},
            {"type": "ThenBranch",  "label": "then",      "children": [node_to_dict(s) for s in node.then_body]},
        ]
        if node.else_body:
            branches.append(
                {"type": "ElseBranch", "label": "else", "children": [node_to_dict(s) for s in node.else_body]}
            )
        return {
            "type": "If",
            "label": "if … then … else",
            "lineno": node.lineno,
            "children": branches,
        }

    if isinstance(node, BinaryOpNode):
        return {
            "type": "BinaryOp",
            "label": node.operator,
            "operator": node.operator,
            "lineno": node.lineno,
            "children": [node_to_dict(node.left), node_to_dict(node.right)],
        }

    if isinstance(node, IntegerLiteralNode):
        return {"type": "Integer", "label": str(node.value), "value": node.value, "children": []}

    if isinstance(node, NoteLiteralNode):
        dur = f":{node.duration}" if node.duration else ""
        return {"type": "Note", "label": f"{node.full_name}{dur}", "children": []}

    if isinstance(node, RestNode):
        dur = f":{node.duration}" if node.duration else ""
        return {"type": "Rest", "label": f"rest{dur}", "children": []}

    if isinstance(node, IdentifierNode):
        return {"type": "Identifier", "label": node.name, "name": node.name, "children": []}

    return {"type": kind, "label": kind, "children": []}


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tree = parse(SAMPLE)
    data = node_to_dict(tree)
    print(json.dumps(data, indent=2))