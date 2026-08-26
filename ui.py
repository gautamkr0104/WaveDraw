import cv2
import numpy as np
import os
import math
from utils import draw_rounded_rect, draw_filled_rounded_rect, hex_to_bgr

class UIManager:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        
        self.bg_color = hex_to_bgr('#F7F4EF')
        self.panel_color = (255, 255, 255)
        self.border_color = hex_to_bgr('#EFECE6')
        self.text_color = hex_to_bgr('#363636')
        self.accent_color = hex_to_bgr('#D1C4E9')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icons = {}
        self._load_icon('brush', os.path.join(base_dir, 'assets', 'brush.png'))
        self._load_icon('eraser', os.path.join(base_dir, 'assets', 'eraser.png'))
        self._load_icon('save', os.path.join(base_dir, 'assets', 'save.png'))
        
        self.top_w, self.top_h = 760, 70
        self.top_x1 = (self.width - self.top_w) // 2
        self.top_y1 = 20
        self.top_x2 = self.top_x1 + self.top_w
        self.top_y2 = self.top_y1 + self.top_h
        
        self.top_tools = ['brush', 'eraser', 'line', 'rectangle', 'circle', 'undo', 'redo', 'save']
        self.top_btn_coords = {}
        btn_w = 55
        btn_h = 50
        gap = (self.top_w - len(self.top_tools) * btn_w) // (len(self.top_tools) + 1)
        
        for i, tool in enumerate(self.top_tools):
            bx1 = self.top_x1 + gap + i * (btn_w + gap)
            by1 = self.top_y1 + (self.top_h - btn_h) // 2
            self.top_btn_coords[tool] = (bx1, by1, bx1 + btn_w, by1 + btn_h)
            
        self.left_x1, self.left_y1 = 20, 130
        self.left_x2, self.left_y2 = 80, 570
        self.slider_y_start = 165
        self.slider_y_end = 335
        
        self.brush_type_coords = [
            ('hard', 385),
            ('soft', 420),
            ('neon', 455),
            ('watercolor', 490),
            ('pencil', 525)
        ]
        
        self.bot_w, self.bot_h = 1000, 60
        self.bot_x1 = (self.width - self.bot_w) // 2
        self.bot_y1 = 630
        self.bot_x2 = self.bot_x1 + self.bot_w
        self.bot_y2 = self.bot_y1 + self.bot_h
        
        self.right_w, self.right_h = 180, 440
        self.right_x1 = 1080
        self.right_y1 = 130
        self.right_x2 = self.right_x1 + self.right_w
        self.right_y2 = self.right_y1 + self.right_h
        
        self.donut_cx, self.donut_cy = 1170, 230
        self.picker_size = 150
        self.pcx, self.pcy = 75, 75
        self.sv_half = 26
        
        self.sv_x1 = self.donut_cx - self.sv_half
        self.sv_y1 = self.donut_cy - self.sv_half
        self.sv_x2 = self.donut_cx + self.sv_half
        self.sv_y2 = self.donut_cy + self.sv_half
        
        self.recent_colors = []
        self.recent_coords = []
        for i in range(5):
            cx = 1105 + i * 32
            self.recent_coords.append((cx, 420, 10))
            
        self.favorite_colors = [
            hex_to_bgr('#9FAF90'),
            hex_to_bgr('#DCAE96'),
            hex_to_bgr('#C46D4B'),
            hex_to_bgr('#BDB2CF'),
            hex_to_bgr('#A9C6D3')
        ]
        self.favorite_coords = []
        for i in range(5):
            cx = 1105 + i * 32
            self.favorite_coords.append((cx, 485, 10))
            
        self.selected_hue = 45
        self.hue_indicator = (self.donut_cx + 42, self.donut_cy - 38)
        self.sv_indicator = (self.donut_cx + 14, self.donut_cy - 12)
        
        self._precompute_static_hue_ring()
        self.update_sv_gradient()
        
        self.ripples = []
        self.notifications = []

    def _load_icon(self, name, path):
        if os.path.exists(path):
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None and img.shape[2] == 4:
                self.icons[name] = cv2.resize(img, (40, 40))

    def _precompute_static_hue_ring(self):
        """Precomputes the BGR rainbow donut Hue ring and its binary mask."""
        self.hue_ring = np.full((self.picker_size, self.picker_size, 3), 255, dtype=np.uint8)
        self.hue_ring_mask = np.zeros((self.picker_size, self.picker_size), dtype=np.uint8)
        
        for r in range(self.picker_size):
            for c in range(self.picker_size):
                dx = c - self.pcx
                dy = r - self.pcy
                dist = math.hypot(dx, dy)
                # Outer donut Hue ring boundary: radius 45 to 68 pixels
                if 45 <= dist <= 68:
                    angle = math.atan2(dy, dx) + math.pi
                    h = int(angle / (2.0 * math.pi) * 179)
                    hsv = np.uint8([[[h, 255, 255]]])
                    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
                    self.hue_ring[r, c] = bgr
                    self.hue_ring_mask[r, c] = 255

    def update_sv_gradient(self):
        """Redraws the S-V gradient square matching the current active Hue angle."""
        self.picker_img = np.full((self.picker_size, self.picker_size, 3), 255, dtype=np.uint8)
        
        idx = (self.hue_ring_mask > 0)
        self.picker_img[idx] = self.hue_ring[idx]
        
        sv_size = self.sv_half * 2
        x_start = self.pcx - self.sv_half
        y_start = self.pcy - self.sv_half
        
        sv_grid = np.zeros((sv_size, sv_size, 3), dtype=np.uint8)
        sv_grid[:, :, 0] = self.selected_hue
        
        s_vals = np.linspace(0, 255, sv_size, dtype=np.uint8)
        sv_grid[:, :, 1] = s_vals
        
        v_vals = np.linspace(255, 0, sv_size, dtype=np.uint8)[:, np.newaxis]
        sv_grid[:, :, 2] = v_vals
        
        sv_bgr = cv2.cvtColor(sv_grid, cv2.COLOR_HSV2BGR)
        self.picker_img[y_start:y_start+sv_size, x_start:x_start+sv_size] = sv_bgr
        cv2.rectangle(self.picker_img, (x_start, y_start), (x_start+sv_size, y_start+sv_size), self.border_color, 1, cv2.LINE_AA)

    def sync_picker_to_color(self, bgr_color):
        """Resolves indicators to BGR color back-projections."""
        bgr_pixel = np.uint8([[bgr_color]])
        hsv = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = hsv
        
        self.selected_hue = h
        self.update_sv_gradient()
        
        # Hue indicator angle projection (radius 56 pixels)
        angle = (h / 179.0) * 2.0 * math.pi - math.pi
        hx = int(self.donut_cx + 56 * math.cos(angle))
        hy = int(self.donut_cy + 56 * math.sin(angle))
        self.hue_indicator = (hx, hy)
        
        # S-V indicator linear scale maps inside the square
        pct_s = s / 255.0
        pct_v = (255.0 - v) / 255.0
        sv_size = self.sv_half * 2
        sx = int((self.donut_cx - self.sv_half) + pct_s * sv_size)
        sy = int((self.donut_cy - self.sv_half) + pct_v * sv_size)
        self.sv_indicator = (sx, sy)

    def check_hud_hover(self, x, y):
        """Resolves target coordinate hits across panel hitboxes."""
        hover = {'type': None, 'value': None}
        
        if self.top_x1 <= x <= self.top_x2 and self.top_y1 <= y <= self.top_y2:
            for name, bounds in self.top_btn_coords.items():
                bx1, by1, bx2, by2 = bounds
                if bx1 <= x <= bx2 and by1 <= y <= by2:
                    hover['type'] = 'tool'
                    hover['value'] = name
                    return hover
                    
        if self.left_x1 <= x <= self.left_x2 and self.left_y1 <= y <= self.left_y2:
            if self.slider_y_start <= y <= self.slider_y_end:
                hover['type'] = 'slider'
                hover['value'] = np.clip((self.slider_y_end - y) / (self.slider_y_end - self.slider_y_start), 0.0, 1.0)
                return hover
            for name, cy_btn in self.brush_type_coords:
                if math.hypot(x - 50, y - cy_btn) <= 15:
                    hover['type'] = 'brush_type'
                    hover['value'] = name
                    return hover
                    
        if self.right_x1 <= x <= self.right_x2 and self.right_y1 <= y <= self.right_y2:
            dist = math.hypot(x - self.donut_cx, y - self.donut_cy)
            if 42 <= dist <= 74:
                hover['type'] = 'color_picker_hue'
                hover['value'] = (x, y)
                return hover
            if (self.donut_cx - self.sv_half - 2) <= x <= (self.donut_cx + self.sv_half + 2) and \
               (self.donut_cy - self.sv_half - 2) <= y <= (self.donut_cy + self.sv_half + 2):
                hover['type'] = 'color_picker_sv'
                hover['value'] = (x, y)
                return hover
            for i, (cx, cy, r) in enumerate(self.recent_coords):
                if i < len(self.recent_colors):
                    if math.hypot(x - cx, y - cy) <= r + 4:
                        hover['type'] = 'recent_color'
                        hover['value'] = i
                        return hover
            for i, (cx, cy, r) in enumerate(self.favorite_coords):
                if math.hypot(x - cx, y - cy) <= r + 4:
                    hover['type'] = 'favorite_color'
                    hover['value'] = i
        return hover

    def is_inside_hud(self, x, y):
        """Checks if coordinate (x, y) is inside any interactive HUD panel boundary."""
        # Top panel and margin above it
        if y < self.top_y2:
            return True
        # Left sidebar panel
        if self.left_x1 <= x <= self.left_x2 and self.left_y1 <= y <= self.left_y2:
            return True
        # Right sidebar panel
        if self.right_x1 <= x <= self.right_x2 and self.right_y1 <= y <= self.right_y2:
            return True
        # Bottom status bar panel
        if self.bot_x1 <= x <= self.bot_x2 and self.bot_y1 <= y <= self.bot_y2:
            return True
        return False

    def draw_ui(self, img, canvas_manager, fps=30):
        """Draws floating translucent panel cards."""
        self._draw_panel_with_shadow(img, (20, 20), (105, 60), radius=6)
        cv2.putText(img, f"FPS: {fps}", (33, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)

        self._draw_panel_with_shadow(img, (self.top_x1, self.top_y1), (self.top_x2, self.top_y2))
        for name, bounds in self.top_btn_coords.items():
            bx1, by1, bx2, by2 = bounds
            is_active = (canvas_manager.current_tool == name)
            
            if is_active:
                draw_filled_rounded_rect(img, (bx1, by1), (bx2, by2), self.accent_color, radius=8)
                
            draw_color = self.text_color
            if name in self.icons:
                cx = bx1 + (bx2 - bx1 - 40) // 2
                cy = by1 + (by2 - by1 - 40) // 2
                self._overlay_png(img, self.icons[name], cx, cy)
            else:
                self._draw_vector_icon(img, name, bounds, draw_color)
                
        self._draw_panel_with_shadow(img, (self.left_x1, self.left_y1), (self.left_x2, self.left_y2))
        cv2.putText(img, "SIZE", (self.left_x1 + 13, self.left_y1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
        cv2.line(img, (50, self.slider_y_start), (50, self.slider_y_end), self.border_color, 4, cv2.LINE_AA)
        
        ratio = (canvas_manager.brush_thickness - 2) / (40 - 2)
        handle_y = int(self.slider_y_end - ratio * (self.slider_y_end - self.slider_y_start))
        
        cv2.circle(img, (50, handle_y), 9, self.accent_color, cv2.FILLED, cv2.LINE_AA)
        cv2.circle(img, (50, handle_y), 9, self.text_color, 1, cv2.LINE_AA)
        cv2.putText(img, f"{canvas_manager.brush_thickness}", (self.left_x1 + 16, self.slider_y_end + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.text_color, 1, cv2.LINE_AA)
                    
        cv2.line(img, (self.left_x1 + 8, 362), (self.left_x2 - 8, 362), self.border_color, 1, cv2.LINE_AA)
        
        for name, cy_btn in self.brush_type_coords:
            cx_btn = 50
            is_active = (canvas_manager.current_brush_type == name)
            bg_col = self.accent_color if is_active else self.panel_color
            border_col = self.text_color if is_active else self.border_color
            
            cv2.circle(img, (cx_btn, cy_btn), 12, bg_col, cv2.FILLED, cv2.LINE_AA)
            cv2.circle(img, (cx_btn, cy_btn), 12, border_col, 1, cv2.LINE_AA)
            
            letter = name[0].upper()
            cv2.putText(img, letter, (cx_btn - 5, cy_btn + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.text_color, 1, cv2.LINE_AA)

        self._draw_panel_with_shadow(img, (self.right_x1, self.right_y1), (self.right_x2, self.right_y2))
        cv2.putText(img, "COLOR SELECTOR", (self.right_x1 + 13, self.right_y1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
        
        x_st = self.donut_cx - self.picker_size // 2
        y_st = self.donut_cy - self.picker_size // 2
        img[y_st:y_st+self.picker_size, x_st:x_st+self.picker_size] = self.picker_img
        
        cv2.circle(img, (self.donut_cx, self.donut_cy), 68, self.border_color, 1, cv2.LINE_AA)
        cv2.circle(img, (self.donut_cx, self.donut_cy), 45, self.border_color, 1, cv2.LINE_AA)
        
        cv2.circle(img, self.sv_indicator, 4, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(img, self.sv_indicator, 4, self.text_color, 1, cv2.LINE_AA)
        
        cv2.circle(img, self.hue_indicator, 4, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(img, self.hue_indicator, 4, self.text_color, 1, cv2.LINE_AA)
        
        cv2.circle(img, (self.donut_cx, self.donut_cy), 13, canvas_manager.current_color, -1, cv2.LINE_AA)
        cv2.circle(img, (self.donut_cx, self.donut_cy), 13, self.border_color, 1, cv2.LINE_AA)
        
        color = canvas_manager.current_color
        b, g, r = color
        cv2.rectangle(img, (1095, 332), (1130, 367), color, -1)
        cv2.rectangle(img, (1095, 332), (1130, 367), self.border_color, 1, cv2.LINE_AA)
        
        cv2.putText(img, f"RGB: {r},{g},{b}", (1138, 345), cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.text_color, 1, cv2.LINE_AA)
        cv2.putText(img, f"HEX: #{r:02X}{g:02X}{b:02X}", (1138, 361), cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.text_color, 1, cv2.LINE_AA)
        
        cv2.putText(img, "RECENTS", (self.right_x1 + 13, 395), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
        for i, (cx, cy, radius) in enumerate(self.recent_coords):
            if i < len(self.recent_colors):
                c_val = self.recent_colors[i]
                cv2.circle(img, (cx, cy), radius, c_val, cv2.FILLED, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), radius, self.border_color, 1, cv2.LINE_AA)
                if canvas_manager.current_color == c_val and canvas_manager.current_tool != 'eraser':
                    cv2.circle(img, (cx, cy), radius + 3, self.text_color, 1, cv2.LINE_AA)
            else:
                cv2.circle(img, (cx, cy), radius, (248, 246, 242), cv2.FILLED, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), radius, self.border_color, 1, cv2.LINE_AA)
                
        cv2.putText(img, "FAVORITES", (self.right_x1 + 13, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
        for i, (cx, cy, radius) in enumerate(self.favorite_coords):
            c_val = self.favorite_colors[i]
            cv2.circle(img, (cx, cy), radius, c_val, cv2.FILLED, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), radius, self.border_color, 1, cv2.LINE_AA)
            if canvas_manager.current_color == c_val and canvas_manager.current_tool != 'eraser':
                cv2.circle(img, (cx, cy), radius + 3, self.text_color, 1, cv2.LINE_AA)

        self._draw_panel_with_shadow(img, (self.bot_x1, self.bot_y1), (self.bot_x2, self.bot_y2))
        
        tool_label = f"TOOL: {canvas_manager.current_tool.upper()} ({canvas_manager.current_brush_type.upper()})"
        cv2.putText(img, tool_label, (self.bot_x1 + 25, self.bot_y1 + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.text_color, 1, cv2.LINE_AA)
        
        cv2.putText(img, f"COLOR: #{r:02X}{g:02X}{b:02X}  RGB({r},{g},{b})", 
                    (self.bot_x1 + 330, self.bot_y1 + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.text_color, 1, cv2.LINE_AA)
        cv2.circle(img, (self.bot_x1 + 310, self.bot_y1 + 31), 8, color, cv2.FILLED, cv2.LINE_AA)
        cv2.circle(img, (self.bot_x1 + 310, self.bot_y1 + 31), 8, self.border_color, 1, cv2.LINE_AA)
        
        size_label = f"SIZE: {canvas_manager.brush_thickness}px"
        cv2.putText(img, size_label, (self.bot_x2 - 120, self.bot_y1 + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.text_color, 1, cv2.LINE_AA)

    def draw_effects(self, img):
        """Draws dynamic ripples and notification banners."""
        active_ripples = []
        for rip in self.ripples:
            x, y, r, r_max, color = rip
            opacity = 1.0 - (r / r_max)
            overlay = img.copy()
            cv2.circle(overlay, (x, y), r, color, 2, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, img, 1.0 - opacity, 0, img)
            
            r += 3
            if r < r_max:
                active_ripples.append([x, y, r, r_max, color])
        self.ripples = active_ripples
        
        active_notifs = []
        y_offset = 120
        for notif in self.notifications:
            text = notif['text']
            frames = notif['frames']
            max_frames = notif['max_frames']
            color = notif['color']
            
            fade_trigger = max_frames * 0.25
            opacity = 1.0
            if frames < fade_trigger:
                opacity = frames / fade_trigger
                
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            bx1 = (self.width - tw) // 2 - 20
            bx2 = (self.width + tw) // 2 + 20
            by1 = y_offset - 10
            by2 = y_offset + th + 10
            
            overlay = img.copy()
            draw_filled_rounded_rect(overlay, (bx1+2, by1+2), (bx2+2, by2+2), (180, 180, 180), radius=6)
            cv2.addWeighted(overlay, 0.1, img, 0.9, 0, img)
            
            overlay = img.copy()
            draw_filled_rounded_rect(overlay, (bx1, by1), (bx2, by2), self.panel_color, radius=6)
            draw_rounded_rect(overlay, (bx1, by1), (bx2, by2), self.border_color, thickness=1, radius=6)
            draw_filled_rounded_rect(overlay, (bx1, by1), (bx1 + 6, by2), color, radius=3)
            
            cv2.putText(overlay, text, (bx1 + 16, by1 + th + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.text_color, 1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, img, 1.0 - opacity, 0, img)
            
            y_offset += 48
            frames -= 1
            if frames > 0:
                active_notifs.append({
                    'text': text,
                    'frames': frames,
                    'max_frames': max_frames,
                    'color': color
                })
        self.notifications = active_notifs

    def draw_cursor(self, img, x, y, gesture_mode, click_progress=0.0):
        """Draws index pointer cursor and circular hover radial timer arcs."""
        if gesture_mode == 'draw':
            cv2.circle(img, (x, y), 4, (255, 255, 255), cv2.FILLED, cv2.LINE_AA)
            cv2.circle(img, (x, y), 6, self.text_color, 1, cv2.LINE_AA)
            
        elif gesture_mode == 'select':
            cv2.circle(img, (x, y), 2, self.accent_color, cv2.FILLED, cv2.LINE_AA)
            
            outer_r = 18
            color = self.accent_color if click_progress > 0.95 else self.text_color
            
            if click_progress > 0.0:
                angle_end = int(click_progress * 360)
                cv2.ellipse(img, (x, y), (outer_r, outer_r), -90, 0, angle_end, self.accent_color, 3, cv2.LINE_AA)
                cv2.circle(img, (x, y), outer_r, self.text_color, 1, cv2.LINE_AA)
            else:
                cv2.circle(img, (x, y), outer_r, color, 1, cv2.LINE_AA)
                
            cv2.line(img, (x - outer_r - 3, y), (x - outer_r + 1, y), color, 1, cv2.LINE_AA)
            cv2.line(img, (x + outer_r - 1, y), (x + outer_r + 3, y), color, 1, cv2.LINE_AA)
            cv2.line(img, (x, y - outer_r - 3), (x, y - outer_r + 1), color, 1, cv2.LINE_AA)
            cv2.line(img, (x, y + outer_r - 1), (x, y + outer_r + 3), color, 1, cv2.LINE_AA)

    def _draw_panel_with_shadow(self, img, pt1, pt2, radius=12):
        x1, y1 = pt1
        x2, y2 = pt2
        
        shadow_overlay = img.copy()
        draw_filled_rounded_rect(shadow_overlay, (x1 + 3, y1 + 3), (x2 + 3, y2 + 3), (200, 195, 190), radius)
        cv2.addWeighted(shadow_overlay, 0.15, img, 0.85, 0, img)
        
        draw_filled_rounded_rect(img, (x1, y1), (x2, y2), self.panel_color, radius)
        draw_rounded_rect(img, (x1, y1), (x2, y2), self.border_color, thickness=1, radius=radius)

    def _draw_vector_icon(self, img, name, bounds, color):
        x1, y1, x2, y2 = bounds
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        if name == 'line':
            cv2.line(img, (x1 + 18, y2 - 18), (x2 - 18, y1 + 18), color, 2, cv2.LINE_AA)
        elif name == 'rectangle':
            cv2.rectangle(img, (x1 + 18, y1 + 15), (x2 - 18, y2 - 15), color, 2, cv2.LINE_AA)
        elif name == 'circle':
            cv2.circle(img, (cx, cy), 12, color, 2, cv2.LINE_AA)
        elif name == 'undo':
            cv2.ellipse(img, (cx + 3, cy + 2), (9, 7), 0, 180, 360, color, 2, cv2.LINE_AA)
            cv2.line(img, (cx - 6, cy + 2), (cx - 10, cy - 2), color, 2, cv2.LINE_AA)
            cv2.line(img, (cx - 6, cy + 2), (cx - 2, cy - 2), color, 2, cv2.LINE_AA)
        elif name == 'redo':
            cv2.ellipse(img, (cx - 3, cy + 2), (9, 7), 0, 180, 360, color, 2, cv2.LINE_AA)
            cv2.line(img, (cx + 6, cy + 2), (cx + 10, cy - 2), color, 2, cv2.LINE_AA)
            cv2.line(img, (cx + 6, cy + 2), (cx + 2, cy - 2), color, 2, cv2.LINE_AA)

    def _overlay_png(self, background, overlay, x, y):
        h, w = overlay.shape[:2]
        if y + h > background.shape[0] or x + w > background.shape[1] or y < 0 or x < 0:
            return
        overlay_img = overlay[:, :, :3]
        mask = overlay[:, :, 3:4] / 255.0
        background[y:y+h, x:x+w] = (background[y:y+h, x:x+w] * (1.0 - mask) + overlay_img * mask).astype(np.uint8)

    def add_ripple(self, x, y, color=None, max_radius=40):
        """Appends a new ripple effect to the ripples list."""
        r_color = color if color is not None else self.accent_color
        self.ripples.append([int(x), int(y), 4, max_radius, r_color])

    def add_notification(self, text, color=None, duration=150):
        self.notifications.append({
            "text": text,
            "frames": duration,
            "max_frames": duration,
            "color": color or self.text_color
        })