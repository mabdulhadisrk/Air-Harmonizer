import cv2
import mediapipe as mp
import pygame
import math
import numpy as np
import time
import os
import threading

# audio setup
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# voice greeting
def play_welcome_voice():
    time.sleep(2)
    os.system("say -v Samantha 'Welcome. This application is an interactive gesture controlled music player.'")

# pitch shifting
def shift_pitch(frequency, semitones):
    return frequency * (2.0 ** (semitones / 12.0))

# rich tone generator
def build_loop(hz1, hz2, hz3, length=3.0, rate=44100):
    total_samples = int(length * rate)
    data_list = []
    
    for step in range(total_samples):
        t = step / rate
        
        # note 1 with harmonics
        w1 = math.sin(2.0 * math.pi * hz1 * t)
        w1 += 0.5 * math.sin(2.0 * math.pi * hz1 * 2.0 * t)
        w1 += 0.25 * math.sin(2.0 * math.pi * hz1 * 3.0 * t)
        
        # note 2 with harmonics
        w2 = math.sin(2.0 * math.pi * hz2 * t)
        w2 += 0.5 * math.sin(2.0 * math.pi * hz2 * 2.0 * t)
        w2 += 0.25 * math.sin(2.0 * math.pi * hz2 * 3.0 * t)
        
        # note 3 with harmonics
        w3 = math.sin(2.0 * math.pi * hz3 * t)
        w3 += 0.5 * math.sin(2.0 * math.pi * hz3 * 2.0 * t)
        w3 += 0.25 * math.sin(2.0 * math.pi * hz3 * 3.0 * t)
        
        combined = (w1 + w2 + w3) / 3.5
        
        # instant attack
        attack_time = 0.01
        if t < attack_time:
            attack = t / attack_time
        else:
            attack = 1.0
        
        # hold then decay
        hold_time = 2.0
        if t < hold_time:
            sustain = 1.0
        else:
            decay_progress = (t - hold_time) / (length - hold_time)
            sustain = math.exp(-decay_progress * 2.0)
        
        # release
        release_time = 0.1
        if t > length - release_time:
            release = (length - t) / release_time
        else:
            release = 1.0
        
        env = attack * sustain * release
        data_list.append(int(combined * 26000 * env))
        
    return pygame.mixer.Sound(np.array(data_list, dtype=np.int16))

# frequencies
notes = {
    'E3': 164.81, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D3': 146.83, 'D4': 293.66, 'E4': 329.63,
    'F3': 174.61, 'Fsharp3': 185.00, 'Fsharp4': 369.99,
    'G4': 392.00, 'Gsharp3': 207.65, 'A4': 440.00
}

# chord families
families = {
    1: [
        (notes['A3'], notes['C4'], notes['E4']),
        (notes['G3'], notes['B3'], notes['D4']),
        (notes['F3'], notes['A3'], notes['C4']),
        (notes['E3'], notes['Gsharp3'], notes['B3'])
    ],
    2: [
        (notes['G3'], notes['B3'], notes['D4']),
        (notes['E3'], notes['G3'], notes['B3']),
        (notes['C4'], notes['E4'], notes['G4']),
        (notes['D3'], notes['Fsharp3'], notes['A3'])
    ],
    3: [
        (notes['E3'], notes['G3'], notes['B3']),
        (notes['D3'], notes['Fsharp3'], notes['A3']),
        (notes['C4'], notes['E4'], notes['G4']),
        (notes['B3'], notes['D4'], notes['Fsharp4'])
    ]
}

am_override = (notes['A3'], notes['C4'], notes['E4'])

# state
active_family = 1
left_capo_shift = 0
current_playing_chord = None
active_channel = None
debounce_counter = 0
DEBOUNCE_FRAMES = 5  # wait 5 frames before switching

TIP_GAP = 0.03

# mouse handler
def mouse_click_handler(event, x, y, flags, param):
    global active_family, current_playing_chord, active_channel, debounce_counter
    if event == cv2.EVENT_LBUTTONDOWN:
        if 480 <= x <= 630:
            if 10 <= y <= 40:
                active_family = 1
            elif 50 <= y <= 80:
                active_family = 2
            elif 90 <= y <= 120:
                active_family = 3
            if active_channel:
                active_channel.stop()
                active_channel = None
            current_playing_chord = None
            debounce_counter = 0

# camera
camera = cv2.VideoCapture(0)
time.sleep(1)

cv2.namedWindow("Air Guitar Pro")
cv2.setMouseCallback("Air Guitar Pro", mouse_click_handler)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)

voice_thread = threading.Thread(target=play_welcome_voice)
voice_thread.daemon = True
voice_thread.start()

while camera.isOpened():
    ret, frame = camera.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    rgb_view = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_view)
    
    # buttons
    c1 = (0, 255, 0) if active_family == 1 else (100, 100, 100)
    cv2.rectangle(frame, (480, 10), (630, 40), c1, -1)
    cv2.putText(frame, "1: Am-G-F-E", (485, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    c2 = (0, 255, 0) if active_family == 2 else (100, 100, 100)
    cv2.rectangle(frame, (480, 50), (630, 80), c2, -1)
    cv2.putText(frame, "2: G-Em-C-D", (485, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    c3 = (0, 255, 0) if active_family == 3 else (100, 100, 100)
    cv2.rectangle(frame, (480, 90), (630, 120), c3, -1)
    cv2.putText(frame, "3: Em-D-C-Bm (T=Am)", (485, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    left_hand_visible = False
    detected_left_semitones = 0
    current_right_fingers = 0
    right_hand_visible = False
    right_thumb_only_active = False
    
    if results.multi_hand_landmarks:
        for hand_pts in results.multi_hand_landmarks:
            pts = hand_pts.landmark
            
            hand_center_x = pts[0].x * w
            is_capo_hand = hand_center_x < (w / 2)
            
            dot_color = (0, 0, 255) if is_capo_hand else (255, 0, 0)
            
            tips = (8, 12, 16, 20)
            pips = (6, 10, 14, 18)
            f_count = 0
            
            for t_idx, p_idx in zip(tips, pips):
                tip_y = pts[t_idx].y
                pip_y = pts[p_idx].y
                
                if (pip_y - tip_y) > TIP_GAP:
                    f_count += 1
                    tx, ty = int(pts[t_idx].x * w), int(pts[t_idx].y * h)
                    cv2.circle(frame, (tx, ty), 10, dot_color, cv2.FILLED)
                else:
                    tx, ty = int(pts[t_idx].x * w), int(pts[t_idx].y * h)
                    cv2.circle(frame, (tx, ty), 5, (80, 80, 80), cv2.FILLED)
            
            # thumb
            thumb_tip = pts[4]
            thumb_ip = pts[3]
            hand_base = pts[0]
            
            thumb_dist = abs(thumb_tip.x - hand_base.x)
            ip_dist = abs(thumb_ip.x - hand_base.x)
            
            if thumb_dist > ip_dist and (thumb_dist - ip_dist) > 0.015:
                thumb_open = True
                bx, by = int(thumb_tip.x * w), int(thumb_tip.y * h)
                cv2.circle(frame, (bx, by), 10, dot_color, cv2.FILLED)
            else:
                thumb_open = False

            if is_capo_hand:
                left_hand_visible = True
                total_extended = f_count + (1 if thumb_open else 0)
                detected_left_semitones = total_extended
            else:
                right_hand_visible = True
                current_right_fingers = f_count
                if thumb_open and f_count == 0:
                    right_thumb_only_active = True

    if left_hand_visible:
        left_capo_shift = detected_left_semitones

    # target chord
    target_chord = None
    
    if right_hand_visible:
        if active_family == 3 and right_thumb_only_active:
            target_chord = am_override
        elif 1 <= current_right_fingers <= 4:
            target_chord = families[active_family][current_right_fingers - 1]
    
    # DEBOUNCE: only switch if the same chord is detected for 5 frames
    if target_chord == current_playing_chord:
        debounce_counter = 0  # same chord, reset counter
    else:
        debounce_counter += 1  # new chord detected, count frames
    
    if debounce_counter >= DEBOUNCE_FRAMES:
        # confirmed stable new gesture - switch audio
        if active_channel:
            active_channel.stop()
            active_channel = None
        
        if target_chord is not None:
            try:
                sh1 = shift_pitch(target_chord[0], left_capo_shift)
                sh2 = shift_pitch(target_chord[1], left_capo_shift)
                sh3 = shift_pitch(target_chord[2], left_capo_shift)
                
                sound = build_loop(sh1, sh2, sh3)
                active_channel = sound.play(loops=-1)
            except:
                pass
        
        current_playing_chord = target_chord
        debounce_counter = 0

    # chord name
    chord_name = "None"
    if right_hand_visible:
        if active_family == 1:
            names = {1: "Am", 2: "Gmaj", 3: "Fmaj", 4: "Emaj"}
            chord_name = names.get(current_right_fingers, "None")
        elif active_family == 2:
            names = {1: "Gmaj", 2: "Emin", 3: "Cmaj", 4: "Dmaj"}
            chord_name = names.get(current_right_fingers, "None")
        elif active_family == 3:
            if right_thumb_only_active:
                chord_name = "Am (Thumb)"
            else:
                names = {1: "Emin", 2: "Dmaj", 3: "Cmaj", 4: "Bmin"}
                chord_name = names.get(current_right_fingers, "None")
    
    # display
    cv2.putText(frame, f"Capo (Red): +{left_capo_shift} semitones", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    cv2.putText(frame, f"Chord (Blue): {chord_name}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)
    
    cv2.imshow("Air Guitar Pro", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
if active_channel:
    active_channel.stop()
pygame.mixer.stop()
cv2.destroyAllWindows()