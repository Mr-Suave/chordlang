# ChordLang Main Makefile
# Assembles generated .asm files and links them with the audio runtime.

RUNTIME_DIR = Assembly
RUNTIME_OBJ = $(RUNTIME_DIR)/audio_runtime.o

# Find all test .asm files in tests/
TEST_ASM = $(wildcard tests/*.asm)
TEST_EXEC = $(TEST_ASM:.asm=)

all: runtime $(TEST_EXEC)

runtime:
	$(MAKE) -C $(RUNTIME_DIR) library

# Rule to compile any .asm file into an executable
%: %.asm runtime
	nasm -f elf64 $< -o $@.o
	ld $@.o $(RUNTIME_OBJ) -o $@
	@echo "Built $@"

clean:
	rm -f tests/*.o tests/*.asm $(TEST_EXEC)
	$(MAKE) -C $(RUNTIME_DIR) clean

.PHONY: all runtime clean
