# AeroHarmonix
Its a gesture-controlled synthesizer that plays chords based on hand movements tracked through a webcam. Built using AI-assisted development as a rapid prototyping tool.
# What It Does 
Place your hands in front of the camera. Your left hand acts as a capo — each extended finger shifts the pitch up by one semitone. Your right hand selects chords from preset families based on how many fingers you show. The sound is generated mathematically in real-time using additive synthesis.
### Controls
- **Left hand (red tracking dots)**: Capo — number of extended fingers = number of semitones
- **Right hand (blue tracking dots)**: Chord selector — 1 finger plays first chord, 2 fingers plays second, etc.
- **On-screen buttons**: Switch between three chord families
- **Q key**: Exit
- 
### Chord Families

| Family | 1 Finger | 2 Fingers | 3 Fingers | 4 Fingers | 5 Fingers ( thumb ) |  
|--------|----------|-----------|-----------|-----------|----------------------|
|    1   |   Am     |    Gmaj   |    Fmaj   |     Emaj  |                      |
|    2   |  Gmaj    |    Emin   |     Cmaj  |     Dmaj  |                      |
|    3   |  Emin    |    Dmaj   |     Cmaj  |     Bmin  |          Am          |

- Family 3 includes a thumb-only gesture that overrides to Am.
