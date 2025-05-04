#!/home/prem/anaconda3/bin/python3
import os
import sys
import cgi
import cgitb
import json
import traceback

# Send HTTP header
print("Content-Type: application/json")
print()
# Debug header send
print("DEBUG: Header sent", file=sys.stderr, flush=True)
# Enable CGI traceback logging
cgitb.enable(display=0, logdir="/tmp")

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio

# -----------------------------------
# Constants and Paths
# -----------------------------------
SAMPLE_RATE = 16000
DURATION = 1.0  # seconds
N_MELS = 128
HOP_LENGTH = 512
N_FFT = 2048
UPLOAD_DIR = '/tmp/uploads'
MODEL_PATH = "/usr/lib/cgi-bin/regnet_92.pt"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------------
# Model Definition
# -----------------------------------
class AudioClassifier(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.resnet = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=False)
        # adapt first conv layer for single-channel
        self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        # adapt final fully-connected layer
        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, num_classes)

    def forward(self, x):
        return self.resnet(x)

# -----------------------------------
# Preprocessing using torchaudio
# -----------------------------------
def preprocess_audio(file_path):
    # Load waveform
    waveform, sr = torchaudio.load(file_path)
    # Resample if needed
    if sr != SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=SAMPLE_RATE)
        waveform = resampler(waveform)
    # Fix length (pad or truncate)
    num_samples = int(SAMPLE_RATE * DURATION)
    if waveform.shape[1] < num_samples:
        waveform = F.pad(waveform, (0, num_samples - waveform.shape[1]))
    else:
        waveform = waveform[:, :num_samples]
    # Compute mel-spectrogram
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS
    )
    mel_spec = mel_transform(waveform)  # shape: [channels, n_mels, time]
    # Convert to decibels
    db_transform = torchaudio.transforms.AmplitudeToDB()
    mel_spec_db = db_transform(mel_spec)
    # Normalize
    mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
    # Add batch dimension
    return mel_spec_db.unsqueeze(0)  # shape: [1, channels, n_mels, time]

# -----------------------------------
# Inference Function
# -----------------------------------
def infer_audio(file_path, model_path=MODEL_PATH):
    device = torch.device('cpu')
    model = AudioClassifier()
    # Load state dict
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # Preprocess and predict
    input_tensor = preprocess_audio(file_path).to(device)
    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)[0]
        prediction = torch.argmax(probs).item()
        confidence = float(probs[prediction].item())

    label = 'FAKE' if prediction == 1 else 'REAL'
    return label, confidence

# -----------------------------------
# CGI Handling
# -----------------------------------
response = {}
try:
    form = cgi.FieldStorage()
    file_field = form.getfirst('audio_file')  # raw filename if present
    if 'audio_file' in form and getattr(form['audio_file'], 'filename', None):
        uploaded = form['audio_file']
        filename = os.path.basename(uploaded.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as out_file:
            out_file.write(uploaded.file.read())
        print(f"DEBUG: File saved to {filepath}", file=sys.stderr, flush=True)

        label, conf = infer_audio(filepath)
        response = {
            'status': 'success',
            'filename': filename,
            'prediction': label,
            'confidence': round(conf, 4)
        }
    else:
        response = {
            'status': 'error',
            'message': 'No audio file uploaded or field missing.'
        }
except Exception as e:
    tb = traceback.format_exc()
    print(f"DEBUG: Exception: {e}\n{tb}", file=sys.stderr, flush=True)
    response = {
        'status': 'error',
        'message': str(e),
        'traceback': tb
    }

# Output JSON
print(json.dumps(response))
