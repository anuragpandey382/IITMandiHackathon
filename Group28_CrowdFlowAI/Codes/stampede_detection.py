import cv2
import torch
import numpy as np
from norfair import Detection, Tracker
from collections import defaultdict

# Load YOLOv5 custom model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_windows.pt', force_reload=True)
model.conf = 0.25

# Setup video
video_path = "04.mp4"
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
height, width = frame.shape[:2]
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
fps = cap.get(cv2.CAP_PROP_FPS)

# Tracker and history
tracker = Tracker(distance_function="euclidean", distance_threshold=30)
track_history = defaultdict(list)
frame_num = 0

def get_color(idx):
    np.random.seed(idx)
    return tuple(int(c) for c in np.random.randint(0, 255, 3))

# --------- Step 1: Track People and Build History ---------
print("🕵️ Tracking people across frames...")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    results = model(frame)
    detections = []

    for *xyxy, conf, cls in results.xyxy[0]:
        x1, y1, x2, y2 = map(int, xyxy)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        detections.append(Detection(points=np.array([[cx, cy]]), scores=np.array([float(conf)])))

    tracked = tracker.update(detections)

    for obj in tracked:
        x, y = obj.estimate[0]
        track_history[obj.id].append((frame_num, int(x), int(y)))

cap.release()

# --------- Step 2: Build Density Map ---------
print("📊 Building density map...")
density_map = np.zeros((height, width), dtype=np.float32)

for points in track_history.values():
    for _, x, y in points:
        if 0 <= x < width and 0 <= y < height:
            density_map[y, x] += 1

density_map_blur = cv2.GaussianBlur(density_map, (25, 25), 0)

# --------- Step 3: Detect Risk Zones ---------
print("🚨 Detecting risk zones...")
cell_size = 50
threshold = 80  # Lowered threshold for visibility
risk_zones = []

for y in range(0, height, cell_size):
    for x in range(0, width, cell_size):
        cell = density_map_blur[y:y+cell_size, x:x+cell_size]
        density_sum = cell.sum()
        print(f"Cell ({x},{y}) density: {density_sum:.2f}")
        if density_sum > threshold:
            risk_zones.append((x, y))

print(f"✅ {len(risk_zones)} risk zones detected.")

# --------- Step 4: Draw and Save Video ---------
print("🎬 Generating output video with risk zones...")

cap = cv2.VideoCapture(video_path)
out = cv2.VideoWriter("stampede_detection.mp4", cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
frame_num = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    # Draw risk zones
    for x, y in risk_zones:
        cv2.rectangle(frame, (x, y), (x + cell_size, y + cell_size), (0, 0, 255), 2)
        cv2.putText(frame, "RISK", (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    out.write(frame)
    cv2.imshow("Stampede Risk Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("✅ Video saved as 'stampede_detection.mp4'")
