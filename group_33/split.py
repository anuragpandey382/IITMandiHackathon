import os
import glob
import shutil
import random
from sklearn.model_selection import train_test_split

def stratified_split(data_dir, output_dir, seed=42):
    # Collect all .flac files recursively from language subfolders
    all_files = glob.glob(os.path.join(data_dir, '*/*/*.flac'))

    # Extract language name from path: dataset/lang_name/audio_folder/audio.flac
    labels = [os.path.basename(os.path.dirname(os.path.dirname(f))) for f in all_files]

    # Stratified split: 80% train, 10% val, 10% test
    train_files, temp_files, train_labels, temp_labels = train_test_split(
        all_files, labels, test_size=0.2, stratify=labels, random_state=seed
    )
    val_files, test_files, _, _ = train_test_split(
        temp_files, temp_labels, test_size=0.5, stratify=temp_labels, random_state=seed
    )

    def save_files(file_list, split):
        for f in file_list:
            lang = os.path.basename(os.path.dirname(os.path.dirname(f)))
            dest_dir = os.path.join(output_dir, split, lang)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy(f, dest_dir)

    save_files(train_files, "train")
    save_files(val_files, "val")
    save_files(test_files, "test")

    print("Stratified split completed.")

# Example usage
stratified_split("dataset", "processed_dataset")
