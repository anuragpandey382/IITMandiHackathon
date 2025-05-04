#!/usr/bin/env python3

# -----------------------------------
# 1. Imports
# -----------------------------------
import os
import cgi
import cgitb
import json
import traceback
import numpy as np
import torch
import torch.nn as nn
import librosa
from torchvision.models import resnet18

# Enable error reporting
cgitb.enable()

# -----------------------------------
# 2. Constants and Paths
# -----------------------------------
SAMPLE_RATE = 16000
DURATION = 1.0
N_MELS = 128
HOP_LENGTH = 512
N_FFT = 2048
UPLOAD_DIR = '/tmp/uploads'
MODEL_PATH = "/usr/lib/cgi-bin/regnet_92.pt"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------------
# 3. Define Model Class
# -----------------------------------
class AudioClassifier(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.resnet = resnet18(pretrained=False)
        self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, num_classes)
    
    def forward(self, x):
        return self.resnet(x)

# -----------------------------------
# 4. Preprocessing Function
# -----------------------------------
def preprocess_audio(file_path):
    audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
    audio = librosa.util.fix_length(audio, size=int(SAMPLE_RATE * DURATION))

    mel_spec = librosa.feature.melspectrogram(
        y=audio, sr=SAMPLE_RATE, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
    )
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)

    return torch.tensor(mel_spec_db, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

# -----------------------------------
# 5. Prediction Function
# -----------------------------------
def infer_audio(file_path, model_path=MODEL_PATH):
    device = torch.device("cpu")
    model = AudioClassifier()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    input_tensor = preprocess_audio(file_path).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        prediction = torch.argmax(output, dim=1).item()

    return "FAKE" if prediction == 1 else "REAL", float(torch.softmax(output, dim=1)[0, prediction].item())

# -----------------------------------
# 6. CGI Handler
# -----------------------------------
print("Content-Type: application/json\n")

try:
    form = cgi.FieldStorage()
    file_field = form['audio_file'] if 'audio_file' in form else None

    if file_field and getattr(file_field, 'filename', None):
        filename = os.path.basename(file_field.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, 'wb') as f:
            f.write(file_field.file.read())

        prediction_label, confidence = infer_audio(filepath, MODEL_PATH)

        response = {
            "status": "success",
            "filename": filename,
            "prediction": prediction_label,
            "confidence": round(confidence, 4)
        }
    else:
        response = {
            "status": "error",
            "message": "No audio file uploaded or field missing."
        }

except Exception as e:
    response = {
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc()
    }

print(json.dumps(response))
