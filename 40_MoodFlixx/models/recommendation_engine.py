#recommendation_engine.py

import sys
import os
import pandas as pd
import numpy as np

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.data_processor import load_movies_data, parse_genres
from utils.embedding_utils import find_similar_movies
from utils.debug_logger import save_similarity_filtered_data, save_genre_filtered_data
from models.text_embedder import TextEmbedder
from models.mood_predictor import MoodPredictor


class RecommendationEngine:
    """
    Core recommendation engine for MoodFlixx
    """
    
    def __init__(self):
        """Initialize the recommendation engine"""
        self.movies_df = load_movies_data()
        self.text_embedder = TextEmbedder()
        self.mood_predictor = MoodPredictor()
    
    def generate_recommendations(self, user_responses, selected_emojis=None):
        """
        Generate movie recommendations based on user responses
        
        Args:
            user_responses: Dictionary of user responses to questionnaire
            selected_emojis: List of selected emoji data (optional)
            
        Returns:
            Tuple of (DataFrame with top recommendations, List of predicted genres)
        """
        # Step 1: Predict genres and emotions from user responses
        genre_emotion_responses = user_responses.copy()
        
        # Add emojis if provided
        if selected_emojis and len(selected_emojis) > 0:
            emoji_str = ", ".join([f"{e['emoji']} ({e['name']})" for e in selected_emojis])
            genre_emotion_responses['selected_emojis'] = emoji_str
        
        predicted = self.mood_predictor.predict_genre_and_emotions(genre_emotion_responses)
        predicted_genres = predicted.get('genres', [])
        predicted_emotions = predicted.get('emotions', [])
        
        # Step 2: Generate story overview from text inputs
        scene_text = user_responses.get('scene_visualization', '')
        feelings_text = user_responses.get('mood_description', '')
        
        story_overview = self.mood_predictor.generate_story_overview(scene_text, feelings_text)
        
        # Step 3: Find similar movies based on story overview
        story_embedding = self.text_embedder.get_embedding(story_overview)
        
        if story_embedding:
            similar_movies = find_similar_movies(
                self.movies_df, 
                story_embedding,
                top_n=config.TOP_N_SIMILARITY,
                threshold=config.SIMILARITY_THRESHOLD
            )
        else:
            # If embedding fails, use a subset of movies
            similar_movies = self.movies_df.sample(min(config.TOP_N_SIMILARITY, len(self.movies_df)))
            similar_movies['similarity_score'] = 0.5  # Default score
        
        # Save similarity filtered data for debugging
        similarity_filtered_file = save_similarity_filtered_data(similar_movies)
        
        # Step 4: Apply enhanced filtering with genre, emotion, and metadata
        final_recommendations = self._apply_enhanced_filtering(
            similar_movies, 
            predicted_genres, 
            predicted_emotions,
            user_responses
        )
        
        # Save genre filtered data for debugging
        genre_filtered_file = save_genre_filtered_data(final_recommendations)
        
        # Return top recommendations along with predicted genres as a tuple
        return final_recommendations.head(config.FINAL_RECOMMENDATIONS), predicted_genres
    
    def _apply_enhanced_filtering(self, similar_movies, predicted_genres, predicted_emotions, user_responses,
                                 similarity_weight=0.5, genre_weight=0.3, emotion_weight=0.2):
        """
        Apply enhanced filtering to similarity-filtered movies
        
        Args:
            similar_movies: DataFrame with similarity-filtered movies
            predicted_genres: List of predicted genres
            predicted_emotions: List of predicted emotions
            user_responses: Dictionary of user responses
            similarity_weight: Weight for similarity score
            genre_weight: Weight for genre match score
            emotion_weight: Weight for emotion match score
            
        Returns:
            DataFrame with filtered movies and final scores
        """
        # Create a copy to avoid modifying the original
        result_df = similar_movies.copy()
        
        # Calculate genre match score with weighted importance
        result_df['genre_match_score'] = result_df['genres'].apply(
            lambda x: self._calculate_weighted_genre_match(x, predicted_genres)
        )
        
        # Calculate emotion match score
        result_df['emotion_match_score'] = result_df.apply(
            lambda row: self._calculate_emotion_match(row, predicted_emotions), axis=1
        )
        
        # Calculate metadata relevance (recency and popularity if available)
        self._calculate_metadata_relevance(result_df)
        
        # Calculate final score (combination of all factors)
        # Normalize weights to sum to 1
        total_weight = similarity_weight + genre_weight + emotion_weight
        norm_similarity_weight = similarity_weight / total_weight
        norm_genre_weight = genre_weight / total_weight
        norm_emotion_weight = emotion_weight / total_weight
        
        result_df['final_score'] = (
            result_df['similarity_score'] * norm_similarity_weight + 
            result_df['genre_match_score'] * norm_genre_weight +
            result_df['emotion_match_score'] * norm_emotion_weight
        )
        
        # Apply recency and popularity modifiers if available
        if 'recency_score' in result_df.columns:
            result_df['final_score'] = result_df['final_score'] * 0.9 + result_df['recency_score'] * 0.1
        
        if 'popularity_score' in result_df.columns:
            result_df['final_score'] = result_df['final_score'] * 0.9 + result_df['popularity_score'] * 0.1
        
        # Apply dynamic threshold based on score distribution
        mean_score = result_df['final_score'].mean()
        std_score = result_df['final_score'].std()
        min_threshold = getattr(config, 'MIN_SCORE_THRESHOLD', 0.3)
        threshold = max(min_threshold, mean_score - 0.5 * std_score)
        
        # Filter by threshold
        filtered_df = result_df[result_df['final_score'] >= threshold]
        
        # If filtering results in too few recommendations, use the original set
        min_recommendations = getattr(config, 'MIN_RECOMMENDATIONS', 5)
        if len(filtered_df) < min_recommendations:
            filtered_df = result_df
        
        # Sort by final score
        filtered_df = filtered_df.sort_values('final_score', ascending=False)
        
        return filtered_df
    
    def _calculate_weighted_genre_match(self, movie_genres_str, predicted_genres):
        """
        Calculate how well a movie's genres match the predicted genres with weighted importance
        
        Args:
            movie_genres_str: String of pipe-separated genres
            predicted_genres: List of predicted genres
            
        Returns:
            Score between 0 and 1
        """
        if not predicted_genres:
            return 0.5  # Neutral score if no predictions
        
        movie_genres = parse_genres(movie_genres_str)
        
        if not movie_genres:
            return 0
        
        # Give higher weight to primary genres (first in the predicted list)
        primary_weight = 1.5
        secondary_weight = 1.0
        
        weighted_matches = 0
        weighted_max = 0
        
        # Process primary genre (first predicted)
        if predicted_genres and len(predicted_genres) > 0:
            primary_genre = predicted_genres[0]
            weighted_max += primary_weight
            
            if primary_genre in movie_genres:
                weighted_matches += primary_weight
        
        # Process secondary genres (remaining predicted)
        for genre in predicted_genres[1:]:
            weighted_max += secondary_weight
            if genre in movie_genres:
                weighted_matches += secondary_weight
        
        # Calculate weighted score
        if weighted_max > 0:
            score = weighted_matches / weighted_max
        else:
            score = 0.5
        
        return score
    
    def _calculate_emotion_match(self, movie_row, predicted_emotions):
        """
        Calculate how well a movie's emotional content matches predicted emotions
        
        Args:
            movie_row: DataFrame row with movie data
            predicted_emotions: List of predicted emotions
            
        Returns:
            Score between 0 and 1
        """
        if not predicted_emotions:
            return 0.5  # Neutral score if no predictions
        
        # Extract movie description or overview if available
        movie_text = ""
        for field in ['overview', 'description', 'summary', 'plot']:
            if field in movie_row and isinstance(movie_row[field], str):
                movie_text += movie_row[field] + " "
        
        movie_text = movie_text.lower()
        
        # Define emotion keywords dictionary
        emotion_keywords = {
            'Happy': ['happy', 'joy', 'uplifting', 'comedy', 'funny', 'humor', 'laugh', 'cheerful', 'fun'],
            'Sad': ['sad', 'tragedy', 'drama', 'melancholy', 'grief', 'sorrow', 'tear', 'heartbreak'],
            'Excited': ['exciting', 'thrill', 'adventure', 'action', 'suspense', 'adrenaline', 'intense'],
            'Relaxed': ['calm', 'peaceful', 'gentle', 'soothing', 'meditation', 'slow-paced', 'easy'],
            'Tense': ['tense', 'anxiety', 'fear', 'horror', 'thriller', 'paranoia', 'stress', 'nervous'],
            'Romantic': ['romance', 'love', 'relationship', 'passion', 'date', 'attraction', 'wedding'],
            'Nostalgic': ['nostalgia', 'memory', 'childhood', 'reminisce', 'past', 'history', 'retro'],
            'Inspired': ['inspiration', 'motivational', 'triumph', 'success', 'achievement', 'overcome'],
            'Fearful': ['fear', 'scary', 'horror', 'terrifying', 'creepy', 'nightmare', 'dread'],
            'Calm': ['calm', 'serene', 'peaceful', 'tranquil', 'relaxed', 'gentle', 'quiet']
        }
        
        # Calculate emotion match score
        total_score = 0
        num_emotions = 0
        
        for emotion in predicted_emotions:
            if emotion in emotion_keywords:
                keywords = emotion_keywords[emotion]
                matches = sum(1 for keyword in keywords if keyword in movie_text)
                if keywords:
                    # Calculate normalized score for this emotion
                    emotion_score = min(1.0, matches / max(1, len(keywords) / 3))
                    total_score += emotion_score
                    num_emotions += 1
        
        # Return average score or default if no emotions matched
        if num_emotions > 0:
            return total_score / num_emotions
        else:
            return 0.5
    
    def _calculate_metadata_relevance(self, df):
        """
        Calculate relevance scores based on movie metadata (recency, popularity)
        
        Args:
            df: DataFrame with movies
            
        Modifies:
            Adds recency_score and popularity_score columns to the DataFrame
        """
        # Calculate recency score if release_year is available
        if 'release_year' in df.columns:
            try:
                # Convert to numeric and handle non-numeric values
                df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
                
                # Calculate recency score (normalize between 0 and 1)
                current_year = pd.Timestamp.now().year
                df['recency_score'] = df['release_year'].apply(
                    lambda y: 0.5 if pd.isna(y) else min(1.0, max(0.0, (y - 1990) / (current_year - 1990)))
                )
            except Exception:
                # If any error occurs, use default value
                df['recency_score'] = 0.5
        
        # Calculate popularity score if available
        popularity_field = next((f for f in ['vote_count', 'popularity', 'vote_average'] 
                               if f in df.columns), None)
        
        if popularity_field:
            try:
                # Convert to numeric and handle non-numeric values
                df[popularity_field] = pd.to_numeric(df[popularity_field], errors='coerce')
                
                # Get max value for normalization
                max_val = df[popularity_field].max()
                
                # Calculate popularity score (normalize between 0 and 1)
                if max_val > 0:
                    df['popularity_score'] = df[popularity_field].apply(
                        lambda v: 0.5 if pd.isna(v) else min(1.0, max(0.0, v / max_val))
                    )
                else:
                    df['popularity_score'] = 0.5
            except Exception:
                # If any error occurs, use default value
                df['popularity_score'] = 0.5