# app.py
import streamlit as st
import pandas as pd
from voice_processing import VoiceProcessor, record_audio
import os
import random

@st.cache_data
def load_movie_data():
    df = pd.read_csv("/home/rohit-saluja/students/sourava/mood2/voice_direct_input/voice_recommendation/data/indian_movies.csv")
    df.columns = [col.strip() for col in df.columns]
    return df

def extract_dynamic_keywords(transcription):
    """Extract keywords dynamically from transcription instead of using hardcoded list"""
    # Get actual genre values from the dataframe
    genres = set()
    movies_df = load_movie_data()
    for genre_str in movies_df['Genre'].dropna():
        if isinstance(genre_str, str):
            genre_list = [g.strip() for g in genre_str.split(',')]
            genres.update(genre_list)
    
    # Find mentioned genres in transcription
    matched_genres = []
    for genre in genres:
        if genre.lower() in transcription.lower():
            matched_genres.append(genre)
    
    return matched_genres

def recommend_movies(transcription, emotions, movies_df, top_n=5):
    # Extract genres mentioned in speech dynamically
    mentioned_genres = extract_dynamic_keywords(transcription)
    
    # Calculate dynamic emotion threshold based on average emotion scores
    emotion_values = list(emotions.values())
    if emotion_values:
        dynamic_threshold = sum(emotion_values) / len(emotion_values)
        dynamic_threshold = max(0.1, min(dynamic_threshold, 0.5))  # Keep within reasonable range
    else:
        dynamic_threshold = 0.3
    
    emotion_genre_map = {
        "excitement": ["Action", "Adventure", "Thriller"],
        "joy": ["Comedy", "Musical", "Family"],
        "anger": ["Action", "Crime", "Drama"],
        "calm": ["Drama", "Romance", "Biography"],
        "sadness": ["Drama", "Romance"],
        "surprise": ["Thriller", "Mystery"]
    }

    emotion_genres = []
    for emotion, score in emotions.items():
        if score > dynamic_threshold:
            emotion_genres.extend(emotion_genre_map.get(emotion, []))

    all_genres = list(set(mentioned_genres + emotion_genres))

    if all_genres:
        genre_filter = movies_df['Genre'].astype(str).apply(
            lambda x: any(genre.lower() in x.lower() for genre in all_genres)
        )
        filtered_movies = movies_df[genre_filter].copy()
    else:
        filtered_movies = movies_df.copy()

    filtered_movies['Rating(10)'] = pd.to_numeric(filtered_movies.get('Rating(10)', 0), errors='coerce').fillna(0)
    filtered_movies['Year'] = pd.to_numeric(filtered_movies.get('Year', 0), errors='coerce').fillna(0)

    # Ensure we get different results each time by shuffling first
    filtered_movies = filtered_movies.sample(frac=1).reset_index(drop=True)
    
    # Add randomness to recommendation logic
    if len(filtered_movies) > top_n:
        # Instead of always getting top N, get some diversity
        top_movies = filtered_movies.sort_values(
            by=['Rating(10)', 'Year'], ascending=[False, False]
        ).head(int(top_n * 2))  # Get more movies than needed
        
        # Pick randomly from top movies
        recommendations = top_movies.sample(n=top_n)
    else:
        recommendations = filtered_movies

    return recommendations

def main():
    st.set_page_config(page_title="🎙️ MoodFlixx Recommender", layout="centered")
    st.title("🎬 Voice-Activated Movie Recommender")
    st.write("Record or upload an audio clip to get movie recommendations based on your **mood** and **spoken genre**!")

    # Initialize session state for recording
    if 'recording_state' not in st.session_state:
        st.session_state.recording_state = None
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None
    if 'recommendation_history' not in st.session_state:
        st.session_state.recommendation_history = []

    vp = VoiceProcessor()
    language = st.radio("📢 Select Audio Language", ("en", "hi"))

    mode = st.radio("🎧 Choose Input Mode", ["Record Audio", "Upload Audio"])

    if mode == "Record Audio":
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider("🕒 Recording Duration (seconds)", 1, 10, 6)
        
        with col2:
            if st.button("🎙️ Start Recording"):
                st.session_state.recording_state = "recording"
                with st.spinner(f"Recording for {duration} seconds..."):
                    audio_path = record_audio(duration=duration, filename="temp_audio.wav")
                    if audio_path:
                        st.session_state.audio_path = audio_path
                        st.session_state.recording_state = "recorded"
                        st.success("Recording complete!")
                    else:
                        st.error("Recording failed!")
        
        if st.session_state.recording_state == "recorded" and st.session_state.audio_path:
            st.audio(st.session_state.audio_path, format='audio/wav')

    elif mode == "Upload Audio":
        uploaded_file = st.file_uploader("📤 Upload your audio file", type=["wav", "mp3"])
        if uploaded_file:
            audio_path = "uploaded_audio.wav"
            with open(audio_path, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state.audio_path = audio_path
            st.audio(audio_path, format='audio/wav')

    # Process audio if available
    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        if st.button("🚀 Process Audio"):
            with st.spinner("Analyzing your audio..."):
                try:
                    transcription = vp.transcribe(st.session_state.audio_path, language=language)
                    emotions = vp.extract_emotion_features(st.session_state.audio_path)

                    movies_df = load_movie_data()
                    
                    # Exclude previously shown movies
                    if st.session_state.recommendation_history:
                        movies_df = movies_df[~movies_df['Movie Name'].isin(st.session_state.recommendation_history)]
                    
                    recommendations = recommend_movies(transcription, emotions, movies_df)

                    # Store recommended movies
                    st.session_state.recommendation_history.extend(recommendations['Movie Name'].tolist())

                    st.subheader("📝 Transcription")
                    st.write(transcription)

                    st.subheader("🎭 Detected Emotions")
                    emotion_chart = {k: v for k, v in emotions.items() if v > 0.1}
                    if emotion_chart:
                        st.bar_chart(emotion_chart)
                    else:
                        st.write("Could not detect strong emotions.")

                    st.subheader("🍿 Recommended Movies")
                    if not recommendations.empty:
                        for _, row in recommendations.iterrows():
                            with st.expander(f"{row['Movie Name']} ({int(row['Year'])}) ⭐ {row['Rating(10)']}"):
                                st.write(f"**Genre:** {row['Genre']}")
                                st.write(f"**Language:** {row['Language']}")
                                st.write(f"**Duration:** {row['Timing(min)']} mins")
                    else:
                        st.warning("😕 No matching recommendations. Showing top-rated movies:")
                        fallback = movies_df.sort_values(by=['Rating(10)', 'Year'], ascending=[False, False]).head(5)
                        st.table(fallback[['Movie Name', 'Genre', 'Rating(10)', 'Year']])
                except Exception as e:
                    st.error(f"Error processing audio: {e}")

    # Add cleanup option
    if st.sidebar.button("🧹 Clear Session"):
        if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
            try:
                os.remove(st.session_state.audio_path)
            except:
                pass
        st.session_state.recording_state = None
        st.session_state.audio_path = None
        st.session_state.recommendation_history = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()
