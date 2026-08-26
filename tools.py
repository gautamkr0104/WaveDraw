import os
import cv2
import numpy as np
import math
from datetime import datetime
from utils import hex_to_bgr

class CanvasManager:
    def __init__(self, width=1280, height=720, max_history=30):
        """Manages the drawing canvas, brush/eraser settings, and Undo/Redo history stacks."""
        self.width = width
        self.height = height
        self.max_history = max_history
        
        # Black canvas background where non-zero BGR pixels represent strokes
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        self.history = []
        self.redo_stack = []
        
        self.COLORS = {
            'sage': hex_to_bgr('#9FAF90'),
            'rose': hex_to_bgr('#DCAE96'),
            'terracotta': hex_to_bgr('#C46D4B'),
            'cream': hex_to_bgr('#F4F1EA'),
            'mocha': hex_to_bgr('#8C7D70'),
            'lavender': hex_to_bgr('#BDB2CF'),
            'charcoal': hex_to_bgr('#363636'),
            'sky': hex_to_bgr('#A9C6D3')
        }
        
        self.current_tool = 'brush'
        self.current_brush_type = 'hard'
        self.current_color_name = 'sage'
        self.current_color = self.COLORS['sage']
        self.brush_thickness = 8
        self.eraser_thickness = 45
        self.beige_bg = hex_to_bgr('#F7F4EF')

    def select_tool(self, tool_name):
        valid_tools = ['brush', 'eraser', 'line', 'rectangle', 'circle']
        if tool_name in valid_tools:
            self.current_tool = tool_name

    def select_color(self, color_name):
        if color_name in self.COLORS:
            self.current_color_name = color_name
            self.current_color = self.COLORS[color_name]
            if self.current_tool == 'eraser':
                self.current_tool = 'brush'

    def set_custom_color(self, bgr_color, name='custom'):
        self.current_color = tuple(int(c) for c in bgr_color)
        self.current_color_name = name
        if self.current_tool == 'eraser':
            self.current_tool = 'brush'

    def set_brush_size(self, size):
        self.brush_thickness = int(np.clip(size, 2, 40))

    def draw_freehand(self, pt1, pt2):
        """Draws continuous brush/eraser segments using calligraphic scaling and brush engines."""
        if self.current_tool == 'eraser':
            cv2.line(self.canvas, pt1, pt2, (0, 0, 0), self.eraser_thickness)
            return

        dx, dy = pt2[0] - pt1[0], pt2[1] - pt1[1]
        speed = math.hypot(dx, dy)
        
        # Speed mapping: fast movement -> thin strokes, slow -> thick strokes
        factor = max(0.45, min(1.25, 1.25 - (speed / 45.0) * 0.8))
        thick = max(1, int(self.brush_thickness * factor))
        
        if self.current_brush_type == 'hard':
            cv2.line(self.canvas, pt1, pt2, self.current_color, thick, cv2.LINE_AA)
            
        elif self.current_brush_type in ['soft', 'neon', 'watercolor', 'pencil']:
            # Localized ROI-based blending to optimize Gaussian blur speeds
            x1, y1 = pt1
            x2, y2 = pt2
            
            pad = max(15, thick * 3)
            rx1 = max(0, min(x1, x2) - pad)
            rx2 = min(self.width, max(x1, x2) + pad)
            ry1 = max(0, min(y1, y2) - pad)
            ry2 = min(self.height, max(y1, y2) + pad)
            
            if rx2 - rx1 > 0 and ry2 - ry1 > 0:
                roi = self.canvas[ry1:ry2, rx1:rx2].copy()
                
                if self.current_brush_type == 'soft':
                    mask = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.uint8)
                    cv2.line(mask, (x1 - rx1, y1 - ry1), (x2 - rx1, y2 - ry1), 255, thick, cv2.LINE_AA)
                    k_size = thick | 1
                    mask_blur = cv2.GaussianBlur(mask, (k_size, k_size), 0)
                    mask_norm = mask_blur[:, :, np.newaxis] / 255.0
                    
                    color_img = np.full(roi.shape, self.current_color, dtype=np.uint8)
                    blended = (roi * (1.0 - mask_norm) + color_img * mask_norm).astype(np.uint8)
                    self.canvas[ry1:ry2, rx1:rx2] = blended
                    
                elif self.current_brush_type == 'neon':
                    # Neon glow pass (blurred backdrop)
                    mask_glow = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.uint8)
                    glow_w = int(thick * 2.2)
                    cv2.line(mask_glow, (x1 - rx1, y1 - ry1), (x2 - rx1, y2 - ry1), 255, glow_w, cv2.LINE_AA)
                    k_glow = glow_w | 1
                    mask_glow_blur = cv2.GaussianBlur(mask_glow, (k_glow, k_glow), 0)
                    mask_glow_norm = mask_glow_blur[:, :, np.newaxis] / 255.0
                    
                    color_glow = np.full(roi.shape, self.current_color, dtype=np.uint8)
                    roi = (roi * (1.0 - mask_glow_norm) + color_glow * mask_glow_norm).astype(np.uint8)
                    
                    # Neon core pass (white center line)
                    core_w = max(1, int(thick * 0.45))
                    cv2.line(roi, (x1 - rx1, y1 - ry1), (x2 - rx1, y2 - ry1), (255, 255, 255), core_w, cv2.LINE_AA)
                    self.canvas[ry1:ry2, rx1:rx2] = roi
                    
                elif self.current_brush_type == 'watercolor':
                    # Translucent glazing overlay blend
                    mask = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.uint8)
                    cv2.line(mask, (x1 - rx1, y1 - ry1), (x2 - rx1, y2 - ry1), 255, thick, cv2.LINE_AA)
                    k_size = (thick * 2) | 1
                    mask_blur = cv2.GaussianBlur(mask, (k_size, k_size), 0)
                    mask_norm = (mask_blur[:, :, np.newaxis] / 255.0) * 0.16
                    
                    color_img = np.full(roi.shape, self.current_color, dtype=np.uint8)
                    blended = (roi * (1.0 - mask_norm) + color_img * mask_norm).astype(np.uint8)
                    self.canvas[ry1:ry2, rx1:rx2] = blended
                    
                elif self.current_brush_type == 'pencil':
                    # Graphite overlay blend pass
                    p_thick = max(1, thick // 3)
                    mask = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.uint8)
                    cv2.line(mask, (x1 - rx1, y1 - ry1), (x2 - rx1, y2 - ry1), 255, p_thick, cv2.LINE_AA)
                    mask_blur = cv2.GaussianBlur(mask, (3, 3), 0)
                    mask_norm = (mask_blur[:, :, np.newaxis] / 255.0) * 0.55
                    
                    color_img = np.full(roi.shape, self.current_color, dtype=np.uint8)
                    blended = (roi * (1.0 - mask_norm) + color_img * mask_norm).astype(np.uint8)
                    self.canvas[ry1:ry2, rx1:rx2] = blended

    def draw_shape(self, pt_start, pt_current, target_canvas=None):
        canvas = self.canvas if target_canvas is None else target_canvas
        thickness = self.brush_thickness
        color = self.current_color
        
        if self.current_tool == 'line':
            cv2.line(canvas, pt_start, pt_current, color, thickness, cv2.LINE_AA)
        elif self.current_tool == 'rectangle':
            cv2.rectangle(canvas, pt_start, pt_current, color, thickness, cv2.LINE_AA)
        elif self.current_tool == 'circle':
            radius = int(math.hypot(pt_current[0] - pt_start[0], pt_current[1] - pt_start[1]))
            cv2.circle(canvas, pt_start, radius, color, thickness, cv2.LINE_AA)

    def save_state(self):
        """Pushes a copy of the canvas onto the history stack."""
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append(self.canvas.copy())
        self.redo_stack.clear()

    def undo(self):
        """Reverts the last stroke. Returns True on success."""
        if len(self.history) > 0:
            self.redo_stack.append(self.canvas.copy())
            self.canvas = self.history.pop()
            return True
        return False

    def redo(self):
        """Reapplies the last undone stroke. Returns True on success."""
        if len(self.redo_stack) > 0:
            self.history.append(self.canvas.copy())
            self.canvas = self.redo_stack.pop()
            return True
        return False

    def clear(self):
        self.save_state()
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def save_drawing(self, outputs_dir="outputs/drawings"):
        """Composites drawings onto a clean beige paper background (#F7F4EF) and saves to disk."""
        os.makedirs(outputs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"HaloScribe_{timestamp}.png"
        filepath = os.path.join(outputs_dir, filename)
        
        paper_bg = np.full((self.height, self.width, 3), self.beige_bg, dtype=np.uint8)
        
        gray_drawing = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask_inv = cv2.threshold(gray_drawing, 5, 255, cv2.THRESH_BINARY_INV)
        mask_inv = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR)
        
        paper_bg = cv2.bitwise_and(paper_bg, mask_inv)
        final_drawing = cv2.bitwise_or(paper_bg, self.canvas)
        
        cv2.imwrite(filepath, final_drawing)
        return filepath
