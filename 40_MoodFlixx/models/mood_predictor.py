import sys
import os
import requests
import json
from langchain.prompts import PromptTemplate

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class MoodPredictor:
    """
    Class for predicting genre and mood using Ollama's Llama3.2 model
    """
    
    def __init__(self, model_name=None, api_url=None):
        """
        Initialize the mood predictor
        
        Args:
            model_name: Name of the Ollama model to use
            api_url: URL of the Ollama API
        """
        self.model_name = model_name or config.OLLAMA_MODEL
        self.api_url = api_url or config.OLLAMA_API_URL
    
    def predict_genre_and_emotions(self, user_responses):
        """
        Predict genres and emotions based on user responses
        
        Args:
            user_responses: Dictionary of user responses to questions
            
        Returns:
            Dictionary with predicted genres and emotions
        """
        # Format the prompt
        prompt = self._format_genre_prediction_prompt(user_responses)
        
        # Get response from Ollama
        response = self._call_ollama(prompt)
        
        # Parse response
        try:
            result = json.loads(response)
            return result
        except:
            # If can't parse as JSON, try to extract genres and emotions from text
            genres = self._extract_genres_from_text(response)
            emotions = self._extract_emotions_from_text(response)
            return {
                "genres": genres,
                "emotions": emotions
            }
    
    def generate_story_overview(self, scene_text, feelings_text):
        """
        Generate a 50-word story overview based on user inputs
        
        Args:
            scene_text: Text describing a specific scene
            feelings_text: Text describing user feelings
            
        Returns:
            Story overview as a string
        """
        # Format the prompt
        prompt = self._format_story_overview_prompt(scene_text, feelings_text)
        
        # Get response from Ollama
        response = self._call_ollama(prompt)
        
        return response.strip()
    
    def _call_ollama(self, prompt):
        """
        Call Ollama API with the given prompt
        
        Args:
            prompt: The prompt to send to Ollama
            
        Returns:
            Response from Ollama as a string
        """
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.api_url, json=data)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"Error calling Ollama API: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Exception when calling Ollama API: {e}")
            return ""
    
    def _format_genre_prediction_prompt(self, user_responses):
        """
        Format prompt for genre and emotion prediction
        Args:
        user_responses: Dictionary of user responses to questions
        Returns:
        Formatted prompt string
        """
        prompt = """Based on the following user responses about their movie watching context,
        predict the most suitable movie genres and emotions/mood for recommendations.
        Respond in valid JSON format with two keys: 'genres' (list of movie genres) and 'emotions' (list of emotions).
        User responses:
        """
        for key, value in user_responses.items():
            prompt += f"\n- {key}: {value}"
        prompt += """
        Return your response as valid JSON like this:
        {
        "genres": ["Genre1", "Genre2", "Genre3"],
        "emotions": ["Emotion1", "Emotion2"]
        }
        Choose from these common movie genres:
        Action, Adventure, Animation, Biography, Comedy, Crime, Documentary, Drama, Family,
        Fantasy, History, Horror, Music, Musical, Mystery, Romance, Sci-Fi, Sport, Thriller, War
        Choose from these common emotions:
        Happy, Sad, Excited, Relaxed, Tense, Romantic, Nostalgic, Inspired, Fearful, Calm
        """
        return prompt

    def _format_story_overview_prompt(self, scene_text, feelings_text):
        """
        Format prompt for story overview generation
        Args:
        scene_text: Text describing a specific scene
        feelings_text: Text describing user feelings
        Returns:
        Formatted prompt string
        """
        prompt = f"""Based on the following user inputs, generate a concise 50-word overview
        of what type of story the user might enjoy watching.
        Specific scene in mind: {scene_text}
        Current feelings: {feelings_text}
        Generate a 50-word overview of a story that would match these preferences:
        """
        return prompt
    
    def _extract_genres_from_text(self, text):
        """
        Extract genre mentions from text response when JSON parsing fails
        
        Args:
            text: Text response from Ollama
            
        Returns:
            List of identified genres
        """
        common_genres = [
            "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", 
            "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", 
            "Music", "Musical", "Mystery", "Romance", "Sci-Fi", "Sport", "Thriller", "War"
        ]
        
        found_genres = []
        for genre in common_genres:
            if genre.lower() in text.lower():
                found_genres.append(genre)
        
        return found_genres or ["Drama"]  # Default to Drama if nothing found
    
    def _extract_emotions_from_text(self, text):
        """
        Extract emotion mentions from text response when JSON parsing fails
        
        Args:
            text: Text response from Ollama
            
        Returns:
            List of identified emotions
        """
        common_emotions = [
            "Happy", "Sad", "Excited", "Relaxed", "Tense", "Romantic", 
            "Nostalgic", "Inspired", "Fearful", "Calm"
        ]
        
        found_emotions = []
        for emotion in common_emotions:
            if emotion.lower() in text.lower():
                found_emotions.append(emotion)
        
        return found_emotions or ["Relaxed"]  # Default to Relaxed if nothing found