import cv2
import torch
import numpy as np
import csv
from norfair import Detection, Tracker
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Load YOLOv5 model (custom weights)
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_windows.pt', force_reload=True)
model.conf = 0.25  # Confidence threshold

# Initialize tracker
tracker = Tracker(distance_function="euclidean", distance_threshold=30)

# Video source
video_path = "03.mp4"
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

# Main loop
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

    # Draw custom colored trajectory lines without ID labels
    for tid, points in track_history.items():
        color = get_color(tid)
        for i in range(1, len(points)):
            cv2.line(frame, points[i - 1][1:], points[i][1:], color, thickness=2)

    # Show live window
    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Save trajectory data to CSV
with open("trajectories3.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Track_ID", "Frame", "X", "Y"])
    for tid, points in track_history.items():
        for frame, x, y in points:
            writer.writerow([tid, frame, x, y])

print("✅ Tracking complete and trajectories saved to 'trajectories3.csv'")

# ---------- DENSITY MAP ----------
density_map = np.zeros((height, width), dtype=np.float32)

for points in track_history.values():
    for _, x, y in points:
        if 0 <= x < width and 0 <= y < height:
            density_map[y, x] += 1

density_map_blur = cv2.GaussianBlur(density_map, (25, 25), 0)

plt.figure(figsize=(10, 8))
sns.heatmap(density_map_blur, cmap='hot', cbar=True)
plt.title("Density Map (Pedestrian Activity Heatmap)")
plt.axis('off')
plt.savefig("density_map3.png")
plt.close()

print("✅ Density map saved as 'density_map3.png'")

# ---------- FLOW VECTORS ----------
flow_img = np.zeros((height, width, 3), dtype=np.uint8)

for tid, points in track_history.items():
    color = get_color(tid)
    for i in range(1, len(points)):
        x1, y1 = points[i - 1][1:]
        x2, y2 = points[i][1:]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) + abs(dy) > 2:
            cv2.arrowedLine(flow_img, (x1, y1), (x2, y2), color, 1, tipLength=0.4)

cv2.imwrite("flow_vectors3.png", flow_img)
print("✅ Flow vectors saved as 'flow_vectors.png'")
