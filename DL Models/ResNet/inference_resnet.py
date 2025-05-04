import os
import sys
import numpy as np
import torch
import torch.nn as nn
import librosa
from torchvision.models import resnet18

# --- Optional: Check version info for debugging ---
print(f"Python: {sys.version}")
print(f"NumPy: {np.__version__}")
print(f"PyTorch: {torch.__version__}")
try:
    import torchvision
    print(f"Torchvision: {torchvision.__version__}")
except:
    print("Torchvision not found!")

# --- Constants for audio preprocessing ---
SAMPLE_RATE = 16000
DURATION = 1.0
N_MELS = 128
HOP_LENGTH = 512
N_FFT = 2048

# --- Model architecture (must match training) ---
class AudioClassifier(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.resnet = resnet18(pretrained=False)
        self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, num_classes)
    
    def forward(self, x):
        return self.resnet(x)

# --- Preprocessing audio into mel-spectrogram tensor ---
def preprocess_audio(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
    except Exception as e:
        print(f"Error loading audio: {e}")
        audio = np.zeros(int(DURATION * SAMPLE_RATE))

    # Pad or trim to fixed length
    target_len = int(SAMPLE_RATE * DURATION)
    audio = librosa.util.fix_length(audio, size=target_len)

    # Compute mel-spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=audio, sr=SAMPLE_RATE, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
    )
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Normalize
    mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)

    # Convert to tensor [1, 1, n_mels, time]
    return torch.tensor(mel_spec_db, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

# --- Inference function ---
def infer_audio(file_path, model_path="best_model.pt"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load model
    model = AudioClassifier()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # Preprocess and predict
    input_tensor = preprocess_audio(file_path).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        prediction = torch.argmax(output, dim=1).item()

    return "FAKE" if prediction == 1 else "REAL"


 


# Example usage (modify the path to your own test file)
if __name__ == "__main__":
    test_audio_path = r"C:\Users\iksmh\Downloads\test_audio\test_audio\fake.wav"   # <--- Change this to test other files
    model_path = r"C:\Users\iksmh\Downloads\Nalin\regnet_92.pt"
    result = infer_audio(test_audio_path, model_path)
    print(f"Prediction: {result}")
