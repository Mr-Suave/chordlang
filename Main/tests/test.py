import ply.lex as lex
from lexer import lexer  # Import your lexer

# Read the ChordLang file
with open('test.cl', 'r') as f:
    data = f.read()

print("Input ChordLang code:")
print("-" * 50)
print(data)
print("-" * 50)
print("\nTokens:")
print("-" * 50)

# Give input to lexer
lexer.input(data)

# Print all tokens
for tok in lexer:
    print(f"{tok.type:15s} | {tok.value}")
