# Demo 4: Optimization Scope
# Demonstrates Constant Folding and IR optimizations

tempo = 100 + 20          # Should be folded to 120
volume = 150 - 50         # Should be folded to 100

# Multiple operations to fold
x = 10 + 20
y = x + 5                 # x is known as 30, so y becomes 35 (if constant propagation is supported)
                          # At minimum, '10 + 20' will be folded.

# Modulo folding
z = 10 % 3                # Should be folded to 1

# Dead code after if/else blocks or loops can be checked in IR
if 1 > 0 then {
    play C4
} else {
    play D4               # The logic for jumps here often creates optimization opportunities
}

repeat 5 + 5 times {      # Folded to 10 times
    play E4
}
