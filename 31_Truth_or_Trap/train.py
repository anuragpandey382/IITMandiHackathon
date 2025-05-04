import argparse
import os
import torch
from torch.utils.data import DataLoader
from transformers import Wav2Vec2Processor, Wav2Vec2Model
from audio_dataset import AudioDataset
from model import Classifier
from trainer_run import trainer


def get_args():
    parser = argparse.ArgumentParser(
        description="Training script"
    )
    parser.add_argument(
        "--model_name", type=str,
        default="facebook/wav2vec2-base-960h",
        help="Name or path of the pretrained Wav2Vec2 model"
    )
    parser.add_argument(
        "--training_dataset_path", type=str,
        default="trainingdataset_reverb.h5",
        help="Path to the training HDF5 dataset file"
    )
    parser.add_argument(
        "--sr", type=int,
        default=16000,
        help="Sampling rate for audio"
    )
    parser.add_argument(
        "--batch_size", type=int,
        default=512,
        help="Batch size for training"
    )
    parser.add_argument(
        "--num_epochs", type=int,
        default=50,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--lr", type=float,
        default=1e-4,
        help="Learning rate for optimizer"
    )
    parser.add_argument(
        "--run_path", type=str,
        default=".",
        help="Base directory for outputs and checkpoints"
    )
    parser.add_argument(
        "--ckpt", type=str,
        default=None,
        help="Directory to save or load checkpoints (defaults to run_path/checkpoints)"
    )

    args = parser.parse_args()

    # Post-processing
    if args.ckpt is None:
        args.ckpt = os.path.join(args.run_path, "checkpoints")

    # Device setup
    use_cuda = torch.cuda.is_available()
    args.device = torch.device("cuda" if use_cuda else "cpu")

    return args



def extract_embedding_batch(waveforms: torch.Tensor):
    with torch.no_grad():
        outputs = wav2vec(waveforms)

        embeddings = outputs.last_hidden_state.mean(dim=1)  # mean pooling
    return embeddings

print("Feature extractor loaded")

if __name__ == "__main__":
    args = get_args()
    # ---------- Data ----------
    dataset = AudioDataset(args.training_dataset_path)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    print("Dataset loaded")

    processor = Wav2Vec2Processor.from_pretrained(args.model_name)
    wav2vec = Wav2Vec2Model.from_pretrained(args.model_name).to(args.device)
    for p in wav2vec.parameters():
        p.requires_grad = False  

    model = Classifier(input_dim=wav2vec.config.hidden_size, dropout=0.2).to(args.device)
    trainer(model, loader, extract_embedding_batch, args)
    print("Training completed")
