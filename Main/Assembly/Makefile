# ChordLang Assembly Runtime Library - Makefile
# Week 7 Deliverable

NASM = nasm
LD = ld
NASMFLAGS = -f elf64
LDFLAGS =

# Object files
RUNTIME_OBJ = audio_runtime.o

# Test executables
TESTS = test_envelope test_sine_sample test_runtime_complete

.PHONY: all clean test library

# Default target: build everything
all: library $(TESTS)

# Build the runtime library object
library: $(RUNTIME_OBJ)

$(RUNTIME_OBJ): audio_runtime.asm
	@echo "Building runtime library..."
	$(NASM) $(NASMFLAGS) audio_runtime.asm -o $(RUNTIME_OBJ)
	@echo "✓ Runtime library built: $(RUNTIME_OBJ)"

# Test 1: Envelope function
test_envelope: test_envelope.o $(RUNTIME_OBJ)
	@echo "Linking test_envelope..."
	$(LD) $(LDFLAGS) test_envelope.o $(RUNTIME_OBJ) -o test_envelope
	@echo "✓ Built: test_envelope"

test_envelope.o: test_envelope.asm
	$(NASM) $(NASMFLAGS) test_envelope.asm -o test_envelope.o

# Test 2: Sine sample generation
test_sine_sample: test_sine_sample.o $(RUNTIME_OBJ)
	@echo "Linking test_sine_sample..."
	$(LD) $(LDFLAGS) test_sine_sample.o $(RUNTIME_OBJ) -o test_sine_sample
	@echo "✓ Built: test_sine_sample"

test_sine_sample.o: test_sine_sample.asm
	$(NASM) $(NASMFLAGS) test_sine_sample.asm -o test_sine_sample.o

# Test 3: Complete runtime test
test_runtime_complete: test_runtime_complete.o $(RUNTIME_OBJ)
	@echo "Linking test_runtime_complete..."
	$(LD) $(LDFLAGS) test_runtime_complete.o $(RUNTIME_OBJ) -o test_runtime_complete
	@echo "✓ Built: test_runtime_complete"

test_runtime_complete.o: test_runtime_complete.asm
	$(NASM) $(NASMFLAGS) test_runtime_complete.asm -o test_runtime_complete.o

# Run all tests
test: all
	@echo ""
	@echo "=========================================="
	@echo "Running Tests"
	@echo "=========================================="
	@echo ""
	@echo "Test 1: Envelope Function"
	@echo "------------------------------------------"
	./test_envelope
	@echo ""
	@echo "Test 2: Sine Sample Generation"
	@echo "------------------------------------------"
	./test_sine_sample
	@echo ""
	@echo "Test 3: Complete Runtime (generates test_output.wav)"
	@echo "------------------------------------------"
	./test_runtime_complete
	@echo ""
	@echo "=========================================="
	@echo "Validating output..."
	@echo "=========================================="
	@if [ -f test_output.wav ]; then \
		echo "✓ test_output.wav created"; \
		ls -lh test_output.wav; \
		file test_output.wav; \
	else \
		echo "✗ test_output.wav not found"; \
	fi
	@echo ""
	@echo "To play the output: aplay test_output.wav"
	@echo ""

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f *.o
	rm -f $(TESTS)
	rm -f test_output.wav
	@echo "✓ Clean complete"

# Help target
help:
	@echo "ChordLang Assembly Runtime Library - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make all       - Build runtime library and all tests"
	@echo "  make library   - Build only the runtime library"
	@echo "  make test      - Build and run all tests"
	@echo "  make clean     - Remove build artifacts"
	@echo ""
	@echo "Individual tests:"
	@echo "  make test_envelope          - Test envelope function"
	@echo "  make test_sine_sample       - Test sine generation"
	@echo "  make test_runtime_complete  - Complete integration test"
