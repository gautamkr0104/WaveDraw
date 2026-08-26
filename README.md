# HaloScribe

HaloScribe is a gesture-controlled drawing application built with Python, OpenCV, and MediaPipe. It uses hand-tracking to let you paint, select tools, and customize brushes directly in front of your webcam.

## Features

- **Stabilized Drawing**: Uses a 1-Euro filter and linear segment interpolation to reduce hand jitter and prevent broken lines during fast movements.
- **UI HUD**: A minimal, Pinterest-inspired interface featuring float panels, an HSV color picker donut, a brush size slider, and brush presets.
- **Brush Engines**: Supports 5 brush types: Hard (solid), Soft (blurred edge), Neon (glowing core), Watercolor (translucent glaze), and Pencil (graphite texture).
- **History & Saving**: Undo/redo stack support and canvas export to a beige paper background.

## Interface & Controls

### Hand Gestures
- **Draw**: Raise index finger only.
- **Select / Move Cursor**: Raise index and middle fingers together. Hover over UI elements for ~0.7 seconds to click them.
- **Undo**: Raise index, middle, and ring fingers.
- **Redo**: Raise index, middle, ring, and pinky fingers.
- **Save**: Raise thumb only (thumbs up gesture).

### Keyboard Shortcuts
- `C` - Clear canvas
- `Z` - Undo
- `Y` - Redo
- `Q` - Quit

## Setup

First, activate the virtual environment and install the dependencies:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running the App

Start the main loop:

```bash
python main.py
```
you can just double click the run.bat file tooo to run the project