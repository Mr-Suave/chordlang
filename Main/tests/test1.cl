intensity = 85
duration_mod = intensity % 30

if intensity > 80 then {
  if duration_mod > 15 then {
    play C5:2000
    rest:1000
  } else {
    play G4:1500
  }
} else {
  play C4:1000
  rest:500
  play E4:1000
}
