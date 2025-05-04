# 🎙️ Truth or Trap: Fake Audio Detection

**Truth or Trap** is a lightweight deep learning-powered tool to detect **fake or spoofed audio**. The system is built around a **3-CNN + Classifier** architecture and benchmarked against **AASIST** and **Wav2Vec2.0** models. It also includes a Streamlit web interface for real-time interaction, recording, and prediction.

---

## 🧠 Model Overview

- **Primary Model**: Custom 3-layer CNN + Fully Connected Classifier.
- **Tested With**:
  - ✅ [AASIST](https://github.com/clovaai/aasist)
  - ✅ [Wav2Vec2.0](https://huggingface.co/facebook/wav2vec2-base)

---

## 📊 Dataset & Features

- **Dataset**: ASVspoof 2019 / 2021
- **Extracted Features**:
  - Mel-Spectrogram
  - MFCC
  - Chroma
  - Spectral Contrast
  - Tonnetz

---

## 🌐 Streamlit App

### 🔧 Features:
- 🎧 Record or Upload Audio
- 🧠 Predict Real or Fake
- 📈 Visualize Embeddings (t-SNE / PCA)
- 📉 Error analysis of similar-sounding samples

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/truth-or-trap.git
cd truth-or-trap


WE have also added a sample for all to check if you are on IIT intranet 
172.19.15.16:8501 
please do check it out 