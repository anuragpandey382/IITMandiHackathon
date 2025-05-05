import pandas as pd
from label_mapping import label_mapping

def prepare(csv_path, output_path):
    df = pd.read_csv(csv_path)
    df["label_id"] = df["label"].map(label_mapping)
    df.to_csv(output_path, index=False)

prepare("data/train.csv", "data/train_prepared.csv")
prepare("data/val.csv", "data/val_prepared.csv")
prepare("data/test.csv",  "data/test_prepared.csv")
