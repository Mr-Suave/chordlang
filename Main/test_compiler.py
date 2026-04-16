"""
Enhanced ChordLang Compiler Test Script
Now includes semantic analysis and IR generation phases.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from parser import parse
from visitors import ASTPrinter, SymbolTableBuilder
from semantic_analyzer import SemanticAnalyzer
from ir_generator import IRGenerator


def test_file(filepath):
    """Test a ChordLang file through all compilation phases."""
    print(f"=== Testing {filepath} ===")
    
    try:
        # ═══════════════════════════════════════════════════════════════════
        # Phase 1: Read Source
        # ═══════════════════════════════════════════════════════════════════
        with open(filepath, 'r') as f:
            source = f.read()
        
        print("--- Source Code ---")
        print(source.strip())
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 2: Parse (Lexer + Parser)
        # ═══════════════════════════════════════════════════════════════════
        ast_root = parse(source)
        
        if not ast_root:
            print("❌ Parsing failed (returned None).")
            return
        
        print("\n--- Abstract Syntax Tree (AST) ---")
        printer = ASTPrinter()
        print(printer.print(ast_root))
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 3: Symbol Table Building
        # ═══════════════════════════════════════════════════════════════════
        print("\n--- Symbol Table ---")
        builder = SymbolTableBuilder()
        sym_table = builder.build(ast_root)
        print(sym_table.dump())
        
        if builder.errors:
            print("\n--- Symbol Table Errors ---")
            for err in builder.errors:
                print(err)
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 4: Semantic Analysis
        # ═══════════════════════════════════════════════════════════════════
        print("\n--- Semantic Analysis ---")
        analyzer = SemanticAnalyzer(sym_table)
        passed = analyzer.analyze(ast_root)
        
        print(analyzer.report())
        
        if not passed:
            print("\n❌ Semantic analysis failed - skipping IR generation")
        else:
            print("\n✅ Semantic analysis passed!")
            
            # ═══════════════════════════════════════════════════════════════
            # Phase 5: IR Generation
            # ═══════════════════════════════════════════════════════════════
            print("\n--- Intermediate Representation (IR) ---")
            ir_gen = IRGenerator(sym_table)
            ir_program = ir_gen.generate(ast_root)
            
            print(ir_program)
            
            # Optional: Apply optimizations
            print("\n--- Optimized IR ---")
            ir_program.optimize()
            print(ir_program)

            # ═══════════════════════════════════════════════════════════════
            # Phase 6: Assembly Generation
            # ═══════════════════════════════════════════════════════════════
            print("\n--- Assembly Generation ---")
            from asm_generator import AsmGenerator
            asm_gen = AsmGenerator()
            asm_code = asm_gen.generate(ir_program)
            
            out_asm = filepath.replace('.cl', '.asm')
            with open(out_asm, 'w') as f:
                f.write(asm_code)
            print(f"✅ Generated assembly to {out_asm}")

        
        # ═══════════════════════════════════════════════════════════════════
        # Summary
        # ═══════════════════════════════════════════════════════════════════
        print("\n--- Compilation Summary ---")
        print(f"  Parse:    {'✅ Success' if ast_root else '❌ Failed'}")
        print(f"  Symbols:  {'✅ Built' if not builder.errors else '⚠️  With errors'}")
        print(f"  Semantic: {'✅ Passed' if passed else '❌ Failed'}")
        print(f"  IR Gen:   {'✅ Generated' if passed else '⏭️  Skipped'}")
        print(f"  Errors:   {len(builder.errors) + len(analyzer.errors)}")
        print(f"  Warnings: {len(analyzer.warnings)}")
        
    except Exception as e:
        print(f"\n❌ Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific files from command line
        for arg in sys.argv[1:]:
            test_file(arg)
            print("\n" + "="*70 + "\n")
    else:
        # Test default files
        test_dir = os.path.join(os.path.dirname(__file__), "tests")
        
        test_files = [
            "test1.cl",
            "test2.cl",
            "test_valid.cl",
            "test_invalid.cl",
        ]
        
        for filename in test_files:
            filepath = os.path.join(test_dir, filename)
            if os.path.exists(filepath):
                test_file(filepath)
                print("\n" + "="*70 + "\n")
            else:
                print(f"⚠️  File not found: {filepath}\n")