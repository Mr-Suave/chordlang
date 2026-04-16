# Instrument Switcher & Logic Test
tempo = 100
volume = 90

sequence riff {
  A4:300, C5:300, D5:300, E5:600, rest:200
}

instrument = piano
play riff

instrument = sawtooth
play riff

instrument = square
play riff

# Logic test
play_ending = 1

if play_ending > 0 then {
  instrument = guitar
  play A4:1000
} else {
  play rest:1000
}