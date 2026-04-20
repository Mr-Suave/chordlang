tempo = 120
volume = 80

# Correct syntax (no quotes)
instrument = guitar

sequence my_seq {
C4:500, G4:500, B4:500, rest:500
}

sequence my_alt_seq {
A4:500, F4:500, B4:500, rest:500
}

counter = 0
repeat 10 times {

# If 'var' is defined here, it goes into 'repeat_14' scope.
# The 'if' statement then enters 'if_then_19' scope.
# The lookup for 'var' should work because it checks parent scopes.
var = counter % 2

if var == 0 then {
play my_seq
}
else {
    play my_alt_seq
}
counter = counter + 1
}
