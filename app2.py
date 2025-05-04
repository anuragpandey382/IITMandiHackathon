import torch
import torchaudio
import librosa
import numpy as np
from io import BytesIO
import tempfile
import wave
# Assuming your model loading is handled elsewhere (as in your Streamlit app)
from model.model_loader import CustomNeuralNetwork, input_height, input_width, num_channels
# model = CustomNeuralNetwork(input_height, input_width, num_channels)
# model_path = 'arjun.pth'
# model.load_state_dict(torch.load(model_path, map_location=torch.device('cuda')))
# model.eval()

RECORDER_SAMPLE_RATE = 16000

def preprocess_audio_inference(audio_file):
    try:
        audio, sample_rate = torchaudio.load(audio_file, format=None)
        if sample_rate != RECORDER_SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=RECORDER_SAMPLE_RATE)
            audio = resampler(audio)

        mel_spec = librosa.feature.melspectrogram(
            y=audio.numpy().astype(float),  # Convert to numpy if needed
            sr=RECORDER_SAMPLE_RATE,
            n_mels=128,
            n_fft=2048,
            hop_length=512
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_spec_db = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min())
        tensor = torch.FloatTensor(mel_spec_db).unsqueeze(0).unsqueeze(0)
        return tensor
    except Exception as e:
        print(f"Error preprocessing audio: {e}")
        return None

def run_inference(audio_file_obj, model):
    try:
        # Save the file-like object to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_file_obj.read())
            temp_file_path = tmp_file.name

        input_tensor = preprocess_audio_inference(temp_file_path)
        if input_tensor is None:
            return None

        with torch.no_grad():
            output = model(input_tensor.to('cuda')) # Ensure model and input are on the same device
            probabilities = torch.softmax(output, dim=1)
            fake_probability = probabilities[0][0].item()
            real_probability = probabilities[0][1].item()

        import os
        os.unlink(temp_file_path) # Clean up the temporary file

        return {
            'fake_probability': fake_probability,
            'real_probability': real_probability
        }
    except Exception as e:
        print(f"Inference error: {e}")
        return None

if __name__ == '__main__':
    # Example usage (for testing inference.py independently)
    # Create a dummy audio file for testing
    sample_rate = 16000
    duration = 2
    frequency = 440
    t = np.linspace(0., duration, int(sample_rate*duration), endpoint=False)
    data = 0.5 * np.sin(2.*np.pi*frequency*t)
    buffer = BytesIO()
    with wave.open(buffer, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((data * 32767).astype(np.int16).tobytes())
    buffer.seek(0)

    # Load a dummy model (replace with your actual loading)
    class DummyModel(torch.nn.Module):
        def __init__(self, in_h, in_w, in_c):
            super().__init__()
            self.fc = torch.nn.Linear(in_h * in_w * in_c, 2)
        def forward(self, x):
            return self.fc(x.flatten())

    dummy_model = DummyModel(input_height, input_width, num_channels)
    dummy_output = run_inference(buffer, dummy_model.eval().to('cuda'))
    print(f"Dummy Inference Result: {dummy_output}")