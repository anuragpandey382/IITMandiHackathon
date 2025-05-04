**MoodFlix** is an AI-powered movie recommendation system that personalizes suggestions based on your **current mood**, preferences, and cultural background. Unlike traditional recommendation engines that rely solely on watch history or trending content, MoodFlix tailors recommendations in real-time using a quick and lightweight mood questionnaire.

---

## 💡 What is MoodFlix?

With the rise of OTT platforms, users are overwhelmed by the vast number of content choices. MoodFlix solves this by asking users a few simple questions at login to determine their **emotional state**, **genre preferences**, **favorite actors**, and **language/cultural tastes**. Using this input, the system recommends movies that best match the user's mood at that moment — offering a smarter, more intuitive viewing experience.

---

## 🚀 How to Run MoodFlix

1. **Clone this repository**
   ```bash
   git clone https://github.com/your-username/MoodFlix-Smart-Movie-Recommender-System.git
   cd MoodFlix-Smart-Movie-Recommender-System
   ```

2. **Install the required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**
   ```bash
   streamlit run run.py
   ```

---
## To see the weights of trained-model
we used a custom trained model to assign moods to movies by inferring from their overviews, to use that model, please load the model [weights](https://drive.google.com/drive/folders/1nI_oh_hDGofhzUgWFaQtgpWmUyUY8Pd8?usp=sharing) into the ```KnowledgeBase``` directory.



## Note
To run voice model, we have made a separate file for it, we did not have time to integrate it into the main application.
run: ```streamlit run voice.py ```

## 🧠 Features

- AI-powered personalized movie recommendations
- Mood-based lightweight questionnaire at login
- Considers user preferences like:
  - Mood and emotional state
  - Favorite genres, actors, and languages
  - Cultural and linguistic tastes

---

## 📌 Future Improvements

- We were trying to integrate other input modalities like voice and input image to infer emations.
- Current Implementation is limited to our dataset, hence we might improve this in the future.
- Imporve latency, current latency is between 5 to 15 seconds, we wish to improve this moving forward.
