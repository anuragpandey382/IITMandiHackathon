import streamlit as st
import sounddevice as sd
import numpy as np
import torch
from scipy.io.wavfile import write
from pydub import AudioSegment
import io
import matplotlib.pyplot as plt
from I_love_hackathons import feature_extractor, Classifier

# ✅ Device setup (CUDA if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ✅ Load model and move to device
model = Classifier().to(device)
model.load_state_dict(torch.load(r"C:\Users\boral\Desktop\Streamlit\LOOOONG_TRAIN.pth", map_location=device))
model.eval()

# ✅ Language labels
langs = {0: 'Bengali', 1: 'Gujarati', 2: 'Hindi', 3: 'Kannada', 4: 'Malayalam', 5: 'Marathi', 6: 'Punjabi', 7: 'Tamil', 8: 'Telugu', 9: 'Urdu'}

# ✅ Predict language function
def predict_language(file):
    data = feature_extractor(file)
    custom_features_tensor = torch.tensor(data, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(custom_features_tensor)
    predictions = torch.argmax(outputs, dim=1).cpu().numpy()
    return langs[int(predictions)]

# ✅ Function to visualize waveform
def plot_waveform(data, fs):
    fig, ax = plt.subplots()
    times = np.arange(len(data)) / fs
    ax.plot(times, data, color='orange')
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Amplitude")
    ax.set_title("Live Audio Waveform")
    st.pyplot(fig)

# ✅ Streamlit UI
st.title("🎙️ AWAZ - Live Voice Recognition ")

st.sidebar.markdown(f"**CUDA Available:** `{torch.cuda.is_available()}`")
if torch.cuda.is_available():
    st.sidebar.markdown(f"**Using Device:** `{torch.cuda.get_device_name(0)}`")

# ✅ Recording parameters
fs = 44100  # Sample rate
clip_duration = 5  # seconds

# Initialize session state
if 'listening' not in st.session_state:
    st.session_state.listening = False

# ✅ Start and Stop Listening button handling
start_button = st.button("🎛️ Start Listening")
stop_button = st.button("⏹️ Stop Listening")

if start_button:
    st.session_state.listening = True
    st.success("Listening live... speak now 🎤")
    audio_placeholder = st.empty()
    waveform_placeholder = st.empty()

    try:
        while st.session_state.listening:
            # Record 5 seconds
            recording = sd.rec(int(clip_duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()

            # Save to WAV bytes
            buf = io.BytesIO()
            write(buf, fs, recording)
            buf.seek(0)

            # Predict language
            try:
                result = predict_language(buf)
                audio_placeholder.success(f"📝 Prediction: {result}")
            except Exception as e:
                audio_placeholder.error(f"Prediction Error: {e}")

            # Plot waveform
            data = recording.flatten()
            waveform_placeholder.empty()
            with waveform_placeholder.container():
                plot_waveform(data, fs)

    except KeyboardInterrupt:
        st.warning("Stopped listening.")

elif stop_button:
    st.session_state.listening = False
    st.warning("Listening stopped.")
