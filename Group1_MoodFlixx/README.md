## 🚀 MOODFLIXX

**AI-Powered Mood-Based Movie Recommender**

> “Find the perfect film—tailored to how you feel or how you _want_ to feel.”

---

## 🔍 How It Works

1. **💬 Chatbot Interface**

   - Talk naturally:
     - _“I'm feeling down”_
     - _“I want something inspiring”_
     - _“Give me a feel-good comedy.”_

2. **🤖 AI Agents**

   - Uses multiple AI agents to:
     - Detect emotions
     - Analyze film metadata
     - Curate recommendations

3. **🎯 Mood Precision**
   - Matches movies to your mood—sad, stressed, excited, nostalgic, and beyond.

---

## ✨ Why MOODFLIXX?

- **Beyond Genres**: Not just action or romance—movies that resonate emotionally.
- **Self-Care**: Perfect for solo nights in or group watch parties.
- **Continuous Learning**: System improves with every chat and feedback loop.

---


## 🧠 Our TWO Models

We use a unique two-model recommendation system, one for short-term mood based recommendations, and the second system for watch history inspired recommendations.

Our first recommendation system leverages a multi-agent AI architecture powered by Gemini 2.0 Flash. When a user inputs their mood or preference, our primary agent analyzes the text to extract emotional context and intent. This emotional fingerprint is then vectorized and matched against our movie database in LanceDB, where each film has been pre-encoded with emotional and thematic embeddings. A secondary agent evaluates metadata factors like genre, actors, and historical user preferences to refine these matches. For complex queries (like "action movies that won't make me more anxious"), our system employs a reasoning layer that balances multiple emotional dimensions. The final recommendations are ranked using a composite scoring algorithm that prioritizes mood-content alignment while maintaining diversity in suggestions. Each interaction improves our model through feedback loops that fine-tune the emotional mapping between user states and content characteristics.

---

## 📽️ Watch History-Based Recommendation

We use Cornac's **BiVAE** model for watch-history based recommendations. BiVAEs are specialisation of the Variational Auto Encoder meant to deal with dyadic data- for example, users and their ratings of movies.
When a user presents their watch history, the model maps it to the latent space and finds the closest related known user. Recommendations are then generated for this known user based on their ratings. (Collaborative Filtering).
The BiVAE model is trained on the **MovieLens 32M** dataset, which includes data of over 750,000 movies and 8 million ratings up to 2023.
The recommendations generated are then filtered through gemini along with information about the user's current mood, hence giving highly relevant recommendations based not only on watch history but also mood.
The recommendations (predicted ratings) for this similar user are then used as recommendations for the new user.

---

## 🎬 Playlist Creation

User feedback serves as a dynamic weighting mechanism to tailor a personalized playlist.  
Based on this feedback, we curate a custom selection of top-rated movies, while intelligently considering various attributes — such as **Genre**, **Cast**, **Emotion**, and **Themes** — extracted from the user's watch history.  
This ensures a deeply personalized and context-aware viewing experience.

---


## 🧰 TECH STACK

| Layer         | Technology                |
| ------------- | ------------------------- |
| **Frontend**  | Next.js (TypeScript)      |
| **Backend**   | FastAPI (Python)          |
| **Database**  | Firebase                  |
| **Vector DB** | LanceDB                   |
| **AI Agents** | Gemini (gemini-2.0-flash) |
| **Bi VAE**    | Cornacs                   |

---

## 👩‍💻 INSTRUCTIONS

- Clone the repository:

```bash
    git clone https://github.com/Voldemort271/cs671-hack.git
    cd cs671-hack
```

- Install dependencies:

```bash
    pip install -r requirements.txt
```

- Set up environment variables:

```bash
    cp .env.example .env
```

- BiVAE QuickStart and Testing:
   - 1. Train BiVAE
   ```bash
      cd BiVAE
      jupyter notebook cornac_bivae_deep_dive_50.ipynb
   ```
   - 2. Download links
      - [🔗 Model Weights](https://drive.google.com/file/d/1QsUqXv-Jk6EdgTiwkIWKvgZkBubb_LFP/view?usp=sharing)  
      - [📁 Dataset](https://drive.google.com/file/d/1S4MpwbRSsAcAas6IjlsT_pDYW3-0hKtE/view?usp=sharing)  
      - [📊 Training Data](https://drive.google.com/file/d/1ZH7Qnw37GcXgHUWiy8MT435kIy8bKFbj/view?usp=sharing)  
      - [💾 Auto-saved Outputs](https://drive.google.com/file/d/1Wz0lKvu0Sz9LS70bdVpny_W1uH3BTQC8/view?usp=sharing)



- cd into the `frontend` directory , install dependencies and start the frontend server:

```bash
    cd frontend
    npm install
    npm run dev
```

- cd into the `backend` directory and start the server:

```bash
    cd backend
    uvicorn main:app --reload --port 8000
```

- cd into the `BiVAE` directory and start the second server:
```bash
   cd backend
   uvicorn bivae_web2:app --reload --port 8001
   ngrok http 8001
```
---


## 📸 SHOWCASE

![Demo: HomePage](https://github.com/Voldemort271/cs671-hack/blob/main/images/img1.jpg)
*Home Page*

<br><br>

![Demo: SideBar](https://github.com/Voldemort271/cs671-hack/blob/main/images/img3.jpg)
*Sidebar Navigation*

<br><br>

![Demo: Search Example](https://github.com/Voldemort271/cs671-hack/blob/main/images/img2.jpg)
_User is asking for action movies by Amitabh Bachchan_

<br><br>

![Demo: Results](https://github.com/Voldemort271/cs671-hack/blob/main/images/img4.jpg)
_Best results for the query_

<br><br>

![Demo: Features](https://github.com/Voldemort271/cs671-hack/blob/main/images/img5.jpg)
_User can rate the recommended movie_

---

## 🛠 CONTRIBUTORS

- Shubham S Padhi
- Piyush Dwivedi
- Harshit Jain
- Aarya Agarwal
- Satvik Pareek
- Arani Ghosh

---
