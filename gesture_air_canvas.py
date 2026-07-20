import json
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "gesture_config.json"
SAVE_DIR = PROJECT_DIR / "saved_drawings"

DEFAULT_CONFIG = {
    "camera_index": 0,
    "brush_size": 8,
    "eraser_size": 55,
    "start_color": "Blue",
    "mirror_camera": True,
    "max_undo": 15,
}

COLORS = {
    "Blue": (255, 80, 20),
    "Green": (60, 190, 70),
    "Red": (40, 40, 230),
    "Yellow": (40, 220, 240),
    "Purple": (220, 90, 210),
    "White": (255, 255, 255),
}

TOOLS = ["Pencil", "Line", "Rectangle", "Circle", "Eraser"]


def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            user_config = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config


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

    return fingers, sum(fingers)


def point_from_landmark(hand_landmarks, landmark_id, width, height):
    landmark = hand_landmarks.landmark[landmark_id]
    return int(landmark.x * width), int(landmark.y * height)


def draw_shape(canvas, tool, start, end, color, thickness):
    if start is None or end is None:
        return

    if tool == "Line":
        cv2.line(canvas, start, end, color, thickness)
    elif tool == "Rectangle":
        cv2.rectangle(canvas, start, end, color, thickness)
    elif tool == "Circle":
        radius = int(((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5)
        cv2.circle(canvas, start, radius, color, thickness)


def preview_shape(frame, tool, start, end, color, thickness):
    if tool not in {"Line", "Rectangle", "Circle"}:
        return frame

    preview = frame.copy()
    draw_shape(preview, tool, start, end, color, thickness)
    return cv2.addWeighted(preview, 0.75, frame, 0.25, 0)


def push_history(history, canvas, max_undo):
    history.append(canvas.copy())
    if len(history) > max_undo:
        history.pop(0)


def save_image(image, prefix):
    SAVE_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SAVE_DIR / f"{prefix}_{timestamp}.png"
    cv2.imwrite(str(path), image)
    return path


def draw_top_panel(frame, tool, color_name, brush_size, eraser_size, fingers, history_count, message):
    height, width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 118), (18, 24, 38), -1)
    frame[:] = cv2.addWeighted(overlay, 0.88, frame, 0.12, 0)

    cv2.putText(frame, "AI Hand Gesture Drawing Board", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
    cv2.putText(
        frame,
        f"Tool: {tool} | Color: {color_name} | Brush: {brush_size} | Eraser: {eraser_size} | Fingers: {fingers} | Undo: {history_count}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (230, 236, 245),
        1,
    )
    cv2.putText(
        frame,
        "Gestures: 1 draw/shape, 2 move, 3 color, 4 clear, 5 erase | Keys: F/L/R/O/E, +/- size, U undo, S save, D canvas, C clear, Q quit",
        (20, 101),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (190, 205, 220),
        1,
    )

    x = width - 330
    for name, color in COLORS.items():
        cv2.circle(frame, (x, 34), 12, color, -1)
        if name == color_name:
            cv2.circle(frame, (x, 34), 16, (255, 255, 255), 2)
        x += 45

    if message:
        cv2.putText(frame, message, (20, height - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (35, 240, 180), 2)


def main():
    config = load_config()
    camera_index = int(config["camera_index"])
    brush_size = int(config["brush_size"])
    eraser_size = int(config["eraser_size"])
    mirror_camera = bool(config["mirror_camera"])
    max_undo = int(config["max_undo"])

    color_names = list(COLORS.keys())
    color_name = config["start_color"] if config["start_color"] in COLORS else "Blue"
    color_index = color_names.index(color_name)
    color = COLORS[color_name]
    tool = "Pencil"

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Camera could not be opened. Try camera_index 1 in the Streamlit settings.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    canvas = None
    history = []
    previous_point = None
    stroke_active = False
    shape_start = None
    shape_last = None
    color_cooldown = 0
    clear_cooldown = 0
    last_message = ""

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.72, min_tracking_confidence=0.72) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if mirror_camera:
                frame = cv2.flip(frame, 1)

            height, width = frame.shape[:2]
            if canvas is None:
                canvas = np.zeros((height, width, 3), dtype=np.uint8)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            fingers_count = 0
            current_point = None
            display = frame.copy()

            if result.multi_hand_landmarks and result.multi_handedness:
                hand_landmarks = result.multi_hand_landmarks[0]
                handedness = result.multi_handedness[0].classification[0].label
                _, fingers_count = count_fingers(hand_landmarks, handedness)
                current_point = point_from_landmark(hand_landmarks, 8, width, height)
                mp_draw.draw_landmarks(display, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                cv2.circle(display, current_point, 10, color if tool != "Eraser" else (255, 255, 255), -1)

                if color_cooldown > 0:
                    color_cooldown -= 1
                if clear_cooldown > 0:
                    clear_cooldown -= 1

                if fingers_count == 1 and current_point:
                    if tool in {"Pencil", "Eraser"}:
                        if not stroke_active:
                            push_history(history, canvas, max_undo)
                            stroke_active = True
                            previous_point = current_point

                        draw_color = (0, 0, 0) if tool == "Eraser" else color
                        draw_size = eraser_size if tool == "Eraser" else brush_size
                        cv2.line(canvas, previous_point, current_point, draw_color, draw_size)
                        previous_point = current_point
                    else:
                        if shape_start is None:
                            push_history(history, canvas, max_undo)
                            shape_start = current_point
                        shape_last = current_point
                        display = preview_shape(display, tool, shape_start, shape_last, color, brush_size)

                elif fingers_count == 2:
                    previous_point = None
                    stroke_active = False
                    if shape_start and shape_last and tool in {"Line", "Rectangle", "Circle"}:
                        draw_shape(canvas, tool, shape_start, shape_last, color, brush_size)
                        shape_start = None
                        shape_last = None

                elif fingers_count == 3 and color_cooldown == 0:
                    color_index = (color_index + 1) % len(color_names)
                    color_name = color_names[color_index]
                    color = COLORS[color_name]
                    color_cooldown = 18
                    last_message = f"Color changed to {color_name}"
                    previous_point = None
                    stroke_active = False

                elif fingers_count == 4 and clear_cooldown == 0:
                    push_history(history, canvas, max_undo)
                    canvas[:] = 0
                    clear_cooldown = 25
                    last_message = "Canvas cleared"
                    previous_point = None
                    stroke_active = False
                    shape_start = None
                    shape_last = None

                elif fingers_count == 5 and current_point:
                    if not stroke_active:
                        push_history(history, canvas, max_undo)
                        stroke_active = True
                        previous_point = current_point
                    cv2.circle(canvas, current_point, eraser_size, (0, 0, 0), -1)
                    tool = "Eraser"
                    previous_point = current_point

                else:
                    previous_point = None
                    stroke_active = False
                    if shape_start and shape_last and tool in {"Line", "Rectangle", "Circle"}:
                        draw_shape(canvas, tool, shape_start, shape_last, color, brush_size)
                    shape_start = None
                    shape_last = None
            else:
                previous_point = None
                stroke_active = False
                if shape_start and shape_last and tool in {"Line", "Rectangle", "Circle"}:
                    draw_shape(canvas, tool, shape_start, shape_last, color, brush_size)
                shape_start = None
                shape_last = None

            mask = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            _, mask_inv = cv2.threshold(mask, 20, 255, cv2.THRESH_BINARY_INV)
            frame_bg = cv2.bitwise_and(display, display, mask=mask_inv)
            drawing_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
            final = cv2.add(frame_bg, drawing_fg)

            draw_top_panel(final, tool, color_name, brush_size, eraser_size, fingers_count, len(history), last_message)
            cv2.imshow("Hand Gesture Drawing Board", final)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("f"):
                tool = "Pencil"
                last_message = "Tool changed to Pencil"
            elif key == ord("l"):
                tool = "Line"
                last_message = "Tool changed to Line"
            elif key == ord("r"):
                tool = "Rectangle"
                last_message = "Tool changed to Rectangle"
            elif key == ord("o"):
                tool = "Circle"
                last_message = "Tool changed to Circle"
            elif key == ord("e"):
                tool = "Eraser"
                last_message = "Tool changed to Eraser"
            elif key in (ord("+"), ord("=")):
                brush_size = min(40, brush_size + 2)
                last_message = f"Brush size {brush_size}"
            elif key == ord("-"):
                brush_size = max(2, brush_size - 2)
                last_message = f"Brush size {brush_size}"
            elif key == ord("["):
                eraser_size = max(20, eraser_size - 5)
                last_message = f"Eraser size {eraser_size}"
            elif key == ord("]"):
                eraser_size = min(140, eraser_size + 5)
                last_message = f"Eraser size {eraser_size}"
            elif key == ord("u") and history:
                canvas = history.pop()
                last_message = "Undo done"
            elif key == ord("c"):
                push_history(history, canvas, max_undo)
                canvas[:] = 0
                last_message = "Canvas cleared"
            elif key == ord("s"):
                path = save_image(final, "camera_plus_drawing")
                last_message = f"Saved {path.name}"
            elif key == ord("d"):
                path = save_image(canvas, "drawing_only")
                last_message = f"Saved {path.name}"

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
