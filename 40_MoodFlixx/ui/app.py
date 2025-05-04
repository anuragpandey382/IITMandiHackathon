#ui/app.py

import streamlit as st
import sys
import os
import pandas as pd
import time

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from models.recommendation_engine import RecommendationEngine
from ui.components.questionnaire import display_questionnaire
from ui.components.emoji_selector import display_emoji_selector
from ui.components.results_display import display_movie_recommendations
from ui.components.feedback_collector import display_feedback_collector


def setup_page():
    """Set up the Streamlit page configuration"""
    st.set_page_config(
        page_title=config.STREAMLIT_PAGE_TITLE,
        layout=config.STREAMLIT_LAYOUT,
        initial_sidebar_state="expanded"
    )
    
    # Enhanced custom CSS for better visual appeal
    st.markdown(f"""
        <style>
            {config.CUSTOM_CSS}
            .main-header {{
                font-size: 3.5rem;
                font-weight: bold;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0;
                animation: gradient 3s ease infinite;
            }}
            .subheader {{
                color: #666;
                font-size: 1.5rem;
                margin-bottom: 2rem;
            }}
            .mood-display {{
                padding: 1rem;
                border-radius: 0.5rem;
                background: #f0f2f6;
                margin: 1rem 0;
            }}
            .predicted-genre {{
                display: inline-block;
                padding: 0.3rem 0.8rem;
                margin: 0.2rem;
                border-radius: 1rem;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                font-weight: bold;
            }}
            @keyframes gradient {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
        </style>
    """, unsafe_allow_html=True)
    
    # Display animated header
    st.markdown('<h1 class="main-header">MoodFlixx 🎬</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Discover movies that match your vibe ✨</p>', unsafe_allow_html=True)
    
    # Add an interactive mood bar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🎭 **Current Mood:**")
    with col2:
        st.markdown("🎬 **Movie Time:**")
    with col3:
        st.markdown("🎯 **Perfect Match:**")
    
    st.markdown("---")


def display_mood_summary(selected_emojis, responses):
    """Display a dynamic mood summary"""
    st.markdown("### Your Current Vibe Check ✨")
    
    if selected_emojis:
        emoji_str = " ".join([e['emoji'] for e in selected_emojis])
        st.markdown(f'<div class="mood-display">Your mood: {emoji_str}</div>', unsafe_allow_html=True)
    
    if responses:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🌟 Energy Level: {responses.get('energy_level', 'N/A')}/5")
        with col2:
            st.info(f"👥 Watching: {responses.get('companions', 'Just me')}")
        
        if responses.get('mood_description'):
            st.markdown(f"**Mood Description:** {responses['mood_description']}")


def main():
    """Main application function"""
    # Set up the page
    setup_page()
    
    # Initialize recommendation engine
    recommendation_engine = RecommendationEngine()
    
    # Initialize session state for tracking app flow
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'input'
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    
    if 'predicted_genres' not in st.session_state:
        st.session_state.predicted_genres = None
    
    # Handle different stages of the app
    if st.session_state.app_stage == 'input':
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display questionnaire
            responses = display_questionnaire()
        
        with col2:
            # Display emoji selector
            selected_emojis = display_emoji_selector()
            
            # Show mood summary in sidebar
            if selected_emojis or responses:
                with st.sidebar:
                    display_mood_summary(selected_emojis, responses)
        
        # Proceed to recommendations when form is submitted
        if responses is not None:
            st.session_state.responses = responses
            st.session_state.selected_emojis = selected_emojis
            st.session_state.app_stage = 'generating'
            st.rerun()
    
    elif st.session_state.app_stage == 'generating':
        # Display loading animation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🎭 Analyzing your mood...")
        progress_bar.progress(25)
        time.sleep(0.5)
        
        status_text.text("🎬 Finding perfect movie matches...")
        progress_bar.progress(50)
        time.sleep(0.5)
        
        status_text.text("🎯 Calculating match scores...")
        progress_bar.progress(75)
        time.sleep(0.5)
        
        # Generate recommendations and predicted genres
        recommendations, predicted_genres = recommendation_engine.generate_recommendations(
            st.session_state.responses,
            st.session_state.selected_emojis
        )
        
        # Store results in session state
        st.session_state.recommendations = recommendations
        st.session_state.predicted_genres = predicted_genres
        st.session_state.app_stage = 'recommendations'
        
        status_text.text("✨ Ready! Preparing your recommendations...")
        progress_bar.progress(100)
        time.sleep(0.5)
        st.rerun()
    
    elif st.session_state.app_stage == 'recommendations':
        # Display mood summary in main area
        display_mood_summary(st.session_state.selected_emojis, st.session_state.responses)
        
        # Display predicted genres prominently
        if st.session_state.predicted_genres:
            st.markdown("### Predicted Genres Based on Your Mood")
            genre_columns = st.columns(min(len(st.session_state.predicted_genres), 5))
            for idx, genre in enumerate(st.session_state.predicted_genres):
                if idx < len(genre_columns):
                    genre_columns[idx].markdown(f'<span class="predicted-genre">{genre}</span>', unsafe_allow_html=True)
            st.markdown("---")
        
        # Display recommendations
        display_movie_recommendations(st.session_state.recommendations)
        
        # Display feedback collector
        feedback = display_feedback_collector()
        
        # Option to start over with fun animation
        if st.button("✨ Discover More Movies", type="primary", use_container_width=True):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()