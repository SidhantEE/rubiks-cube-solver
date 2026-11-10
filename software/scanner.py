"""Webcam color scanner for a 3x3 cube.

Shows a 3x3 grid overlay. Hold each face up to the camera in the order the
on-screen prompt asks for and press SPACE to capture it. Press Q to quit.

Orientation matters for Kociemba. Scan with WHITE on top (U) and GREEN facing
you (F):
  U: white center, green facing down toward you
  R, F, L, B: rotate the whole cube around the vertical axis, white stays on top
  D: yellow center, green at the top of the image
"""

import cv2
import numpy as np

FACE_ORDER = ["U", "R", "F", "D", "L", "B"]
FACE_HINTS = {
    "U": "white center, green toward the bottom",
    "R": "red center, white on top",
    "F": "green center, white on top",
    "D": "yellow center, green toward the top",
    "L": "orange center, white on top",
    "B": "blue center, white on top",
}

GRID_SIZE = 240  # pixel size of the overlay square
SAMPLE = 14      # half-width of the sample patch at each sticker center


def sticker_centers(frame_w, frame_h):
    x0 = (frame_w - GRID_SIZE) // 2
    y0 = (frame_h - GRID_SIZE) // 2
    cell = GRID_SIZE // 3
    return [(x0 + cell * c + cell // 2, y0 + cell * r + cell // 2)
            for r in range(3) for c in range(3)], (x0, y0, cell)


def sample_face(frame):
    """Return 9 mean colors (Lab) in reading order."""
    h, w = frame.shape[:2]
    centers, _ = sticker_centers(w, h)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    out = []
    for (x, y) in centers:
        patch = lab[y - SAMPLE:y + SAMPLE, x - SAMPLE:x + SAMPLE].reshape(-1, 3)
        out.append(np.median(patch, axis=0))
    return out


def draw_overlay(frame, face, captured):
    h, w = frame.shape[:2]
    _, (x0, y0, cell) = sticker_centers(w, h)
    for i in range(4):
        cv2.line(frame, (x0 + i * cell, y0), (x0 + i * cell, y0 + 3 * cell), (255, 255, 255), 2)
        cv2.line(frame, (x0, y0 + i * cell), (x0 + 3 * cell, y0 + i * cell), (255, 255, 255), 2)
    msg = f"Face {face} ({len(captured) + 1}/6): {FACE_HINTS[face]}  [SPACE]=capture"
    cv2.putText(frame, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)


def classify(faces_lab):
    """Assign each sticker to the face whose CENTER color is nearest (in Lab).

    Using the six centers as references adapts to your lighting automatically.
    Returns the 54-char facelet string in URFDLB order.
    """
    centers = {f: faces_lab[f][4] for f in FACE_ORDER}
    result = []
    for f in FACE_ORDER:
        for color in faces_lab[f]:
            best = min(FACE_ORDER, key=lambda k: np.linalg.norm(color - centers[k]))
            result.append(best)
    return "".join(result)


def scan(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {camera_index}")

    faces_lab = {}
    try:
        for face in FACE_ORDER:
            while True:
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("Camera read failed")
                view = frame.copy()
                draw_overlay(view, face, faces_lab)
                cv2.imshow("Cube scanner", view)
                key = cv2.waitKey(1) & 0xFF
                if key == ord(" "):
                    faces_lab[face] = sample_face(frame)
                    break
                if key == ord("q"):
                    raise KeyboardInterrupt
    finally:
        cap.release()
        cv2.destroyAllWindows()

    state = classify(faces_lab)
    counts = {f: state.count(f) for f in FACE_ORDER}
    if any(c != 9 for c in counts.values()):
        raise ValueError(f"Color scan looks wrong (each color should appear 9 times): {counts}")
    return state


if __name__ == "__main__":
    print(scan())
