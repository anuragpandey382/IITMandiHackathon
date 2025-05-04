import os
import glob
import numpy as np
import pandas as pd
import librosa
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, precision_score, recall_score, classification_report
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import kagglehub
from torchvision.models import resnet18
import gradio as gr
from audiomentations import Compose, AddGaussianNoise, TimeStretch, PitchShift
import warnings
import json
from datetime import datetime
warnings.filterwarnings("ignore")

# Define dataset paths
BASE_PATH = "/home/sp_students/.cache/kagglehub/datasets/prathav01022002/for-norm/versions/1/for-norm"
TRAIN_PATH = os.path.join(BASE_PATH, "training")
VAL_PATH = os.path.join(BASE_PATH, "validation")
TEST_PATH = os.path.join(BASE_PATH, "testing")

# Create results directory
RESULTS_DIR = "results_" + datetime.now().strftime("%Y%m%d_%H%M%S")
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

# Debug: Print directory structure
def print_directory_structure(path):
    print(f"Directory structure for {path}:")
    for root, dirs, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in files[:5]:
            print(f"{indent}    {f}")
        if len(files) > 5:
            print(f"{indent}    ... ({len(files)} total files)")

print_directory_structure(BASE_PATH)

# Audio preprocessing parameters
SAMPLE_RATE = 16000
DURATION = 3.0
N_MELS = 128
HOP_LENGTH = 512
N_FFT = 2048

# Data augmentation
augment = Compose([
    AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
    TimeStretch(min_rate=0.8, max_rate=1.2, p=0.5),
    PitchShift(min_semitones=-4, max_semitones=4, p=0.5)
])

# Custom Dataset class
class AudioDataset(Dataset):
    def __init__(self, file_paths, labels, augment=False):
        self.file_paths = file_paths
        self.labels = labels
        self.augment = augment

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        try:
            audio, sr = librosa.load(self.file_paths[idx], sr=SAMPLE_RATE, duration=DURATION)
        except Exception as e:
            print(f"Error loading {self.file_paths[idx]}: {e}")
            audio = np.zeros(int(DURATION * SAMPLE_RATE))
            sr = SAMPLE_RATE
        
        target_length = int(DURATION * SAMPLE_RATE)
        if len(audio) < target_length:
            audio = np.pad(audio, (0, target_length - len(audio)))
        else:
            audio = audio[:target_length]
        
        if self.augment:
            audio = augment(audio, sample_rate=SAMPLE_RATE)
        
        mel_spec = librosa.feature.melspectrogram(
            y=audio, sr=SAMPLE_RATE, n_mels=N_MELS, hop_length=HOP_LENGTH, n_fft=N_FFT
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
        mel_spec_tensor = torch.tensor(mel_spec_db, dtype=torch.float32).unsqueeze(0)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return mel_spec_tensor, label

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
train_dataset = AudioDataset(train_files, train_labels, augment=True)
val_dataset = AudioDataset(val_files, val_labels, augment=False)
test_dataset = AudioDataset(test_files, test_labels, augment=False)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4, pin_memory=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4, pin_memory=True)

# Define CNN model
class AudioClassifier(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.resnet = resnet18(pretrained=True)
        self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, num_classes)
    
    def forward(self, x):
        return self.resnet(x)

# Training function with enhanced statistics
def train_model(model, train_loader, val_loader, optimizer, criterion, device, epochs=50):
    model.to(device)
    best_val_f1 = 0.0
    history = {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_f1': [], 'val_precision': [], 'val_recall': []}
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * inputs.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        model.eval()
        val_loss = 0.0
        val_preds, val_true = [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                preds = torch.argmax(outputs, dim=1)
                val_preds.extend(preds.cpu().numpy())
                val_true.extend(labels.cpu().numpy())
        
        val_loss /= len(val_loader.dataset)
        val_acc = accuracy_score(val_true, val_preds)
        val_f1 = f1_score(val_true, val_preds, average='macro')
        val_precision = precision_score(val_true, val_preds, average='macro')
        val_recall = recall_score(val_true, val_preds, average='macro')
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['val_f1'].append(val_f1)
        history['val_precision'].append(val_precision)
        history['val_recall'].append(val_recall)
        
        print(f"Epoch {epoch+1}/{epochs}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
              f"Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}, Val Precision: {val_precision:.4f}, Val Recall: {val_recall:.4f}")
        
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "best_model.pt"))
    
    # Save training history
    with open(os.path.join(RESULTS_DIR, "training_history.json"), 'w') as f:
        json.dump(history, f, indent=4)
    
    return history

# Evaluation function with detailed statistics
def evaluate_model(model, test_loader, device):
    model.eval()
    preds, true = [], []
    embeddings = []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            preds.extend(torch.argmax(outputs, dim=1).cpu().numpy())
            true.extend(labels.cpu().numpy())
            features = model.resnet.avgpool(model.resnet.layer4(model.resnet.layer3(
                model.resnet.layer2(model.resnet.layer1(model.resnet.maxpool(
                    model.resnet.relu(model.resnet.bn1(model.resnet.conv1(inputs))))
                ))
            ))).squeeze(-1).squeeze(-1)
            embeddings.extend(features.cpu().numpy())
    
    accuracy = accuracy_score(true, preds)
    f1 = f1_score(true, preds, average='macro')
    precision = precision_score(true, preds, average='macro')
    recall = recall_score(true, preds, average='macro')
    cm = confusion_matrix(true, preds)
    report = classification_report(true, preds, target_names=['REAL', 'FAKE'], output_dict=True)
    
    # Save evaluation results
    eval_results = {
        'accuracy': accuracy,
        'f1_score': f1,
        'precision': precision,
        'recall': recall,
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }
    with open(os.path.join(RESULTS_DIR, "evaluation_results.json"), 'w') as f:
        json.dump(eval_results, f, indent=4)
    
    return accuracy, f1, precision, recall, cm, np.array(embeddings), np.array(true)

# Visualization functions
def plot_metrics(history):
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Loss Curves')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(2, 2, 2)
    plt.plot(history['val_acc'], label='Val Accuracy')
    plt.plot(history['val_f1'], label='Val F1 Score')
    plt.title('Validation Metrics')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
    plt.legend()
    
    plt.subplot(2, 2, 3)
    plt.plot(history['val_precision'], label='Val Precision')
    plt.plot(history['val_recall'], label='Val Recall')
    plt.title('Precision and Recall')
    plt.xlabel('Epoch')
    plt.ylabel('Score')
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

# Gradio interface
def classify_audio(audio):
    if audio is None:
        return "No audio provided."
    
    audio, sr = librosa.load(audio, sr=SAMPLE_RATE, duration=DURATION)
    target_length = int(DURATION * SAMPLE_RATE)
    if len(audio) < target_length:
        audio = np.pad(audio, (0, target_length - len(audio)))
    else:
        audio = audio[:target_length]
    
    mel_spec = librosa.feature.melspectrogram(
        y=audio, sr=SAMPLE_RATE, n_mels=N_MELS, hop_length=HOP_LENGTH, n_fft=N_FFT
    )
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
    mel_spec_tensor = torch.tensor(mel_spec_db, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    
    model = AudioClassifier()
    model.load_state_dict(torch.load(os.path.join(RESULTS_DIR, "best_model.pt")))
    model.eval()
    model.to(device)
    
    with torch.no_grad():
        output = model(mel_spec_tensor.to(device))
        pred = torch.argmax(output, dim=1).cpu().numpy()[0]
    
    return "FAKE" if pred == 1 else "REAL"

# Main execution
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = AudioClassifier().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    
    # Train for 50 epochs
    history = train_model(model, train_loader, val_loader, optimizer, criterion, device, epochs=50)
    
    # Evaluate model
    accuracy, f1, precision, recall, cm, embeddings, test_labels = evaluate_model(model, test_loader, device)
    print(f"Test Accuracy: {accuracy:.4f}")
    print(f"Test F1 Score: {f1:.4f}")
    print(f"Test Precision: {precision:.4f}")
    print(f"Test Recall: {recall:.4f}")
    print("Confusion Matrix:")
    print(cm)
    
    # Visualize and save results
    plot_metrics(history)
    plot_confusion_matrix(cm)
    plot_tsne(embeddings, test_labels)
    
    # Launch Gradio interface
    iface = gr.Interface(fn=classify_audio, inputs="audio", outputs="text")
    iface.launch()
