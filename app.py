import streamlit as st
import numpy as np
import plotly.express as px
from audio_recorder_streamlit import audio_recorder
import wave
import torch
import librosa
from io import BytesIO
import time
from pathlib import Path
from model.model_loader import CustomNeuralNetwork , input_height , input_width , num_channels
import torch
import torchaudio
import io
import numpy as np # Keep numpy for comparison or if needed elsewhere
from inference import run_inference

# --- Model Loading ---
# @st.cache_resource
model_main = CustomNeuralNetwork(input_height , input_width , num_channels)
model_path = 'arjun.pth'
model_main.load_state_dict(torch.load(model_path, map_location=torch.device('cuda')))
model_main.eval()


# --- Configuration ---
MAX_RECORDING_DURATION_S = 4
RECORDER_SAMPLE_RATE = 16000

# --- Audio Processing ---
def preprocess_audio(audio_bytes):
† † # Convert bytes to numpy array
† † # write with librosa maybe†
† † audio = io.BytesIO(audio_bytes)
† ††

† † # Write the stuff
† † with open("audio.wav", "wb") as f:
† † 	f.write(audio.getbuffer())
† † return "audio.wav"

def get_prediction(audio_bytes):
† † † † start_time = time.time()
† † † ††
† † † † # Preprocess
† † † † audio_path = preprocess_audio(audio_bytes)
† † † ††
† † † † # Predict
		
† † † † output = run_inference(audio_path = audio_path , model_path = 'arjun.pth' , device_str = 'cuda' )
† † † † † ††
† † † † processing_time = time.time() - start_time
† † † ††
† † † † return {
† † † † † † f'Prediction : {output} , Time : {processing_time} '†
† † † † }
† † † ††
# --- Rest of your existing UI code remains the same ---
# (Keep all your existing UI components, just replace the backend calls)

# --- Main App ---
st.set_page_config(
† † page_title="Speech DeepFake Detector",
† † page_icon="üéôÔ∏è",
† † layout="wide"
)

# Initialize session state
if 'analysis_done' not in st.session_state:
† † st.session_state.update({
† † † † 'analysis_done': False,
† † † † 'current_prediction': None,
† † † † 'viz_method': 't-SNE',
† † † † 'audio_ready': False,
† † † † 'last_input_method': None
† † })

# --- Sidebar ---
with st.sidebar:
† † st.title("TRUTH-OR-TRAP")
† † st.markdown("""
† † **AI Speech Classifier**††
† † Detect synthetic speech using a deep learning classifier.
† † """)
† ††
† † input_method = st.radio(
† † † † "Input Method",
† † † † ["üé§ Record Live", "üìÅ Upload File"],
† † † † index=0
† † )
† ††
† † st.markdown("---")
† ††
† † if input_method == "üé§ Record Live":
† † † † st.write("Record audio (max 4 seconds):")
† † † † audio_bytes = audio_recorder(
† † † † † † energy_threshold=(-1.0, 1.0),
† † † † † † pause_threshold=MAX_RECORDING_DURATION_S,
† † † † † † sample_rate=RECORDER_SAMPLE_RATE,
† † † † † † text="",
† † † † † † recording_color="#e74c3c",
† † † † † † neutral_color="#34495e"
† † † † )
† † † ††
† † † † if audio_bytes:
† † † † † † duration = len(audio_bytes) / (2 * RECORDER_SAMPLE_RATE)† # Estimate duration
† † † † † † if duration <= MAX_RECORDING_DURATION_S:
† † † † † † † † st.session_state.audio_ready = True
† † † † † † † † st.session_state.audio_bytes = audio_bytes
† † † † † † † † st.session_state.filename = f"recording_{int(time.time())}.wav"
† † † † † † † † st.success("‚úî Recording ready")
† † † † † † else:
† † † † † † † † st.error(f"Recording too long ({duration:.1f}s > {MAX_RECORDING_DURATION_S}s)")
† ††
† † else:
† † † † uploaded_file = st.file_uploader(
† † † † † † "Upload audio file",
† † † † † † type=["wav", "mp3", "flac"],
† † † † † † accept_multiple_files=False
† † † † )
† † † ††
† † † † if uploaded_file:
† † † † † † st.session_state.audio_ready = True
† † † † † † st.session_state.audio_bytes = uploaded_file.getvalue()
† † † † † † st.session_state.filename = uploaded_file.name
† † † † † † st.success("‚úî File ready")

# --- Main Content ---
st.title("Voice DeepFake Detector")
st.markdown("Detect AI-generated speech using a custom deep learning model.")

if st.session_state.audio_ready:
† † st.subheader("Audio Preview")
† † st.audio(st.session_state.audio_bytes, format='audio/wav')

† † if not st.session_state.analysis_done:
† † † † if st.button("Analyze Audio"):
† † † † † † st.session_state.current_prediction = get_prediction(
† † † † † † † † st.session_state.audio_bytes
† † † † † † )
† † † † † † st.session_state.analysis_done = True
† † † † † † st.rerun()

if st.session_state.analysis_done and st.session_state.current_prediction:
† † pred_data = st.session_state.current_prediction
† ††
† † st.subheader("Analysis Results")
† ††
† † col1, col2 = st.columns([1, 2])
† † with col1:
† † † † prediction = pred_data
† † † † † † † ††
† † † † st.success(f"**‚úÖ Speech** {prediction} ")
† † † † † † † †
† † † ††
† ††
† † with col2:
† † † pass† ††
† † st.markdown("---")
† † st.subheader("Model Insights")
† † features=None
† † if features:
† † † † # Visualization code remains the same
† † † † ref_real = np.random.normal(0.5, 0.2, (50, 2))
† † † † ref_fake = np.random.normal(-0.5, 0.2, (50, 2))
† † † ††
† † † † all_embeddings = np.vstack([ref_real, ref_fake, [[features[0], features[1]]]])
† † † † labels = ['REAL']*50 + ['FAKE']*50 + [prediction]
† † † ††
† † † † fig = px.scatter(
† † † † † † x=all_embeddings[:-1,0], y=all_embeddings[:-1,1],†
† † † † † † color=labels[:-1],
† † † † † † color_discrete_map={'REAL': '#2ecc71', 'FAKE': '#e74c3c'}
† † † † )
† † † ††
† † † † fig.add_scatter(
† † † † † † x=[all_embeddings[-1,0]], y=[all_embeddings[-1,1]],
† † † † † † mode='markers',
† † † † † † marker=dict(size=12, symbol='star', color='#f1c40f'),
† † † † † † name='Your Sample'
† † † † )
† † † ††
† † † † fig.update_layout(
† † † † † † title="Probability Space",
† † † † † † xaxis_title="Fake Probability",
† † † † † † yaxis_title="Real Probability"
† † † † )
† † † ††
† † † † st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Powered by custom PyTorch classifier | Running locally")
create a button that clears all the inputs and the uploaded sessions everything , cleared out 