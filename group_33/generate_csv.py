import os
import csv
from pathlib import Path

def generate_csv(root_dir, split):
    rows = [("ID", "wav", "label")]
    root = Path(root_dir) / split
    for lang_dir in root.iterdir():
        if lang_dir.is_dir():
            label = lang_dir.name
            for i, file in enumerate(lang_dir.glob("*.flac")):
                utt_id = f"{label}_{i}"
                rows.append((utt_id, str(file.resolve()), label))
    with open(f"{split}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

for split in ["train", "val", "test"]:
    generate_csv("../processed_dataset", split)