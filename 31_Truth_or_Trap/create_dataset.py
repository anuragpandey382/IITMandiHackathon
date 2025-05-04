import os
import librosa
import numpy as np
import h5py
import pyroomacoustics as pra
from scipy.signal import fftconvolve
from pydub import AudioSegment, silence

# ====== Helper functions ======

def change_to_mono(audio):
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio

def remove_silence(audio, sr=16000):
    audio_segment = AudioSegment(
        (audio * 32767).astype(np.int16).tobytes(),  # Convert to int16: full int16 range is from -32768 to 32767
        frame_rate=sr,
        sample_width=2,
        channels=1
    )
    chunks = silence.split_on_silence(
        audio_segment,
        min_silence_len=500,
        silence_thresh=-40,
        keep_silence=100
    )
    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += chunk
    samples = np.array(combined.get_array_of_samples()).astype(np.float32) / 32768
    return samples

def generate_rir(room_dim, source_pos, mic_pos, fs, rt60):
    e_absorption, max_order = pra.inverse_sabine(rt60, room_dim)
    room = pra.ShoeBox(room_dim, fs=fs, materials=pra.Material(e_absorption), max_order=max_order)
    room.add_source(source_pos)
    room.add_microphone_array(pra.MicrophoneArray(np.array([mic_pos]).T, room.fs))
    room.compute_rir()
    rir = room.rir[0][0]
    return rir

def apply_reverb_to_array(audio, rir):
    rir = rir / np.max(np.abs(rir))
    reverbed = fftconvolve(audio, rir, mode='full')[:len(audio)]
    return reverbed

def divide_chunks(audio, sr=16000, mask_fraction=0.10):
    def sliding_windows(audio, window_size, hop_size):
        for start in range(0, len(audio) - window_size + 1, hop_size):
            yield audio[start:start + window_size]

    window_size = sr * 2   # 2 seconds
    hop_size = sr * 1      # 50% overlap

    masked_chunks = []

    # Handle audio shorter than 2 seconds
    if len(audio) < window_size:
        pad_length = window_size - len(audio)
        audio = np.pad(audio, (0, pad_length), mode='constant')
        print(f"Padded audio from {len(audio) - pad_length} to {len(audio)} samples (2 seconds)")
        
        chunk = np.copy(audio)
        mask_size = int(len(chunk) * mask_fraction)
        if mask_size > 0:
            mask_start = np.random.randint(0, len(chunk) - mask_size + 1)
            chunk[mask_start:mask_start + mask_size] = 0
        masked_chunks.append(chunk)
    else:
        for chunk in sliding_windows(audio, int(window_size), int(hop_size)):
            chunk = np.copy(chunk)
            mask_size = int(len(chunk) * mask_fraction)
            if mask_size > 0:
                mask_start = np.random.randint(0, len(chunk) - mask_size + 1)
                chunk[mask_start:mask_start + mask_size] = 0
            masked_chunks.append(chunk)

    return masked_chunks

def divide_chunks_infer(audio, sr=16000, mask_fraction=0.10):
    def sliding_windows(audio, window_size, hop_size):
        for start in range(0, len(audio) - window_size + 1, hop_size):
            yield audio[start:start + window_size]

    window_size = sr * 2   # 2 seconds
    hop_size = sr * 1      # 50% overlap

    chunks = []

    # Handle audio shorter than 2 seconds
    if len(audio) < window_size:
        pad_length = window_size - len(audio)
        audio = np.pad(audio, (0, pad_length), mode='constant')
        print(f"Padded audio from {len(audio) - pad_length} to {len(audio)} samples (2 seconds)")
        
        chunk = np.copy(audio)
        
        chunks.append(chunk)
    else:
        for chunk in sliding_windows(audio, int(window_size), int(hop_size)):
            chunk = np.copy(chunk)
            chunks.append(chunk)
        # ----- added for last part chunk if not counted
        last_start = ((len(audio) - window_size) // hop_size + 1) * hop_size
        if last_start < len(audio):
            last_chunk = audio[last_start:]
            pad_len = window_size - len(last_chunk)
            last_chunk = np.pad(last_chunk, (0, pad_len), mode='constant')
            chunks.append(last_chunk)

    return chunks

def process_and_save_to_h5_with_reverb(fake_dir, real_dir, output_h5, sr=16000):
    waveforms = []
    labels = []

    # Set up RIR once
    room_dim = [6, 5, 3]
    source_pos = [2, 2, 1.5]
    mic_pos = [4, 3, 1.5]
    rt60 = 0.15
    rir = generate_rir(room_dim, source_pos, mic_pos, sr, rt60)

    def process_file(filepath, label):
        audio, _ = librosa.load(filepath, sr=sr)  # Didn't used change_mono as dataset is already single channel
        audio = remove_silence(audio, sr=sr) # Silence removed for training 
        audio = apply_reverb_to_array(audio, rir)  # Added Reverb for more robust training
        chunks = divide_chunks(audio, sr=sr)
        # print(f"{os.path.basename(filepath)}: {len(chunks)} chunks")
        return chunks, [label] * len(chunks)

    # Process fake files
    for filename in os.listdir(fake_dir):
        if filename.endswith('.wav'):
            filepath = os.path.join(fake_dir, filename)
            chunks, chunk_labels = process_file(filepath, label=1)
            waveforms.extend(chunks)
            labels.extend(chunk_labels)

    # Process real files
    for filename in os.listdir(real_dir):
        if filename.endswith('.wav'):
            filepath = os.path.join(real_dir, filename)
            chunks, chunk_labels = process_file(filepath, label=0)
            waveforms.extend(chunks)
            labels.extend(chunk_labels)

    # Pad all chunks to same length
    max_len = max(len(w) for w in waveforms)
    print(f"Max chunk length: {max_len}")

    waveforms_padded = []
    for w in waveforms:
        if len(w) < max_len:
            padded = np.pad(w, (0, max_len - len(w)), mode='constant')
        else:
            padded = w[:max_len]
        waveforms_padded.append(padded)

    waveforms_array = np.stack(waveforms_padded)
    labels_array = np.array(labels)

    # Save to HDF5
    with h5py.File(output_h5, 'w') as f:
        f.create_dataset('waveforms', data=waveforms_array)
        f.create_dataset('labels', data=labels_array)
        print(f"HDF5 saved: {output_h5}")
        print(f"Waveforms shape: {waveforms_array.shape}, Labels shape: {labels_array.shape}")

if __name__ == "__main__":
    process_and_save_to_h5_with_reverb(fake_dir='fake', real_dir='real', output_h5='dataset_reverb.h5')