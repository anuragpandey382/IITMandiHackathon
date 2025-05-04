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
from torchvision.models import mobilenet_v2
import gradio as gr
from audiomentations import Compose, AddGaussianNoise, TimeStretch, PitchShift
import noisereduce as nr
import warnings
import json
from datetime import datetime
from collections import Counter
warnings.filterwarnings("ignore")

# Define dataset paths
BASE_PATH = "/home/sp_students/.cache/kagglehub/datasets/prathav01022002/for-norm/versions/1/for-norm"
TRAIN_PATH = os.path.join(BASE_PATH, "training")
VAL_PATH = os.path.join(BASE_PATH, "validation")
TEST_PATH = os.path.join(BASE_PATH, "testing")

# Create results directory
RESULTS_DIR = "results_" + datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Check dataset existence, download if needed
if not os.path.exists(BASE_PATH):
    print(f"Dataset not found at {BASE_PATH}. Downloading...")
    try:
        path = kagglehub.dataset_download("prathav01022002/for-norm")
        print("Path to downloaded dataset files:", path)
        BASE_PATH = path
        TRAIN_PATH = os.path.join(BASE_PATH, "training")
        VAL_PATH = os.path.join(BASE_PATH, "validation")
        TEST_PATH = os.path.join(BASE_PATH, "testing")
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        exit(1)
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
N_MELS = 64
HOP_LENGTH = 512
N_FFT = 1024

# Enhanced data augmentation (removed Gain due to parameter error)
augment = Compose([
    AddGaussianNoise(min_amplitude=0.02, max_amplitude=0.08, p=0.9),  # Stronger noise for test robustness
    TimeStretch(min_rate=0.5, max_rate=1.5, p=0.8),  # Wider range
    PitchShift(min_semitones=-8, max_semitones=8, p=0.8)  # Wider pitch
])

# Custom Dataset class with noise reduction
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
            audio = nr.reduce_noise(y=audio, sr=SAMPLE_RATE, stationary=False)
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

# Load dataset and check class distribution
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
    print(f"Class distribution: {Counter(labels)}")
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

# Compute class weights
class_counts = Counter(train_labels)
total_samples = len(train_labels)
class_weights = torch.tensor([total_samples / (len(class_counts) * class_counts[i]) for i in range(len(class_counts))], dtype=torch.float32).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

# Create datasets and dataloaders
train_dataset = AudioDataset(train_files, train_labels, augment=True)
val_dataset = AudioDataset(val_files, val_labels, augment=False)
test_dataset = AudioDataset(test_files, test_labels, augment=False)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4, pin_memory=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4, pin_memory=True)

# Lightweight model with dropout
class AudioClassifier(nn.Module):
    def __init__(self, num_classes=2, dropout_rate=0.5):
        super().__init__()
        self.mobilenet = mobilenet_v2(pretrained=True)
        self.mobilenet.features[0][0] = nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1, bias=False)
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(self.mobilenet.classifier[1].in_features, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)

# Count model parameters
def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

# Training function with early stopping
def train_model(model, train_loader, val_loader, optimizer, criterion, scheduler, device, epochs=50, patience=5):
    model.to(device)
    best_val_f1 = 0.0
    epochs_no_improve = 0
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
        val_preds, val_true, val_embeddings = [], [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                preds = torch.argmax(outputs, dim=1)
                val_preds.extend(preds.cpu().numpy())
                val_true.extend(labels.cpu().numpy())
                features = model.mobilenet.features(inputs).mean([2, 3])
                val_embeddings.extend(features.cpu().numpy())
        
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
        
        # t-SNE visualization every 10 epochs
        if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
            plot_tsne(np.array(val_embeddings), np.array(val_true), f"val_epoch_{epoch+1}")
        
        # Save best model and check early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "best_model.pt"))
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
        
        scheduler.step(val_loss)
        
        if epochs_no_improve >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    with open(os.path.join(RESULTS_DIR, "training_history.json"), 'w') as f:
        json.dump(history, f, indent=4)
    
    return history

# Evaluation function
def evaluate_model(model, test_loader, device):
    model.eval()
    preds, true, embeddings = [], [], []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            preds.extend(torch.argmax(outputs, dim=1).cpu().numpy())
            true.extend(labels.cpu().numpy())
            features = model.mobilenet.features(inputs).mean([2, 3])
            embeddings.extend(features.cpu().numpy())
    
    accuracy = accuracy_score(true, preds)
    f1_scores = f1_score(true, preds, average=None)
    precision = precision_score(true, preds, average=None)
    recall = recall_score(true, preds, average=None)
    cm = confusion_matrix(true, preds)
    report = classification_report(true, preds, target_names=['REAL', 'FAKE'], output_dict=True)
    
    # Detailed confusion matrix analysis
    cm_analysis = {
        'True Positives (FAKE)': cm[1, 1],
        'True Negatives (REAL)': cm[0, 0],
        'False Positives': cm[0, 1],
        'False Negatives': cm[1, 0],
        'Analysis': (
            f"Model correctly identifies {cm[1, 1]} FAKE and {cm[0, 0]} REAL samples. "
            f"False positives ({cm[0, 1]}): REAL audio misclassified as FAKE, possibly due to noise or spectral overlap. "
            f"False negatives ({cm[1, 0]}): FAKE audio misclassified as REAL, likely due to test FAKE audio resembling REAL audio. "
            f"High false negatives suggest the need for more diverse FAKE audio augmentation or test set alignment."
        )
    }
    
    eval_results = {
        'accuracy': accuracy,
        'f1_scores': {'REAL': f1_scores[0], 'FAKE': f1_scores[1]},
        'precision': {'REAL': precision[0], 'FAKE': precision[1]},
        'recall': {'REAL': recall[0], 'FAKE': recall[1]},
        'confusion_matrix': cm.tolist(),
        'cm_analysis': cm_analysis,
        'classification_report': report
    }
    with open(os.path.join(RESULTS_DIR, "evaluation_results.json"), 'w') as f:
        json.dump(eval_results, f, indent=4)
    
    return accuracy, f1_scores, cm, np.array(embeddings), np.array(true)

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

def plot_tsne(embeddings, labels, stage="test"):
    tsne = TSNE(n_components=2, random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=labels, cmap='viridis', alpha=0.6)
    plt.colorbar(scatter, ticks=[0, 1], label='Class (0=REAL, 1=FAKE)')
    plt.title(f't-SNE Visualization of Embeddings ({stage})')
    plt.savefig(os.path.join(RESULTS_DIR, f'tsne_{stage}.png'))
    plt.close()

# Gradio interface
def classify_audio(audio):
    if audio is None:
        return "No audio provided."
    
    try:
        audio, sr = librosa.load(audio, sr=SAMPLE_RATE, duration=DURATION)
        audio = nr.reduce_noise(y=audio, sr=SAMPLE_RATE, stationary=False)
    except Exception as e:
        print(f"Error processing audio: {e}")
        return "Error processing audio."
    
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
    try:
        model.load_state_dict(torch.load(os.path.join(RESULTS_DIR, "best_model.pt")))
    except Exception as e:
        print(f"Error loading model: {e}")
        return "Error loading model."
    
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
    
    model = AudioClassifier(dropout_rate=0.5).to(device)
    print(f"Model parameters: {count_parameters(model):,}")
    
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=3)
    
    # Train model
    history = train_model(model, train_loader, val_loader, optimizer, criterion, scheduler, device, epochs=50, patience=5)
    
    # Evaluate model
    accuracy, f1_scores, cm, embeddings, test_labels = evaluate_model(model, test_loader, device)
    print(f"Test Accuracy: {accuracy:.4f}")
    print(f"F1 Scores: REAL={f1_scores[0]:.4f}, FAKE={f1_scores[1]:.4f}")
    print("Confusion Matrix:")
    print(cm)
    
    # Visualize results
    plot_metrics(history)
    plot_confusion_matrix(cm)
    plot_tsne(embeddings, test_labels, "test")
    
    # Launch Gradio interface
    try:
        iface = gr.Interface(
            fn=classify_audio,
            inputs=gr.Audio(source="microphone", type="filepath"),
            outputs="text",
            title="Real-time Audio Classifier",
            description="Record or upload audio to classify as REAL or FAKE."
        )
        iface.launch()
    except Exception as e:
        print(f"Error launching Gradio interface: {e}")
