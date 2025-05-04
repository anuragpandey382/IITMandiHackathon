#ui/components/results_display.py

import streamlit as st
import sys
import os
import pandas as pd

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def display_movie_recommendations(recommendations_df):
    """
    Display movie recommendations in an enhanced, interactive format
    
    Args:
        recommendations_df: DataFrame with movie recommendations
    """
    st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h2>✨ Your Personalized Movie Recommendations</h2>
            <p style="color: #666;">Movies hand-picked based on your current mood and preferences</p>
        </div>
    """, unsafe_allow_html=True)
    
    if recommendations_df.empty:
        st.warning("No recommendations found. Please try different inputs.")
        return
    
    # Ensure we show exactly 5 recommendations
    num_to_show = min(5, len(recommendations_df))
    if num_to_show < 5:
        st.warning(f"Only {num_to_show} movies matched your criteria. Consider broadening your preferences.")
    
    # Display each recommendation with enhanced styling
    for i, (_, movie) in enumerate(recommendations_df.head(5).iterrows(), 1):
        # Create a card for each movie
        st.markdown(f"""
            <div style="background: linear-gradient(45deg, #f6f8fc, #ffffff); 
                        border-radius: 1rem; padding: 1.5rem; margin: 1.5rem 0; 
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 0.5rem;">
                    {i}. {movie['movie_name']} ({movie.get('year', 'N/A')})
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns([3, 1])
        
        # Movie details
        with cols[0]:
            # Display genres with emoji categorization
            genres = movie.get('genres', '')
            if genres:
                genres_list = genres.split('|')
                genre_emojis = {
                    'Action': '💥', 'Adventure': '🗺️', 'Animation': '🎨', 'Biography': '📚',
                    'Comedy': '😂', 'Crime': '🚔', 'Documentary': '📺', 'Drama': '🎭',
                    'Family': '👨‍👩‍👧‍👦', 'Fantasy': '🦄', 'History': '📜', 'Horror': '👻',
                    'Music': '🎵', 'Musical': '🎭🎵', 'Mystery': '🔍', 'Romance': '❤️',
                    'Sci-Fi': '🚀', 'Sport': '⚽', 'Thriller': '😱', 'War': '⚔️'
                }
                
                genre_tags = []
                for genre in genres_list:
                    emoji = genre_emojis.get(genre, '🎬')
                    genre_tags.append(f"{emoji} {genre}")
                
                st.markdown("**Genres:**")
                genre_cols = st.columns(min(len(genre_tags), 4))
                for idx, tag in enumerate(genre_tags):
                    if idx < len(genre_cols):
                        genre_cols[idx].markdown(f"""
                            <div style="background: #f0f2f6; padding: 0.3rem 0.8rem; 
                                        border-radius: 1rem; margin: 0.2rem 0; text-align: center;">
                                {tag}
                            </div>
                        """, unsafe_allow_html=True)
            
            # Display cast if available
            if 'cast' in movie and movie['cast']:
                st.markdown(f"**⭐ Cast:** {movie['cast']}")
            
            # Display overview
            overview = movie.get('overview', '')
            if overview:
                st.markdown("**📝 Overview:**")
                st.markdown(f"<p style='color: #555;'>{overview}</p>", unsafe_allow_html=True)
            
            # Display match details with enhanced visualization
            col1, col2 = st.columns(2)
            with col1:
                similarity_score = int(movie.get('similarity_score', 0) * 100)
                st.markdown(f"""
                    <div style="background: #e8f4fd; padding: 0.5rem; border-radius: 0.5rem; text-align: center;">
                        <strong>🎯 Content Match</strong><br>
                        <span style="font-size: 1.5rem; color: #1976d2;">{similarity_score}%</span>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                genre_score = int(movie.get('genre_match_score', 0) * 100)
                st.markdown(f"""
                    <div style="background: #f3e5f5; padding: 0.5rem; border-radius: 0.5rem; text-align: center;">
                        <strong>🎭 Genre Match</strong><br>
                        <span style="font-size: 1.5rem; color: #7b1fa2;">{genre_score}%</span>
                    </div>
                """, unsafe_allow_html=True)
            
            # Display overall match with animated progress bar
            match_score = int(movie.get('final_score', 0) * 100)
            st.markdown(f"""
                <div style="margin: 1rem 0;">
                    <strong>Overall Match:</strong>
                    <div style="background: #e0e0e0; border-radius: 1rem; height: 1.5rem; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #4caf50, #8bc34a); 
                                    width: {match_score}%; height: 100%; border-radius: 1rem;
                                    display: flex; align-items: center; justify-content: center; 
                                    color: white; font-weight: bold;">
                            {match_score}%
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Movie poster or placeholder with better styling
        with cols[1]:
            st.markdown("""
                <div style="background: #f5f5f5; border-radius: 0.5rem; padding: 0.5rem; text-align: center;">
                    <img src="https://via.placeholder.com/150x225" style="border-radius: 0.5rem;"/>
                    <p style="color: #666; margin-top: 0.5rem; font-size: 0.9rem;">Poster coming soon</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Add a call-to-action
    st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 1rem; margin: 2rem 0;">
            <h4>Ready to watch? 🍿</h4>
            <p style="color: #666;">Pick your favorite and enjoy your movie night!</p>
        </div>
    """, unsafe_allow_html=True)