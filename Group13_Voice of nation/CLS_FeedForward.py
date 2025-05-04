from transformers import Wav2Vec2Processor, Wav2Vec2Model
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pickle
import pandas as pd
import numpy as np
import librosa
import sys
import warnings
warnings.filterwarnings("ignore")

class TransformerEncoderBlock(nn.Module):
    def __init__(self, embed_dim, num_heads, expansion, dropout=0.1):
        super(TransformerEncoderBlock, self).__init__()
        
        self.attention = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.dropout1 = nn.Dropout(dropout)

        self.ff = nn.Sequential(
            nn.Linear(embed_dim, expansion * embed_dim),
            nn.ReLU(),
            nn.Linear(expansion*embed_dim, embed_dim)
        )
        self.norm2 = nn.LayerNorm(embed_dim)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, src_mask=None):
        attn_output, _ = self.attention(x, x, x, attn_mask=src_mask)
        x = x + self.dropout1(attn_output)
        x = self.norm1(x)
        ff_output = self.ff(x)
        x = x + self.dropout2(ff_output)
        x = self.norm2(x)

        return x
    
class ClassificationHead(nn.Sequential):
    def __init__(self, emb_size, n_classes):
        super().__init__()
        
        self.fc = nn.Sequential(
            nn.Linear(emb_size, 256),
            nn.ELU(),
            nn.Dropout(0.5),
            nn.Linear(256, 32),
            nn.ELU(),
            nn.Dropout(0.3),
            nn.Linear(32, n_classes),
            nn.Softmax(dim=1)
            
        )

    def forward(self, x):
        out = self.fc(x)
        return out
class TransformerEncoder(nn.Sequential):
    def __init__(self, depth, emb_size):
        super().__init__(*[TransformerEncoderBlock(emb_size,num_heads=6,expansion=4) for _ in range(depth)])
class Classifier(nn.Sequential):
    def __init__(self, emb_size=40, depth=3, **kwargs):
        super().__init__(
            TransformerEncoder(depth, emb_size),
            ClassificationHead(emb_size, 9)
        )

class TransformerWithCLS(nn.Module):
    def __init__(self, emb_size, depth=3, num_classes=9):
        super().__init__()
        self.cls_token = nn.Parameter(torch.randn(1, 1, emb_size))
        self.transformer = TransformerEncoder(depth, emb_size)  # your custom encoder
        self.classifier = ClassificationHead(emb_size, num_classes)

    def forward(self, x):
        B = x.size(0)
        cls_tok = self.cls_token.expand(B, 1, -1)
        x = torch.cat([cls_tok, x], dim=1)  # (B, seq_len + 1, emb_size)
        x = x.transpose(0, 1)  # -> (seq_len + 1, B, emb_size)

        x = self.transformer(x)
        cls_out = x[0]  # Take output of CLS token (at position 0)
        return self.classifier(cls_out)

def main(audinput):
    device = torch.device("cpu")
    # Load the weights
    model = TransformerWithCLS(emb_size=768, depth=3, num_classes=9)
    model.load_state_dict(torch.load('CLS_model_5000.pth', map_location=device))
    model.to(device)
    model.eval()

    # Load Wav2Vec2 processor and model
    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
    wav2vec_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")

    def normalize_amplitude(y):
        """Normalize audio signal to -1 to 1 range."""
        return y / np.max(np.abs(y))

    def fast_pitch_normalize(y, sr, target_pitch_hz=300.0):
        # Estimate pitch using YIN
        f0 = librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        mean_pitch = np.mean(f0)

        # Calculate semitone shift
        n_steps = librosa.hz_to_midi(target_pitch_hz) - librosa.hz_to_midi(mean_pitch)

        # Apply pitch shift
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
        return y_shifted

    def feature_extractor(file):
        audio_data,sample_rate = librosa.load(file, sr=16000)
        audio_data,index = librosa.effects.trim(audio_data)
        audio_data = normalize_amplitude(audio_data)
        audio_data = fast_pitch_normalize(audio_data, sample_rate)
        # mfcc_feature = librosa.feature.mfcc(y=audio_data,sr=sample_rate,n_mfcc=40)
        # audio, sr = librosa.load("file", )
        # audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        inputs = processor(audio_data, sampling_rate=sample_rate, return_tensors="pt")
        #scaled_feature = np.mean(mfcc_feature.T,axis=0)
        
    # Extract token embeddings
        with torch.no_grad():
            outputs = wav2vec_model(**inputs)
            tokens = outputs.last_hidden_state  # Shape: (batch_size, time_steps, hidden_dim)
        return tokens

    # Languages
    langs = ['Bengali', 'Gujarati', 'Hindi', 'Kannada', 'Malayalam', 'Marathi', 'Tamil', 'Telugu', 'Urdu']

    tokens = feature_extractor(audinput)
    tokens = tokens.to(device)

    with torch.no_grad():
        pred_logits = model(tokens)  # shape: (1, 9)
        pred_class = torch.argmax(pred_logits, dim=-1).item()
        print("Predicted Language:", langs[pred_class])
    return langs[pred_class]
if __name__ == "__main__":
    main(sys.argv[1])
