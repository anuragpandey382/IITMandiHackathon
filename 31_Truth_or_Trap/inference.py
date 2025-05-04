import torch
import torchaudio
import numpy as np
from create_dataset import change_to_mono, divide_chunks_infer
from model_infer import ModelInfer
import soundfile as sf
import subprocess
import argparse
import io

def get_args():
    parser = argparse.ArgumentParser(
        description="Inference script"
    )
    parser.add_argument(
        "--file_path", type=str,
        default="",
        help="Path to the audio file"
    )
    parser.add_argument(
        "--ckpt", type=str,
        default=None,
        help="Checkpoint Path"
    )

    args = parser.parse_args()
    return args

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


def majority_fake_decision(averaged_scores, p):
    averaged_scores = np.array(averaged_scores)
    total_chunks = len(averaged_scores)
    fake_chunks = np.sum(averaged_scores>=0.5)
    fake_p = (fake_chunks/total_chunks)*100
    final_dec = "fake" if fake_p > p else "real"
    return final_dec, fake_p

def preprocess(waveform, sr):
    audio = torchaudio.transforms.Resample(sr, 16000)(waveform)
    audio = change_to_mono(audio)
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


    decision, fake_p = majority_fake_decision(averaged_scores, 20)

    return decision, fake_p, chunks, audio


def styled_decision_display(dec, fake_p):
    # Style colours
    green = "\033[92m"
    red = "\033[91m"
    reset = "\033[0m"

    uncolored_dec = dec.upper()
    line1 = f"Fake Percentage : {fake_p:.2f}%"
    line2_plain = f"Final Prediction: {uncolored_dec}"

    color = green if dec.lower() == 'real' else red
    line2_colored = f"Final Prediction: {color}{uncolored_dec}{reset}"

    width = max(len(line1), len(line2_plain)) + 4

    print("┌"+"─" * width + "┐")
    print("│ " + line1.ljust(width - 2) + " │")
    print("│ " + line2_colored.ljust(width - 2 + len(color) + len(reset)) + " │")
    print("└" + "─" * width + "┘")



if __name__ == "__main__":
    args = get_args()
    model = ModelInfer(args.ckpt)
    if args.file_path.split('.')[-1] != "webm":
        waveform, sr = torchaudio.load(args.file_path)

        # Ensure waveform is mono (1 channel) for consistency
        if waveform.ndim > 1:
            waveform = waveform.mean(dim=0, keepdim=True)  # Convert to mono by averaging channels

        waveform_np = waveform.numpy().flatten()

        dec,fake_p, res_lst, waveform = preprocess(waveform_np, sr)

        styled_decision_display(dec, fake_p)
    
    else:
        try:
            with open(args.file_path, "rb") as f:
                wav_np, sr = convert_webm_bytes_to_wav_array(f)
            dec, fake_p, res_lst, wav_np = preprocess(wav_np, sr)
            styled_decision_display(dec, fake_p)
        except Exception as e:
            pass
