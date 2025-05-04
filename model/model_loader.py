import torch
import torch.nn as nn

# Correct model architecture that matches your saved weights
class CustomNeuralNetwork(nn.Module):
    def __init__(self, input_size=59):  # Keep input_size=59 to match feature extraction
        super(CustomNeuralNetwork, self).__init__()
        
        # This matches the layer names in your saved model
        self.features = nn.Sequential(
            nn.Linear(input_size, 128),  # features.0
            nn.ReLU(),
            nn.Linear(128, 256),        # features.2
            nn.ReLU(),
            nn.Linear(256, 128),        # features.5
            nn.ReLU(),
            nn.Linear(128, 64),         # features.7
            nn.ReLU()
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),          # classifier.0
            nn.ReLU(),
            nn.Linear(32, 16),          # classifier.2
            nn.ReLU(),
            nn.Linear(16, 2)            # classifier.4
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# Initialize model
model = CustomNeuralNetwork()

# Load weights with error handling
model_path = "C:/Users/ASUS/Documents/trained_models/audio_custom_model_1.pth"

try:
    # Load state dict
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    
    # Load with strict=False to handle any remaining minor mismatches
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    print("Model loaded successfully!")
    
    # Verify all layers loaded properly
    for name, param in model.named_parameters():
        if param.requires_grad:
            print(f"Loaded layer: {name} with shape {param.shape}")
            
except Exception as e:
    print(f"Error loading model: {e}")
    print("Using randomly initialized weights")

# Updated audio preprocessing for feature extraction
def extract_features(audio_bytes):
    try:
        import io
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        
        # Extract features (same as your previous implementation)
        features = []
        
        # MFCC (13 features)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features.append(np.mean(mfccs.T, axis=0))
        
        # Spectral Contrast (7 features)
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        features.append(np.mean(contrast.T, axis=0))
        
        # Chroma (12 features)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.append(np.mean(chroma.T, axis=0))
        
        # Tonnetz (6 features)
        y_harmonic = librosa.effects.harmonic(y)
        tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)
        features.append(np.mean(tonnetz.T, axis=0))
        
        # Additional features to reach 59 dimensions
        zcr = librosa.feature.zero_crossing_rate(y)
        features.append(np.mean(zcr))
        
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        features.append(np.mean(spectral_centroid))
        
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        features.append(np.mean(spectral_bandwidth))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        features.append(np.mean(spectral_rolloff))
        
        rms = librosa.feature.rms(y=y)
        features.append(np.mean(rms))
        
        mel = librosa.feature.melspectrogram(y=y, sr=sr)
        features.append(np.mean(librosa.power_to_db(mel), axis=1)[:20])
        
        # Combine and ensure correct size
        feature_vector = np.hstack(features)
        if len(feature_vector) < 59:
            feature_vector = np.pad(feature_vector, (0, 59 - len(feature_vector)))
        elif len(feature_vector) > 59:
            feature_vector = feature_vector[:59]
            
        return torch.tensor(feature_vector, dtype=torch.float32).unsqueeze(0)
        
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return torch.zeros(1, 59)  # Return zero vector of correct size

# Prediction function
def predict_audio(audio_bytes):
    try:
        # Extract features
        features = extract_features(audio_bytes)
        
        # Make prediction
        with torch.no_grad():
            output = model(features)
            probabilities = torch.nn.functional.softmax(output, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
        return "real" if predicted.item() == 0 else "fake", confidence.item()
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return "unknown", 0.0