import cv2
import mediapipe as mp
import math

class HandTracker:
    def __init__(self, mode=False, max_hands=1, detection_con=0.75, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.results = None
        self.lm_list = []

    def get_landmarks(self, img, draw=True):
        """Extracts hand coordinates from BGR frame."""
        self.lm_list = []
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, hand_lms, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(144, 175, 159), thickness=2, circle_radius=2),
                        self.mp_draw.DrawingSpec(color=(150, 150, 210), thickness=2, circle_radius=2)
                    )
                h, w, c = img.shape
                for id, lm in enumerate(hand_lms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lm_list.append([id, cx, cy])
        return self.lm_list

    def fingers_up(self):
        """Returns list of raised fingers: [Thumb, Index, Middle, Ring, Pinky]."""
        fingers = []
        if len(self.lm_list) == 0:
            return [0, 0, 0, 0, 0]
            
        # Thumb state determined by distance of tip to index knuckle
        x4, y4 = self.lm_list[4][1], self.lm_list[4][2]
        x3, y3 = self.lm_list[3][1], self.lm_list[3][2]
        x5, y5 = self.lm_list[5][1], self.lm_list[5][2]
        
        dist_tip_base = math.hypot(x4 - x5, y4 - y5)
        dist_ip_base = math.hypot(x3 - x5, y3 - y5)
        
        if dist_tip_base > dist_ip_base:
            fingers.append(1)
        else:
            fingers.append(0)
            
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        
        for i in range(4):
            if self.lm_list[tip_ids[i]][2] < self.lm_list[pip_ids[i]][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers

    def distance(self, p1, p2):
        if len(self.lm_list) == 0:
            return 9999.0
        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        return math.hypot(x2 - x1, y2 - y1)
