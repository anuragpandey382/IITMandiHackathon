import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'models')))
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import torch
from model.model_loader import  preprocess_audio
import uvicorn

app = FastAPI()

# Allow CORS (for Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once at startup
# model = load_model("model.pth")
LABELS = ["REAL", "FAKE"]

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    audio_tensor = preprocess_audio(audio_bytes)
    audio_tensor = audio_tensor.unsqueeze(0)  # Add batch dimension

    with torch.no_grad():
        logits = model(audio_tensor)
        probs = torch.softmax(logits, dim=1)
        pred_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_class].item()

    return {
        "prediction": LABELS[pred_class],
        "confidence": confidence
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)

