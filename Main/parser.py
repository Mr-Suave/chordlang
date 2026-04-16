"""
ChordLang Parser
Builds an AST from a token stream produced by the lexer.
"""

import ply.yacc as yacc
from lexer import lexer, tokens          # we reuse the existing lexer
from ast_nodes import (
    ProgramNode, AssignmentNode, SequenceNode, ChordNode,
    PlayNode, RepeatNode, IfNode,
    BinaryOpNode, IntegerLiteralNode, NoteLiteralNode,
    RestNode, IdentifierNode,
)

# ─── Operator Precedence (low → high) ────────────────────────────────────────
# Mirrors standard expression precedence inside conditions.

precedence = (
    ('left',  'EQ',   'NEQ'),
    ('left',  'GT',   'LT',  'GTE', 'LTE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'MODULO'),
    ('right', 'UMINUS'),
)


# ─── Top-level ───────────────────────────────────────────────────────────────

def p_program(p):
    """program : statement_list"""
    p[0] = ProgramNode(statements=p[1], lineno=1)


def p_statement_list_multi(p):
    """statement_list : statement_list statement"""
    p[0] = p[1] + [p[2]]


def p_statement_list_single(p):
    """statement_list : statement"""
    p[0] = [p[1]]


def p_statement_list_empty(p):
    """statement_list : """
    p[0] = []


# ─── Statements ──────────────────────────────────────────────────────────────

def p_statement(p):
    """statement : assignment
                 | sequence_decl
                 | chord_decl
                 | play_stmt
                 | repeat_stmt
                 | if_stmt"""
    p[0] = p[1]


# assignment: IDENTIFIER = expr
def p_assignment(p):
    """assignment : IDENTIFIER ASSIGN expression"""
    p[0] = AssignmentNode(name=p[1], value=p[3], lineno=p.lineno(1))

# ADDED THIS NEW RULE as part of WEEK 4 submission ( incorporate y = C4:500 type of statement ):
def p_assignment_note(p):
    """assignment : IDENTIFIER ASSIGN note_literal"""
    p[0] = AssignmentNode(name=p[1], value=p[3], lineno=p.lineno(1))


# tempo = 120  / volume = 80  (reserved keywords as LHS)
def p_assignment_tempo(p):
    """assignment : TEMPO ASSIGN expression"""
    p[0] = AssignmentNode(name="tempo", value=p[3], lineno=p.lineno(1))


def p_assignment_volume(p):
    """assignment : VOLUME ASSIGN expression"""
    p[0] = AssignmentNode(name="volume", value=p[3], lineno=p.lineno(1))


def p_assignment_instrument(p):
    """assignment : INSTRUMENT ASSIGN expression"""
    p[0] = AssignmentNode(name="instrument", value=p[3], lineno=p.lineno(1))


# sequence myMelody { note, note, ... }
def p_sequence_decl(p):
    """sequence_decl : SEQUENCE IDENTIFIER LBRACE note_list RBRACE"""
    p[0] = SequenceNode(name=p[2], notes=p[4], lineno=p.lineno(1))


# chord Cmaj { note, note, note }
def p_chord_decl(p):
    """chord_decl : CHORD IDENTIFIER LBRACE note_list RBRACE"""
    p[0] = ChordNode(name=p[2], notes=p[4], lineno=p.lineno(1))


# play target, target, ...
def p_play_stmt(p):
    """play_stmt : PLAY play_target_list"""
    # If there's only one item, we keep the original behavior for compatibility,
    # or we can wrap them all in a list of PlayNodes in the generator.
    # For now, let's return a list of PlayNodes if we want to stick to the AST, 
    # but the simplest AST change is to make PlayNode accept a list.
    p[0] = PlayNode(targets=p[2], lineno=p.lineno(1))

def p_play_target_list_multi(p):
    """play_target_list : play_target_list COMMA play_target"""
    p[0] = p[1] + [p[3]]

def p_play_target_list_single(p):
    """play_target_list : play_target"""
    p[0] = [p[1]]

def p_play_target(p):
    """play_target : note_literal
                   | rest_literal
                   | IDENTIFIER"""
    if isinstance(p[1], str):
        p[0] = IdentifierNode(name=p[1], lineno=p.lineno(1))
    else:
        p[0] = p[1]


# repeat N times { ... }
def p_repeat_stmt(p):
    """repeat_stmt : REPEAT expression TIMES LBRACE statement_list RBRACE"""
    p[0] = RepeatNode(count=p[2], body=p[5], lineno=p.lineno(1))


# if condition then { ... } else { ... }
def p_if_stmt_with_else(p):
    """if_stmt : IF expression THEN LBRACE statement_list RBRACE ELSE LBRACE statement_list RBRACE"""
    p[0] = IfNode(
        condition=p[2],
        then_body=p[5],
        else_body=p[9],
        lineno=p.lineno(1),
    )


def p_if_stmt_no_else(p):
    """if_stmt : IF expression THEN LBRACE statement_list RBRACE"""
    p[0] = IfNode(
        condition=p[2],
        then_body=p[5],
        else_body=None,
        lineno=p.lineno(1),
    )


# ─── Expressions ─────────────────────────────────────────────────────────────

def p_expression_binop(p):
    """expression : expression PLUS   expression
                  | expression MINUS  expression
                  | expression MODULO expression
                  | expression GT     expression
                  | expression LT     expression
                  | expression GTE    expression
                  | expression LTE    expression
                  | expression EQ     expression
                  | expression NEQ    expression"""
    p[0] = BinaryOpNode(operator=p[2], left=p[1], right=p[3], lineno=p.lineno(2))


def p_expression_integer(p):
    """expression : INTEGER"""
    p[0] = IntegerLiteralNode(value=p[1], lineno=p.lineno(1))


def p_expression_identifier(p):
    """expression : IDENTIFIER"""
    p[0] = IdentifierNode(name=p[1], lineno=p.lineno(1))


def p_expression_tempo(p):
    """expression : TEMPO"""
    p[0] = IdentifierNode(name="tempo", lineno=p.lineno(1))


def p_expression_volume(p):
    """expression : VOLUME"""
    p[0] = IdentifierNode(name="volume", lineno=p.lineno(1))

def p_expression_instrument(p):
    """expression : INSTRUMENT"""
    p[0] = IdentifierNode(name="instrument", lineno=p.lineno(1))

def p_expression_uminus(p):
    """expression : MINUS expression %prec UMINUS"""
    p[0] = BinaryOpNode(
        operator='-',
        left=IntegerLiteralNode(value=0, lineno=p.lineno(1)),
        right=p[2],
        lineno=p.lineno(1)
    )


# ─── Note list (used in sequence / chord bodies) ─────────────────────────────

def p_note_list_multi(p):
    """note_list : note_list COMMA note_item"""
    p[0] = p[1] + [p[3]]


def p_note_list_single(p):
    """note_list : note_item"""
    p[0] = [p[1]]


def p_note_list_empty(p):
    """note_list : """
    p[0] = []


def p_note_item_note(p):
    """note_item : note_literal"""
    p[0] = p[1]


def p_note_item_rest(p):
    """note_item : rest_literal"""
    p[0] = p[1]


def p_note_item_identifier(p):
    """note_item : IDENTIFIER"""
    p[0] = IdentifierNode(name=p[1], lineno=p.lineno(1))


# ─── Terminals ───────────────────────────────────────────────────────────────

def p_note_literal(p):
    """note_literal : NOTE_LITERAL"""
    raw = p[1]                   # e.g. "G#3:8" or "C4"
    if ":" in raw:
        note_part, dur_part = raw.split(":", 1)
        duration = int(dur_part)
    else:
        note_part = raw
        duration  = None

    # Split pitch from octave digit
    if len(note_part) >= 2 and note_part[-2] in ("#", "b"):
        pitch  = note_part[:-1]
        octave = int(note_part[-1])
    else:
        pitch  = note_part[:-1]
        octave = int(note_part[-1])

    p[0] = NoteLiteralNode(pitch=pitch, octave=octave, duration=duration, lineno=p.lineno(1))


def p_rest_literal(p):
    """rest_literal : REST
                    | REST COLON INTEGER"""
    if len(p) == 2:
        p[0] = RestNode(duration=None, lineno=p.lineno(1))
    else:
        p[0] = RestNode(duration=p[3], lineno=p.lineno(1))




# ─── Error recovery ──────────────────────────────────────────────────────────

def p_error(p):
    if p:
        print(f"[ParseError] Unexpected token {p.type!r} ({p.value!r}) at line {p.lineno}")
        # Attempt recovery: skip tokens until we find a synchronisation point
        # while True:
        #     tok = parser.token()
        #     if tok is None or tok.type == "RBRACE":
        #         break
        parser.errok()
    else:
        print("[ParseError] Unexpected end of input.")


# ─── Build ───────────────────────────────────────────────────────────────────

parser = yacc.yacc(debug=False, write_tables=False)


# ─── Public API ──────────────────────────────────────────────────────────────

def parse(source: str) -> ProgramNode:
    """
    Parse a ChordLang source string and return a ProgramNode (AST root).

    Parameters
    ----------
    source : str
        ChordLang source code.

    Returns
    -------
    ProgramNode
        Root of the AST.
    """
    lexer.lineno = 1
    return parser.parse(source, lexer=lexer, tracking=True)