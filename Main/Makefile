# ChordLang Main Makefile
# Coordinates the full compilation pipeline from .cl to audio output.

PYTHON = python3
COMPILER = test_compiler.py
RUNTIME_DIR = Assembly
RUNTIME_OBJ = $(RUNTIME_DIR)/audio_runtime.o
OUTPUTS_DIR = ../outputs

.PHONY: all runtime clean run help

# Now 'all' will run the full pipeline if a FILE is provided
all: runtime
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(COMPILER) $(FILE) --run; \
	else \
		$(PYTHON) $(COMPILER); \
	fi

# Build the audio runtime library
runtime:
	@$(MAKE) -C $(RUNTIME_DIR) library

# Explicit target for just running
run: runtime
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(COMPILER) $(FILE) --run; \
	else \
		@echo "Please specify a file: make run FILE=tests/test.cl"; \
	fi

# Clean build artifacts
clean:
	rm -f tests/*.o tests/*.asm tests/test1 tests/test2 tests/test tests/test_instrument tests/test_invalid tests/test_ir_loop tests/test_ir_simple tests/test_valid tests/test_warnings
	$(MAKE) -C $(RUNTIME_DIR) clean
	@echo "✓ Clean complete"

# Help message
help:
	@echo "ChordLang Compiler Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make FILE=path          - Compile, link, and generate audio for a file"
	@echo "  make run FILE=path      - Same as above (explicit run)"
	@echo "  make all                - Compile all default test files (no audio)"
	@echo "  make runtime            - Build only the assembly runtime library"
	@echo "  make clean              - Remove temporary build files"
	@echo ""
	@echo "Example:"
	@echo "  make FILE=tests/test_valid.cl"
