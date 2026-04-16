"""
Test Suite for Semantic Analysis
Tests both valid and invalid ChordLang programs.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from parser import parse
from visitors import SymbolTableBuilder
from semantic_analyzer import SemanticAnalyzer


def test_semantic(source_code: str, test_name: str, should_pass: bool = True):
    """
    Test semantic analysis on a code snippet.
    
    Args:
        source_code: ChordLang source code
        test_name: Name of the test
        should_pass: True if code should pass semantic analysis
    """
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"Expected: {'PASS' if should_pass else 'FAIL'}")
    print('='*70)
    print("Code:")
    print(source_code)
    print('-'*70)
    
    try:
        # Parse
        ast = parse(source_code)
        if not ast:
            print("❌ Parse failed")
            return
        
        # Build symbol table
        builder = SymbolTableBuilder()
        sym_table = builder.build(ast)
        
        # Run semantic analysis
        analyzer = SemanticAnalyzer(sym_table)
        passed = analyzer.analyze(ast)
        
        # Print report
        print(analyzer.report())
        
        # Check result
        if passed and should_pass:
            print("\n✅ TEST PASSED (no errors, as expected)")
        elif not passed and not should_pass:
            print("\n✅ TEST PASSED (caught errors, as expected)")
        elif passed and not should_pass:
            print("\n❌ TEST FAILED (should have caught errors, but didn't)")
        else:
            print("\n❌ TEST FAILED (unexpected errors)")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# Valid Programs (should pass)
# ═══════════════════════════════════════════════════════════════════════════

VALID_1 = """
tempo = 120
volume = 80

sequence melody {
  C4:500, D4:500, E4:500
}

play melody
"""

VALID_2 = """
tempo = 100

chord c_major { C4:1000, E4:1000, G4:1000 }
chord g_major { G3:1000, B3:1000, D4:1000 }

if tempo > 90 then {
  play c_major
} else {
  play g_major
}
"""

VALID_3 = """
repeat_count = 3

sequence verse {
  C4:250, rest:250, E4:500
}

repeat repeat_count times {
  play verse
  play rest:1000
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# Invalid Programs (should fail)
# ═══════════════════════════════════════════════════════════════════════════

INVALID_1_UNDEFINED_VAR = """
# Error: Using undefined variable
play melody
"""

INVALID_2_PLAY_VARIABLE = """
# Error: Trying to play a numeric variable
tempo = 120
play tempo
"""

INVALID_3_INVALID_OCTAVE = """
# Error: Octave out of range
sequence test {
  C12:500
}
"""

INVALID_4_INVALID_PITCH = """
# Error: Invalid pitch
sequence test {
  H4:500
}
"""

INVALID_5_NEGATIVE_DURATION = """
# Error: Negative duration
sequence test {
  C4:-500
}
"""

INVALID_6_ZERO_REPEAT = """
# Error: Zero or negative repeat count
repeat 0 times {
  play C4:500
}
"""

INVALID_7_ASSIGN_NOTE = """
# Error: Assigning note to variable
x = C4:500
"""

INVALID_8_NEGATIVE_TEMPO = """
# Warning: Invalid tempo
tempo = -50
"""

INVALID_9_VOLUME_OUT_OF_RANGE = """
# Warning: Volume out of range
volume = 200
"""

INVALID_10_UNDEFINED_IN_SEQUENCE = """
# Error: Using undefined symbol in sequence
sequence melody {
  C4:500, undefined_note, E4:500
}
"""

INVALID_11_VARIABLE_IN_CHORD = """
# Error: Using variable in chord
tempo = 120
chord bad { C4:500, tempo }
"""

INVALID_12_EMPTY_SEQUENCE = """
# Warning: Empty sequence
sequence empty { }
"""

INVALID_13_SINGLE_NOTE_CHORD = """
# Warning: Chord with only one note
chord single { C4:1000 }
"""

INVALID_14_VERY_LONG_DURATION = """
# Warning: Extremely long duration
sequence long {
  C4:99999
}
"""

INVALID_15_VERY_HIGH_REPEAT = """
# Warning: Very high repeat count
repeat 5000 times {
  play C4:100
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# Run All Tests
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "CHORDLANG SEMANTIC ANALYSIS TEST SUITE")
    print("="*70)
    
    # Valid tests
    test_semantic(VALID_1, "Valid: Basic sequence and play", should_pass=True)
    test_semantic(VALID_2, "Valid: Chords with conditionals", should_pass=True)
    test_semantic(VALID_3, "Valid: Repeat with rest", should_pass=True)
    
    # Invalid tests
    test_semantic(INVALID_1_UNDEFINED_VAR, "Invalid: Undefined variable", should_pass=False)
    test_semantic(INVALID_2_PLAY_VARIABLE, "Invalid: Playing a variable", should_pass=False)
    test_semantic(INVALID_3_INVALID_OCTAVE, "Invalid: Octave out of range", should_pass=False)
    test_semantic(INVALID_4_INVALID_PITCH, "Invalid: Invalid pitch", should_pass=False)
    test_semantic(INVALID_5_NEGATIVE_DURATION, "Invalid: Negative duration", should_pass=False)
    test_semantic(INVALID_6_ZERO_REPEAT, "Invalid: Zero repeat count", should_pass=False)
    test_semantic(INVALID_7_ASSIGN_NOTE, "Invalid: Assigning note to variable", should_pass=False)
    test_semantic(INVALID_8_NEGATIVE_TEMPO, "Invalid: Negative tempo", should_pass=False)
    test_semantic(INVALID_9_VOLUME_OUT_OF_RANGE, "Invalid: Volume out of range", should_pass=False)
    test_semantic(INVALID_10_UNDEFINED_IN_SEQUENCE, "Invalid: Undefined in sequence", should_pass=False)
    test_semantic(INVALID_11_VARIABLE_IN_CHORD, "Invalid: Variable in chord", should_pass=False)
    test_semantic(INVALID_12_EMPTY_SEQUENCE, "Warning: Empty sequence", should_pass=True)  # Warning, not error
    test_semantic(INVALID_13_SINGLE_NOTE_CHORD, "Warning: Single note chord", should_pass=True)  # Warning
    test_semantic(INVALID_14_VERY_LONG_DURATION, "Warning: Very long duration", should_pass=True)  # Warning
    test_semantic(INVALID_15_VERY_HIGH_REPEAT, "Warning: Very high repeat count", should_pass=True)  # Warning
    
    print("\n" + "="*70)
    print(" " * 20 + "TEST SUITE COMPLETE")
    print("="*70 + "\n")