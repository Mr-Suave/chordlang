# Arpeggio Test - Showcasing "Chords" (which play sequentially right now) and loops
tempo = 140
volume = 80

instrument = guitar

# Since our runtime plays chords sequentially, this will sound like a fast arpeggio
chord c_major { C4:150, E4:150, G4:150, C5:400 }
chord f_major { F3:150, A3:150, C4:150, F4:400 }
chord g_major { G3:150, B3:150, D4:150, G4:400 }

repeat 2 times {
  play c_major
  play rest:100
  play f_major
  play rest:100
  play g_major
  play rest:100
  play c_major
  play rest:300
}

# Finish with a booming bass note
instrument = "bass"
volume = 120
play C3:1500
