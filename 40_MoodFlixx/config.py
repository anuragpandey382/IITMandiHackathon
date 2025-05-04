# Configuration settings for MoodFlixx

# File paths
MOVIES_CSV_PATH = "data/movies.csv"
EMOJI_CSV_PATH = "data/emoji_data.csv"

# Logging
SIMILARITY_FILTERED_DIR = "logs/similarity_filtered"
GENRE_FILTERED_DIR = "logs/genre_filtered"
LOG_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Model settings
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Recommendation settings
TOP_N_SIMILARITY = 100  # Number of movies to retain after similarity filtering
FINAL_RECOMMENDATIONS = 5  # Number of final recommendations to show
EMOJI_WEIGHT = 4.0  # Weight multiplier for emoji-based emotions
SIMILARITY_THRESHOLD = 0.55  # Minimum similarity score to consider
MIN_SCORE_THRESHOLD = 0.3  # Minimum score threshold for filtering
MIN_RECOMMENDATIONS = 5  # Minimum number of recommendations to show

# Default values
DEFAULT_TIME_AVAILABLE = "No time limit"

# UI settings
STREAMLIT_PAGE_TITLE = "MoodFlixx: Smart Movie Recommendations"
STREAMLIT_LAYOUT = "wide"
STREAMLIT_THEME = "light"

# Enhanced CSS styles
CUSTOM_CSS = """
    .sub-header {
        font-size: 20px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    
    .emoji-selector {
        font-size: 24px;
        cursor: pointer;
    }
    
    .movie-card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Enhanced UI elements */
    .main-header {
        font-size: 3.5rem !important;
        font-weight: bold;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        background-size: 200% auto;
        animation: gradient-animation 3s ease infinite;
    }
    
    .subheader {
        color: #666;
        font-size: 1.5rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Animations */
    @keyframes gradient-animation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Enhanced movie card */
    .movie-card {
        background: #ffffff;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: fade-in 0.5s ease-out;
    }
    
    .mood-display {
        padding: 1rem;
        border-radius: 0.5rem;
        background: #f0f2f6;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.5rem;
    }
    
    .predicted-genre {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 1rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        font-weight: bold;
        animation: fade-in 0.5s ease-out;
    }
    
    /* Enhanced buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(45deg, #667eea, #764ba2);
        border-radius: 1rem;
        animation: progress-animation 1s ease-in;
    }
    
    @keyframes progress-animation {
        from { width: 0%; }
        to { width: var(--value); }
    }
    
    /* Form elements */
    .stSelectbox label, .stTextInput label, .stTextArea label {
        font-weight: bold;
        color: #2c3e50;
    }
    
    .stSlider {
        padding: 1rem 0;
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        padding: 1rem;
        text-align: center;
        color: #666;
        border-top: 1px solid #ddd;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem !important;
        }
        
        .subheader {
            font-size: 1.2rem;
        }
    }
"""

# Emoji categories for the selector
EMOJI_CATEGORIES = {
    "happy": ['smile', 'happy', 'joy', 'laugh', 'grin'],
    "sad": ['sad', 'cry', 'worried', 'disappointed'], 
    "love": ['love', 'heart', 'kiss'],
    "other": []  # Everything else
}

# Emoji mappings for genres
GENRE_EMOJIS = {
    'Action': '💥',
    'Adventure': '🗺️',
    'Animation': '🎨',
    'Biography': '📚',
    'Comedy': '😂',
    'Crime': '🚔',
    'Documentary': '📺',
    'Drama': '🎭',
    'Family': '👨‍👩‍👧‍👦',
    'Fantasy': '🦄',
    'History': '📜',
    'Horror': '👻',
    'Music': '🎵',
    'Musical': '🎭🎵',
    'Mystery': '🔍',
    'Romance': '❤️',
    'Sci-Fi': '🚀',
    'Sport': '⚽',
    'Thriller': '😱',
    'War': '⚔️',
    'Western': '🤠',
    'Default': '🎬'
}

# Feedback rating labels
FEEDBACK_RATING_LABELS = {
    1: "😟 Not relevant at all",
    2: "😕 Somewhat relevant",
    3: "😊 Relevant enough",
    4: "😃 Very relevant",
    5: "🌟 Perfectly relevant!"
}

# Loading messages for the recommendation generation
LOADING_MESSAGES = [
    "🎭 Analyzing your mood...",
    "🎬 Finding perfect movie matches...",
    "🎯 Calculating match scores...",
    "✨ Preparing your recommendations..."
]

# Application stages
APP_STAGES = {
    'input': 'input',
    'generating': 'generating',
    'recommendations': 'recommendations'
}

# Data file paths (adjusted to your file paths)
DATA_PATHS = {
    'movies': MOVIES_CSV_PATH,
    'emoji_data': EMOJI_CSV_PATH
}