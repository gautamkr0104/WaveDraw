import cv2
import numpy as np
import time
import math

def hex_to_bgr(hex_str):
    """Convert Hex string to BGR tuple."""
    hex_str = hex_str.lstrip('#')
    rgb = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])

class OneEuroFilter:
    def __init__(self, mincutoff=0.8, beta=0.03, dcutoff=1.0):
        self.mincutoff = float(mincutoff)
        self.beta = float(beta)
        self.dcutoff = float(dcutoff)
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def filter(self, t, x):
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x
            
        dt = t - self.t_prev
        if dt <= 0:
            return self.x_prev
            
        # Velocity filter (derivative)
        alpha_d = 1.0 / (1.0 + 1.0 / (2 * math.pi * self.dcutoff * dt))
        dx = (x - self.x_prev) / dt
        dx_hat = alpha_d * dx + (1.0 - alpha_d) * self.dx_prev
        
        # Adaptive cutoff value filtering
        cutoff = self.mincutoff + self.beta * abs(dx_hat)
        alpha = 1.0 / (1.0 + 1.0 / (2 * math.pi * cutoff * dt))
        x_hat = alpha * x + (1.0 - alpha) * self.x_prev
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

    def reset(self):
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

class CoordinateSmoother:
    def __init__(self, mincutoff=0.8, beta=0.03, dcutoff=1.0):
        """Stabilizes 2D coordinates using dual 1-Euro filters."""
        self.x_filter = OneEuroFilter(mincutoff, beta, dcutoff)
        self.y_filter = OneEuroFilter(mincutoff, beta, dcutoff)

    def smooth(self, x, y):
        t = time.time()
        sx = self.x_filter.filter(t, x)
        sy = self.y_filter.filter(t, y)
        return int(sx), int(sy)

    def reset(self):
        """Clear filter history to prevent stroke trailing."""
        self.x_filter.reset()
        self.y_filter.reset()

def draw_rounded_rect(img, pt1, pt2, color, thickness=1, radius=12):
    x1, y1 = pt1
    x2, y2 = pt2
    
    cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness, cv2.LINE_AA)
    
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness, cv2.LINE_AA)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness, cv2.LINE_AA)

def draw_filled_rounded_rect(img, pt1, pt2, color, radius=12):
    x1, y1 = pt1
    x2, y2 = pt2
    
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    
    cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1, cv2.LINE_AA)
    cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1, cv2.LINE_AA)
    cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1, cv2.LINE_AA)
    cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1, cv2.LINE_AA)
