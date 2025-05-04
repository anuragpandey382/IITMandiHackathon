#!/usr/bin/env python3

import cgi
import cgitb
import json
import os
import traceback
import librosa
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

# Enable CGI traceback debugging
cgitb.enable()

# Constants
UPLOAD_DIR = '/tmp/uploads'
MODEL_PATH = '/path/to/vgg16_full_86.h5'  # <-- UPDATE this path
CLASS_NAMES = ['real', 'fake']

# Make sure upload directory exists
os.makedirs(UPLOAD_DIR, mode=0o777, exist_ok=True)

def load_and_pad(file_path, sr=16000):
    y, _ = librosa.load(file_path, sr=sr)
    if len(y) < sr:
        y = np.pad(y, (0, sr - len(y)))
    return y

def preprocess_single_file_vgg(file_path, sr=16000, n_mfcc=40):
    y = load_and_pad(file_path, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

    if mfcc.shape[1] < 64:
        pad_width = 64 - mfcc.shape[1]
        mfcc = np.pad(mfcc, ((0, 0), (0, pad_width)))
    else:
        mfcc = mfcc[:, :64]

    mfcc_resized = tf.image.resize(mfcc[..., np.newaxis], [40, 64]).numpy()
    mfcc_rgb = np.repeat(mfcc_resized, 1, axis=-1)
    mfcc_rgb = np.expand_dims(mfcc_rgb, axis=0)
    return mfcc_rgb

# Load model once (global reuse)
try:
    model = load_model(MODEL_PATH)
except Exception as e:
    print("Content-Type: application/json\n")
    print(json.dumps({"error": f"Model loading failed: {str(e)}"}))
    exit()

# Handle form input
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
        input_tensor = preprocess_single_file_vgg(filepath)
        prediction = model.predict(input_tensor)
        predicted_class = int(np.argmax(prediction))
        confidence = float(prediction[0][predicted_class])

        # Prepare response
        response = {
            "status": "success",
            "filename": filename,
            "prediction": CLASS_NAMES[predicted_class],
            "confidence": round(confidence, 4)
        }
    else:
        response = {
            "status": "error",
            "message": "No file uploaded or filename missing"
        }

except Exception as e:
    response = {
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc()
    }

print(json.dumps(response))
