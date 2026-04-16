# Ode to Joy - A simple, recognizable melody
tempo = 120
volume = 100

instrument = piano

sequence ode_to_joy_part1 {
  E4:500, E4:500, F4:500, G4:500,
  G4:500, F4:500, E4:500, D4:500,
  C4:500, C4:500, D4:500, E4:500,
  E4:750, D4:250, D4:1000
}

sequence ode_to_joy_part2 {
  E4:500, E4:500, F4:500, G4:500,
  G4:500, F4:500, E4:500, D4:500,
  C4:500, C4:500, D4:500, E4:500,
  D4:750, C4:250, C4:1000
}

play ode_to_joy_part1
play rest:200
play ode_to_joy_part2
