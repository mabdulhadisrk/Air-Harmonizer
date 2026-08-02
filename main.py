import cv2
import mediapipe as mp
import pygame
import math
import numpy as np
import time
import os
import threading

# audio setup
pygame.mixer.init(frequency=22050, size=-16, channels=1)

# samantha voice greeting (runs in background so it doesnt freeze the webcam)
def play_welcome_voice():
    time.sleep(2)
    os.system("say -v Samantha 'Welcome. This application is an interactive gesture controlled music player.'")

# basic pitch shifting - same math as guitar frets
def shift_pitch(frequency, semitones):
    return frequency * (2.0 ** (semitones / 12.0))

# generates a chord as raw audio data (no wav files needed)
def build_loop(hz1, hz2, hz3, length=1.2, rate=22050):
    total_samples = int(length * rate)
    data_list = []
    
    for step in range(total_samples):
        t = step / rate
        
        # three sine waves added together
        w1 = math.sin(2.0 * math.pi * hz1 * t)
        w2 = math.sin(2.0 * math.pi * hz2 * t)
        w3 = math.sin(2.0 * math.pi * hz3 * t)
        
        combined = (w1 + w2 + w3) / 3.0
        
        # fade in/out to avoid clicking sounds
        edge_buffer = 1000
        if step < edge_buffer:
            env = step / edge_buffer
        elif step > total_samples - edge_buffer:
            env = (total_samples - step) / edge_buffer
        else:
            env = 1.0
            
        data_list.append(int(combined * 32767 * env))
        
    return pygame.mixer.Sound(np.array(data_list, dtype=np.int16))

# frequency reference (A3 = 220Hz as base)
notes = {
    'A3': 220.00, 'C4': 261.63, 'E4': 329.63, 'G3': 196.00, 'B3': 246.94, 'D4': 293.66,
    'F3': 174.61, 'A4': 440.00, 'E3': 164.81, 'G4': 392.00, 'C5': 523.25, 'F4': 349.23,
    'D3': 146.83, 'Fsharp3': 185.00, 'B4': 493.88, 'D5': 587.33, 'Fsharp4': 369.99
}

# chord families - each finger count triggers a different chord
families = {
    1: [  # Am, Gmaj, Fmaj, Emaj
        (notes['A3'], notes['C4'], notes['E4']),
        (notes['G3'], notes['B3'], notes['D4']),
        (notes['F3'], notes['A3'], notes['C4']),
        (notes['E3'], notes['Fsharp3'], notes['B3'])
    ],
    2: [  # Gmaj, Emin, Cmaj, Dmaj
        (notes['G3'], notes['B3'], notes['D4']),
        (notes['E3'], notes['G3'], notes['B3']),
        (notes['C4'], notes['E4'], notes['G4']),
        (notes['D3'], notes['Fsharp3'], notes['A4'])
    ],
    3: [  # Emin, Dmaj, Cmaj, Bmin (thumb only = Am override)
        (notes['E3'], notes['G3'], notes['B3']),
        (notes['D3'], notes['Fsharp3'], notes['A4']),
        (notes['C4'], notes['E4'], notes['G4']),
        (notes['B3'], notes['D4'], notes['Fsharp4'])
    ]
}

# special case: family 3 + thumb only = Am chord
custom_am_override_chord = (notes['A3'], notes['C4'], notes['E4'])

# state variables
active_family = 1
left_capo_shift = 0
last_state_signature = ""

# threshold: fingertip must be at least this far above the pip to count as "shown"
# (as a fraction of the frame height - 0.04 means ~4% of screen height)
TIP_VISIBILITY_THRESHOLD = 0.04

# mouse click handler for switching chord families
def mouse_click_handler(event, x, y, flags, param):
    global active_family, last_state_signature
    if event == cv2.EVENT_LBUTTONDOWN:
        if 480 <= x <= 630:
            if 10 <= y <= 40:
                active_family = 1
            elif 50 <= y <= 80:
                active_family = 2
            elif 90 <= y <= 120:
                active_family = 3
            last_state_signature = "RESET"

# camera setup - skip iphone continuity camera (index 0 is sometimes external on mac)
camera = None
for dev_idx in range(3):
    test_cap = cv2.VideoCapture(dev_idx, cv2.CAP_AVFOUNDATION)
    if test_cap.isOpened():
        w_check = test_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        if w_check > 0 and w_check != 1920:  # 1920 is usually the external cam
            camera = test_cap
            break
        test_cap.release()

if camera is None:
    camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

time.sleep(1)
cv2.namedWindow("Air Guitar Pro")
cv2.setMouseCallback("Air Guitar Pro", mouse_click_handler)

# mediapipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6)

# start the voice greeting in background
voice_thread = threading.Thread(target=play_welcome_voice)
voice_thread.daemon = True
voice_thread.start()

# main loop
while camera.isOpened():
    ret, frame = camera.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    # draw the three family buttons on screen
    # family 1 button
    color1 = (0, 255, 0) if active_family == 1 else (100, 100, 100)
    cv2.rectangle(frame, (480, 10), (630, 40), color1, -1)
    cv2.putText(frame, "1: Am-G-F-E", (485, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # family 2 button
    color2 = (0, 255, 0) if active_family == 2 else (100, 100, 100)
    cv2.rectangle(frame, (480, 50), (630, 80), color2, -1)
    cv2.putText(frame, "2: G-Em-C-D", (485, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # family 3 button (shows Am thumb override in label)
    color3 = (0, 255, 0) if active_family == 3 else (100, 100, 100)
    cv2.rectangle(frame, (480, 90), (630, 120), color3, -1)
    cv2.putText(frame, "3: Em-D-C-Bm (T=Am)", (485, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # process hand tracking
    rgb_view = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_view)
    
    # reset per-frame variables
    left_hand_visible = False
    detected_left_semitones = 0
    current_right_fingers = 0
    right_hand_visible = False
    right_thumb_only_active = False
    
    if results.multi_hand_landmarks:
        for hand_pts in results.multi_hand_landmarks:
            pts = hand_pts.landmark
            
            # figure out which side of screen the hand is on
            # left side = capo hand (red), right side = strum hand (blue)
            hand_center_x = pts[0].x * w
            is_capo_hand = hand_center_x < (w / 2)
            
            # red for left hand, blue for right
            dot_color = (0, 0, 255) if is_capo_hand else (255, 0, 0)
            
            # finger tip and pip joint indices
            tips = (8, 12, 16, 20)
            pips = (6, 10, 14, 18)
            f_count = 0
            
            # count ONLY fingers where tip is clearly above pip (showing, not folded)
            # uses a threshold so slightly bent fingers dont trigger
            for t_idx, p_idx in zip(tips, pips):
                tip_y = pts[t_idx].y
                pip_y = pts[p_idx].y
                
                # tip must be significantly above pip to count as "shown"
                if (pip_y - tip_y) > TIP_VISIBILITY_THRESHOLD:
                    f_count += 1
                    tx, ty = int(pts[t_idx].x * w), int(pts[t_idx].y * h)
                    cv2.circle(frame, (tx, ty), 10, dot_color, cv2.FILLED)
                else:
                    # still draw the dot but smaller/dimmer to show its detected but not active
                    tx, ty = int(pts[t_idx].x * w), int(pts[t_idx].y * h)
                    cv2.circle(frame, (tx, ty), 6, (100, 100, 100), cv2.FILLED)
                    
            # check if thumb is extended separately (same threshold logic)
            thumb_tip = pts[4]
            thumb_ip = pts[3]
            hand_base = pts[0]
            
            # thumb needs to be sticking out sideways from the hand, not just above the IP joint
            thumb_horizontal_distance = abs(thumb_tip.x - hand_base.x)
            thumb_ip_horizontal_distance = abs(thumb_ip.x - hand_base.x)
            
            if thumb_horizontal_distance > thumb_ip_horizontal_distance and \
               (thumb_horizontal_distance - thumb_ip_horizontal_distance) > 0.02:
                thumb_open = True
                bx, by = int(thumb_tip.x * w), int(thumb_tip.y * h)
                cv2.circle(frame, (bx, by), 10, dot_color, cv2.FILLED)
            else:
                thumb_open = False

            # assign semitones for capo hand, finger count for strum hand
            if is_capo_hand:
                left_hand_visible = True
                if f_count == 4:
                    detected_left_semitones = 5
                elif f_count == 3:
                    detected_left_semitones = 4
                elif f_count == 2:
                    detected_left_semitones = 3
                elif f_count == 1:
                    detected_left_semitones = 2
                elif thumb_open and f_count == 0:
                    detected_left_semitones = 1
                else:
                    detected_left_semitones = 0
            else:
                right_hand_visible = True
                current_right_fingers = f_count
                if thumb_open and f_count == 0:
                    right_thumb_only_active = True

    # keep the capo shift even if hand disappears temporarily
    if left_hand_visible:
        left_capo_shift = detected_left_semitones

    # build a signature so we only update audio when something actually changes
    state_signature = f"F:{active_family}_C:{left_capo_shift}_R:{current_right_fingers}_T:{right_thumb_only_active}_V:{right_hand_visible}"
    
    if state_signature != last_state_signature:
        pygame.mixer.stop()
        
        if right_hand_visible:
            base_chord = None
            
            # family 3 thumb-only override to Am
            if active_family == 3 and right_thumb_only_active:
                base_chord = custom_am_override_chord
            elif 1 <= current_right_fingers <= 4:
                base_chord = families[active_family][current_right_fingers - 1]
                
            if base_chord is not None:
                # apply capo shift to all three notes
                shifted_hz1 = shift_pitch(base_chord[0], left_capo_shift)
                shifted_hz2 = shift_pitch(base_chord[1], left_capo_shift)
                shifted_hz3 = shift_pitch(base_chord[2], left_capo_shift)
                
                active_loop = build_loop(shifted_hz1, shifted_hz2, shifted_hz3)
                active_loop.play(loops=-1)
            
        last_state_signature = state_signature
        
    # figure out chord name for display
    current_chord_name = "None"
    if right_hand_visible:
        if active_family == 1:
            if current_right_fingers == 1:
                current_chord_name = "Am"
            elif current_right_fingers == 2:
                current_chord_name = "Gmaj"
            elif current_right_fingers == 3:
                current_chord_name = "Fmaj"
            elif current_right_fingers == 4:
                current_chord_name = "Emaj"
        elif active_family == 2:
            if current_right_fingers == 1:
                current_chord_name = "Gmaj"
            elif current_right_fingers == 2:
                current_chord_name = "Emin"
            elif current_right_fingers == 3:
                current_chord_name = "Cmaj"
            elif current_right_fingers == 4:
                current_chord_name = "Dmaj"
        elif active_family == 3:
            if right_thumb_only_active:
                current_chord_name = "Am (Thumb Override)"
            elif current_right_fingers == 1:
                current_chord_name = "Emin"
            elif current_right_fingers == 2:
                current_chord_name = "Dmaj"
            elif current_right_fingers == 3:
                current_chord_name = "Cmaj"
            elif current_right_fingers == 4:
                current_chord_name = "Bmin"
    
    # display info on screen
    cv2.putText(frame, f"Scale Semitones (Red Dots Capo): +{left_capo_shift}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, f"Chord Trigger (Blue Dots Strum): {current_chord_name}", (20, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    cv2.imshow("Air Guitar Pro", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# cleanup
camera.release()
pygame.mixer.stop()
cv2.destroyAllWindows()