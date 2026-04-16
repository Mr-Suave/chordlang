from lexer import lexer

def test_lexer(input_string, description=""):
    """Test the lexer with given input and print results."""
    if description:
        print(f"\n{'='*70}")
        print(f"TEST: {description}")
        print(f"{'='*70}")
    
    print(f"Input:\n{input_string}\n")
    
    lexer.input(input_string)
    
    print(f"{'TOKEN TYPE':<20} {'VALUE':<25} {'LINE':<10}")
    print("-" * 70)
    
    token_count = 0
    for tok in lexer:
        print(f"{tok.type:<20} {str(tok.value):<25} {tok.lineno:<10}")
        token_count += 1
    
    print(f"\nTotal tokens: {token_count}\n")
    return token_count

# Run basic tests
if __name__ == '__main__':
    
    # Test 1: Keywords
    test_lexer(
        "tempo volume sequence chord play repeat times if then else rest",
        "All Keywords"
    )
    
    # Test 2: Operators
    test_lexer(
        "= > < >= <= == != + - %",
        "All Operators"
    )
    
    # Test 3: Note Literals
    test_lexer(
        "C4 C4:500 F#5:250 Gb3:1000 A0 G9:100",
        "Note Literals"
    )
    
    # Test 4: Identifiers
    test_lexer(
        "bass_line melody soft_chord myVar _private var123",
        "Identifiers"
    )
    
    # Test 5: Integers
    test_lexer(
        "0 1 120 500 999999",
        "Integer Literals"
    )
    
    # Test 6: Delimiters
    test_lexer(
        "{ } , :",
        "Delimiters"
    )
