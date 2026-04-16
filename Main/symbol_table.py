"""
ChordLang Symbol Table
Tracks variables, sequences, and chords with scope management.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional


class SymbolKind(Enum):
    VARIABLE = auto()   # tempo, volume, user-defined numeric vars
    SEQUENCE = auto()   # named note sequences
    CHORD    = auto()   # named chords


class Symbol:
    """An entry in the symbol table."""

    def __init__(
        self,
        name: str,
        kind: SymbolKind,
        value: Any = None,
        lineno: int = 0,
    ):
        self.name   = name
        self.kind   = kind
        self.value  = value     # runtime value or AST node
        self.lineno = lineno

    def __repr__(self):
        return f"Symbol(name={self.name!r}, kind={self.kind.name}, value={self.value!r})"


class Scope:
    """
    A single scope (e.g. global, or a block inside repeat/if).
    Symbols are stored in a flat dict keyed by name.
    """

    def __init__(self, name: str = "global", parent: Optional["Scope"] = None):
        self.name    = name
        self.parent  = parent
        self.children: List["Scope"] = []
        self._table: Dict[str, Symbol] = {}

    # ── Mutation ──────────────────────────────────────────────────────────

    def define(self, symbol: Symbol) -> None:
        """Add or overwrite a symbol in THIS scope."""
        self._table[symbol.name] = symbol

    # ── Lookup ────────────────────────────────────────────────────────────

    def lookup(self, name: str, local_only: bool = False) -> Optional[Symbol]:
        """
        Search for a symbol by name.
        Walks up the scope chain unless local_only=True.
        """
        if name in self._table:
            return self._table[name]
        if not local_only and self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self._table.get(name)

    # ── Introspection ─────────────────────────────────────────────────────

    def symbols(self) -> List[Symbol]:
        return list(self._table.values())

    def __repr__(self):
        return f"Scope({self.name!r}, symbols={list(self._table.keys())})"


class SymbolTable:
    """
    Manages a stack of Scope objects.

    Usage (for our personal or future use):
    -----
        st = SymbolTable()
        st.define_variable("tempo", 120)
        st.enter_scope("repeat_block")
        st.define_variable("x", 5)
        st.exit_scope()
    """

    def __init__(self):
        self._global = Scope("global")
        self._scope_stack: List[Scope] = [self._global]
        self._seed_builtins()

    # ── Built-in symbols ─────────────────────────────────────────────────

    def _seed_builtins(self):
        """Pre-populate well-known variables with sensible defaults."""
        self.define_variable("tempo",  120, lineno=0)
        self.define_variable("volume", 100, lineno=0)

    # ── Scope management ─────────────────────────────────────────────────

    @property
    def current_scope(self) -> Scope:
        return self._scope_stack[-1]

    def enter_scope(self, name: str = "block") -> Scope:
        new_scope = Scope(name=name, parent=self.current_scope)
        self.current_scope.children.append(new_scope) 
        self._scope_stack.append(new_scope)
        return new_scope

    def exit_scope(self) -> Scope:
        if len(self._scope_stack) == 1:
            raise RuntimeError("Cannot exit the global scope.")
        return self._scope_stack.pop()

    def scope_depth(self) -> int:
        return len(self._scope_stack)

    # ── Defining symbols ─────────────────────────────────────────────────

    def define_variable(self, name: str, value: Any = None, lineno: int = 0) -> Symbol:
        sym = Symbol(name, SymbolKind.VARIABLE, value, lineno)
        self.current_scope.define(sym)
        return sym

    def define_sequence(self, name: str, notes: Any = None, lineno: int = 0) -> Symbol:
        sym = Symbol(name, SymbolKind.SEQUENCE, notes, lineno)
        self.current_scope.define(sym)
        return sym

    def define_chord(self, name: str, notes: Any = None, lineno: int = 0) -> Symbol:
        sym = Symbol(name, SymbolKind.CHORD, notes, lineno)
        self.current_scope.define(sym)
        return sym

    # ── Looking up symbols ────────────────────────────────────────────────

    def lookup(self, name: str) -> Optional[Symbol]:
        """Walk the scope chain from current to global."""
        return self.current_scope.lookup(name)

    def lookup_variable(self, name: str) -> Optional[Symbol]:
        sym = self.lookup(name)
        return sym if sym and sym.kind == SymbolKind.VARIABLE else None

    def lookup_sequence(self, name: str) -> Optional[Symbol]:
        sym = self.lookup(name)
        return sym if sym and sym.kind == SymbolKind.SEQUENCE else None

    def lookup_chord(self, name: str) -> Optional[Symbol]:
        sym = self.lookup(name)
        return sym if sym and sym.kind == SymbolKind.CHORD else None

    # ── Updating values ───────────────────────────────────────────────────

    def update(self, name: str, value: Any) -> bool:
        """
        Update the value of an existing symbol (searches scope chain).
        Returns True if found and updated, False otherwise.
        """
        sym = self.lookup(name)
        if sym:
            sym.value = value
            return True
        return False

    # ── Debugging ─────────────────────────────────────────────────────────

    def dump(self) -> str:
        """Dump the entire symbol table hierarchy."""
        return self._dump_scope(self._global, indent=0)

    def _dump_scope(self, scope: Scope, indent: int = 0) -> str:
        """Recursively dump a scope and its children."""
        lines = []
        prefix = "  " * indent
        
        # Print scope header
        lines.append(f"{prefix}[Scope: {scope.name}]")
        
        # Print symbols in this scope
        for sym in scope.symbols():
            value_repr = repr(sym.value)
            if len(value_repr) > 80:
                value_repr = value_repr[:77] + "..."
            lines.append(f"{prefix}  {sym.name}: {sym.kind.name} = {value_repr}")
        
        # Recursively print child scopes
        for child in scope.children:
            lines.append(self._dump_scope(child, indent + 1))
        
        return "\n".join(lines)

    def __repr__(self):
        return f"SymbolTable(depth={self.scope_depth()}, current={self.current_scope.name!r})"