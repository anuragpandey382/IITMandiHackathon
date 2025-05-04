# Truth or Trap: Fake Speech Detection Using Deep Learning

This is a PyTorch-based implementation of our solution **"Truth or Trap"** developed for the **AITech Hackathon 2025** (HCLTech x IIT Mandi), focused on real-time detection of fake speech using Wav2Vec2 embeddings and a lightweight classifier.

![Project Overview](assets/flow-chart.png?raw=true "Truth or Trap Overview")

> We present a robust deep learning pipeline that detects synthetic or deepfake voice recordings. Our system leverages Wav2Vec2 for feature extraction and a custom neural classifier for binary classification. With data augmentation, real-time preprocessing, and a user-friendly Streamlit interface, the model can operate effectively in dynamic and noisy conditions.

##  Team  
**Ankit, Bhavik Ostwal, Lavish Singal, Nishant Nehra, Piyush Roy**

---

##  Environment Setup

Tested on:

- Windows 11 / Ubuntu 22.04  
- Python 3.10.12  
- torch==2.1.0  
- CUDA 11.8  

###  Installation

Clone this repository and install the required packages:

```bash
pip install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
```


```bash
git clone https://github.com/your-username/truth-or-trap.git
cd truth-or-trap
pip install -r requirements.txt
```

---

##  Dataset

- **Name**: Fake-or-Real (FoR) Dataset  
- **Labels**: Real (0), Fake (1)  
- **Format**: `.wav` files  
- **Source**: [Kaggle - Fake-or-Real Dataset](https://www.kaggle.com/datasets/mohammedabdeldayem/the-fake-or-real-dataset)



---

##  Model Architecture

- **Encoder**: [facebook/wav2vec2-base-960h](https://huggingface.co/facebook/wav2vec2-base-960h) (frozen)
- **Classifier**:
  - Linear(768 → 256) + ReLU
  - Dropout(0.2)
  - Linear(256 → 1)

Implemented in: `model.py`, `model_infer.py`

---

##  Training

```bash
python train.py --training_dataset_path <path-to-h5-dataset> --bath_size <batch_size> --num_epochs --lr --ckpt <checkpoint path>
```

There are other arguments also, check train.py.

---

##  Inference

Run the inference pipeline with:

```bash
python inference.py --file_path --ckpt
```

Or use the Streamlit interface:

```bash
streamlit run app.py
```

Steps:
1. Upload or record audio via microphone.
2. Audio is preprocessed and chunked.
3. Each chunk is classified as real/fake.
4. Aggregate score is thresholded (20% chunks fake → audio is fake).
5. Real vs Fake chunks are visualized using Plotly.

---

##  UI Screenshot

![Streamlit UI](assets/streamlit.png?raw=true "Streamlit Interface")

---

##  Project Structure

```
final_git/
│
├── app.py               # Streamlit Web App
├── inference.py         # Inference backend
├── train.py             # Training loop
├── trainer_run.py       # Optional training runner
├── create_dataset.py    # Data preprocessing pipeline
├── audio_dataset.py     # Dataset class
├── model.py             # Classifier definition
├── model_infer.py       # Inference model wrapper
├── classifier_epoch_50.pt  # Final trained model
├── requirements.txt
├── README.md
├── temp_audio/          # Temporary audio files
└── for-norm/            # Normalized dataset output
```

---

## 🔗 Useful Links

- **Dataset**: [Fake-or-Real Dataset on Kaggle](https://www.kaggle.com/datasets/mohammedabdeldayem/the-fake-or-real-dataset)  
- **HuggingFace Wav2Vec2**: [facebook/wav2vec2-base-960h](https://huggingface.co/facebook/wav2vec2-base-960h)  

---

##  Demo
[Youtube Link](https://youtu.be/KwvSDXksr94)

---

##  Report
[G Drive](https://drive.google.com/file/d/1NK2dWjPE9eLvH9OwqCgWqGiM03JDYDRd/view?usp=sharing)

---
##  Acknowledgments

Inspired by the advances in self-supervised speech representation learning and the growing need for deepfake detection. Special thanks to HuggingFace, PyTorch, and the creators of the Fake-or-Real dataset.

---
