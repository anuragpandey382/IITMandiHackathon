import cv2
import os
import random
from pathlib import Path

# === CONFIG ===
input_dir = Path("Crowd_Videos_Dataset")
output_dir = Path("Processed_Videos")
screenshot_dir = Path("Screenshots_Comparisons")
output_dir.mkdir(exist_ok=True)
screenshot_dir.mkdir(exist_ok=True)

frames_to_capture = 2  # number of random screenshots per video

# === Contrast enhancement using CLAHE ===
def enhance_contrast(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

# === Process videos ===
for video_path in sorted(input_dir.glob("*.mp4")):
    video_id = video_path.stem
    cap = cv2.VideoCapture(str(video_path))

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_path = output_dir / f"{video_id}.mp4"
    out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    print(f"🔧 Processing: {video_id}")

    prev_gray = None
    captured_frames = sorted(random.sample(range(10, frame_count - 10), min(frames_to_capture, frame_count - 20)))
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        orig_frame = frame.copy()
        frame = enhance_contrast(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
            if prev_pts is not None:
                curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, prev_pts, None)
                if curr_pts is not None:
                    m = cv2.estimateAffinePartial2D(prev_pts, curr_pts, method=cv2.RANSAC)[0]
                    if m is not None:
                        frame = cv2.warpAffine(frame, m, (width, height))


        # Save side-by-side screenshots
        if frame_idx in captured_frames:
            comparison = cv2.hconcat([orig_frame, frame])
            screenshot_path = screenshot_dir / f"{video_id}_frame{frame_idx:04d}.jpg"
            cv2.imwrite(str(screenshot_path), comparison)

        out.write(frame)
        prev_gray = gray
        frame_idx += 1

    cap.release()
    out.release()
    print(f"✅ Saved video: {out_path.name}")

print("📸 Screenshots saved to 'Screenshots_Comparisons'")
print("🚀 All videos processed and enhanced.")
