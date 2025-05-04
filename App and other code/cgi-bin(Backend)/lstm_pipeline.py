#!/usr/bin/env python3

import cgi
import cgitb
import json
import os
import traceback

try: 
    import librosa
    import numpy as np
    from tensorflow.keras.models import load_model

    # Enable debugging
    cgitb.enable()

    # === Configuration ===
    UPLOAD_DIR = '/tmp/uploads'
    MODEL_PATH = "/usr/lib/cgi-bin/lstm_full_94.h5"  # Update this path if needed
    CLASS_NAMES = ['real', 'fake']

    # Create upload directory if not exists
    os.makedirs(UPLOAD_DIR, mode=0o777, exist_ok=True)

    # === Model Loading ===
    try:
        model = load_model(MODEL_PATH)
    except Exception as e:
        print("Content-Type: application/json\n")
        print(json.dumps({"error": f"Failed to load model: {str(e)}"}))
        exit()

    # === Preprocessing ===
    def load_and_pad(file_path, sr=16000):
        try:
            y, _ = librosa.load(file_path, sr=sr)
            if len(y) < sr:
                y = np.pad(y, (0, sr - len(y)))
            return y
        except Exception as e:
            print(f"Error loading audio: {e}")
            return None

    def preprocess_single_file(file_path, sr=16000, n_mfcc=40):
        y = load_and_pad(file_path, sr=sr)
        if y is None:
            raise ValueError("Audio loading failed")

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

        if mfcc.shape[1] < 64:
            pad_width = 64 - mfcc.shape[1]
            mfcc = np.pad(mfcc, ((0, 0), (0, pad_width)))
        else:
            mfcc = mfcc[:, :64]

        mfcc = np.expand_dims(mfcc.T, axis=0)  # shape: (1, 64, 40)
        return mfcc

    # === Handle CGI Input ===
    print("Content-Type: application/json\n")

    try:
        form = cgi.FieldStorage()
        file_field = form['audio_file'] if 'audio_file' in form else None

        if file_field and getattr(file_field, 'filename', None):
            filename = os.path.basename(file_field.filename)
            filepath = os.path.join(UPLOAD_DIR, filename)

            # Save uploaded file
            with open(filepath, 'wb') as f:
                f.write(file_field.file.read())

            # Preprocess and predict
            processed_input = preprocess_single_file(filepath)
            prediction = model.predict(processed_input)
            predicted_class = int(np.argmax(prediction))
            confidence = float(prediction[0][predicted_class])

            # Return prediction
            result = {
                "status": "success",
                "filename": filename,
                "predicted_class": CLASS_NAMES[predicted_class],
                "confidence": round(confidence, 4)
            }
        else:
            result = {
                "status": "error",
                "message": "No file uploaded or invalid field name."
            }

    except Exception as e:
        result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
except Exception as e:
        result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

print(json.dumps(result))
