import cv2
import torch
import numpy as np
import csv
from pathlib import Path
from norfair import Detection, Tracker
from collections import defaultdict

# === CONFIG ===
video_path = "03.mp4"
weights_path = "best_windows_final.pt"
output_csv = "trajectories_03.csv"
output_video_path = "trajectory_output_03.mp4"
zoom_factor = 2.5
conf_threshold = 0.4

# === Load YOLOv5 Model ===
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, force_reload=False)
model.conf = conf_threshold

# === Initialize Norfair Tracker ===
tracker = Tracker(
    distance_function="euclidean",
    distance_threshold=30,
    hit_counter_max=15,
    initialization_delay=3,
    detection_threshold=conf_threshold
)

track_history = defaultdict(list)
frame_num = 0

# === Open Video ===
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
if not ret or frame is None:
    raise ValueError(f"❌ Failed to load video: {video_path}")

h, w = frame.shape[:2]
half_h = h // 2
half_w = w // 2
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

# === Output Video Writer ===
fps = cap.get(cv2.CAP_PROP_FPS)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (w, h))

# === Color Generator ===
def get_color(idx):
    np.random.seed(idx)
    return tuple(int(c) for c in np.random.randint(0, 255, size=3))

print("🔍 Tracking with quadrant zoom enhancement and saving video...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1
    detections = []

    # === Split Frame ===
    top_half = frame[:half_h, :]
    bottom_half = frame[half_h:, :]
    top_left = top_half[:, :half_w]
    top_right = top_half[:, half_w:]

    # === Zoom Top Quadrants ===
    zoomed_left = cv2.resize(top_left, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
    zoomed_right = cv2.resize(top_right, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)

    # === YOLOv5 Inference ===
    result_left = model(zoomed_left)
    result_right = model(zoomed_right)
    result_bottom = model(bottom_half)

    # === LEFT quadrant detections ===
    for *xyxy, conf, cls in result_left.xyxy[0]:
        if float(conf) < conf_threshold:
            continue
        x1, y1, x2, y2 = map(int, xyxy)
        cx = int((x1 + x2) / (2 * zoom_factor))
        cy = int((y1 + y2) / (2 * zoom_factor))
        detections.append(Detection(points=np.array([[cx, cy]]), scores=np.array([float(conf)])))

    # === RIGHT quadrant detections ===
    for *xyxy, conf, cls in result_right.xyxy[0]:
        if float(conf) < conf_threshold:
            continue
        x1, y1, x2, y2 = map(int, xyxy)
        cx = int((x1 + x2) / (2 * zoom_factor)) + half_w
        cy = int((y1 + y2) / (2 * zoom_factor))
        detections.append(Detection(points=np.array([[cx, cy]]), scores=np.array([float(conf)])))

    # === BOTTOM half detections ===
    for *xyxy, conf, cls in result_bottom.xyxy[0]:
        if float(conf) < conf_threshold:
            continue
        x1, y1, x2, y2 = map(int, xyxy)
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2) + half_h
        detections.append(Detection(points=np.array([[cx, cy]]), scores=np.array([float(conf)])))

    # === Update Tracker ===
    tracked_objects = tracker.update(detections)

    # === Save Tracking Info ===
    for obj in tracked_objects:
        tid = obj.id
        x, y = obj.estimate[0]
        track_history[tid].append((frame_num, int(x), int(y)))

    # === Draw Flow Vectors ===
    for tid, points in track_history.items():
        color = get_color(tid)
        for i in range(1, len(points)):
            pt1 = points[i - 1][1:]
            pt2 = points[i][1:]
            if pt1 != pt2:
                cv2.arrowedLine(frame, pt1, pt2, color, thickness=1, tipLength=0.3)

    # === Show & Save Frame ===
    cv2.imshow("Zoomed Tracking", frame)
    out.write(frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# === Cleanup ===
cap.release()
out.release()
cv2.destroyAllWindows()

# === Save Trajectory CSV ===
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Track_ID", "Frame", "X", "Y"])
    for tid, points in track_history.items():
        for frame_id, x, y in points:
            writer.writerow([tid, frame_id, x, y])

print(f"✅ Trajectories saved to: {output_csv}")
print(f"🎥 Video saved to: {output_video_path}")

import matplotlib.pyplot as plt
import seaborn as sns

# === A. DENSITY MAP ===
density_map = np.zeros((h, w), dtype=np.float32)

# Accumulate points across all tracks
for points in track_history.values():
    for _, x, y in points:
        if 0 <= x < w and 0 <= y < h:
            density_map[y, x] += 1

# Smooth and normalize
density_map_blur = cv2.GaussianBlur(density_map, (25, 25), 0)
norm_density = cv2.normalize(density_map_blur, None, 0, 255, cv2.NORM_MINMAX)

# Save with heatmap coloring
heatmap = cv2.applyColorMap(norm_density.astype(np.uint8), cv2.COLORMAP_JET)
cv2.imwrite("density_map.png", heatmap)
print("📸 Density map saved as 'density_map.png'")

# === B. FLOW VECTOR FIELD ===
flow_img = np.zeros((h, w, 3), dtype=np.uint8)
grid_size = 32
motion_vectors = {}

# Build average motion per grid cell
for points in track_history.values():
    for i in range(1, len(points)):
        _, x1, y1 = points[i - 1]
        _, x2, y2 = points[i]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) + abs(dy) < 2:  # skip static
            continue
        gx, gy = x1 // grid_size, y1 // grid_size
        key = (gx, gy)
        if key not in motion_vectors:
            motion_vectors[key] = []
        motion_vectors[key].append((dx, dy))

# Draw average vectors per grid cell
for (gx, gy), vectors in motion_vectors.items():
    avg_dx = int(np.mean([v[0] for v in vectors]))
    avg_dy = int(np.mean([v[1] for v in vectors]))
    start_x = gx * grid_size + grid_size // 2
    start_y = gy * grid_size + grid_size // 2
    end_x = start_x + avg_dx
    end_y = start_y + avg_dy
    cv2.arrowedLine(flow_img, (start_x, start_y), (end_x, end_y), (0, 255, 255), 1, tipLength=0.3)

cv2.imwrite("flow_vector_field.png", flow_img)
print("📸 Flow vector field saved as 'flow_vector_field.png'")
