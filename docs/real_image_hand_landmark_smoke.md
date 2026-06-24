# Real-Image Hand Landmark Smoke Test

## Purpose

This recipe verifies the local image -> MediaPipe Tasks -> `HandLandmarkFrame`
JSON path used by `tabgen frames-to-landmarks`.

This is an advanced video smoke checkpoint, not the public MVP path. It only
checks that hand landmark extraction can run on a real image and produce the
project JSON shape. It does not validate fret-number inference, fretboard
calibration accuracy, TAB generation from image evidence, or full video
transcription.

## Prerequisites

- The package installed from this local repository.
- Optional `mediapipe` installed in the smoke environment.
- A local image file, for example `guitar.jpg`.
- A local MediaPipe Hand Landmarker `.task` model file.

Do not commit the model file, source images, generated JSON, overlay images, or
other local smoke artifacts.

## Model Download

Download the MediaPipe Hand Landmarker task model into a local smoke directory:

```bash
mkdir -p /Users/kengo/tmp/guitar-tab-agent-smoke/models
curl -L \
  -o /Users/kengo/tmp/guitar-tab-agent-smoke/models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

Keep this file as a local smoke artifact. Do not commit it.

## Frame List

Create `frames.json` next to the image, or use an absolute image path:

```json
[
  {
    "path": "guitar.jpg",
    "timestamp": 0.0
  }
]
```

Relative paths are resolved relative to the parent directory of `frames.json`.

## Extract Landmarks

Run `frames-to-landmarks` with the local model path:

```bash
tabgen frames-to-landmarks frames.json \
  --hand-index 0 \
  --mediapipe-model /Users/kengo/tmp/guitar-tab-agent-smoke/models/hand_landmarker.task \
  --out hand_landmarks.image.json
```

`hand_landmarks.image.json` is generated smoke output. Do not commit it.

## Verify Output

Use this local script to inspect the generated JSON:

```python
import json

data = json.load(open("hand_landmarks.image.json"))
print("num frames:", len(data))
for frame in data:
    print("timestamp:", frame["timestamp"])
    print("confidence:", frame.get("confidence"))
    print("num landmarks:", len(frame["landmarks"]))
    for lm in frame["landmarks"][:8]:
        print(lm)
```

Expected smoke success:

- One frame.
- Around 21 landmarks when a hand is detected.
- Non-null confidence when MediaPipe returns handedness confidence.

Observed local success on a guitar image:

- `num frames: 1`
- `confidence: 0.9812201261520386`
- `num landmarks: 21`
- sample landmark names included `left:wrist`, `left:thumb_cmc`, and
  `left:index_finger_*`.

## Optional Overlay Visualization

For local debugging, this Pillow snippet draws landmark points and a simple hand
skeleton. Install Pillow only in the local smoke environment if needed. The
overlay image is a debug artifact and must not be committed.

```python
import json
from pathlib import Path

from PIL import Image, ImageDraw

image_path = Path("guitar.jpg")
landmarks_path = Path("hand_landmarks.image.json")
out_path = Path("guitar.hand_overlay.png")

connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
]

image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image)
width, height = image.size
frames = json.loads(landmarks_path.read_text())

for frame in frames:
    points = [
        (float(x) * width, float(y) * height)
        for _, x, y in frame["landmarks"]
    ]
    for start, end in connections:
        if start < len(points) and end < len(points):
            draw.line([points[start], points[end]], fill="green", width=3)
    for x, y in points:
        radius = 5
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill="red",
        )

image.save(out_path)
print(f"Wrote {out_path}")
```

## Troubleshooting

- If the command asks for a `.task` model path, pass a real local
  `--mediapipe-model` value.
- Placeholder paths such as `/path/to/hand_landmarker.task` must be replaced
  with an actual local file path.
- If the image path is invalid or unreadable, check the `frames.json` location
  and remember that relative paths are resolved from that file's directory.
- If `num landmarks: 0`, MediaPipe ran but did not detect a hand in the frame.
- MediaPipe logs and warnings are often non-fatal if output JSON is written.
- If image loading fails, try absolute image paths or re-encoding the image
  locally.

## Non-Goals

- No fretboard calibration accuracy guarantee.
- No fret-line tracing.
- No OpenCV or YOLO.
- No fret-number inference.
- No TAB generation validation from image evidence.
- No continuation into image or video implementation in this smoke recipe.
