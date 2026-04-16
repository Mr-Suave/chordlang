# Invalid ChordLang Program - Should Catch Multiple Errors

# Error 1: Undefined variable
play undefined_sequence

# Error 2: Invalid octave
sequence bad_octave {
  C15:500
}

# Error 3: Invalid pitch
sequence bad_pitch {
  H4:500, Z3:250
}

# Error 4: Negative duration
sequence negative_dur {
  C4:-500
}

# repeat 0 times : error must be thrown

repeat 0 times {
    play undefined_sequence

}

# Error 7: Assigning note to variable
x = C4:500

# Error 8: Using variable in chord
y = 100
chord bad_chord { C4:500, y }

# Warning 1: Empty sequence
sequence empty { }

# Warning 2: Very high tempo
tempo = 500

# Warning 3: Negative volume
volume = -10