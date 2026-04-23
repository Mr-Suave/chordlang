# Demo 5: Final Music Generation
# An arpeggiated melody with a rhythmic bass line

tempo = 140
volume = 90

# Define a melody sequence
sequence melody {
    C4:250, E4:250, G4:250, C5:500,
    B3:250, D4:250, G4:250, B4:500,
    A3:250, C4:250, E4:250, A4:500,
    G3:250, B3:250, D4:250, G4:500
}

# Define a bass chord
chord c_bass { C2, C3 }
chord g_bass { G1, G2 }

instrument = piano
repeat 2 times {
    play melody
}

instrument = guitar
volume = 110
play C4:1000, E4:1000, G4:1000

instrument = drums_kick
play rest:0, rest:500, rest:0, rest:500

instrument = bass
volume = 120
play c_bass
play rest:250
play g_bass
