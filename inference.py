# inference_func.py (renamed to avoid conflict if inference.py exists)
import torch
import torch.nn as nn
import librosa
import numpy as np
import cv2
import os
import argparse # Keep for example usage block

# --- Constants ---
TARGET_SHAPE = (128, 87) # Must match training
CLASS_MAP = {0: 'Fake', 1: 'Real'}
N_FFT = 2048 # Mel spectrogram parameter
HOP_LENGTH = 512 # Mel spectrogram parameter

# --- Model Definition ---
# Needs to be identical to the architecture saved in the .pth file
# Using the definition for the *original float model* here.
class CustomNeuralNetwork(nn.Module):
    def __init__(self, image_height, image_width, in_channels=1):
        super().__init__()
        self.image_height = image_height
        self.image_width = image_width
        self.in_channels = in_channels

        # Feature Extractor
        self.features = nn.Sequential(
            nn.Conv2d(in_channels=self.in_channels, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        self.flatten = nn.Flatten(start_dim=1)

        # Calculate flattened size dynamically
        with torch.no_grad():
            dummy_input = torch.zeros(1, self.in_channels, self.image_height, self.image_width)
            dummy_output = self.features(dummy_input)
            flattened_size = self.flatten(dummy_output).shape[1]

        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(in_features=flattened_size, out_features=256),
            nn.ReLU(inplace=True),
            nn.Linear(in_features=256, out_features=256),
            nn.ReLU(inplace=True),
            nn.Linear(in_features=256, out_features=2)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.flatten(x)
        x = self.classifier(x)
        return x

# --- Preprocessing Function ---
def preprocess_audio(file_path, target_shape):
    """Loads audio, creates Mel spectrogram, resizes, and prepares tensor."""
    try:
        audio_data, sample_rate = librosa.load(file_path, sr=None)
        n_mels = target_shape[0]

        if len(audio_data) < N_FFT:
            audio_data = np.pad(audio_data, (0, N_FFT - len(audio_data)), mode='constant')

        mel_spectrogram = librosa.feature.melspectrogram(
            y=audio_data, sr=sample_rate, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=n_mels
        )
        mel_db_spectrogram = librosa.power_to_db(mel_spectrogram, ref=np.max)

        if not np.isfinite(mel_db_spectrogram).all():
            mel_db_spectrogram[~np.isfinite(mel_db_spectrogram)] = 0

        resized_spectrogram = cv2.resize(mel_db_spectrogram, target_shape[::-1], interpolation=cv2.INTER_LINEAR)
        tensor = torch.tensor(resized_spectrogram).unsqueeze(0).unsqueeze(0).float()
        return tensor
    except Exception as e:
        print(f"Error during preprocessing {file_path}: {e}")
        raise # Re-raise to be caught by the main function

# --- Prediction Function ---
def predict(model, input_tensor, device):
    """Runs inference and returns predicted label and confidence."""
    model.eval()
    input_tensor = input_tensor.to(device)
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        _, predicted_class = torch.max(outputs, 1)

    predicted_idx = predicted_class.item()
    prediction_label = CLASS_MAP.get(predicted_idx, "Unknown")
    confidence = probabilities[0][predicted_idx].item()
    return prediction_label, confidence

# --- Main Inference Function ---
def run_inference(audio_path: str, model_path: str, device_str: str = 'auto') -> str:
    """
    Loads a trained model, preprocesses an audio file, and returns the predicted class label.

    Args:
        audio_path: Path to the input audio file (.wav).
        model_path: Path to the trained model (.pth file).
        device_str: Device to run on ('auto', 'cuda', 'cpu'). Defaults to 'auto'.

    Returns:
        Predicted class label ('Fake', 'Real') or an error message string starting with "Error:".
    """
    # --- Device Setup ---
    if device_str == 'auto':
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        # Validate device string
        if device_str not in ['cuda', 'cpu']:
             print(f"Warning: Invalid device '{device_str}'. Defaulting to 'auto'.")
             device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
             device = torch.device(device_str)

    # Use print for logging within the function if desired, or use logging module
    # print(f"Using device: {device}")

    # --- Validate inputs ---
    if not os.path.isfile(audio_path):
        return f"Error: Audio file not found at {audio_path}"
    if not os.path.isfile(model_path):
        return f"Error: Model file not found at {model_path}"

    # --- Load Model ---
    try:
        model = CustomNeuralNetwork(
                image_height=TARGET_SHAPE[0],
                image_width=TARGET_SHAPE[1],
                in_channels=1
            )
            # Load the state dictionary.
            # Using strict=False as you had before - be cautious, this might hide problems
            # if the model definition doesn't *truly* match the saved weights.
        model.load_state_dict(torch.load(model_path, map_location=device), strict=False)
        model.to(device)
        model.eval()
    except Exception as e:
        return f"Error: Failed loading the model - {e}" # Return error message

    # --- Preprocess Audio ---
    try:
        input_tensor = preprocess_audio(audio_path, TARGET_SHAPE)
    except Exception as e:
        # Error message already printed in preprocess_audio, return clean error
        return f"Error: Failed processing audio file"

    # --- Perform Inference ---
    try:
        predicted_label, _ = predict(model, input_tensor, device) # Ignore confidence for return value
        return predicted_label # Return the string 'Fake' or 'Real'
    except Exception as e:
        return f"Error: Failed during inference - {e}" # Return error message

# --- Example Usage (Runnable from command line) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify an audio file using the run_inference function.")
    parser.add_argument("audio_path", help="Path to the input audio file (.wav).")
    parser.add_argument("--model_path", required=True, help="Path to the trained model (.pth file).")
    parser.add_argument("--device", default="auto", choices=['auto', 'cuda', 'cpu'], help="Device for inference ('auto', 'cuda', 'cpu'). Default: auto")

    args = parser.parse_args()

    print(f"Running inference for: {args.audio_path}")
    # Call the main inference function
    result = run_inference(
        audio_path=args.audio_path,
        model_path=args.model_path,
        device_str=args.device
    )

    # Print the result nicely
    print("-" * 30)
    print(f"Inference Function Result:")
    print(f"  Audio File: {os.path.basename(args.audio_path)}")
    if result.startswith("Error:"):
        print(f"  Status: {result}")
    else:
        print(f"  Predicted Class: {result}")
    print("-" * 30)
