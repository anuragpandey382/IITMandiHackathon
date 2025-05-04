import torch.nn as nn

class Classifier(nn.Module):
    # use wav2vec2 embeddings to classify using MLP
    def __init__(self, input_dim, hidden_dim=256, dropout=0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),    # Trained with 0.2 Droupout, Removed while Testing, 0 done to avoid mismatch state_dict
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, emb):
        return self.net(emb).squeeze(-1)
