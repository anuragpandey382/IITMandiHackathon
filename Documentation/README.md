# VOICE OF THE NATION: Deep Learning for Indian Languag Indentification

## 1) Project Setup

Follow the instructions below to set up the environment-frontend, backend, flask servers and install dependencies for this project.

#### 1. Frontend Setup
```bash
cd frontend            ## Navigate to frontend
npm install            ## Install dependencies
npm run dev            ## Start dev server (http://localhost:5173)
```
#### 2. Backend Setup
```bash
cd ../backend          ## Navigate to backend
npm install            ## Install dependencies
npm run dev            ## Start dev server (http://localhost:8787)
```
#### 3. Flask Server Setup
```bash
https://8644-14-139-34-101.ngrok-free.app/
```
To host on your own server, download the ```environment.yaml``` file.
For inference and training we have separate environments

## 2) Dataset Download

Download the dataset from 
```bash
https://www.kaggle.com/datasets/hbchaitanyabharadwaj/audio-dataset-with-10-indian-languages
```

## 3) Download weights
Follow this link to check weights
```bash
https://drive.google.com/drive/folders/1uAo9HKDtGGJGl2yLtHLVPgAzjkrzxW3W?usp=sharing
```
## 4) Finally, Run this command!
```bash
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```




