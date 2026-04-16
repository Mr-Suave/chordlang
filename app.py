#!/usr/bin/env python3
"""
ChordLang Web IDE - Flask Server
Provides a web interface for the ChordLang compiler
"""

from flask import Flask, render_template, request, jsonify, send_file
import sys
import os
import io
import subprocess
from contextlib import redirect_stdout, redirect_stderr

# Add Main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Main'))

from parser import parse
from visitors import ASTPrinter, SymbolTableBuilder
from semantic_analyzer import SemanticAnalyzer
from ir_generator import IRGenerator
from asm_generator import AsmGenerator

app = Flask(__name__)

# Store compilation outputs
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    """Serve the main IDE page"""
    return render_template('index.html')

@app.route('/api/compile', methods=['POST'])
def compile_code():
    """Compile ChordLang code through all phases"""
    try:
        data = request.json
        source_code = data.get('code', '')
        
        if not source_code.strip():
            return jsonify({
                'success': False,
                'error': 'No source code provided'
            })
        
        result = {
            'success': True,
            'phases': {}
        }
        
        # Phase 1: Parsing
        try:
            ast_root = parse(source_code)
            if not ast_root:
                return jsonify({
                    'success': False,
                    'error': 'Parsing failed - invalid syntax',
                    'phase': 'parsing'
                })
            
            # Get AST representation
            printer = ASTPrinter()
            ast_output = io.StringIO()
            with redirect_stdout(ast_output):
                print(printer.print(ast_root))
            
            result['phases']['ast'] = {
                'success': True,
                'output': ast_output.getvalue()
            }
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Parsing error: {str(e)}',
                'phase': 'parsing'
            })
        
        # Phase 2: Symbol Table
        try:
            builder = SymbolTableBuilder()
            sym_table = builder.build(ast_root)
            
            symbol_output = io.StringIO()
            with redirect_stdout(symbol_output):
                print(sym_table.dump())
            
            result['phases']['symbols'] = {
                'success': len(builder.errors) == 0,
                'output': symbol_output.getvalue(),
                'errors': builder.errors
            }
            
            if builder.errors:
                result['success'] = False
                return jsonify(result)
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Symbol table error: {str(e)}',
                'phase': 'symbols'
            })
        
        # Phase 3: Semantic Analysis
        try:
            analyzer = SemanticAnalyzer(sym_table)
            passed = analyzer.analyze(ast_root)
            
            result['phases']['semantic'] = {
                'success': passed,
                'output': analyzer.report(),
                'errors': analyzer.errors,
                'warnings': analyzer.warnings
            }
            
            if not passed:
                result['success'] = False
                return jsonify(result)
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Semantic analysis error: {str(e)}',
                'phase': 'semantic'
            })
        
        # Phase 4: IR Generation
        try:
            ir_gen = IRGenerator(sym_table)
            ir_program = ir_gen.generate(ast_root)
            
            # Get IR before optimization
            ir_before = str(ir_program)
            
            # Optimize
            ir_program.optimize()
            ir_after = str(ir_program)
            
            result['phases']['ir'] = {
                'success': True,
                'before_optimization': ir_before,
                'after_optimization': ir_after
            }
            
            # Phase 5: Assembly Generation
            try:
                asm_gen = AsmGenerator()
                asm_code = asm_gen.generate(ir_program)
                
                result['phases']['assembly'] = {
                    'success': True,
                    'output': asm_code
                }
                
                # Save assembly file
                asm_path = os.path.join(OUTPUT_DIR, 'output.asm')
                with open(asm_path, 'w') as f:
                    f.write(asm_code)
                
                result['asm_file'] = 'output.asm'
                
            except Exception as e:
                result['phases']['assembly'] = {
                    'success': False,
                    'error': str(e)
                }
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'IR generation error: {str(e)}',
                'phase': 'ir'
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })

@app.route('/api/assemble', methods=['POST'])
def assemble_and_link():
    """Assemble the generated assembly code and link to create executable"""
    try:
        asm_path = os.path.join(OUTPUT_DIR, 'output.asm')
        obj_path = os.path.join(OUTPUT_DIR, 'output.o')
        exe_path = os.path.join(OUTPUT_DIR, 'output')
        runtime_obj = os.path.join(os.path.dirname(__file__), 'Main', 'Assembly', 'audio_runtime.o')
        
        if not os.path.exists(asm_path):
            return jsonify({
                'success': False,
                'error': 'No assembly file found. Compile first.'
            })
        
        # Assemble
        result = subprocess.run(
            ['nasm', '-f', 'elf64', asm_path, '-o', obj_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Assembly failed: {result.stderr}'
            })
        
        # Link
        result = subprocess.run(
            ['ld', obj_path, runtime_obj, '-o', exe_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Linking failed: {result.stderr}'
            })
        
        # Execute to generate WAV
        result = subprocess.run(
            [exe_path],
            capture_output=True,
            text=True,
            cwd=OUTPUT_DIR
        )
        
        wav_path = os.path.join(OUTPUT_DIR, 'output.wav')
        if os.path.exists(wav_path):
            return jsonify({
                'success': True,
                'message': 'Audio generated successfully',
                'wav_file': 'output.wav'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Executable ran but no WAV file generated'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Build error: {str(e)}'
        })

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download generated files"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/examples')
def get_examples():
    """Get example ChordLang programs"""
    examples = {
        'hello_world': {
            'name': 'Hello World',
            'code': '''# Simple Hello World in ChordLang
tempo = 120
volume = 100

play C4:500
play E4:500
play G4:500
play C5:1000
'''
        },
        'arpeggio': {
            'name': 'Arpeggio Pattern',
            'code': '''# Arpeggio Test - Chord progression
tempo = 140
volume = 80

instrument = guitar

chord c_major { C4:150, E4:150, G4:150, C5:400 }
chord f_major { F3:150, A3:150, C4:150, F4:400 }
chord g_major { G3:150, B3:150, D4:150, G4:400 }

repeat 2 times {
  play c_major
  play rest:100
  play f_major
  play rest:100
  play g_major
  play rest:100
  play c_major
  play rest:300
}

instrument = "bass"
volume = 120
play C3:1500
'''
        },
        'melody': {
            'name': 'Simple Melody',
            'code': '''# Simple melody with dynamics
tempo = 100
volume = 90

sequence happy_birthday {
  C4:400, C4:200, D4:600,
  C4:600, F4:600, E4:1200,
  C4:400, C4:200, D4:600,
  C4:600, G4:600, F4:1200
}

play happy_birthday
'''
        },
        'loops': {
            'name': 'Loops & Conditionals',
            'code': '''# Demonstrating control flow
tempo = 120
volume = 80

counter = 0

repeat 4 times {
  counter = counter + 1
  
  if counter == 2 then {
    volume = 60
    play E4:500
  } else {
    volume = 100
    play C4:500
  }
  
  play rest:200
}
'''
        }
    }
    return jsonify(examples)

if __name__ == '__main__':
    print("="*70)
    print("ChordLang Web IDE Starting...")
    print("="*70)
    print("\nAccess the IDE at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)
