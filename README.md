# ChordLang

ChordLang is a domain-specific language (DSL) designed for music generation and audio synthesis. It allows users to write high-level musical constructs—like melodies, chords, and instrument changes—and compiles them into low-level assembly code. The resulting assembly is linked with a custom audio runtime to produce high-quality WAV audio files.

## Project Structure

- `app.py`: Flask-based Web IDE for browser-based development.
- `Main/`: Core compiler implementation.
  - `lexer.py` & `parser.py`: PLY-based front-end.
  - `semantic_analyzer.py`: Type checking and symbol validation.
  - `ir_generator.py`: Intermediate Representation with optimization.
  - `asm_generator.py`: x86-64 assembly code generation.
  - `Assembly/`: Audio runtime library and assembly utilities.
- `tests/`: Collection of `.cl` example files.
- `outputs/`: Directory where generated `.asm`, `.o`, and `.wav` files are stored.

## Prerequisites

To compile and run ChordLang programs, you need:

1.  **Python 3.8+**
2.  **NASM**: The Netwide Assembler (for assembly generation).
3.  **GCC/binutils**: Specifically `ld` for linking the audio runtime.

### Installing NASM

- **macOS**: `brew install nasm`
- **Ubuntu/Debian**: `sudo apt-get install nasm build-essential`

## Installation

1.  **Clone the repository and navigate to the project root:**
    ```bash
    cd chordlang
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Web IDE (Recommended)

Launch the interactive web interface to write, compile, and listen to your musical creations in the browser.

```bash
python3 app.py
```
Then visit `http://localhost:5000` in your web browser.

### 2. Command Line Interface (CLI)

You can compile and run `.cl` files directly from the terminal using the provided Makefile.

**Compile and Generate Audio:**
```bash
cd Main
make FILE=tests/test_valid.cl
```

**Clean Build Artifacts:**
```bash
make clean
```

## Example ChordLang Code

```chordlang
# Simple Melody
tempo = 120
volume = 80
instrument = guitar

chord c_major { C4:500, E4:500, G4:500 }

play c_major
play C5:1000
play rest:500
```

## Compilation Pipeline

1.  **Lexical Analysis**: Tokens are extracted from source code.
2.  **Parsing**: An Abstract Syntax Tree (AST) is built.
3.  **Semantic Analysis**: Validates symbols, types, and musical logic.
4.  **IR Generation**: Translates AST to a simplified Intermediate Representation.
5.  **Optimization**: Performs dead code elimination and constant folding on the IR.
6.  **Code Generation**: Produces x86-64 assembly.
7.  **Assembly & Linking**: Assembles the code with NASM and links it with the `audio_runtime.o` to create an executable that generates a `.wav` file.
