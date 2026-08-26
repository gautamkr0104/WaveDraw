import cv2
import numpy as np
import os
import math
from hand_tracker import HandTracker
from tools import CanvasManager
from ui import UIManager
from utils import CoordinateSmoother

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    success, test_frame = cap.read()
    if not success:
        print("Error: Could not initialize camera.")
        return
        
    h, w, _ = test_frame.shape
    print(f"HaloScribe active. Stream dimensions: {w}x{h}")
    
    # Establish a virtual resolution of 1280x720 for consistent UI rendering
    target_w, target_h = 1280, 720
    if w != target_w or h != target_h:
        print(f"Adapting stream aspect ratio. Canvas Virtual Resolution: {target_w}x{target_h}")
        
    tracker = HandTracker(detection_con=0.82, track_con=0.70)
    canvas_manager = CanvasManager(width=target_w, height=target_h)
    ui_manager = UIManager(width=target_w, height=target_h)
    smoother = CoordinateSmoother(mincutoff=0.80, beta=0.03)
    
    xp, yp = 0, 0
    shape_start_pt = None
    shape_last_pt = None
    previous_gesture_mode = 'idle'
    
    # Hold-gesture state flags
    undo_gesture_held = False
    redo_gesture_held = False
    save_gesture_held = False
    
    # Hover selection confirm states
    current_hover_type = None
    current_hover_val = None
    hover_frames = 0
    
    # FPS ticking metrics
    fps_start_time = cv2.getTickCount()
    fps_counter = 0
    fps_val = 30
    
    ui_manager.sync_picker_to_color(canvas_manager.current_color)
    
    window_name = "HaloScribe"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    ui_manager.add_notification("WELCOME TO HaloScribe", color=ui_manager.accent_color, duration=150)
    ui_manager.add_notification("Hold gestures: 3 fingers = Undo | 4 fingers = Redo | Thumbs up = Save", color=ui_manager.text_color, duration=220)
    
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break
            
        img = cv2.flip(img, 1)
        img = cv2.resize(img, (target_w, target_h))
        
        # Calculate real-time FPS
        fps_counter += 1
        elapsed = (cv2.getTickCount() - fps_start_time) / cv2.getTickFrequency()
        if elapsed >= 1.0:
            fps_val = int(fps_counter / elapsed)
            fps_counter = 0
            fps_start_time = cv2.getTickCount()
            
        lm_list = tracker.get_landmarks(img, draw=False)
        
        gesture_mode = 'idle'
        cursor_x, cursor_y = 0, 0
        click_progress = 0.0
        
        if len(lm_list) != 0:
            x_raw, y_raw = lm_list[8][1], lm_list[8][2]
            
            # Stabilize coordinates using adaptive One-Euro Filter
            cursor_x, cursor_y = smoother.smooth(x_raw, y_raw)
            fingers = tracker.fingers_up()
            
            # Gesture mapping conditions
            if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                gesture_mode = 'save'
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                # Disregard thumb state for more reliable four-finger redo gesture
                gesture_mode = 'redo'
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                # Disregard thumb state for more reliable three-finger undo gesture
                gesture_mode = 'undo'
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                gesture_mode = 'select'
            elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                gesture_mode = 'draw'
            
            if gesture_mode != 'undo':
                undo_gesture_held = False
            if gesture_mode != 'redo':
                redo_gesture_held = False
            if gesture_mode != 'save':
                save_gesture_held = False
                
            if gesture_mode == 'draw':
                # Block drawing within HUD bounds
                if ui_manager.is_inside_hud(cursor_x, cursor_y):
                    xp, yp = 0, 0
                else:
                    if canvas_manager.current_tool in ['brush', 'eraser']:
                        if xp == 0 and yp == 0:
                            canvas_manager.save_state()
                            xp, yp = cursor_x, cursor_y
                            
                        # Sub-pixel coordinate interpolation for continuous rendering
                        dist = math.hypot(cursor_x - xp, cursor_y - yp)
                        if dist > 5:
                            steps = int(dist / 3)
                            for step in range(1, steps + 1):
                                t_int = step / steps
                                ix = int(xp * (1.0 - t_int) + cursor_x * t_int)
                                iy = int(yp * (1.0 - t_int) + cursor_y * t_int)
                                canvas_manager.draw_freehand((xp, yp), (ix, iy))
                                xp, yp = ix, iy
                        else:
                            canvas_manager.draw_freehand((xp, yp), (cursor_x, cursor_y))
                            xp, yp = cursor_x, cursor_y
                    else:
                        if shape_start_pt is None:
                            canvas_manager.save_state()
                            shape_start_pt = (cursor_x, cursor_y)
                        shape_last_pt = (cursor_x, cursor_y)
                        
            elif gesture_mode == 'select':
                xp, yp = 0, 0
                smoother.reset()
                
                hover = ui_manager.check_hud_hover(cursor_x, cursor_y)
                
                # 0.7s hover selection confirmation timer
                if hover['type'] in ['tool', 'recent_color', 'favorite_color', 'brush_type']:
                    if hover['type'] == current_hover_type and hover['value'] == current_hover_val:
                        hover_frames += 1
                    else:
                        current_hover_type = hover['type']
                        current_hover_val = hover['value']
                        hover_frames = 0
                        
                    click_progress = min(1.0, hover_frames / 20.0)
                    
                    if hover_frames >= 20:
                        ui_manager.add_ripple(cursor_x, cursor_y)
                        
                        if hover['type'] == 'tool':
                            val = hover['value']
                            if val == 'undo':
                                if canvas_manager.undo():
                                    ui_manager.add_notification("UNDO COMPLETED", ui_manager.accent_color)
                                else:
                                    ui_manager.add_notification("HISTORY EMPTY", (50, 50, 220))
                            elif val == 'redo':
                                if canvas_manager.redo():
                                    ui_manager.add_notification("REDO COMPLETED", ui_manager.accent_color)
                                else:
                                    ui_manager.add_notification("REDO STACK EMPTY", (50, 50, 220))
                            elif val == 'save':
                                saved_path = canvas_manager.save_drawing()
                                ui_manager.add_notification(f"SAVED: {os.path.basename(saved_path)}", ui_manager.accent_color)
                            else:
                                canvas_manager.select_tool(val)
                                ui_manager.add_notification(f"TOOL: {val.upper()}", ui_manager.accent_color)
                                
                        elif hover['type'] == 'recent_color':
                            c_val = ui_manager.recent_colors[hover['value']]
                            canvas_manager.set_custom_color(c_val)
                            ui_manager.sync_picker_to_color(c_val)
                            ui_manager.add_notification("COLOR SELECTED", c_val)
                            
                        elif hover['type'] == 'favorite_color':
                            c_val = ui_manager.favorite_colors[hover['value']]
                            canvas_manager.set_custom_color(c_val)
                            ui_manager.sync_picker_to_color(c_val)
                            ui_manager.add_notification("COLOR SELECTED", c_val)
                            
                        elif hover['type'] == 'brush_type':
                            val = hover['value']
                            canvas_manager.current_brush_type = val
                            ui_manager.add_notification(f"BRUSH: {val.upper()}", ui_manager.accent_color)
                            
                        hover_frames = 0
                        current_hover_type = None
                        current_hover_val = None
                else:
                    hover_frames = 0
                    current_hover_type = None
                    current_hover_val = None
                    
                    # Instant tracking for Hue ring and S-V square sliders
                    if hover['type'] == 'color_picker_hue':
                        hx, hy = hover['value']
                        # Hue angle relative to donut center
                        dx = hx - ui_manager.donut_cx
                        dy = hy - ui_manager.donut_cy
                        angle = math.atan2(dy, dx) + math.pi
                        h = int(angle / (2.0 * math.pi) * 179)
                        
                        ui_manager.selected_hue = h
                        ui_manager.update_sv_gradient()
                        ui_manager.hue_indicator = (hx, hy)
                        
                        # Re-sample S-V square based on current indicator
                        sy = np.clip(ui_manager.sv_indicator[1] - ui_manager.sv_y1, 0, ui_manager.sv_half * 2 - 1)
                        sx = np.clip(ui_manager.sv_indicator[0] - ui_manager.sv_x1, 0, ui_manager.sv_half * 2 - 1)
                        pct_s = sx / float(ui_manager.sv_half * 2 - 1)
                        pct_v = 1.0 - sy / float(ui_manager.sv_half * 2 - 1)
                        
                        bgr = cv2.cvtColor(np.uint8([[[h, int(pct_s * 255), int(pct_v * 255)]]]), cv2.COLOR_HSV2BGR)[0][0]
                        canvas_manager.set_custom_color(bgr)
                        
                    elif hover['type'] == 'color_picker_sv':
                        hx, hy = hover['value']
                        pct_s = (hx - ui_manager.sv_x1) / float(ui_manager.sv_half * 2)
                        pct_v = 1.0 - (hy - ui_manager.sv_y1) / float(ui_manager.sv_half * 2)
                        
                        pct_s = np.clip(pct_s, 0.0, 1.0)
                        pct_v = np.clip(pct_v, 0.0, 1.0)
                        
                        h = ui_manager.selected_hue
                        s = int(pct_s * 255)
                        v = int(pct_v * 255)
                        
                        bgr = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
                        canvas_manager.set_custom_color(bgr)
                        ui_manager.sv_indicator = (hx, hy)
                        
                    elif hover['type'] == 'slider':
                        new_size = int(2 + hover['value'] * 38)
                        canvas_manager.set_brush_size(new_size)
                        
            elif gesture_mode == 'undo':
                xp, yp = 0, 0
                smoother.reset()
                if not undo_gesture_held:
                    undo_gesture_held = True
                    if canvas_manager.undo():
                        ui_manager.add_notification("UNDO (GESTURE)", ui_manager.accent_color)
                    else:
                        ui_manager.add_notification("HISTORY EMPTY", (50, 50, 220))
                        
            elif gesture_mode == 'redo':
                xp, yp = 0, 0
                smoother.reset()
                if not redo_gesture_held:
                    redo_gesture_held = True
                    if canvas_manager.redo():
                        ui_manager.add_notification("REDO (GESTURE)", ui_manager.accent_color)
                    else:
                        ui_manager.add_notification("REDO STACK EMPTY", (50, 50, 220))
                        
            elif gesture_mode == 'save':
                xp, yp = 0, 0
                smoother.reset()
                if not save_gesture_held:
                    save_gesture_held = True
                    saved_path = canvas_manager.save_drawing()
                    ui_manager.add_notification(f"SAVED: {os.path.basename(saved_path)}", ui_manager.accent_color)
                    
            else:
                xp, yp = 0, 0
                smoother.reset()
        else:
            xp, yp = 0, 0
            smoother.reset()
            undo_gesture_held = False
            redo_gesture_held = False
            save_gesture_held = False
            hover_frames = 0
            current_hover_type = None
            current_hover_val = None
            
        if gesture_mode != 'draw' and shape_start_pt is not None:
            if shape_last_pt is not None:
                canvas_manager.draw_shape(shape_start_pt, shape_last_pt)
                ui_manager.add_notification("SHAPE COMPLETED", ui_manager.accent_color)
                ui_manager.add_ripple(shape_last_pt[0], shape_last_pt[1], ui_manager.accent_color)
            shape_start_pt = None
            shape_last_pt = None
            
        if previous_gesture_mode == 'draw' and gesture_mode != 'draw':
            if canvas_manager.current_tool != 'eraser':
                current_color = canvas_manager.current_color
                if current_color in ui_manager.recent_colors:
                    ui_manager.recent_colors.remove(current_color)
                ui_manager.recent_colors.insert(0, current_color)
                if len(ui_manager.recent_colors) > 5:
                    ui_manager.recent_colors.pop()
                    
        # Alpha compositing BGR canvas onto webcam frame
        gray_canvas = cv2.cvtColor(canvas_manager.canvas, cv2.COLOR_BGR2GRAY)
        _, mask_inv = cv2.threshold(gray_canvas, 5, 255, cv2.THRESH_BINARY_INV)
        mask_inv = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR)
        
        img = cv2.bitwise_and(img, mask_inv)
        img = cv2.bitwise_or(img, canvas_manager.canvas)
        
        if shape_start_pt is not None and shape_last_pt is not None:
            canvas_manager.draw_shape(shape_start_pt, shape_last_pt, target_canvas=img)
            
        ui_manager.draw_ui(img, canvas_manager, fps=fps_val)
        ui_manager.draw_effects(img)
        
        if len(lm_list) != 0:
            ui_manager.draw_cursor(img, cursor_x, cursor_y, gesture_mode, click_progress)
            
        cv2.imshow(window_name, img)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas_manager.clear()
            ui_manager.add_notification("CANVAS CLEARED")
        elif key == ord('z'):
            if canvas_manager.undo():
                ui_manager.add_notification("UNDO")
            else:
                ui_manager.add_notification("HISTORY EMPTY", (50, 50, 220))
        elif key == ord('y'):
            if canvas_manager.redo():
                ui_manager.add_notification("REDO")
            else:
                ui_manager.add_notification("REDO STACK EMPTY", (50, 50, 220))
                
        previous_gesture_mode = gesture_mode
        
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
