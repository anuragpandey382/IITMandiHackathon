import os
import cv2
from pathlib import Path

# === CONFIGURATION ===
input_folder = Path("Crowd_Videos_Dataset")  # folder containing 01.mp4 to 20.mp4
output_folder = Path("Processed_Frames")     # output root folder
frame_rate = 5                                # frames to extract per second
resize_dim = (640, 360)                       # output resolution (width, height)

# === PREPROCESSING FUNCTION ===
def preprocess_videos():
    output_folder.mkdir(exist_ok=True)
    
    for video_file in sorted(input_folder.glob("*.mp4")):
        video_name = video_file.stem
        cap = cv2.VideoCapture(str(video_file))
        fps = cap.get(cv2.CAP_PROP_FPS)
        interval = int(round(fps / frame_rate))
        
        video_output_path = output_folder / video_name
        video_output_path.mkdir(exist_ok=True)
        
        count, saved = 0, 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % interval == 0:
                resized_frame = cv2.resize(frame, resize_dim)
                frame_filename = video_output_path / f"frame_{saved:04d}.jpg"
                cv2.imwrite(str(frame_filename), resized_frame)
                saved += 1
            count += 1
        cap.release()
        print(f"[✓] {video_name}: Saved {saved} frames")

# === RUN SCRIPT ===
if __name__ == "__main__":
    preprocess_videos()
