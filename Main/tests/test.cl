tempo = 100
intensity = 75
volume = 10
kalidas = 100


blah blah
;;


chord soft_chord { C4:1000, E4:1000, G4:1000 }
chord loud_chord { C3:1000, E3:1000, G3:1000 }
sequence melody {C#4:1000, Eb3:1000, Gb3:1000}

if intensity > 50 then {
  play loud_chord
} else {
  play soft_chord
}
