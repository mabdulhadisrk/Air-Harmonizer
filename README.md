# AeroHarmonix
AeroHarmonix is a functional musical instrument that turns a basic laptop webcam into a real-time synthesizer. The application eliminates the need for expensive MIDI controllers or physical hardware sensors, relying entirely on pure math and computer vision to translate hand gestures into live audio.

### What It Does 

Place your hands in front of the camera. Your left hand acts as a capo — each extended finger shifts the pitch up by one semitone. Your right hand selects chords from preset families based on how many fingers you show. The sound is generated mathematically in real-time using additive synthesis.

### Controls

- Left hand (red tracking dots): Capo — number of extended fingers = number of semitones
- Right hand (blue tracking dots): Chord selector — 1 finger plays first chord, 2 fingers plays second, etc.
- On-screen buttons: Switch between three chord families
- Q key: Exit

### Chord Families

| Family | 1 Finger | 2 Fingers | 3 Fingers | 4 Fingers | 5 Fingers ( thumb ) |  
|--------|----------|-----------|-----------|-----------|----------------------|
|    1   |   Am     |    Gmaj   |    Fmaj   |     Emaj  |                      |
|    2   |  Gmaj    |    Emin   |     Cmaj  |     Dmaj  |                      |
|    3   |  Emin    |    Dmaj   |     Cmaj  |     Bmin  |          Am          |

- Family 3 includes a thumb-only gesture that overrides to Am.

## How It Works

**Hand Tracking** — Uses MediaPipe to detect hand landmarks. The screen is split vertically at the midpoint to assign / differentiate left and right hands based on position rather than MediaPipe's labels, which were inconsistent under varying light.

**Finger Detection** — Compares each fingertip's Y-position to its PIP joint. A small threshold filters out partially curled fingers ( which played random notes ) so only clearly extended fingers register.

**Audio Engine** — Each chord note is built from sine waves with added harmonics (2nd and 3rd) to give the sound more body than a pure tone. The three notes are mixed, shaped with a fast attack ( instant detection of fingers ) and gradual decay, and sent to pygame's mixer through NumPy arrays for minimal latency.

## Development Approach

This project was built using AI-assisted development (Gemini and DeepSeek) as a prototyping accelerator across roughly 13 iterations. Rather than writing every line from scratch, I focused on:

- Defining the architecture and feature set
- Testing each iteration and identifying bugs
- Making design decisions: splitting the screen to fix the handedness bug, tuning the harmonic mix so chords sounded warm rather than harsh, and adjusting how quickly notes start and fade so the instrument felt responsive
- Debugging hardware-specific issues (Mac Continuity Camera, MediaPipe handedness glitches)
- Iterating on sound quality until the tone felt right

The AI handled syntax and boilerplate so I could focus on the actual engineering — what features to build, how they should work, and why certain approaches were better than others.

## Bugs I Had To Figure Out And Solve

- Handedness flipping: MediaPipe would randomly swap left/right labels. Solved by ignoring labels and dividing the screen by absolute position.
- Audio lag on chord change: Generating new chord sounds in real-time was blocking the camera feed and causing stutter. Fixed by adding a sound cache — once a chord is generated, it's stored and reused instantly instead of being rebuilt every time.
- Capo offset bug: 3 fingers were producing +4 semitones due to a mapping error. Corrected to direct 1:1 finger-to-semitone mapping.
- External camera priority: macOS kept defaulting to my iPhone Continuity Camera. Added a resolution check to identify and skip external devices.
- Sound quality: Pure sine waves sounded thin and cheap. Added harmonic overtones and tuned the envelope to sound closer to a harmonium.

## Setup

### Requirements
- Python 3.8 or newer
- A working webcam (built-in or external)
- macOS or Windows (tested on both)

### Installation

Clone the repo:
git clone https://github.com/mabdulhadisrk/AeroHarmonix.git
cd AeroHarmonix

### Install dependencies

pip install opencv-python mediapipe pygame numpy

### Run

python main.py

### Start-up Default

A voice prompt will play after 2 seconds. Show your hands to the webcam and start playing.

Press **Q** to quit.

### Mac Users

If your Mac tries to use an iPhone Continuity Camera instead of the built-in webcam, the script will automatically detect and skip it. Just make sure your laptop camera isn't blocked.

### Troubleshooting

- No camera feed: Check if another app is using your webcam (Zoom, FaceTime, etc.). Close it and restart.
- Audio sounds distorted: Try closing background apps to free up CPU. The audio synthesis runs in real-time and needs some processing power.
- Hands not detected: Make sure you're in a well-lit room. MediaPipe needs decent lighting to track hand landmarks.
