import cv2
import torch
import numpy as np
from pathlib import Path
from collections import deque

# === CONFIG ===
video_path = Path('21.mp4')
weights_path = 'best_windows_final.pt'
output_path = Path('21_final.mp4')
zoom_factor = 2.5
conf_top = 0.20
conf_bottom = 0.40
count_smoothing_window = 10  # Number of frames to average over

# === Load YOLOv5 model ===
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, force_reload=False)

# === Open video ===
cap = cv2.VideoCapture(str(video_path))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
half_h = h // 2
half_w = w // 2

out = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
frame_idx = 0
smoothed_counts = deque(maxlen=count_smoothing_window)
total_detected = []

print(f"🎬 Processing {video_path.name} with multi-threshold detection...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_idx += 1
    frame_display = frame.copy()
    detections = 0

    # === Split frame ===
    top_half = frame[:half_h, :]
    bottom_half = frame[half_h:, :]
    top_left = top_half[:, :half_w]
    top_right = top_half[:, half_w:]

    # === Zoom top quadrants ===
    zoomed_left = cv2.resize(top_left, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)
    zoomed_right = cv2.resize(top_right, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)

    # === Inference ===
    model.conf = conf_top
    result_left = model(zoomed_left)
    result_right = model(zoomed_right)

    model.conf = conf_bottom
    result_bottom = model(bottom_half)

    # === LEFT detections ===
    for *xyxy, conf, cls in result_left.xyxy[0]:
        x1, y1, x2, y2 = map(int, xyxy)
        x1 = int(x1 / zoom_factor)
        y1 = int(y1 / zoom_factor)
        x2 = int(x2 / zoom_factor)
        y2 = int(y2 / zoom_factor)
        cv2.rectangle(frame_display, (x1, y1), (x2, y2), (0, 255, 0), 1)
        detections += 1

    # === RIGHT detections ===
    for *xyxy, conf, cls in result_right.xyxy[0]:
        x1, y1, x2, y2 = map(int, xyxy)
        x1 = int(x1 / zoom_factor) + half_w
        y1 = int(y1 / zoom_factor)
        x2 = int(x2 / zoom_factor) + half_w
        y2 = int(y2 / zoom_factor)
        cv2.rectangle(frame_display, (x1, y1), (x2, y2), (0, 255, 0), 1)
        detections += 1

    # === BOTTOM detections ===
    for *xyxy, conf, cls in result_bottom.xyxy[0]:
        x1, y1, x2, y2 = map(int, xyxy)
        y1 += half_h
        y2 += half_h
        cv2.rectangle(frame_display, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)
        detections += 1

    # === Smooth & Display Crowd Count ===
    smoothed_counts.append(detections)
    avg_count = int(np.mean(smoothed_counts))
    total_detected.append(avg_count)
    cv2.putText(frame_display, f"People Count: {avg_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    out.write(frame_display)

    if frame_idx % 30 == 0:
        print(f"Processed {frame_idx} frames...")

cap.release()
out.release()

# === Final Summary ===
final_avg = int(np.mean(total_detected))
print(f"✅ Video saved to: {output_path}")
print(f"👥 Estimated Average Crowd Count: {final_avg}")
