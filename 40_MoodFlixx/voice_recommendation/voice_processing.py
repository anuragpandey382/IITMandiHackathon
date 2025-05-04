# voice_processing.py
import librosa
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import soundfile as sf
import os

def record_audio(duration=6, filename="temp_audio.wav", sample_rate=16000):
    """Record audio with improved error handling and visual feedback"""
    try:
        print(f"Recording for {duration} seconds...")
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        write(filename, sample_rate, audio)
        print(f"Recording saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

class VoiceProcessor:
    def __init__(self):
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-small")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

    def transcribe(self, audio_file_path: str, language: str = "en") -> str:
        """Transcribe audio with error handling"""
        try:
            audio, sr = librosa.load(audio_file_path, sr=16000)
            input_features = self.processor(audio, sampling_rate=sr, return_tensors="pt").input_features
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                language="english" if language == "en" else "hindi", task="transcribe"
            )
            predicted_ids = self.model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
            return self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        except Exception as e:
            print(f"Error in transcription: {e}")
            return ""

    def extract_emotion_features(self, audio_file_path: str) -> dict:
        """Extract emotion features dynamically without hardcoded thresholds"""
        try:
            y, sr = librosa.load(audio_file_path, sr=None)
            
            # Extract features
            energy = np.mean(librosa.feature.rms(y=y))
            pitches, _ = librosa.piptrack(y=y, sr=sr)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # Calculate dynamic energy thresholds based on the audio characteristics
            energy_percentiles = np.percentile(librosa.feature.rms(y=y)[0], [25, 50, 75])
            energy_threshold = energy_percentiles[1]  # Use median as base threshold
            
            # Calculate pitch thresholds dynamically
            if np.any(pitches > 0):
                pitch_percentiles = np.percentile(pitches[pitches > 0], [25, 50, 75])
                pitch_threshold = pitch_percentiles[1]
            else:
                pitch_threshold = 0
            
            emotions = {}
            
            # Energy-based emotions with dynamic scaling
            if energy > energy_threshold:
                # Scale based on how much the energy exceeds threshold
                energy_scale = energy / energy_threshold
                emotions["excitement"] = min(energy_scale * 0.5, 1.0)
                emotions["joy"] = min(energy_scale * 0.3, 0.8)
                emotions["anger"] = min(energy_scale * 0.2, 0.6)
            else:
                energy_scale = 1 - (energy / energy_threshold)
                emotions["calm"] = min(energy_scale * 0.8, 1.0)
                emotions["sadness"] = min(energy_scale * 0.6, 0.9)
            
            # Pitch-based emotions with dynamic scaling
            if pitch_mean > pitch_threshold and pitch_threshold > 0:
                pitch_scale = pitch_mean / pitch_threshold
                emotions["happiness"] = min(emotions.get("happiness", 0) + pitch_scale * 0.3, 1.0)
                emotions["surprise"] = min(emotions.get("surprise", 0) + pitch_scale * 0.2, 1.0)
            elif pitch_mean < pitch_threshold and pitch_threshold > 0:
                pitch_scale = 1 - (pitch_mean / pitch_threshold)
                emotions["sadness"] = min(emotions.get("sadness", 0) + pitch_scale * 0.3, 1.0)
            
            return emotions
        except Exception as e:
            print(f"Error extracting emotion features: {e}")
            return {}
