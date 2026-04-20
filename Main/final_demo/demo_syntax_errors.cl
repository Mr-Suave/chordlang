# Demo 2: Intentional Syntax Errors
# These should be caught by the Parser (parser.py)

# Error 1: Missing assignment operator
tempo 120

# Error 2: Missing opening brace for sequence
sequence badSeq C4, E4, G4 }

# Error 3: Illegal character
volume = 80 @

# Error 4: Incomplete repeat statement
repeat 4 times {
    play C4
# Missing closing brace
