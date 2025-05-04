from model import Classifier
from transformers import Wav2Vec2Processor, Wav2Vec2Model
import torch


MODEL_NAME = "facebook/wav2vec2-base-960h"
CHECKPOINT_PATH = "classifier_epoch_50.pt"
DEVICE = torch.device("cpu") # Streamlit does not support GPU yet

class ModelInfer:
    def __init__(self, CHECKPOINT_PATH=CHECKPOINT_PATH):
        # Load feature extractor
        self.processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
        self.wav2vec = Wav2Vec2Model.from_pretrained(MODEL_NAME).to(DEVICE)
        for p in self.wav2vec.parameters():
            
            p.requires_grad = False

        # Load classifier
        self.classifier = Classifier(input_dim=self.wav2vec.config.hidden_size).to(DEVICE)
        self.classifier.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE)['model_state_dict'])
        self.classifier.eval()
        self.wav2vec.eval()

    def extract_embedding(self, waveform: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            outputs = self.wav2vec(waveform)
            return outputs.last_hidden_state.mean(dim=1)  # mean pooling

    def predict(self, waveform: torch.Tensor) -> str:
        waveform = waveform.to(DEVICE)
        embedding = self.extract_embedding(waveform)
        with torch.no_grad():
            logits = self.classifier(embedding)
            prob = torch.sigmoid(logits).item()
        return prob
