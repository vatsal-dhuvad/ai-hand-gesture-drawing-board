# AI Hand Gesture Drawing Board

Draw in the air using your hand and browser camera. This deploy-friendly version uses Streamlit for the page and MediaPipe Hands JavaScript in the browser for live hand tracking and drawing.

## Features

- Live browser camera inside Streamlit
- Hand landmark detection using MediaPipe Hands JavaScript
- Air drawing with index finger
- Pencil, eraser, line, rectangle, and circle tools
- Color picker with six colors
- Adjustable pencil and eraser size
- Gesture-based clear, erase, and color change
- Download drawing result as PNG
- Separate local OpenCV script included for laptop-only demos

## Gesture Controls

- 1 finger: draw, erase, or preview selected shape
- 2 fingers: move without drawing and finish shape
- 3 fingers: change color
- 4 fingers: clear canvas
- 5 fingers: erase

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then click **Start** in the camera panel and allow camera permission.

## Streamlit Cloud Deployment

Upload these files to GitHub:

- `app.py`
- `gesture_air_canvas.py`
- `requirements.txt`
- `runtime.txt`
- `.gitignore`
- `LICENSE`
- `README.md`

Deploy on Streamlit Community Cloud with:

- Main file path: `app.py`
- Any supported Python version

Camera access works on localhost or HTTPS deployed links.

This deploy version only needs `streamlit` in `requirements.txt`. Camera and hand detection run in the browser through JavaScript, so Streamlit Cloud does not need to install OpenCV, MediaPipe, AV, or WebRTC Python packages.

## Local OpenCV Window Version

The file `gesture_air_canvas.py` opens a separate OpenCV desktop window. Use this only for local laptop demos:

```bash
python gesture_air_canvas.py
```

Saved images go into the `saved_drawings` folder.
