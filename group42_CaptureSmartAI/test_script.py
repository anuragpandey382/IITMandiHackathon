import os
import pandas as pd
import torch
import timm
import torch.nn as nn
from tqdm import tqdm
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader


class EfficientNetRegressionModel(nn.Module):
    def __init__(self):
        super().__init__()

        # EfficientNet-Lite0 as feature extractor
        self.feature_extractor = timm.create_model('efficientnet_lite0', pretrained=True, num_classes=0)

        # Output is already [B, 1280]
        self.layer_norm = nn.LayerNorm(1280)

        self.fnn = nn.Sequential(
            nn.Linear(1280, 128),
            nn.ReLU()
        )

        self.head_ss_var  = nn.Linear(128, 1)
        self.head_iso_var = nn.Linear(128, 1)

    def forward(self, x):
        x = self.feature_extractor(x)  # [B, 1280]
        x = self.layer_norm(x)
        x = self.fnn(x)
        return self.head_ss_var(x), self.head_iso_var(x)

# -------------------------
# Custom Dataset for Single Image
# -------------------------
class SingleImageDataset(Dataset):
    def __init__(self, image_path, ss_label, iso_label, transform=None):
        self.image_path = image_path
        self.ss_label = torch.tensor(ss_label, dtype=torch.float32)
        self.iso_label = torch.tensor(iso_label, dtype=torch.float32)
        self.transform = transform

    def __len__(self):
        return 1

    def __getitem__(self, idx):
        image = Image.open(self.image_path)

        if self.transform:
            image = self.transform(image)

        return image, self.ss_label, self.iso_label

# -------------------------
# Load Model
# -------------------------
def load_model(model_path, device):
    model = EfficientNetRegressionModel().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model

# -------------------------
# Test Function
# -------------------------
def test():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "/home/teaching/G42/Hack/best_model_ss.pth"
    IMG_PATH   = "/home/teaching/G42/Hack/test/D_500_1030.jpg"
    SS_LABEL   = 130 # difference between optimal and current Shutter Speed
    ISO_LABEL  = 930 # difference between optimal and current ISO

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

    model = load_model(MODEL_PATH, DEVICE)
    dataset = SingleImageDataset(IMG_PATH, SS_LABEL, ISO_LABEL, transform=transform)
    loader = DataLoader(dataset, batch_size=1, shuffle=False) # return image, actual_diff_between_ss, actual_diff_iso

    ss_diffs, iso_diffs = [], []

    with torch.no_grad():
        for image, ss_true, iso_true in loader:
            image    = image.to(DEVICE)
            ss_true  = ss_true.to(DEVICE)
            iso_true = iso_true.to(DEVICE)

            ss_pred, iso_pred = model(image)
            ss_pred  = ss_pred.squeeze(1)
            iso_pred = iso_pred.squeeze(1)

            ss_diff  = torch.abs(abs(ss_pred)  - abs(ss_true)).item() # calculate difference between (actual_diff_ss - predicted_diff_ss)
            iso_diff = torch.abs(abs(iso_pred) - abs(iso_true)).item() # calculate difference between (actual_diff_iso - predicted_diff_iso)

            print(f"SS_pred: {abs(ss_pred.item()):.3f}, SS_true: {abs(ss_true.item()):.3f}, Δ={ss_diff:.3f}")
            print(f"ISO_pred: {abs(iso_pred.item()):.3f}, ISO_true: {abs(iso_true.item()):.3f}, Δ={iso_diff:.3f}")

            ss_diffs.append(ss_diff)
            iso_diffs.append(iso_diff)

    # Optional: Plot error bars (redundant for 1 image but included for completeness)
    plt.figure(figsize=(6, 4))
    plt.bar(['SS Error', 'ISO Error'], [ss_diffs[0], iso_diffs[0]])
    plt.title("Prediction Error")
    plt.ylabel("Absolute Error")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    test()
