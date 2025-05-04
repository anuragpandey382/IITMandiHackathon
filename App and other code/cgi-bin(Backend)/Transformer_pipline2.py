#!/usr/bin/env python3

# -----------------------------------
# 1. Imports
# -----------------------------------
import cgi
import cgitb
import json
import os
import traceback
import torch
import torchaudio
import torch.nn.functional as F

# Enable detailed error reporting
cgitb.enable()

# -----------------------------------
# 2. Configuration
# -----------------------------------
UPLOAD_DIR = '/tmp/uploads'
MODEL_PATH = "/usr/lib/cgi-bin/New_Transformer_model_71.pkl"
CLASS_NAMES = ['FAKE', 'REAL']

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, mode=0o777, exist_ok=True)

# -----------------------------------
# 3. Preprocessing Function
# -----------------------------------
def preprocess_raw_audio(path, target_sr=16000, clip_duration=2.0, frame_size=400):
    waveform, sr = torchaudio.load(path)

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)

    num_samples = int(target_sr * clip_duration)
    if waveform.shape[1] > num_samples:
        waveform = waveform[:, :num_samples]
    elif waveform.shape[1] < num_samples:
        waveform = F.pad(waveform, (0, num_samples - waveform.shape[1]))

    waveform = waveform.squeeze(0)

    remainder = waveform.shape[0] % frame_size
    if remainder != 0:
        pad_len = frame_size - remainder
        waveform = F.pad(waveform, (0, pad_len))

    return waveform.unsqueeze(0)

# -----------------------------------
# 4. Load Model Once
# -----------------------------------
try:
    model = torch.load(MODEL_PATH, map_location='cpu')
    model.eval()
except Exception as e:
    print("Content-Type: application/json\n")
    print(json.dumps({"status": "error", "message": f"Model loading failed: {str(e)}"}))
    exit()

# -----------------------------------
# 5. Handle CGI Request
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

        # Preprocess and predict
        waveform = preprocess_raw_audio(filepath)
        with torch.no_grad():
            output = model(waveform)
            predicted_class = torch.argmax(output, dim=1).item()
            probs = torch.softmax(output, dim=1)
            confidence = float(probs[0, predicted_class].item())
            label = CLASS_NAMES[predicted_class]

        result = {
            "status": "success",
            "filename": filename,
            "prediction": label,
            "confidence": round(confidence, 4)
        }

    else:
        result = {
            "status": "error",
            "message": "No audio file uploaded."
        }

except Exception as e:
    result = {
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc()
    }

print(json.dumps(result))
