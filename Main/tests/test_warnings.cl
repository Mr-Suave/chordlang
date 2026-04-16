# Test Warning Generation (should compile but show warnings)

# Warning: Very slow tempo
tempo = 10

# Warning: Very fast tempo  
fast_tempo = 400

# Warning: Volume over MIDI max
volume = 200

# Warning: Empty sequence
sequence nothing { }

# Warning: Single-note chord
chord single { C4:1000 }

# Warning: Very long duration
sequence super_long {
  C4:50000
}

# Warning: Very high repeat count
repeat 10000 times {
  play rest:1
}

# Warning: Very long rest
play rest:100000