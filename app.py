import threading
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from mediapipe.python.solutions import drawing_utils as mp_draw
from mediapipe.python.solutions import hands as mp_hands
from streamlit_webrtc import RTCConfiguration, VideoProcessorBase, WebRtcMode, webrtc_streamer

try:
    import av
except ModuleNotFoundError:
    av = None


PROJECT_DIR = Path(__file__).resolve().parent
SAVE_DIR = PROJECT_DIR / "saved_drawings"
SAVE_DIR.mkdir(exist_ok=True)

COLORS = {
    "Blue": (255, 80, 20),
    "Green": (60, 190, 70),
    "Red": (40, 40, 230),
    "Yellow": (40, 220, 240),
    "Purple": (220, 90, 210),
    "White": (255, 255, 255),
}

SHAPE_TOOLS = {"Line", "Rectangle", "Circle"}


st.set_page_config(
    page_title="AI Hand Gesture Drawing Board",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
        }
        :root {
            --app-bg: #f3f6fb;
            --panel-bg: #ffffff;
            --ink: #111827;
            --muted: #4b5563;
            --border: #d8e0ec;
            --blue: #2563eb;
        }
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stHeader"] {
            background: var(--app-bg) !important;
            color: var(--ink) !important;
        }
        [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid var(--border);
        }
        h1, h2, h3, h4, p, label, span,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: var(--ink) !important;
            opacity: 1 !important;
        }
        .hero-title {
            color: var(--ink);
            font-size: 2.35rem;
            font-weight: 850;
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }
        .hero-subtitle {
            color: var(--muted);
            font-size: 1rem;
            margin-bottom: 1.2rem;
        }
        .info-box {
            background: #e8f5ee;
            border: 1px solid #b8e2c8;
            border-radius: 8px;
            color: #14532d;
            padding: 0.9rem 1rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.5rem 0 1rem;
        }
        .control-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.8rem;
            min-height: 92px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }
        .control-card strong {
            display: block;
            margin-bottom: 0.25rem;
            color: var(--ink);
        }
        .control-card span {
            color: var(--muted) !important;
            font-size: 0.92rem;
        }
        div[data-testid="stMetric"] {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        }
        div[data-testid="stMetric"] * {
            color: var(--ink) !important;
            opacity: 1 !important;
        }
        div[data-testid="stSlider"] *,
        div[data-testid="stSelectbox"] *,
        div[data-testid="stCheckbox"] *,
        div[data-testid="stButton"] * {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            opacity: 1 !important;
        }
        div[data-testid="stButton"] button {
            border-radius: 8px !important;
            font-weight: 800 !important;
            border: 1px solid #bfdbfe !important;
        }
        @media (max-width: 900px) {
            .control-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def count_fingers(hand_landmarks, handedness):
    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]
    landmarks = hand_landmarks.landmark
    fingers = []

    if handedness == "Right":
        fingers.append(landmarks[tips[0]].x < landmarks[pips[0]].x)
    else:
        fingers.append(landmarks[tips[0]].x > landmarks[pips[0]].x)

    for tip, pip in zip(tips[1:], pips[1:]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)

    return sum(fingers)


def point_from_landmark(hand_landmarks, landmark_id, width, height):
    landmark = hand_landmarks.landmark[landmark_id]
    return int(landmark.x * width), int(landmark.y * height)


def draw_shape(canvas, tool, start, end, color, thickness):
    if not start or not end:
        return
    if tool == "Line":
        cv2.line(canvas, start, end, color, thickness)
    elif tool == "Rectangle":
        cv2.rectangle(canvas, start, end, color, thickness)
    elif tool == "Circle":
        radius = int(((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5)
        cv2.circle(canvas, start, radius, color, thickness)


def draw_panel(frame, tool, color_name, brush_size, eraser_size, fingers_count):
    height, width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 96), (18, 24, 38), -1)
    frame[:] = cv2.addWeighted(overlay, 0.86, frame, 0.14, 0)

    cv2.putText(frame, "AI Hand Gesture Drawing Board", (18, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(
        frame,
        f"Tool: {tool} | Color: {color_name} | Brush: {brush_size} | Eraser: {eraser_size} | Fingers: {fingers_count}",
        (18, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (230, 236, 245),
        1,
    )

    x = max(18, width - 315)
    for name, color in COLORS.items():
        cv2.circle(frame, (x, height - 28), 11, color, -1)
        if name == color_name:
            cv2.circle(frame, (x, height - 28), 15, (255, 255, 255), 2)
        x += 45


def image_gallery():
    return sorted(SAVE_DIR.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)


class GestureDrawingProcessor(VideoProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()
        self.settings = {
            "tool": "Pencil",
            "color_name": "Blue",
            "brush_size": 8,
            "eraser_size": 55,
            "mirror": True,
        }
        self.canvas = None
        self.previous_point = None
        self.shape_start = None
        self.shape_last = None
        self.color_cooldown = 0
        self.clear_requested = False
        self.save_requested = False
        self.last_frame = None
        self.hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.72,
            min_tracking_confidence=0.72,
        )
        self.drawer = mp_draw
        self.hand_connections = mp_hands.HAND_CONNECTIONS

    def update_settings(self, settings):
        with self.lock:
            self.settings.update(settings)

    def request_clear(self):
        with self.lock:
            self.clear_requested = True

    def request_save(self):
        with self.lock:
            self.save_requested = True

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")

        with self.lock:
            settings = self.settings.copy()
            clear_requested = self.clear_requested
            save_requested = self.save_requested
            self.clear_requested = False
            self.save_requested = False

        if settings["mirror"]:
            image = cv2.flip(image, 1)

        height, width = image.shape[:2]
        if self.canvas is None or self.canvas.shape[:2] != image.shape[:2]:
            self.canvas = np.zeros_like(image)

        if clear_requested:
            self.canvas[:] = 0
            self.previous_point = None
            self.shape_start = None
            self.shape_last = None

        display = image.copy()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        tool = settings["tool"]
        color_name = settings["color_name"]
        color = COLORS[color_name]
        brush_size = int(settings["brush_size"])
        eraser_size = int(settings["eraser_size"])
        fingers_count = 0

        if result.multi_hand_landmarks and result.multi_handedness:
            hand_landmarks = result.multi_hand_landmarks[0]
            handedness = result.multi_handedness[0].classification[0].label
            fingers_count = count_fingers(hand_landmarks, handedness)
            point = point_from_landmark(hand_landmarks, 8, width, height)

            self.drawer.draw_landmarks(display, hand_landmarks, self.hand_connections)
            cv2.circle(display, point, 10, color if tool != "Eraser" else (255, 255, 255), -1)

            if self.color_cooldown > 0:
                self.color_cooldown -= 1

            if fingers_count == 1:
                if tool in SHAPE_TOOLS:
                    if self.shape_start is None:
                        self.shape_start = point
                    self.shape_last = point
                    preview = display.copy()
                    draw_shape(preview, tool, self.shape_start, self.shape_last, color, brush_size)
                    display = cv2.addWeighted(preview, 0.75, display, 0.25, 0)
                else:
                    draw_color = (0, 0, 0) if tool == "Eraser" else color
                    draw_size = eraser_size if tool == "Eraser" else brush_size
                    if self.previous_point is None:
                        self.previous_point = point
                    cv2.line(self.canvas, self.previous_point, point, draw_color, draw_size)
                    self.previous_point = point

            elif fingers_count == 2:
                self.previous_point = None
                if tool in SHAPE_TOOLS and self.shape_start and self.shape_last:
                    draw_shape(self.canvas, tool, self.shape_start, self.shape_last, color, brush_size)
                self.shape_start = None
                self.shape_last = None

            elif fingers_count == 3 and self.color_cooldown == 0:
                names = list(COLORS.keys())
                next_index = (names.index(color_name) + 1) % len(names)
                with self.lock:
                    self.settings["color_name"] = names[next_index]
                self.color_cooldown = 18
                self.previous_point = None

            elif fingers_count == 4:
                self.canvas[:] = 0
                self.previous_point = None
                self.shape_start = None
                self.shape_last = None

            elif fingers_count == 5:
                cv2.circle(self.canvas, point, eraser_size, (0, 0, 0), -1)
                self.previous_point = None
        else:
            self.previous_point = None
            if tool in SHAPE_TOOLS and self.shape_start and self.shape_last:
                draw_shape(self.canvas, tool, self.shape_start, self.shape_last, color, brush_size)
            self.shape_start = None
            self.shape_last = None

        mask = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask_inv = cv2.threshold(mask, 20, 255, cv2.THRESH_BINARY_INV)
        frame_bg = cv2.bitwise_and(display, display, mask=mask_inv)
        drawing_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
        final = cv2.add(frame_bg, drawing_fg)

        draw_panel(final, tool, color_name, brush_size, eraser_size, fingers_count)

        if save_requested:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(str(SAVE_DIR / f"gesture_drawing_{timestamp}.png"), final)

        self.last_frame = final.copy()
        return av.VideoFrame.from_ndarray(final, format="bgr24")


if av is None:
    st.error("The `av` package is missing. Add `av` to requirements.txt and reboot the app.")
    st.stop()

with st.sidebar:
    st.header("Drawing Settings")
    tool = st.selectbox("Tool", ["Pencil", "Line", "Rectangle", "Circle", "Eraser"])
    color_name = st.selectbox("Color", list(COLORS.keys()))
    brush_size = st.slider("Pencil / shape size", 2, 40, 8)
    eraser_size = st.slider("Eraser size", 20, 140, 55)
    mirror = st.checkbox("Mirror camera", value=True)

st.markdown('<div class="hero-title">AI Hand Gesture Drawing Board</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Draw in the air with your hand using live browser camera, OpenCV, and MediaPipe.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="info-box">Click Start below, allow camera permission, then use your hand in front of the camera. This version works inside Streamlit because it uses browser WebRTC camera.</div>',
    unsafe_allow_html=True,
)

metric_a, metric_b, metric_c, metric_d = st.columns(4)
metric_a.metric("Gesture Engine", "MediaPipe")
metric_b.metric("Drawing Tools", "5")
metric_c.metric("Colors", "6")
metric_d.metric("Camera", "WebRTC")

rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

ctx = webrtc_streamer(
    key="hand-gesture-drawing-board",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=rtc_configuration,
    video_processor_factory=GestureDrawingProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

if ctx.video_processor:
    ctx.video_processor.update_settings(
        {
            "tool": tool,
            "color_name": color_name,
            "brush_size": brush_size,
            "eraser_size": eraser_size,
            "mirror": mirror,
        }
    )

action_a, action_b = st.columns(2)
if action_a.button("Clear Canvas", use_container_width=True) and ctx.video_processor:
    ctx.video_processor.request_clear()
if action_b.button("Save Current Frame", use_container_width=True) and ctx.video_processor:
    ctx.video_processor.request_save()
    st.success("Save requested. It will appear in the gallery after the next camera frame.")

st.subheader("Gesture Controls")
st.markdown(
    """
    <div class="control-grid">
        <div class="control-card"><strong>1 finger</strong><span>Draw with pencil, erase, or preview a selected shape.</span></div>
        <div class="control-card"><strong>2 fingers</strong><span>Move without drawing and finish line, rectangle, or circle.</span></div>
        <div class="control-card"><strong>3 fingers</strong><span>Cycle to the next color.</span></div>
        <div class="control-card"><strong>4 fingers</strong><span>Clear the full canvas.</span></div>
        <div class="control-card"><strong>5 fingers</strong><span>Erase using your open hand.</span></div>
        <div class="control-card"><strong>Sidebar</strong><span>Pick tool, color, pencil size, eraser size, and mirror mode.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Saved Drawing Gallery")
images = image_gallery()
if not images:
    st.caption("No saved drawings yet. Click Save Current Frame after starting the camera.")
else:
    cols = st.columns(3)
    for index, image_path in enumerate(images[:9]):
        with cols[index % 3]:
            st.image(image_path, caption=image_path.name, use_container_width=True)
