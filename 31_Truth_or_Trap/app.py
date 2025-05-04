import streamlit as st
import torch
import torchaudio
import numpy as np
from pathlib import Path
from streamlit_mic_recorder import mic_recorder as stt
import soundfile as sf
from create_dataset import change_to_mono, divide_chunks_infer
import subprocess
import io
import plotly.graph_objects as go
import uuid
from model_infer import ModelInfer


st.title("Truth or Trap: Audio Deepfake Detection")
st.write("Upload an audio file or record via mic, and the model will predict if it's real or fake.")

# === Setup temp directory ===
TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

# === Model & Processor Loading ===

model = ModelInfer()

# === Audio Preprocessing ===
def majority_fake_decision(averaged_scores, p):
    averaged_scores = np.array(averaged_scores)
    total_chunks = len(averaged_scores)
    fake_chunks = np.sum(averaged_scores>=0.5)
    fake_p = (fake_chunks/total_chunks)*100
    st.write("Fake percentage: ", fake_p)
    return "fake" if fake_p > p else "real"


def preprocess(waveform, sr):
    audio = torchaudio.transforms.Resample(sr, 16000)(waveform)
    audio = change_to_mono(audio)
    # rir = generate_rir(room_dim=[6, 5, 3], source_pos=[2, 2, 1.5], mic_pos=[4, 3, 1.5], fs=16000, rt60=0.15)
    # audio  = apply_reverb_to_array(audio, rir)
    chunks = divide_chunks_infer(audio)

    window_size_sec = 2
    hop_size_sec = 1

    num_chunks = len(chunks)
    total_seconds = (num_chunks - 1) * hop_size_sec + window_size_sec

    scores_sum = np.zeros(total_seconds)
    counts = np.zeros(total_seconds)

    for idx, chunk in enumerate(chunks):
        input_data = np.expand_dims(chunk, axis=0)  # (1, len_chunk)
        input_data = torch.tensor(input_data, dtype=torch.float32)
        with torch.no_grad():
            score = model.predict(input_data)

        start_sec = idx
        end_sec = start_sec + 2

        for sec in range(start_sec, end_sec):
            if sec < total_seconds:
                scores_sum[sec] += score
                counts[sec] += 1

    counts[counts == 0] = 1
    averaged_scores = scores_sum / counts

    chunks = [
        {
            "start": i,
            "end": i + 1,
            "label": int(score >= 0.5),
            "conf": score if score >= 0.5 else 1 - score
        }
        for i, score in enumerate(averaged_scores)
    ]

    mean_score = np.mean(averaged_scores)
    # decision = "fake" if mean_score >= 0.5 else "real"
    decision = majority_fake_decision(averaged_scores, 20)

    return decision, chunks, audio

# === Plotting Function ===
def plot_waveform_with_chunks(waveform_np, sr, chunks):
    if waveform_np.ndim == 1:
        waveform_np = np.expand_dims(waveform_np, axis=0)

    duration = waveform_np.shape[-1] / sr
    times = np.linspace(0, duration, waveform_np.shape[-1])
    waveform = waveform_np[0].astype(np.float32).flatten()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=waveform, mode='lines', line=dict(color='black', width=1), name='Waveform'))

    for c in chunks:
        color = f"rgba(0,255,0,{c['conf']})" if c["label"] == 0 else f"rgba(255,0,0,{c['conf']})"
        fig.add_shape(type="rect", x0=c["start"], x1=c["end"], y0=-1, y1=1, fillcolor=color, line=dict(width=0), layer="below")

    fig.update_layout(title="Audio Waveform with Fake/Real Chunks", xaxis_title="Time (s)", yaxis_title="Amplitude", showlegend=False, height=300, margin=dict(l=10, r=10, t=30, b=30))
    st.plotly_chart(fig, use_container_width=True)

# === Styled Decision Display ===
def display_decision(decision, mean_score):
    color = "red" if decision == "fake" else "green"
    label = decision.upper()
    animation_class = f"pop-{uuid.uuid4().hex[:6]}"  # Unique class name per render

    st.markdown(
        f"""
        <style>
        .{animation_class} {{
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: {color};
            animation: pop 0.6s ease-out;
            margin-top: 20px;
        }}
        .{animation_class} .prediction-box {{
            border: 2px solid white;
            padding: 10px 20px;
            border-radius: 12px;
            display: inline-block;
            color: {color};
            margin-bottom: 10px;
        }}
        @keyframes pop {{
            0% {{ transform: scale(0.5); opacity: 0.2; }}
            100% {{ transform: scale(1.0); opacity: 1; }}
        }}
        </style>

        <div class="{animation_class}">
            <div class="prediction-box">Prediction: {label}</div>
            <br>
            <span style="font-size:18px; color:black;">Confidence: {mean_score*100:.1f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )



# === Convert WebM to WAV Array ===
def convert_webm_bytes_to_wav_array(webm_file_obj):
    command = ["ffmpeg", "-i", "pipe:0", "-f", "wav", "-ar", "16000", "-ac", "1", "-loglevel", "error", "pipe:1"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    webm_bytes = webm_file_obj.read()
    wav_data, stderr = process.communicate(input=webm_bytes)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
    audio_array, sample_rate = sf.read(io.BytesIO(wav_data))
    if audio_array.ndim == 0 or audio_array.shape[0] == 0:
        raise ValueError("Decoded audio is empty.")
    return audio_array, sample_rate

# === TABS for UI Separation ===
tab1, tab2 = st.tabs(["📁 Upload", "🎤 Record"])

# === File Upload Tab ===
with tab1:
    st.write("Upload WAV/WEBM file")
    audio_file = st.file_uploader("Upload File", type=["wav", "webm"], key="upload_file")

    if audio_file is not None:
        # Clear old temp files
        for f in TEMP_DIR.glob("*"):
            f.unlink()

        # Save with unique name
        unique_name = f"uploaded_{uuid.uuid4()}{Path(audio_file.name).suffix}"
        uploaded_path = TEMP_DIR / unique_name

        with open(uploaded_path, "wb") as f:
            f.write(audio_file.read())


        if uploaded_path.suffix != ".webm":
            waveform, sr = torchaudio.load(str(uploaded_path))

            # # Ensure waveform is mono (1 channel) for consistency
            if waveform.ndim > 1:
                waveform = waveform.mean(dim=0, keepdim=True)  # Convert to mono by averaging channels

            # Convert the waveform from PyTorch tensor to a NumPy array
            waveform_np = waveform.numpy().flatten()  # Flatten to make it 1D for plotting



            dec, res_lst, waveform = preprocess(waveform_np, sr)

            # Now plot the waveform with chunks
            plot_waveform_with_chunks(waveform_np=waveform_np, sr=sr, chunks=res_lst)

            st.audio(str(uploaded_path))
            display_decision(dec, np.mean([c["conf"] for c in res_lst]))
        else:
            try:
                with open(uploaded_path, "rb") as f:
                    wav_np, sr = convert_webm_bytes_to_wav_array(f)
                dec, res_lst, wav_np = preprocess(wav_np, sr)
                plot_waveform_with_chunks(waveform_np=np.expand_dims(wav_np, axis=0), sr=sr, chunks=res_lst)
                st.audio(str(uploaded_path))
                display_decision(dec, np.mean([c["conf"] for c in res_lst]))
            except Exception as e:
                st.error(f"WebM conversion failed: {e}")


with tab2:
    st.write("Record via microphone")
    audio_data = stt()

    if audio_data and "bytes" in audio_data:
        st.success("Recording complete!")

        try:
            # Convert WebM bytes to WAV bytes
            wav_np, sr = convert_webm_bytes_to_wav_array(io.BytesIO(audio_data["bytes"]))
            wav_bytes_io = io.BytesIO()
            sf.write(wav_bytes_io, wav_np, sr, format='WAV')
            wav_bytes_io.seek(0)
            st.audio(wav_bytes_io, format="audio/wav")
        except Exception as e:
            st.error(f"Playback conversion failed: {e}")


        # Clear old temp files
        for f in TEMP_DIR.glob("*"):
            f.unlink()

        webm_path = TEMP_DIR / f"recorded_{uuid.uuid4()}.webm"
        with open(webm_path, "wb") as f:
            f.write(audio_data["bytes"])

        # try:
        with open(webm_path, "rb") as f:
            wav_np, sr = convert_webm_bytes_to_wav_array(f)

        try: 
            dec, res_lst, wav_np = preprocess(wav_np, sr)
            wav_np = np.array(wav_np, dtype=np.float32)
            plot_waveform_with_chunks(waveform_np=np.expand_dims(wav_np, axis=0), sr=sr, chunks=res_lst)
            display_decision(dec, np.mean([c["conf"] for c in res_lst]))
        except Exception as e:
            print(e)
            st.error(f"Mic conversion failed: {e}")
