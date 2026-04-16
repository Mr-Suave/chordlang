# Loop with modulo for variation
repeat_count = 3
counter = 0
chord c_major { C4:250 }
sequence verse {
  C4:250, D4:250, E4:250, rest:500, 
  G4:500, rest:250, E4:250, rest:250
}

repeat repeat_count times {
  sequence melody {
  C4:250, D4:250, E4:250, rest:500
}
  play verse
  play rest:500
  
  # Play chord every other time
  variation = counter % 2
  if variation == 0 then {
    play c_major
  } else {
    play g_major
  }
  
  counter = counter + 1
}
