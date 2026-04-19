# ChordLang Main Makefile
# Coordinates the full compilation pipeline from .cl to audio output.

PYTHON = python3
COMPILER = test_compiler.py
RUNTIME_DIR = Assembly
RUNTIME_OBJ = $(RUNTIME_DIR)/audio_runtime.o
OUTPUTS_DIR = ../outputs

# Find all test files
TEST_CL = $(wildcard tests/*.cl)
TEST_ASM = $(TEST_CL:.cl=.asm)
TEST_EXEC = $(TEST_CL:.cl=)

.PHONY: all runtime clean compile run help

all: runtime compile

# Build the audio runtime library
runtime:
	@$(MAKE) -C $(RUNTIME_DIR) library

# Compile .cl files to .asm
compile: runtime
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(COMPILER) $(FILE); \
	else \
		$(PYTHON) $(COMPILER); \
	fi

# Compile and run to generate audio
run: runtime
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(COMPILER) $(FILE) --run; \
	else \
		@echo "Please specify a file: make run FILE=tests/test.cl"; \
	fi

# Clean build artifacts
clean:
	rm -f tests/*.o tests/*.asm $(TEST_EXEC)
	$(MAKE) -C $(RUNTIME_DIR) clean
	@echo "✓ Clean complete"

# Help message
help:
	@echo "ChordLang Compiler Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make all                - Build runtime and compile default tests"
	@echo "  make runtime            - Build only the assembly runtime library"
	@echo "  make compile FILE=path  - Compile a specific .cl file to .asm"
	@echo "  make run FILE=path      - Compile, link, and generate audio for a file"
	@echo "  make clean              - Remove temporary build files"
	@echo ""
	@echo "Example:"
	@echo "  make run FILE=tests/test_valid.cl"
