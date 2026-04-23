# Demo 1: Basic Functionality
# Shows variables, sequences, chords, and loops

tempo = 120
volume = 100
instrument = piano

sequence scale { C4, D4, E4, F4, G4, A4, B4, C5 }
chord c_maj { C4, E4, G4 }

# Simple loop playing a scale
repeat 2 times {
    play scale
    play rest:250
    play c_maj
}

# Changing settings mid-program
instrument = guitar
volume = 80
play E3:1000
