import torch
import torch.nn as nn
import pandas as pd
import torchaudio
from torch.utils.data import DataLoader, Dataset
from speechbrain.inference.classifiers import EncoderClassifier
import torch.nn.functional as F
from tqdm import tqdm
import os
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from label_mapping import label_mapping

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load pre-trained SpeechBrain LID model
lid = EncoderClassifier.from_hparams(
    source="speechbrain/lang-id-voxlingua107-ecapa",
    savedir="tmpdir",
    run_opts={"device": device}
)

# Custom model
class CustomLID(nn.Module):
    def __init__(self, lid_model, num_classes, device):
        super(CustomLID, self).__init__()
        self.lid = lid_model
        self.device = device

        for name, module in self.lid.mods.items():
            self.lid.mods[name] = module.to(device)

        dummy_wav = torch.randn(1, 16000).to(device)
        with torch.no_grad():
            emb = self.lid.encode_batch(dummy_wav)
            in_features = emb.shape[-1]

        self.classifier = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Linear(512, num_classes)
        )

    def forward(self, wav):
        wav = wav.to(self.device)
        with torch.no_grad():
            features = self.lid.encode_batch(wav).squeeze(1)
        return self.classifier(features.to(self.device))

# Dataset class
class SpeechDataset(Dataset):
    def __init__(self, csv_file, target_sr=16000, num_samples=64000):
        self.data = pd.read_csv(csv_file)
        self.target_sr = target_sr
        self.num_samples = num_samples
        self.resampler = torchaudio.transforms.Resample(orig_freq=24000, new_freq=self.target_sr)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        wav_path = self.data.iloc[idx, 1]
        label = int(self.data.iloc[idx, 3])
        waveform, sample_rate = torchaudio.load(wav_path)

        if sample_rate != self.target_sr:
            waveform = self.resampler(waveform)

        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if waveform.shape[1] < self.num_samples:
            padding = self.num_samples - waveform.shape[1]
            waveform = F.pad(waveform, (0, padding))
        else:
            waveform = waveform[:, :self.num_samples]

        waveform = waveform.squeeze(0)
        return waveform.to(device), torch.tensor(label).to(device)

# Load test data
test_dataset = SpeechDataset(csv_file="test_prepared.csv")
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# Load model
num_classes = 10
model = CustomLID(lid_model=lid, num_classes=num_classes, device=device).to(device)
model = nn.DataParallel(model, device_ids=[0, 1]).to(device)
model.load_state_dict(torch.load("checkpoints/model_best.pt"))
model.eval()

# Evaluation
criterion = nn.CrossEntropyLoss()
test_loss = 0.0
all_preds, all_labels = [], []

with torch.no_grad():
    with tqdm(test_loader, desc="Testing", unit="batch") as test_progress:
        for inputs, labels in test_progress:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

            acc = (np.array(all_preds) == np.array(all_labels)).mean()
            test_progress.set_postfix(loss=test_loss/len(test_progress), accuracy=acc)

# Final metrics
test_accuracy = (np.array(all_preds) == np.array(all_labels)).mean() * 100
print(f"\nTest Loss: {test_loss/len(test_loader):.4f}, Test Accuracy: {test_accuracy:.2f}%")

# Save evaluation reports
os.makedirs("evaluation1", exist_ok=True)
label_names = [label for label, _ in sorted(label_mapping.items(), key=lambda x: x[1])]
report = classification_report(all_labels, all_preds, target_names=label_names, digits=4)

with open("evaluation1/classification_report.txt", "w") as f:
    f.write(f"Test Accuracy: {test_accuracy:.2f}%\n\n")
    f.write(report)

# Plot and save confusion matrix
conf_mat = confusion_matrix(all_labels, all_preds)
plt.figure(figsize=(10, 8))
sns.heatmap(conf_mat, annot=True, fmt="d", cmap="Blues",
            xticklabels=label_names, yticklabels=label_names)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig("evaluation1/confusion_matrix.png")
plt.close()
