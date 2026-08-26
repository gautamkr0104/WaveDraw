# HaloScribe

**A gesture-controlled digital painting application that lets you draw in mid-air using your webcam and hand tracking.**

HaloScribe uses your webcam as input, tracks your hand via MediaPipe, and translates finger gestures into brush strokes, tool selections, and UI interactions — all without touching a mouse or keyboard. It renders a floating HUD over the live video feed, so you're literally painting on your camera view.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Gesture-Based Drawing** | Raise one finger to draw, two fingers to navigate the UI, three for undo, four for redo, and a thumbs-up to save — all detected in real-time. |
| **5 Brush Engines** | Hard (solid), Soft (blurred edge), Neon (glowing core), Watercolor (translucent glaze), and Pencil (graphite texture), each with speed-adaptive calligraphic scaling. |
| **Real-Time Coordinate Smoothing** | Dual 1-Euro adaptive filters stabilize hand jitter, and linear segment interpolation fills gaps during fast movements to prevent broken strokes. |
| **HSB Color Picker** | A donut-style hue ring with an inner saturation-value square — drag to pick any color. Recent and favorite palettes are one hover away. |
| **Shape Tools** | Draw lines, rectangles, and circles by holding the draw gesture and moving your hand. Shapes are completed when you release. |
| **Full Undo/Redo** | A 30-state history stack with both gesture and keyboard shortcuts. |
| **Export to Paper** | Saved drawings are composited onto a clean beige paper background and timestamped to `outputs/drawings/`. |
| **Hover Confirmation Timer** | UI elements require a ~0.7s dwell-to-click, preventing accidental selections. A radial progress arc shows the countdown. |
| **Ripple & Notification FX** | Animated ripple effects on selection and fade-in notification banners for every action. |
| **FPS Counter** | Real-time performance readout in the top-left corner. |

---

## 🖐️ Hand Gestures

All gestures are performed with your right hand in front of the webcam.

| Gesture | Action | Mode |
|---|---|---|
| ☝️ Index finger up | **Draw** | Brush/Eraser/Shape stroke |
| ✌️ Index + Middle fingers up | **Select / Navigate** | Hover over UI elements to interact |
| 🤟 Index + Middle + Ring fingers up | **Undo** | Hold to trigger once |
| 🖖 Index + Middle + Ring + Pinky up | **Redo** | Hold to trigger once |
| 👍 Thumb up | **Save** | Composites drawing to a PNG and saves it |

**Drawing mode** activates brush, eraser, or shape tools depending on the selected tool.
**Select mode** moves a crosshair cursor — hover over a UI element for ~0.7 seconds to confirm a click (shown by a radial progress arc).

---

## 🖌️ Brush Engines

| Brush | Behavior |
|---|---|
| **Hard** | Solid `cv2.LINE_AA` stroke, speed-adaptive thickness (faster → thinner). |
| **Soft** | Gaussian-blurred mask blended via alpha compositing for feathered edges. |
| **Neon** | Two-pass: wide blurred glow layer + sharp white core line on top. |
| **Watercolor** | Low-opacity (16%) translucent glaze — strokes build up color with repeated passes. |
| **Pencil** | Narrow graphite-like overlay (55% opacity) simulating pencil texture. |

All non-hard brushes use localized ROI-based rendering — only the region around the current stroke is blurred, keeping performance high.

---

## 🖥️ Interface Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  FPS: 30   [Brush][Eraser][Line][Rect][Circ][Undo][Redo][Save]  │
│                                                                  │
│ ┌──────┐                                          ┌──────────┐  │
│ │ SIZE │                                          │  COLOR   │  │
│ │  ●   │                                          │  SELECTOR│  │
│ │  │   │                                          │  ┌─────┐ │  │
│ │  │   │                                          │  │HUE  │ │  │
│ │ 8px │                                          │  │RING │ │  │
│ │      │                                          │  └─────┘ │  │
│ │ [H]  │                                          │  RGB/HX  │  │
│ │ [S]  │                                          │ RECENTS  │  │
│ │ [N]  │                                          │ FAVORITES│  │
│ │ [W]  │                                          └──────────┘  │
│ │ [P]  │                                                        │
│ └──────┘                                                        │
│        TOOL: BRUSH (HARD)  ● #9FAF90  SIZE: 8px                 │
└──────────────────────────────────────────────────────────────────┘
```

- **Top Bar** — Tool selection (brush, eraser, line, rectangle, circle, undo, redo, save)
- **Left Panel** — Brush size slider + brush type selector (H/S/N/W/P)
- **Right Panel** — HSV color picker donut, RGB/HEX readout, recent colors, favorite palette
- **Bottom Bar** — Current tool, color, and size readout

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Z` | Undo |
| `Y` | Redo |
| `C` | Clear canvas |
| `Q` | Quit |

---

## 🏗️ Project Structure

```
HaloScribe/
├── main.py              # Application entry point — camera loop, gesture dispatch, compositing
├── hand_tracker.py      # MediaPipe hand landmark extraction and finger-state detection
├── tools.py             # CanvasManager — drawing engine, brush types, shape tools, undo/redo
├── ui.py                # UIManager — HUD panels, color picker, notifications, cursor, effects
├── utils.py             # OneEuroFilter, CoordinateSmoother, hex_to_bgr, drawing helpers
├── generate_assets.py   # Procedural icon generation (brush, eraser, save) with Pillow glow FX
├── requirements.txt     # Python dependencies
├── run.bat              # Windows quick-launch script
├── assets/              # Generated PNG icons (brush.png, eraser.png, save.png)
└── outputs/drawings/    # Saved drawings (timestamped PNGs on beige paper)
```

---

## 🛠️ Tech Stack

| Library | Role |
|---|---|
| **OpenCV** | Camera capture, image processing, drawing, GUI window |
| **MediaPipe** | Real-time hand landmark detection and tracking |
| **NumPy** | Canvas arrays, alpha blending, HSV color math |
| **Pillow** | Procedural icon generation with glow effects |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A webcam
- Windows, macOS, or Linux

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd HaloScribe

# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

### Generate Assets

Run this once to create the toolbar icons:

```bash
python generate_assets.py
```

### Run

```bash
python main.py
```

Or on Windows, double-click `run.bat`.

---

## 💾 How Saving Works

When you trigger a save (thumbs-up gesture, the save button, or hovering for 0.7s):

1. The current canvas is composited onto a clean beige paper background (`#F7F4EF`)
2. The result is saved as a timestamped PNG: `outputs/drawings/HaloScribe_YYYYMMDD_HHMMSS.png`

---

## 📐 Architecture Overview

1. **Camera Capture** — Frames are captured at 1280×720, flipped horizontally for mirror view.
2. **Hand Tracking** — MediaPipe extracts 21 hand landmarks per frame.
3. **Gesture Classification** — Finger states (`fingers_up()`) map to modes: `draw`, `select`, `undo`, `redo`, `save`, or `idle`.
4. **Coordinate Smoothing** — Raw index-finger tip coordinates pass through dual 1-Euro filters to eliminate jitter.
5. **Stroke Rendering** — In draw mode, interpolated segments are rendered onto an off-screen canvas using the active brush engine.
6. **HUD Compositing** — The canvas is alpha-composited onto the webcam frame, then the UI panels are drawn on top.
7. **Effects Layer** — Ripples, notifications, and the cursor indicator are rendered last.

---

## 📜 License

This project is for educational and personal use. See the repository for licensing details.

---

<p align="center"><i>Built with OpenCV, MediaPipe, and a lot of hand waving.</i></p>
