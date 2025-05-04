# 🎙️ Real-Time Fake Speech Detection System

With the increasing rise of AI-generated voices and deepfakes, ensuring the authenticity of voice-based interactions has become critical. This project aims to detect fake (AI-generated) vs. real (human) voices **in real time** during phone or audio/video calls.

---

## 🔍 Problem Statement

AI-generated deepfake voices pose a serious threat to **phone-based communication**, security, and trust. This project addresses the challenge of distinguishing between **real human speech** and **synthetic audio** with high accuracy in real-time.

---

## 🎯 Objectives

- ✅ Detect whether audio is **real** or **fake** during **live calls**.
- ✅ Segment audio streams and classify each segment in real time.
- ✅ Display live classification results during and after the call.
- ✅ Provide web dashboards and APIs for offline analysis.

---

## 📱 Mobile App

Built using **Flutter** and integrated with **WebRTC** for **live audio and video calls**.

- Live call audio is continuously monitored.
- Each 1-second audio segment is analyzed and classified.
- Real-time prediction is shown during the call.
- Powered by REST APIs hosted on a custom **Apache server**.

---

## 🌐 Dashboards

Two interactive **web dashboards** were developed:

1. **Upload Audio Dashboard**: Upload `.wav` or `.mp3` files and classify audio segments.
2. **Analytics Dashboard**: Visualize segment-level predictions and compare models.

---

## 🧠 Machine & Deep Learning Models Used

### 🔹 Traditional Machine Learning Models
- **Random Forest** – Baseline tree-based ensemble method.
- **SVM (Support Vector Machine)** – Classifier using spectral features.
- **XGBoost** – Gradient boosted decision trees.
- **Neural Network on FFT** – Fully connected NN trained on FFT-transformed features.
- **MLP (Multilayer Perceptron)** – Basic deep learning model using MFCC/log-mel inputs.

### 🔹 Deep Learning Architectures
- **VGG16** – Fine-tuned on speech spectrogram images.
- **ResNet18** – Residual CNN trained on MFCC features.
- **LSTM** – Sequential model capturing temporal audio dependencies.
- **Transformer** – Raw waveform ingestion without handcrafted features.

---

## 🧪 Model Pipeline

- Input audio is segmented into **1-second chunks**.
- Preprocessing:
  - MFCC / Log-mel / FFT / Raw waveform (depending on model)
- Each chunk is classified:  
  **`1 → Real`**  
  **`0 → Fake`**

All models follow a **uniform segment-level inference pipeline** to ensure consistent evaluation and deployment.

---

## 🌐 Server & Backend

- **Apache HTTP Server** hosts the prediction API.
- **Python Flask** (or Django, optionally) handles requests and returns predictions.
- Models are loaded and executed on server-side with preloaded weights.

---

## 🧰 Tech Stack

| Area               | Tools & Frameworks                          |
|--------------------|---------------------------------------------|
| Mobile App         | Flutter, WebRTC                             |
| Web Dashboards     | HTML/CSS, JavaScript, Flask/Django          |
| Backend API        | Apache Server, Python, Flask                |
| Audio Processing   | Librosa, Numpy, Scipy, Pydub                |
| Deep Learning      | PyTorch, TensorFlow, Scikit-learn           |
| Visualization      | Matplotlib, Seaborn, Plotly                 |

---
