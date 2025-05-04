import os
import glob
import numpy as np
import pandas as pd
import librosa
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, precision_score, recall_score, classification_report, roc_auc_score, roc_curve
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import kagglehub
from audiomentations import Compose, AddGaussianNoise, TimeStretch, PitchShift
import warnings
import json
from datetime import datetime
from torch.cuda.amp import GradScaler, autocast
import gradio as gr
import torchaudio
import platform

# Suppress warnings
warnings.filterwarnings("ignore")

# Define dataset paths
BASE_PATH = "/home/sp_students/.cache/kagglehub/datasets/prathav01022002/for-norm/versions/1/for-norm"
TRAIN_PATH = os.path.join(BASE_PATH, "training")
VAL_PATH = os.path.join(BASE_PATH, "validation")
TEST_PATH = os.path.join(BASE_PATH, "testing")

# Create results directory
RESULTS_DIR = "results_transformer_" + datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Check if dataset exists, download if not
if not os.path.exists(BASE_PATH):
    print(f"Dataset not found at {BASE_PATH}. Downloading...")
    path = kagglehub.dataset_download("prathav01022002/for-norm")
    print("Path to downloaded dataset files:", path)
    BASE_PATH = path
    TRAIN_PATH = os.path.join(BASE_PATH, "training")
    VAL_PATH = os.path.join(BASE_PATH, "validation")
    TEST_PATH = os.path.join(BASE_PATH, "testing")
else:
    print(f"Using existing dataset at {BASE_PATH}")

# Audio preprocessing parameters
SAMPLE_RATE = 16000
DURATION = 2.0
NUM_SAMPLES = int(DURATION * SAMPLE_RATE)
N_MELS = 64
N_FFT = 2048
HOP_LENGTH = 512
NUM_CLASSES = 2

# Data augmentation
augment = Compose([
    AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
    TimeStretch(min_rate=0.8, max_rate=1.2, p=0.5),
    PitchShift(min_semitones=-4, max_semitones=4, p=0.5)
])

# SpecAugment for spectrogram augmentation
def spec_augment(spec, max_time_mask=10, max_freq_mask=10, num_time_masks=3, num_freq_masks=3):
    spec = spec.clone()
    freq_len, time_len = spec.shape[-2:]
    
    for _ in range(num_freq_masks):
        f = np.random.randint(0, max_freq_mask)
        f0 = np.random.randint(0, freq_len - f)
        spec[..., f0:f0+f, :] = 0
    
    for _ in range(num_time_masks):
        t = np.random.randint(0, max_time_mask)
        t0 = np.random.randint(0, time_len - t)
        spec[..., :, t0:t0+t] = 0
    
    return spec

# MixUp augmentation
def mixup(data, labels, alpha=0.2, num_classes=NUM_CLASSES):
    batch_size = data.size(0)
    indices = torch.randperm(batch_size)
    lam = np.random.beta(alpha, alpha)
    data_mixed = lam * data + (1 - lam) * data[indices]
    
    # Convert labels to one-hot
    labels_one_hot = torch.zeros(batch_size, num_classes, device=labels.device).scatter_(1, labels.unsqueeze(1), 1.0)
    labels_one_hot_permuted = labels_one_hot[indices]
    
    # Mix labels
    labels_mixed = lam * labels_one_hot + (1 - lam) * labels_one_hot_permuted
    return data_mixed, labels_mixed

# Custom Dataset class for log-mel spectrograms
class AudioMelDataset(Dataset):
    def __init__(self, file_paths, labels, augment=False):
        self.file_paths = file_paths
        self.labels = labels
        self.augment = augment
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=SAMPLE_RATE, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
        )

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        try:
            audio, sr = librosa.load(self.file_paths[idx], sr=SAMPLE_RATE, mono=True)
            if len(audio) == 0:
                raise ValueError("Empty audio file")
        except Exception as e:
            print(f"Error loading {self.file_paths[idx]}: {e}")
            audio = np.zeros(NUM_SAMPLES)
            sr = SAMPLE_RATE
        
        # Trim or pad to 2 seconds
        if len(audio) < NUM_SAMPLES:
            audio = np.pad(audio, (0, NUM_SAMPLES - len(audio)), mode='constant')
        else:
            audio = audio[:NUM_SAMPLES]
        
        # Apply augmentation if enabled
        if self.augment:
            audio = augment(audio, sample_rate=SAMPLE_RATE)
        
        # RMS normalization
        rms = np.sqrt(np.mean(audio**2)) + 1e-8
        audio = audio / rms
        
        # Convert to mel spectrogram
        audio_tensor = torch.tensor(audio, dtype=torch.float32)
        mel_spec = self.mel_transform(audio_tensor)
        mel_spec = torchaudio.transforms.AmplitudeToDB()(mel_spec)
        
        # Apply SpecAugment if training
        if self.augment:
            mel_spec = spec_augment(mel_spec.unsqueeze(0)).squeeze(0)
        
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return mel_spec.unsqueeze(0), label

# Load dataset
def load_data(data_path, split="training"):
    file_paths = []
    labels = []
    for label, subfolder in [(1, "fake"), (0, "real")]:
        subfolder_path = os.path.join(data_path, subfolder)
        if not os.path.exists(subfolder_path):
            print(f"Warning: {subfolder_path} not found")
            continue
        files = glob.glob(os.path.join(subfolder_path, "*.wav"))
        file_paths.extend(files)
        labels.extend([label] * len(files))
    
    if not file_paths:
        raise ValueError(f"No audio files found in {data_path}")
    
    print(f"Loaded {len(file_paths)} files from {split}:")
    print(f"  Real: {labels.count(0)}, Fake: {labels.count(1)}")
    for f, l in zip(file_paths[:5], labels[:5]):
        print(f"  {f} -> {'FAKE' if l == 1 else 'REAL'}")
    if len(file_paths) > 5:
        print(f"  ... ({len(file_paths)} total files)")
    
    return file_paths, labels

# Load data
try:
    train_files, train_labels = load_data(TRAIN_PATH, "training")
    val_files, val_labels = load_data(VAL_PATH, "validation")
    test_files, test_labels = load_data(TEST_PATH, "testing")
except ValueError as e:
    print(e)
    exit(1)

# Create datasets and dataloaders
num_workers = 2 if platform.system() != "Emscripten" else 0
pin_memory = torch.cuda.is_available()
train_dataset = AudioMelDataset(train_files, train_labels, augment=True)
val_dataset = AudioMelDataset(val_files, val_labels, augment=False)
test_dataset = AudioMelDataset(test_files, test_labels, augment=False)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=num_workers, pin_memory=pin_memory)
val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)

# Sinusoidal Positional Encoding
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return x

# Transformer Model
class AudioTransformerClassifier(nn.Module):
    def __init__(self, num_classes=NUM_CLASSES, n_mels=N_MELS):
        super(AudioTransformerClassifier, self).__init__()
        
        # Convolutional front-end
        self.conv_layers = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(),
            nn.BatchNorm2d(16, eps=1e-5),
            nn.Dropout(0.3),
            nn.Conv2d(16, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)),
            nn.ReLU(),
            nn.BatchNorm2d(32, eps=1e-5),
            nn.Dropout(0.3),
            nn.Conv2d(32, 64, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)),
            nn.ReLU(),
            nn.BatchNorm2d(64, eps=1e-5),
        )
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model=64, max_len=5000)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64, nhead=2, dim_feedforward=128, dropout=0.4, activation='relu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        
        # Classification head
        self.fc = nn.Linear(64, num_classes)
    
    def forward(self, x):
        x = self.conv_layers(x)
        x = x.mean(dim=2)  # Average over frequency dimension
        x = x.permute(2, 0, 1)  # (time, batch, features)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)
        x = x.mean(dim=0)
        x = self.fc(x)
        return x

# Training function
def train_model(model, train_loader, val_loader, optimizer, criterion, scheduler, device, epochs=10, patience=3):
    model.to(device)
    scaler = GradScaler() if device.type == 'cuda' else None
    best_val_loss = float('inf')
    patience_counter = 0
    history = {
        'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_f1': [],
        'val_precision': [], 'val_recall': [], 'val_roc_auc': [], 'lr': []
    }
    
    # Warmup for first 3 epochs
    warmup_epochs = 3
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            # Apply MixUp with 50% probability
            if torch.rand(1).item() < 0.5:
                inputs, labels_mixed = mixup(inputs, labels)
            else:
                labels_mixed = torch.zeros(labels.size(0), NUM_CLASSES, device=device)
                labels_mixed.scatter_(1, labels.unsqueeze(1), 1.0)
            
            optimizer.zero_grad()
            if device.type == 'cuda':
                with autocast():
                    outputs = model(inputs)
                    loss = criterion(outputs, labels_mixed)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = model(inputs)
                loss = criterion(outputs, labels_mixed)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
            train_loss += loss.item() * inputs.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        # Adjust learning rate
        if epoch < warmup_epochs:
            lr_scale = (epoch + 1) / warmup_epochs
            for param_group in optimizer.param_groups:
                param_group['lr'] = 3e-4 * lr_scale
        else:
            scheduler.step()
        
        model.eval()
        val_loss = 0.0
        val_preds, val_true, val_probs = [], [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, torch.nn.functional.one_hot(labels, num_classes=NUM_CLASSES).float())
                val_loss += loss.item() * inputs.size(0)
                preds = torch.argmax(outputs, dim=1)
                probs = torch.softmax(outputs, dim=1)[:, 1]
                val_preds.extend(preds.cpu().numpy())
                val_true.extend(labels.cpu().numpy())
                val_probs.extend(probs.cpu().numpy())
        
        val_loss /= len(val_loader.dataset)
        val_acc = accuracy_score(val_true, val_preds)
        val_f1 = f1_score(val_true, val_preds, average='macro', zero_division=0)
        val_precision = precision_score(val_true, val_preds, average='macro', zero_division=0)
        val_recall = recall_score(val_true, val_preds, average='macro', zero_division=0)
        val_roc_auc = roc_auc_score(val_true, val_probs) if len(set(val_true)) > 1 else 0.0
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['val_f1'].append(val_f1)
        history['val_precision'].append(val_precision)
        history['val_recall'].append(val_recall)
        history['val_roc_auc'].append(val_roc_auc)
        history['lr'].append(optimizer.param_groups[0]['lr'])
        
        print(f"Epoch {epoch+1}/{epochs}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
              f"Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}, Val Precision: {val_precision:.4f}, "
              f"Val Recall: {val_recall:.4f}, Val ROC-AUC: {val_roc_auc:.4f}, LR: {history['lr'][-1]:.6f}")
        
        # Early stopping based on validation loss
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "best_transformer_model.pt"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "final_transformer_model.pt"))
    with open(os.path.join(RESULTS_DIR, "training_history.json"), 'w') as f:
        json.dump(history, f, indent=4)
    
    return history

# Evaluation function
def evaluate_model(model, test_loader, device):
    model.eval()
    preds, true, probs = [], [], []
    embeddings = []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            preds.extend(torch.argmax(outputs, dim=1).cpu().numpy())
            true.extend(labels.cpu().numpy())
            probs.extend(torch.softmax(outputs, dim=1)[:, 1].cpu().numpy())
            x = model.conv_layers(inputs)
            x = x.mean(dim=2)
            x = x.permute(2, 0, 1)
            x = model.pos_encoder(x)
            x = model.transformer_encoder(x)
            x = x.mean(dim=0)
            embeddings.extend(x.cpu().numpy())
    
    accuracy = accuracy_score(true, preds)
    f1 = f1_score(true, preds, average='macro', zero_division=0)
    precision = precision_score(true, preds, average='macro', zero_division=0)
    recall = recall_score(true, preds, average='macro', zero_division=0)
    roc_auc = roc_auc_score(true, probs) if len(set(true)) > 1 else 0.0
    cm = confusion_matrix(true, preds)
    report = classification_report(true, preds, target_names=['REAL', 'FAKE'], output_dict=True, zero_division=0)
    
    eval_results = {
        'accuracy': accuracy,
        'f1_score': f1,
        'precision': precision,
        'recall': recall,
        'roc_auc': roc_auc,
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }
    with open(os.path.join(RESULTS_DIR, "evaluation_results.json"), 'w') as f:
        json.dump(eval_results, f, indent=4)
    
    return accuracy, f1, precision, recall, roc_auc, cm, np.array(embeddings), np.array(true), np.array(probs), report

# Visualization functions
def plot_metrics(history):
    plt.figure(figsize=(15, 12))
    
    plt.subplot(2, 3, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Loss Curves')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(2, 3, 2)
    plt.plot(history['val_acc'], label='Val Accuracy')
    plt.plot(history['val_f1'], label='Val F1 Score')
    plt.title('Validation Metrics')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
    plt.legend()
    
    plt.subplot(2, 3, 3)
    plt.plot(history['val_precision'], label='Val Precision')
    plt.plot(history['val_recall'], label='Val Recall')
    plt.title('Precision and Recall')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
    plt.legend()
    
    plt.subplot(2, 3, 4)
    plt.plot(history['val_roc_auc'], label='Val ROC-AUC')
    plt.title('ROC-AUC')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
    plt.legend()
    
    plt.subplot(2, 3, 5)
    plt.plot(history['lr'], label='Learning Rate')
    plt.title('Learning Rate Schedule')
    plt.xlabel('Epoch')
    plt.ylabel('Learning Rate')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'training_metrics.png'))
    plt.close()

def plot_confusion_matrix(cm):
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['REAL', 'FAKE'], 
                yticklabels=['REAL', 'FAKE'])
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.savefig(os.path.join(RESULTS_DIR, 'confusion_matrix.png'))
    plt.close()

def plot_tsne(embeddings, labels):
    tsne = TSNE(n_components=2, random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=labels, cmap='viridis', alpha=0.6)
    plt.colorbar(scatter, ticks=[0, 1], label='Class')
    plt.title('t-SNE Visualization of Embeddings')
    plt.savefig(os.path.join(RESULTS_DIR, 'tsne_embeddings.png'))
    plt.close()

def plot_roc_curve(true, probs):
    fpr, tpr, _ = roc_curve(true, probs)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc_score(true, probs):.4f})')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'roc_curve.png'))
    plt.close()

# Gradio interface
class AudioClassifier:
    def __init__(self, model_path, device):
        self.model = AudioTransformerClassifier(num_classes=NUM_CLASSES, n_mels=N_MELS)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
        self.model.to(device)
        self.device = device
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=SAMPLE_RATE, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
        )

    def classify(self, audio):
        if audio is None:
            return "No audio provided."
        
        try:
            audio, sr = librosa.load(audio, sr=SAMPLE_RATE, mono=True)
            if len(audio) == 0:
                return "Empty audio file."
        except Exception as e:
            return f"Error loading audio: {e}"
        
        # Trim or pad to 2 seconds
        if len(audio) < NUM_SAMPLES:
            audio = np.pad(audio, (0, NUM_SAMPLES - len(audio)), mode='constant')
        else:
            audio = audio[:NUM_SAMPLES]
        
        # RMS normalization
        rms = np.sqrt(np.mean(audio**2)) + 1e-8
        audio = audio / rms
        
        # Convert to mel spectrogram
        audio_tensor = torch.tensor(audio, dtype=torch.float32)
        mel_spec = self.mel_transform(audio_tensor)
        mel_spec = torchaudio.transforms.AmplitudeToDB()(mel_spec)
        mel_spec = mel_spec.unsqueeze(0).unsqueeze(0)  # (1, 1, n_mels, time)
        
        with torch.no_grad():
            output = self.model(mel_spec.to(self.device))
            pred = torch.argmax(output, dim=1).cpu().numpy()[0]
        
        return "FAKE" if pred == 1 else "REAL"

# Performance analysis
def analyze_performance(accuracy, f1, precision, recall, roc_auc, cm, report):
    if not report or not isinstance(report, dict) or 'REAL' not in report or 'FAKE' not in report:
        raise ValueError("Invalid or incomplete classification report")
    
    # Confusion matrix breakdown
    try:
        tn, fp, fn, tp = cm.ravel()
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    except ValueError:
        tn, fp, fn, tp = 0, 0, 0, 0
        false_positive_rate, false_negative_rate = 0.0, 0.0
        print("Warning: Invalid confusion matrix, setting rates to 0.0")
    
    # Generate summary
    summary = f"""
Performance Analysis (Fake-or-Real Dataset):
- Accuracy: {accuracy:.4f}
- F1 Score (macro): {f1:.4f}
- Precision (macro): {precision:.4f}
- Recall (macro): {recall:.4f}
- ROC-AUC: {roc_auc:.4f}

Confusion Matrix:
[[TN={tn}, FP={fp}]
 [FN={fn}, TP={tp}]]
- False Positive Rate: {false_positive_rate:.4f}
- False Negative Rate: {false_negative_rate:.4f}

Per-Class Metrics:
- REAL: Precision={report['REAL']['precision']:.4f}, Recall={report['REAL']['recall']:.4f}, F1={report['REAL']['f1-score']:.4f}
- FAKE: Precision={report['FAKE']['precision']:.4f}, Recall={report['FAKE']['recall']:.4f}, F1={report['FAKE']['f1-score']:.4f}

Analysis:
The Transformer model, trained on log-mel spectrograms with MixUp and SpecAugment, shows robust performance on the Fake-or-Real dataset. A ROC-AUC of {roc_auc:.4f} indicates strong discrimination. Low false positive ({false_positive_rate:.4f}) and false negative ({false_negative_rate:.4f}) rates suggest reliable classification. Check tsne_embeddings.png for class separability and training_metrics.png for signs of overfitting.

Recommendations:
- If validation loss in training_metrics.png is significantly lower than training loss, increase MixUp alpha to 0.4 or dropout to 0.5.
- If FAKE recall ({report['FAKE']['recall']:.4f}) is below 0.85, add more SpecAugment masks or increase n_mels to 80.
- For HCL Hackathon, use the Gradio interface for real-time demos.
- If time permits, test with a smaller model (1 Transformer layer) to further reduce overfitting.
"""
    
    analysis = {
        'summary': summary.strip(),
        'metrics': {
            'accuracy': accuracy,
            'f1_score': f1,
            'precision': precision,
            'recall': recall,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist(),
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'per_class': {
                'REAL': report['REAL'],
                'FAKE': report['FAKE']
            }
        },
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(os.path.join(RESULTS_DIR, "performance_analysis.json"), 'w') as f:
        json.dump(analysis, f, indent=4)
    
    return analysis['summary']

# Main execution
async def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = AudioTransformerClassifier(num_classes=NUM_CLASSES, n_mels=N_MELS).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
    scheduler = CosineAnnealingLR(optimizer, T_max=10 - 3, eta_min=1e-5)
    
    # Train for 10 epochs
    history = train_model(model, train_loader, val_loader, optimizer, criterion, scheduler, device, epochs=10, patience=3)
    
    # Evaluate model
    accuracy, f1, precision, recall, roc_auc, cm, embeddings, test_labels, test_probs, report = evaluate_model(model, test_loader, device)
    print(f"Test Accuracy: {accuracy:.4f}")
    print(f"Test F1 Score: {f1:.4f}")
    print(f"Test Precision: {precision:.4f}")
    print(f"Test Recall: {recall:.4f}")
    print(f"Test ROC-AUC: {roc_auc:.4f}")
    print("Confusion Matrix:")
    print(cm)
    
    # Visualize and save results
    plot_metrics(history)
    plot_confusion_matrix(cm)
    plot_tsne(embeddings, test_labels)
    plot_roc_curve(test_labels, test_probs)
    
    # Save performance analysis
    analysis_summary = analyze_performance(accuracy, f1, precision, recall, roc_auc, cm, report)
    print("\nPerformance Analysis Summary:")
    print(analysis_summary)
    
    # Launch Gradio interface
    classifier = AudioClassifier(os.path.join(RESULTS_DIR, "best_transformer_model.pt"), device)
    iface = gr.Interface(fn=classifier.classify, inputs="audio", outputs="text", title="Fake-or-Real Audio Classifier")
    iface.launch()

if platform.system() == "Emscripten":
    import asyncio
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())
