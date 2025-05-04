#ui/components/questionnaire.py

import streamlit as st
import sys
import os

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def display_questionnaire():
    """
    Display all questionnaire fields at once with skip options (Time limit removed)
    
    Returns:
        Dictionary with user responses
    """
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>🎬 Tell us about your movie watching mood</h2>
            <p style="color: #666;">Help us understand what you're in the mood for</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize responses in session state if not already done
    if 'questionnaire_responses' not in st.session_state:
        st.session_state.questionnaire_responses = {}
    
    # Viewing Environment
    st.markdown("""
        <div style="padding: 1rem; border-left: 4px solid #4ECDC4; margin: 1rem 0;">
            <h4>🏠 Your Viewing Environment</h4>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        surroundings = st.selectbox(
            "How would you describe your surroundings right now?",
            ["Bright and open", "Cozy and dim", "Noisy and busy", "Quiet and calm"],
            index=0
        )
        location = st.selectbox(
            "Where are you planning to watch the movie?",
            ["Bedroom", "Living room", "Home theater", "Outdoors", "Other"],
            index=0
        )
    with col2:
        lighting = st.selectbox(
            "What's the lighting like in your viewing space?",
            ["Bright daylight", "Soft ambient", "Dark with minimal light"],
            index=0
        )
        time_of_day = st.selectbox(
            "What time of day is it for you?",
            ["Morning", "Afternoon", "Evening", "Late night"],
            index=0
        )
    
    # Social context
    st.markdown("""
        <div style="padding: 1rem; border-left: 4px solid #FF6B6B; margin: 1rem 0;">
            <h4>👥 Who's Watching?</h4>
        </div>
    """, unsafe_allow_html=True)
    
    companions = st.selectbox(
        "Who will be watching with you?",
        ["Just me", "With partner", "Family group", "Friends", "Mixed group"],
        index=0
    )
    
    # Mood & Visualization
    st.markdown("""
        <div style="padding: 1rem; border-left: 4px solid #9B59B6; margin: 1rem 0;">
            <h4>🎭 Your Current Mood</h4>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        energy_level = st.slider(
            "What's your current energy level?",
            min_value=1, max_value=5, value=3,
            help="1 = Very low, 5 = Very high"
        )
    with col2:
        scene_visualization = st.text_input(
            "What type of movie scene are you imagining or craving right now?",
            placeholder="e.g., A thrilling car chase, A heartfelt reunion, etc."
        )
    
    mood_description = st.text_area(
        "Describe your current mood in 2-3 lines (feel free to use emojis)",
        placeholder="e.g., I'm feeling relaxed but a bit nostalgic. Looking for something that will lift my spirits without being too intense. 😌✨",
        height=100
    )
    
    # Submit button with animation
    if st.button("🎬 Find My Perfect Movies", type="primary", use_container_width=True):
        # Save all responses to session state (time_available is fixed to "No time limit")
        st.session_state.questionnaire_responses = {
            "surroundings": surroundings,
            "location": location,
            "lighting": lighting,
            "companions": companions,
            "time_available": "No time limit",  # Fixed value
            "time_of_day": time_of_day,
            "energy_level": energy_level,
            "scene_visualization": scene_visualization,
            "mood_description": mood_description
        }
        
        # Add loading animation
        with st.spinner("Preparing your personalized recommendations..."):
            st.success("Got it! Analyzing your preferences...")
        
        return st.session_state.questionnaire_responses
    
    return None