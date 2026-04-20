# Demo 3: Intentional Semantic Errors
# These should be caught by the Semantic Analyzer (semantic_analyzer.py)

tempo = 120
instrument = non_existent_instrument # Error: Unknown instrument

# Error: Assigning a note to a variable (Variables only hold numeric values)
myVar = C4 

# Error: Playing an undefined symbol
play mystery_sequence

# Error: Playing a numeric variable
x = 50
play x

# Error: Out of range octave
play C9:500

# Error: Negative duration
play A4:-100
