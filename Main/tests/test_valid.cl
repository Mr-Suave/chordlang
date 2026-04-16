# Valid ChordLang Program - Should Pass All Checks
tempo = 120
volume = 80

sequence intro {
  C4:500, D4:500, E4:500, rest:250, G4:1000
}

sequence verse {
  C4:250, D4:250, E4:250, F4:250,
  G4:500, rest:500
}

chord c_major { C4:1000, E4:1000, G4:1000 }
chord g_major { G3:1000, B3:1000, D4:1000 }

play intro
play rest:500

repeat 2 times {
  play verse
  play c_major
  play rest:250
}

intensity = 75

if intensity > 50 then {
  play g_major
} else {
  play intro
}