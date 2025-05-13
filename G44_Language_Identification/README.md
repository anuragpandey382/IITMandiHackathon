# Voice of the Nation: Deep Learning for Indian Language Identification

**AITech Hackathon 2025 (IIT Mandi & HCLTech)**

**Team:** [Group 44/Rishiteja, Varshith, Jayasheela, Geetamsh, Madhu]

## 1. Project Overview

This project addresses Problem 7 ("Voice of the Nation") of the AITech Hackathon 2025. The goal is to develop and evaluate deep learning models for Automatic Language Identification (LID) capable of classifying audio clips into one of **10 Indian languages**:

1.  Bengali
2.  Gujarati
3.  Hindi
4.  Kannada
5.  Malayalam
6.  Marathi
7.  Punjabi
8.  Tamil
9.  Telugu
10. Urdu

Two primary approaches were implemented and compared:
* **Whisper Fine-tuning:** Utilizing a pre-trained Whisper 'tiny' model with a frozen encoder and fine-tuning a custom classification head.
* **Conformer Model:** Training a Conformer-based architecture from scratch using offline-generated log-Mel spectrogram features.

A real-time demonstration interface using Gradio was also developed.

## 2. Dataset

* **Source:** [Audio Dataset with 10 Indian Languages](https://www.kaggle.com/datasets/hbchaitanyabharadwaj/audio-dataset-with-10-indian-languages) on Kaggle, downloaded via `kagglehub`.
* **Format:** MP3 audio files organized into language-specific folders.
* **Note on Languages:** The downloaded dataset contained 'Urdu' instead of 'Odia' (which was mentioned in the original problem description). This project uses the 10 languages present in the downloaded dataset.

## 3. Setup and Installation

1.  **Clone Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```
2.  **Environment (Recommended):**
    ```bash
    conda create -n lid_project python=3.9
    conda activate lid_project
    ```
3.  **Install Dependencies:**
    * **PyTorch:** Install based on your system/CUDA version from [pytorch.org](https://pytorch.org/).
    * **Whisper:** `pip install -U openai-whisper`
    * **Other Libraries:**
        ```bash
        pip install pandas numpy scikit-learn matplotlib tqdm soundfile librosa joblib pydub ipython gradio seaborn kagglehub
        ```
    * **FFmpeg (Required for pydub/Whisper):**
        * Conda: `conda install ffmpeg -c conda-forge`
        * Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
        * MacOS (Homebrew): `brew install ffmpeg`

4.  **Download Dataset:**
    * The scripts using `kagglehub` (`import kagglehub; kagglehub.dataset_download(...)`) can download the data automatically if Kaggle credentials are set up.
    * Alternatively, manually download from Kaggle and place the `Language Detection Dataset` folder into the designated data directory (e.g., `data/raw/`). Ensure the structure is `data/raw/Language Detection Dataset/[LanguageName]/audio.mp3`. Update paths in scripts if necessary.

## 4. Preprocessing

* **Common:** All audio resampled to 16kHz. Data split using stratified 80/10/10 (Train/Val/Test) ratio with `random_state=42`. Label mapping (language name -> integer ID) created and saved.
* **Whisper Pipeline (`whisper_pipeline.py` - Example Name):**
    * Processes audio on-the-fly using `WhisperFeatureDataset`.
    * Pads/Trims audio to **30 seconds**.
    * Extracts **80-band** log-Mel spectrograms using `whisper.audio`.
    * Applies random noise, speed, and pitch augmentation during training.
    * Splits saved as CSV files (e.g., `data/splits/whisper/train.csv`).
* **Conformer Pipeline (`conformer_preprocessing.py` - Example Name):**
    * Performs **offline** feature generation.
    * Loads audio using `safe_load_audio` (`librosa`/`pydub`).
    * Pads/Trims audio to **3 seconds**.
    * Applies fixed pitch shift augmentation (-2, 0, +2 semitones), saving each augmented version.
    * Applies silence trimming and peak normalization.
    * Extracts **128-band** log-Mel spectrograms (`librosa`), Z-score normalized per sample.
    * Saves features as `.npy` files (e.g., `data/features/[LanguageName]/file_ps0.npy`).
    * *Note:* ~155 files were skipped due to loading errors.
    * Splits saved as pickled lists of `.npy` paths/labels (e.g., `data/features/splits/train.pkl`).

## 5. Model Architectures

* **`LIDWhisper` (in `whisper_pipeline.py` or `models.py`):**
    * Uses frozen Whisper 'tiny' encoder.
    * Adds a classification head (Mean Pooling -> Linear -> ReLU -> Dropout -> Linear).
* **`MFCCConformerModel` (in `conformer_pipeline.py` or `models.py`):**
    * Custom Conformer architecture (4 blocks, `d_model=144`, 4 heads).
    * Takes 128-dim Mel features (from 3s clips) as input.
    * Uses Attention Pooling before the classifier.
    * Total parameters: ~1.24M (all trainable).

## 6. Training

* **Whisper:** Run `whisper_pipeline.py`. Trains for 5 epochs (AdamW, CosineAnnealingLR, BS=16). Saves best model based on Val Macro F1.
* **Conformer:** Run `conformer_pipeline.py` (assuming it includes training). Trains for 5 epochs (Adam, ReduceLROnPlateau, BS=32). Saves best model based on Val Loss.

*(Note: Adapt script names and execution commands based on your actual file structure).*

## 7. Results Summary

| Model             | Evaluation Set | Accuracy | Macro F1 | Key Confusion Areas                     |
| :---------------- | :------------- | :------- | :------- | :-------------------------------------- |
| Whisper ('tiny')  | Test           | 80.78%   | 0.797    | Hindi/Urdu, Guj/Mar/Pun               |
| Conformer         | Validation     | 88.61%   | 0.870    | Punjabi -> Gujarati (Major), Others minor |

* The Conformer model showed significantly better validation performance than the Whisper model's test performance.
* The Conformer excelled on 8/10 languages but struggled severely with Punjabi/Gujarati confusion.
* t-SNE visualization of Conformer embeddings confirmed better separation for most classes but overlap for problematic pairs.

*(Refer to the full report (`report.pdf`) or generated plots in the output directory for detailed results, training curves, and confusion matrices).*

## 8. Real-Time Demo (`gradio_app.py`)

* A Gradio interface was implemented using the trained **Whisper 'tiny'** model.
* Allows real-time LID from microphone input or file upload.
* Applies the Whisper preprocessing pipeline.
* Displays the top predicted language and confidence.
* **To Run:** `python gradio_app.py`

## 9. Usage (Example Inference)

```python
# --- Example for Whisper Model ---
from whisper_pipeline import create_model, predict_language # Adapt import
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "path/to/best/whisper_model.pt"
AUDIO_FILE = "path/to/audio.wav"

model = create_model(whisper_size="tiny", num_languages=10, freeze_encoder=True, device=DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()
predictions = predict_language(model, AUDIO_FILE, device=DEVICE)
print(predictions)

# --- Example for Conformer Model ---
# (Requires similar helper functions for loading model and predicting single file)
# from conformer_pipeline import MFCCConformerModel, preprocess_mic_audio # Adapt import
# ... load model ...
# preprocessed_tensor = preprocess_mic_audio(audio_data)
# with torch.no_grad():
#     logits = model(preprocessed_tensor)
#     # ... get prediction ...
10. File Structure (Example).
├── data/
│   ├── raw/                  # Location for downloaded dataset
│   │   └── Language Detection Dataset/
│   │       ├── Bengali/
│   │       └── ... (other languages)
│   ├── features/             # Output features for Conformer
│   │   ├── Bengali/
│   │   ├── ...
│   │   ├── splits/           # Conformer train/val/test .pkl files
│   │   └── label_mapping.pkl
│   └── splits/               # Whisper train/val/test .csv files
├── output/
│   ├── whisper/              # Whisper model outputs
│   │   ├── best_model.pt
│   │   ├── plots/
│   │   └── results.json
│   └── conformer/            # Conformer model outputs
│       ├── best_model.pt
│       └── plots/
├── src/                      # Optional: Source code directory
│   ├── models.py
│   ├── whisper_pipeline.py
│   ├── conformer_pipeline.py
│   ├── conformer_preprocessing.py
│   └── gradio_app.py
├── report.pdf                # Detailed project report
├── requirements.txt          # Python dependencies
└── README.md                 # This file
11. LimitationsConformer model evaluated on validation data; test set results pending.Significant Punjabi/Gujarati confusion in the Conformer model needs addressing.Dataset issues: Urdu instead of Odia, ~155
