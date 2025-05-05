import torch
import torch.nn as nn
import pandas as pd
import torchaudio
from torch.utils.data import DataLoader, Dataset
from speechbrain.inference.classifiers import EncoderClassifier
import torch.nn.functional as F
from tqdm import tqdm
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load pre-trained LID model
lid = EncoderClassifier.from_hparams(source="speechbrain/lang-id-voxlingua107-ecapa", savedir="tmpdir",run_opts={"device": "cuda"})
class CustomLID(nn.Module):
    def __init__(self, lid_model, num_classes, device):
        super(CustomLID, self).__init__()
        self.lid = lid_model
        self.device = device

        # Move internal modules to device BEFORE encode_batch
        for name, module in self.lid.mods.items():
            self.lid.mods[name] = module.to(device)

        # Get the embedding dimension by encoding a dummy batch
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
        # Ensure the input is on the correct device
        wav = wav.to(self.device)

        with torch.no_grad():
            features = self.lid.encode_batch(wav)  # [B, 1, D]
            features = features.squeeze(1)         # [B, D]
        
        return self.classifier(features.to(self.device))  # Ensure the classifier is on the right device


# Set the number of classes to 10 (adjust as needed)
num_classes = 10
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Create custom model
custom_lid = CustomLID(lid, num_classes, device).to(device)

# Use DataParallel for multi-GPU
custom_lid = nn.DataParallel(custom_lid, device_ids=[0, 1]).to(device)

# Freeze encoder parameters
for param in custom_lid.module.lid.parameters():  # Access 'lid' through 'module'
    param.requires_grad = False
for param in custom_lid.module.classifier.parameters():  # Access 'classifier' through 'module'
    param.requires_grad = True

# Optimizer and loss
optimizer = torch.optim.Adam(custom_lid.parameters(), lr=1e-4)
criterion = nn.CrossEntropyLoss()

# Custom Dataset for loading audio and labels
class SpeechDataset(Dataset):
    def __init__(self, csv_file, target_sr=16000, num_samples=64000, transform=None):
        self.data = pd.read_csv(csv_file)
        self.target_sr = target_sr
        self.num_samples = num_samples
        self.transform = transform
        self.resampler = torchaudio.transforms.Resample(orig_freq=24000, new_freq=self.target_sr)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        wav_path = self.data.iloc[idx, 1]  # Audio path
        label = int(self.data.iloc[idx, 3])  # Label
        waveform, sample_rate = torchaudio.load(wav_path)

        # Resample if needed
        if sample_rate != self.target_sr:
            waveform = self.resampler(waveform)

        # Convert to mono
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Pad or truncate
        if waveform.shape[1] < self.num_samples:
            padding = self.num_samples - waveform.shape[1]
            waveform = F.pad(waveform, (0, padding))
        else:
            waveform = waveform[:, :self.num_samples]

        waveform = waveform.squeeze(0)  # [time_steps]
        return waveform.to(device), torch.tensor(label).to(device)

# Data loader setup
train_dataset = SpeechDataset(csv_file="data/train_prepared.csv")
val_dataset = SpeechDataset(csv_file="data/val_prepared.csv")

train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False)

# Training loop with tqdm progress bar
num_epochs = 10
best_val_accuracy = 0.0  # Initialize variable to track best validation accuracy

for epoch in range(num_epochs):
    custom_lid.train()
    running_loss = 0.0
    correct_train_preds = 0
    total_train_preds = 0
    
    epoch_start_time = time.time()

    # Training with tqdm progress bar
    with tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}", unit="batch") as train_progress:
        for inputs, labels in train_progress:
            optimizer.zero_grad()
            inputs = inputs.to(device)
            labels = labels.to(device)

            # Forward pass
            outputs = custom_lid(inputs)

            # Compute loss
            loss = criterion(outputs, labels)

            # Backward pass
            loss.backward()
            optimizer.step()

            # Track training accuracy
            _, predicted = torch.max(outputs, 1)
            total_train_preds += labels.size(0)
            correct_train_preds += (predicted == labels).sum().item()

            running_loss += loss.item()

            # Update the progress bar with loss and accuracy
            train_progress.set_postfix(loss=running_loss/len(train_progress), accuracy=correct_train_preds/total_train_preds)

    train_accuracy = correct_train_preds / total_train_preds * 100
    epoch_end_time = time.time()
    epoch_duration = epoch_end_time - epoch_start_time
    avg_epoch_time = epoch_duration / (epoch + 1)
    remaining_epochs = num_epochs - (epoch + 1)
    eta_seconds = avg_epoch_time * remaining_epochs
    eta_minutes = eta_seconds / 60
    eta_hours = eta_minutes / 60

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/len(train_loader):.4f}, "
          f"Training Accuracy: {train_accuracy:.2f}%, "
          f"ETA: {eta_hours:.2f} hours")

    # Validation loop with tqdm progress bar
    custom_lid.eval()
    val_loss = 0.0
    correct_preds = 0
    total_preds = 0
    with torch.no_grad():
        with tqdm(val_loader, desc="Validation", unit="batch") as val_progress:
            for inputs, labels in val_progress:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # Forward pass
                outputs = custom_lid(inputs)

                # Compute loss
                loss = criterion(outputs, labels)
                val_loss += loss.item()

                # Track validation accuracy
                _, predicted = torch.max(outputs, 1)
                total_preds += labels.size(0)
                correct_preds += (predicted == labels).sum().item()

                # Update the progress bar with validation loss and accuracy
                val_progress.set_postfix(val_loss=val_loss/len(val_progress), val_accuracy=correct_preds/total_preds)

    val_accuracy = correct_preds / total_preds * 100
    print(f"Validation Loss: {val_loss/len(val_loader):.4f}, Validation Accuracy: {val_accuracy:.2f}%")

    # Save the model if validation accuracy is the best seen so far
    if val_accuracy > best_val_accuracy:
        best_val_accuracy = val_accuracy
        torch.save(custom_lid.state_dict(), f"checkpoints/model_best.pt")
        print(f"Best model saved at epoch {epoch+1} with validation accuracy: {val_accuracy:.2f}%")

    # Save the model after each epoch (even if not the best)
    torch.save(custom_lid.state_dict(), f"checkpoints/model_epoch_{epoch+1}.pt")
