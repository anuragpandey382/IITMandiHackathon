#!/home/prem/anaconda3/bin/python3
import os

# Disable all Numba JIT (so Librosa never tries to cache)
cache_dir = "/tmp/numba_cache"
os.makedirs(cache_dir, exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = cache_dir

import cgi, cgitb, json, traceback, sys

# 1) Header—tjek at den altid skrives
print("Content-Type: application/json\n")
print("DEBUG: Header sent", file=sys.stderr, flush=True)

# Fejlsporing via cgitb til logfil
cgitb.enable(display=0, logdir="/tmp")
# Disable all Numba JIT (so Librosa never tries to cache)
os.environ["NUMBA_DISABLE_JIT"] = "1"

UPLOAD_DIR = '/tmp/uploads'
MODEL_PATH = '/usr/lib/cgi-bin/lstm_full_94.h5'
print(f"DEBUG: UPLOAD_DIR={UPLOAD_DIR}, MODEL_PATH={MODEL_PATH}", file=sys.stderr, flush=True)

# Lav upload-mappe
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print("DEBUG: Upload dir ok", file=sys.stderr, flush=True)
except Exception as e:
    print(f"DEBUG: Failed to mkdir: {e}", file=sys.stderr, flush=True)

result = {}
try:
    # 2) Model load
    from tensorflow.keras.models import load_model
    print("DEBUG: Imported load_model", file=sys.stderr, flush=True)
    model = load_model(MODEL_PATH)
    print("DEBUG: Model loaded", file=sys.stderr, flush=True)

    import librosa, numpy as np
    print("DEBUG: Imported librosa & numpy", file=sys.stderr, flush=True)

    form = cgi.FieldStorage()
    print(f"DEBUG: Fields: {list(form.keys())}", file=sys.stderr, flush=True)

    if 'audio_file' not in form or not form['audio_file'].filename:
        raise ValueError("No file under 'audio_file'")
    fileitem = form['audio_file']
    filename = os.path.basename(fileitem.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    print(f"DEBUG: Saving to {filepath}", file=sys.stderr, flush=True)

    with open(filepath, 'wb') as f:
        data = fileitem.file.read()
        print(f"DEBUG: Read {len(data)} bytes from upload", file=sys.stderr, flush=True)
        f.write(data)
    print("DEBUG: File written", file=sys.stderr, flush=True)

    # 3) Preprocess
    def load_and_pad(fp, sr=16000):
        print("DEBUG: load_and_pad start", file=sys.stderr, flush=True)
        y, _ = librosa.load(fp, sr=sr)
        print(f"DEBUG: Loaded audio length={len(y)}", file=sys.stderr, flush=True)
        y = np.pad(y, (0, max(0, sr-len(y))))
        return y

    def preprocess(fp):
        print("DEBUG: preprocess start", file=sys.stderr, flush=True)
        y = load_and_pad(fp)
        mfcc = librosa.feature.mfcc(y=y, sr=16000, n_mfcc=40)
        print(f"DEBUG: MFCC shape={mfcc.shape}", file=sys.stderr, flush=True)
        mfcc = (mfcc - mfcc.mean())/(mfcc.std()+1e-8)
        if mfcc.shape[1] < 64:
            mfcc = np.pad(mfcc, ((0,0),(0,64-mfcc.shape[1])))
        else:
            mfcc = mfcc[:,:64]
        arr = np.expand_dims(mfcc.T, axis=0)
        print(f"DEBUG: Preprocessed array shape={arr.shape}", file=sys.stderr, flush=True)
        return arr

    arr = preprocess(filepath)
    print("DEBUG: Calling model.predict", file=sys.stderr, flush=True)
    preds = model.predict(arr)
    print(f"DEBUG: Prediction done: {preds}", file=sys.stderr, flush=True)

    idx = int(np.argmax(preds))
    result = {
        "status": "success",
        "filename": filename,
        "predicted_class": ['real','fake'][idx],
        "confidence": float(round(preds[0][idx],4))
    }

except Exception as e:
    # 4) Exception—log detaljeret
    tb = traceback.format_exc()
    print(f"DEBUG: Exception: {str(e)}", file=sys.stderr, flush=True)
    print(f"DEBUG: Traceback:\n{tb}", file=sys.stderr, flush=True)
    result = {"status":"error","message":str(e),"traceback":tb}

print(json.dumps(result))
