import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import numpy as np
import librosa
from tensorflow.keras.models import load_model

UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'model/lstm_full_94.h5'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
model = load_model(MODEL_PATH)
class_names = ['real', 'fake']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def segment_audio(y, sr=16000, segment_duration=1.0):
    segment_length = int(sr * segment_duration)
    segments = []
    for start in range(0, len(y), segment_length):
        end = start + segment_length
        segment = y[start:end]
        if len(segment) < segment_length:
            segment = np.pad(segment, (0, segment_length - len(segment)))
        segments.append(segment)
    return segments

def preprocess_segment(segment, sr=16000, n_mfcc=40):
    mfcc = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=n_mfcc)
    mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)
    mfcc = np.pad(mfcc, ((0, 0), (0, max(0, 64 - mfcc.shape[1]))), mode='constant')
    mfcc = mfcc[:, :64]
    mfcc = np.expand_dims(mfcc, axis=[0, -1])
    return mfcc

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        y, sr = librosa.load(filepath, sr=16000)
        segments = segment_audio(y, sr=sr)

        results = []
        for i, segment in enumerate(segments):
            x = preprocess_segment(segment, sr=sr)
            prediction = model.predict(x, verbose=0)
            label = class_names[np.argmax(prediction)]
            confidence = float(np.max(prediction))
            results.append({'segment': i+1, 'label': label, 'confidence': round(confidence, 4)})

        return jsonify(results)
    else:
        return jsonify({'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
