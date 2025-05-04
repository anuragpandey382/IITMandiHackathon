# Deepfake Audio Detection Using PaSST and Other Deep Learning Models

This repository contains a deep learning project aimed at detecting deepfake audio. The challenge involves distinguishing between real human speech and machine-generated speech (AI-generated). The primary model used is the **PaSST (Patchout Spectrogram Transformer)**, fine-tuned with additional MLP layers for classification. Baseline models, such as **SVM**, **Random Forest**, and **XGBoost**, are also implemented for comparison. The repository also includes a web application for real-time audio classification using **Streamlit**.

## Project Structure

The repository contains the following key files:

### Notebooks
1. **PaSST_Method_1_1000.ipynb**  
   Fine-tuned PaSST model for classification using 1,000 audio samples.

2. **PaSST_10000.ipynb**  
   Fine-tuned PaSST model using 10,000 audio samples, enhanced with MLP layers for slow downgrading to 2 classes (Real vs Fake).

3. **PaSST_Full_Dataset.ipynb**  
   Full dataset training with PaSST and MLP layers for slow downgrading to 2 classes.

4. **Baseline.ipynb**  
   Implements baseline models for comparison, such as **SVM**, **Random Forest**, and **XGBoost**.

5. **Deepfake_audio_detection.ipynb**  
   Contains a combination of **VGG16** and **SVM** models with ensemble learning techniques for classification.

### Python Scripts
1. **LSTM.py**  
   LSTM model implementation for audio feature extraction and classification.

2. **VGG.py**  
   Implements **VGG16** architecture for feature extraction and classification tasks.

3. **Model.py**  
   Contains the overall model pipeline, integrating different models and training routines.

4. **Streamlit_app.py**  
   Streamlit app for real-time audio classification via microphone input.

### Pretrained Models and Weights
This repository includes the following pretrained models and weights:
- **PaSST_Model_Weights.pth**  
  Pretrained weights for the PaSST model fine-tuned on the audio dataset. You can use these weights to start your experiments without retraining from scratch.

- **VGG_Model_Weights.h5**  
  Pretrained weights for the **VGG16** model, fine-tuned on the audio dataset for feature extraction and classification.

- **LSTM_Model_Weights.h5**  
  Pretrained weights for the LSTM-based model used in audio classification tasks.

- **SVM_Model.pkl**  
  Pretrained **SVM** model for comparison with deep learning models.

### Dataset
- The dataset used for this project is the **for-norm** version of the speech dataset, which contains both **REAL** and **FAKE** audio clips.
- The dataset is balanced in terms of gender and class, and it has been normalized for sample rate, volume, and number of channels.

## How to Run the Project

### 1. Install Dependencies
Make sure to install the required dependencies before running the notebooks or scripts. You can do so by running the following command:
```bash
pip install -r requirements.txt


Drive link for all the trained models:
https://drive.google.com/file/d/1KhM7cz3jC7rTvJuzpk32XiFmMbq9GOve/view?usp=sharing
