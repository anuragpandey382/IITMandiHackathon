import torch
import torch.nn as nn
import pandas as pd
import torchaudio
from torch.utils.data import DataLoader, Dataset
import torch.nn.functional as F
from speechbrain.inference.classifiers import EncoderClassifier
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm  # <-- Added

# === Import label mapping ===
from label_mapping import label_mapping
inv_label_mapping = {v: k for k, v in label_mapping.items()}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load pre-trained LID model
lid = EncoderClassifier.from_hparams(source="speechbrain/lang-id-voxlingua107-ecapa", savedir="tmpdir", run_opts={"device": device})

# Define model wrapper
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

    def extract_features(self, wav):
        wav = wav.to(self.device)
        with torch.no_grad():
            features = self.lid.encode_batch(wav).squeeze(1)
        return features  # [B, D]

# Dataset class
class SpeechDataset(Dataset):
    def __init__(self, csv_file, target_sr=16000, num_samples=64000):
        self.data = pd.read_csv(csv_file)
        self.target_sr = target_sr
        self.num_samples = num_samples
        self.resampler = torchaudio.transforms.Resample(orig_freq=24000, new_freq=target_sr)

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
            waveform = F.pad(waveform, (0, self.num_samples - waveform.shape[1]))
        else:
            waveform = waveform[:, :self.num_samples]

        return waveform.squeeze(0), label

# Load model
num_classes = 10
model = CustomLID(lid_model=lid, num_classes=num_classes, device=device).to(device)
model = nn.DataParallel(model, device_ids=[0, 1]).to(device)
model.load_state_dict(torch.load("checkpoints/model_best.pt"))
model.eval()

# Load validation dataset
dataset = SpeechDataset(csv_file="data/val_prepared.csv")
loader = DataLoader(dataset, batch_size=64, shuffle=False)

# Extract features with tqdm
all_embeddings = []
all_labels = []

with torch.no_grad():
    for inputs, labels in tqdm(loader, desc="Extracting embeddings"):
        inputs = inputs.to(device)
        embeddings = model.module.extract_features(inputs)  # shape: [B, D]
        all_embeddings.append(embeddings.cpu())
        all_labels.extend(labels.cpu().tolist())

all_embeddings = torch.cat(all_embeddings, dim=0).numpy()
all_labels = np.array(all_labels)

# t-SNE
tsne = TSNE(n_components=2, perplexity=30, learning_rate=200, n_iter=1000, random_state=42)
features_2d = tsne.fit_transform(all_embeddings)

# Convert labels to language names
label_names = [inv_label_mapping[label] for label in all_labels]

# Plot
plt.figure(figsize=(10, 8))
sns.set(style="whitegrid", font_scale=1.2)
palette = sns.color_palette("hls", len(label_mapping))

sns.scatterplot(
    x=features_2d[:, 0],
    y=features_2d[:, 1],
    hue=label_names,
    palette=palette,
    legend='full',
    s=40,
    alpha=0.8
)

plt.title("t-SNE Visualization of Language Embeddings")
plt.xlabel("Component 1")
plt.ylabel("Component 2")
plt.legend(title="Language", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("tsne_visualization.png", dpi=300)
plt.show()
