import os
import cv2
import pandas as pd

def extract_frames(video_path, output_folder, frame_rate, labels_dict, global_frame_counter, category):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return global_frame_counter

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"Warning: Unable to read FPS for {video_path}, defaulting to 30")
        fps = 30.0

    frame_interval = fps / frame_rate
    next_capture = 0.0
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count >= next_capture:
            filename = f"{category}-image-{global_frame_counter}.jpg"  # Add category at the beginning of the filename
            filepath = os.path.join(output_folder, filename)
            cv2.imwrite(filepath, frame)

            labels_dict["image_name"].append(filename)
            labels_dict["shutter_speed"].append(labels_dict.get("current_ss"))
            labels_dict["iso"].append(labels_dict.get("current_iso"))
            labels_dict["SS_var"].append(labels_dict.get("current_ss_var"))
            labels_dict["ISO_var"].append(labels_dict.get("current_iso_var"))

            global_frame_counter += 1
            next_capture += frame_interval

        frame_count += 1

    cap.release()
    return global_frame_counter


def load_metadata(path):
    if not os.path.exists(path):
        print(f"Error: Metadata file {path} does not exist.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    required = {'ID', 'SS', 'ISO'}
    if not required.issubset(df.columns):
        print(f"Error: Metadata file {path} missing columns {required}.")
        return pd.DataFrame()
    return df


def process_videos_and_metadata(folder_path, frame_rate=1.0):
    categories = {"C": "car", "F": "fan", "P": "person", "S": "screen"}
    labels_dict = {"image_name": [], "shutter_speed": [], "iso": [], "SS_var": [], "ISO_var": []}
    global_frame_counter = 1

    # Prepare single output folder
    frames_output_folder = os.path.join(folder_path, "frames")
    os.makedirs(frames_output_folder, exist_ok=True)

    for category, _ in categories.items():
        metadata_file = os.path.join(folder_path, f"{category}.csv")
        df = load_metadata(metadata_file)
        if df.empty:
            continue

        gt_id = f"{category}0"
        gt_row = df[df['ID'] == gt_id]
        if gt_row.empty:
            print(f"Error: No ground truth entry '{gt_id}' in {metadata_file}. Skipping.")
            continue

        gt_ss = gt_row.iloc[0]['SS']
        gt_iso = gt_row.iloc[0]['ISO']

        for _, row in df.iterrows():
            vid = row['ID']
            video_file = f"{vid}.mp4"
            video_path = os.path.join(folder_path, video_file)
            if not os.path.exists(video_path):
                print(f"Warning: {video_file} not found. Skipping.")
                continue

            ss_var = row['SS'] - gt_ss
            iso_var = row['ISO'] - gt_iso

            labels_dict['current_ss'] = row['SS']
            labels_dict['current_iso'] = row['ISO']
            labels_dict['current_ss_var'] = ss_var
            labels_dict['current_iso_var'] = iso_var

            global_frame_counter = extract_frames(
                video_path,
                frames_output_folder,
                frame_rate,
                labels_dict,
                global_frame_counter,
                category  # Pass category to extract_frames function
            )

    # Save combined labels
    labels_df = pd.DataFrame({
        'image_name': labels_dict['image_name'],
        'shutter_speed': labels_dict['shutter_speed'],
        'iso': labels_dict['iso'],
        'SS_var': labels_dict['SS_var'],
        'ISO_var': labels_dict['ISO_var']
    })
    csv_path = os.path.join(folder_path, "frames", "frame_labels.csv")
    labels_df.to_csv(csv_path, index=False)
    print(f"Labels saved to {csv_path}")


if __name__ == '__main__':
    base_dir = 'videos'
    process_videos_and_metadata(base_dir, frame_rate=2.0)  # adjust fps as needed
