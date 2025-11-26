import cv2
import torch
import numpy as np
import csv
from norfair import Detection, Tracker
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load YOLOv5 model (custom weights)
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_windows_final.pt', force_reload=True)
model.conf = 0.40 # Confidence threshold

# Initialize tracker
tracker = Tracker(distance_function="euclidean", distance_threshold=30)

# Video source
video_path = "17.mp4"
cap = cv2.VideoCapture(video_path)

# Track history: {track_id: [(frame_num, x, y), ...]}
track_history = defaultdict(list)
frame_num = 0
ret, frame = cap.read()
height, width = frame.shape[:2]
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning

# Generate consistent colors for each track ID
def get_color(idx):
    np.random.seed(idx)
    return tuple(int(c) for c in np.random.randint(0, 255, size=3))

# Tracking Loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    # YOLOv5 inference
    results = model(frame)
    detections = []

    for *xyxy, conf, cls in results.xyxy[0]:
        x1, y1, x2, y2 = map(int, xyxy)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        detections.append(
            Detection(
                points=np.array([[cx, cy]]),
                scores=np.array([float(conf)])
            )
        )

    # Update tracker
    tracked_objects = tracker.update(detections)

    # Save tracking info
    for obj in tracked_objects:
        tid = obj.id
        x, y = obj.estimate[0]
        track_history[tid].append((frame_num, int(x), int(y)))

cap.release()

# ------------ PANIC SIMULATION -------------
panic_origin = (600, 400)       # Panic starts here
panic_frame_start = 100         # Trigger panic at this frame
panic_radius = 150              # Panic radius
panic_force = 20                # Repulsion strength

print(f"💥 Injecting panic at frame {panic_frame_start} around {panic_origin}...")

for tid, points in track_history.items():
    new_points = []
    for frame, x, y in points:
        if frame >= panic_frame_start:
            dx = x - panic_origin[0]
            dy = y - panic_origin[1]
            dist = np.hypot(dx, dy)
            if dist < panic_radius and dist != 0:
                scale = panic_force * (1 - dist / panic_radius)
                x += int(scale * dx / dist)
                y += int(scale * dy / dist)
        new_points.append((frame, int(x), int(y)))
    track_history[tid] = new_points

print("✅ Panic simulation applied: trajectories updated.")

# ------------ SAVE TRAJECTORIES -------------
with open("trajectories.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Track_ID", "Frame", "X", "Y"])
    for tid, points in track_history.items():
        for frame, x, y in points:
            writer.writerow([tid, frame, x, y])

# ------------ FLOW VECTORS -------------
flow_img = np.zeros((height, width, 3), dtype=np.uint8)

for tid, points in track_history.items():
    color = get_color(tid)
    for i in range(1, len(points)):
        x1, y1 = points[i - 1][1:]
        x2, y2 = points[i][1:]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) + abs(dy) > 2:
            cv2.arrowedLine(flow_img, (x1, y1), (x2, y2), color, 1, tipLength=0.4)

cv2.imwrite("flow_vectors.png", flow_img)

# ------------ CREATE CLEAN VIDEO (NO HEATMAP OVERLAY) -------------
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("output_panic_highlighted.mp4", fourcc, fps, (width, height))
frame_num = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    # Draw panic radius and label
    if frame_num >= panic_frame_start:
        cv2.circle(frame, panic_origin, panic_radius, (0, 0, 255), 2)
        cv2.putText(frame, "PANIC!", (panic_origin[0]-30, panic_origin[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Draw trajectory lines (thick after panic)
    for tid, points in track_history.items():
        color = get_color(tid)
        past_points = [p for p in points if p[0] <= frame_num]
        for i in range(1, len(past_points)):
            x1, y1 = past_points[i - 1][1:]
            x2, y2 = past_points[i][1:]

            if past_points[i][0] >= panic_frame_start:
                cv2.line(frame, (x1, y1), (x2, y2), color, 3)
            else:
                cv2.line(frame, (x1, y1), (x2, y2), color, 1)

    out.write(frame)
    cv2.imshow("Panic Visualization", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("🎥 Clean video with panic simulation saved as 'output_panic_highlighted.mp4'")
