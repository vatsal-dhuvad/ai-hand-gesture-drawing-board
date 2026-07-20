# AI Hand Gesture Drawing Board

Draw in the air using your hand and browser camera. This project uses Streamlit for the UI, WebRTC for live camera streaming, MediaPipe for hand landmark detection, and OpenCV for drawing.

## Features

- Live browser camera inside Streamlit
- Hand landmark detection using MediaPipe
- Air drawing with index finger
- Pencil, eraser, line, rectangle, and circle tools
- Color picker with six colors
- Adjustable pencil and eraser size
- Gesture-based clear, erase, and color change
- Save current camera frame with drawing
- Saved drawing gallery
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
- Python version: choose `3.11` from Advanced settings

Camera access works on localhost or HTTPS deployed links.

If your existing Streamlit app already deployed with Python 3.14, delete that app from Streamlit Cloud and deploy it again. Streamlit does not reliably change the Python version for an existing deployed app from a repo file.

## Local OpenCV Window Version

The file `gesture_air_canvas.py` opens a separate OpenCV desktop window. Use this only for local laptop demos:

```bash
python gesture_air_canvas.py
```

Saved images go into the `saved_drawings` folder.
