# --- Must be at the very top ---
import streamlit as st
st.set_page_config(page_title="Speech DeepFake Detector", page_icon="???", layout="wide")

# --- Imports ---
import numpy as np
import time
import io
import torch
from audio_recorder_streamlit import audio_recorder
from model.model_loader import CustomNeuralNetwork, input_height, input_width, num_channels
from inference import run_inference

# --- Constants ---
MAX_RECORDING_DURATION_S = 4
RECORDER_SAMPLE_RATE = 16000
MODEL_PATH = 'arjun.pth'

# --- Load Model with Caching ---
@st.cache_resource
def load_model():
    model = CustomNeuralNetwork(input_height, input_width, num_channels)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cuda')))
    model.eval()
    return model

model_main = load_model()

# --- Preprocessing Audio ---
def preprocess_audio(audio_bytes):
    if isinstance(audio_bytes, bytes):
        with open("audio.wav", "wb") as f:
            f.write(audio_bytes)
        return "audio.wav"
    else:
        st.error("Audio data is not in byte format.")
        return None

# --- Inference Function ---
def get_prediction(audio_bytes):
    start_time = time.time()
    audio_path = preprocess_audio(audio_bytes)
    if not audio_path:
        return "? Invalid audio input."
    
    output = run_inference(audio_path=audio_path, model_path=MODEL_PATH, device_str='cuda')
    processing_time = time.time() - start_time
    return f"Prediction: {output} | Time: {processing_time:.2f}s"

# --- Initialize Session State ---
if 'analysis_done' not in st.session_state:
    st.session_state.update({
        'analysis_done': False,
        'current_prediction': None,
        'audio_ready': False,
        'audio_bytes': None,
        'filename': None
    })

# --- Sidebar Input ---
with st.sidebar:
    st.title("TRUTH-OR-TRAP")
    st.markdown("**AI Speech Classifier**\n\nDetect synthetic speech using a deep learning classifier.")

    input_method = st.radio("Input Method", ["?? Record Live", "?? Upload File"], index=0)
    st.markdown("---")

    if input_method == "?? Record Live":
        st.write("Record audio (max 4 seconds):")
        audio_bytes = audio_recorder(
            energy_threshold=(-1.0, 1.0),
            pause_threshold=MAX_RECORDING_DURATION_S,
            sample_rate=RECORDER_SAMPLE_RATE,
            recording_color="#e74c3c",
            neutral_color="#34495e"
        )

        if audio_bytes:
            duration = len(audio_bytes) / (2 * RECORDER_SAMPLE_RATE)
            if duration <= MAX_RECORDING_DURATION_S:
                st.session_state.audio_ready = True
                st.session_state.audio_bytes = audio_bytes
                st.session_state.filename = f"recording_{int(time.time())}.wav"
                st.success("?? Recording ready")
            else:
                st.error(f"Recording too long ({duration:.1f}s > {MAX_RECORDING_DURATION_S}s)")

    else:
        uploaded_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "flac"])
        if uploaded_file:
            st.session_state.audio_ready = True
            st.session_state.audio_bytes = uploaded_file.getvalue()
            st.session_state.filename = uploaded_file.name
            st.success("?? File ready")

# --- Main Page Content ---
st.title("Voice DeepFake Detector")
st.markdown("Detect AI-generated speech using a custom deep learning model.")

if st.session_state.audio_ready:
    st.subheader("Audio Preview")
    st.audio(st.session_state.audio_bytes, format='audio/wav')

    if not st.session_state.analysis_done:
        if st.button("?? Analyze Audio"):
            st.session_state.current_prediction = get_prediction(st.session_state.audio_bytes)
            st.session_state.analysis_done = True
            st.rerun()

# --- Display Results ---
if st.session_state.analysis_done and st.session_state.current_prediction:
    st.subheader("Analysis Results")
    col1, _ = st.columns([1, 2])
    with col1:
        st.success(f"? {st.session_state.current_prediction}")

# --- Clear All Button ---
st.markdown("---")
if st.button("?? Clear All"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# --- Footer ---
st.markdown("---")
st.caption("Powered by custom PyTorch classifier | Running locally")
