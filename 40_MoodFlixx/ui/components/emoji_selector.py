#ui/components/emoji_selector.py

import streamlit as st
import pandas as pd
import sys
import os

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.data_processor import load_emoji_data


def display_emoji_selector():
    """
    Display enhanced emoji selector component with animation and better UX
    
    Returns:
        List of selected emoji data
    """
    st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h3>🎭 How are you feeling right now?</h3>
            <p style="color: #666;">Select the emojis that best match your current mood (multiple selections welcome)</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load emoji data
    emoji_df = load_emoji_data()
    
    if emoji_df.empty:
        st.error("Could not load emoji data")
        return []
    
    # Filter to common emotion emojis
    emotion_groups = ['Smileys & Emotion', 'People & Body']
    filtered_emojis = emoji_df[emoji_df['group'].isin(emotion_groups)]
    
    # Initialize selected emojis in session state
    if 'selected_emojis' not in st.session_state:
        st.session_state.selected_emojis = []
    
    # Group emojis by category for better organization
    happy_emojis = []
    sad_emojis = []
    love_emojis = []
    other_emojis = []
    
    for _, row in filtered_emojis.iterrows():
        name = row['name'].lower()
        if any(word in name for word in ['smile', 'happy', 'joy', 'laugh', 'grin']):
            happy_emojis.append(row)
        elif any(word in name for word in ['sad', 'cry', 'worried', 'disappointed']):
            sad_emojis.append(row)
        elif any(word in name for word in ['love', 'heart', 'kiss']):
            love_emojis.append(row)
        else:
            other_emojis.append(row)
    
    # Display emojis by category
    categories = [
        ("😊 Happy Vibes", happy_emojis),
        ("😢 Not So Great", sad_emojis),
        ("❤️ Love & Warmth", love_emojis),
        ("🎭 Other Feelings", other_emojis)
    ]
    
    for category_name, emoji_list in categories:
        if emoji_list:
            st.markdown(f"### {category_name}")
            cols = st.columns(8)
            
            for i, row in enumerate(emoji_list):
                col_idx = i % 8
                emoji = row['emoji']
                name = row['name']
                
                # Create a unique key for each emoji
                key = f"emoji_{emoji}_{i}"
                
                # Check if emoji is already selected
                is_selected = any(e.get('emoji') == emoji for e in st.session_state.selected_emojis)
                
                # Create button with different style based on selection state
                button_text = emoji
                help_text = f"{name}"
                
                # Custom styling for selected emojis
                if is_selected:
                    button_style = """
                        <div style="text-align: center; padding: 0.5rem; border-radius: 0.5rem; 
                                    background-color: #e3f2fd; border: 2px solid #1976d2; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem;">{}</span>
                        </div>
                    """.format(emoji)
                    cols[col_idx].markdown(button_style, unsafe_allow_html=True)
                
                # Display emoji in a button
                if cols[col_idx].button(
                    " " if is_selected else button_text,
                    key=key,
                    help=help_text,
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    # Toggle selection
                    if is_selected:
                        # Remove emoji from selected list
                        st.session_state.selected_emojis = [
                            e for e in st.session_state.selected_emojis if e.get('emoji') != emoji
                        ]
                    else:
                        # Add emoji to selected list
                        st.session_state.selected_emojis.append({
                            'emoji': emoji,
                            'name': name,
                            'group': row['group'],
                            'sub_group': row['sub_group']
                        })
                    
                    # Force a rerun to update the UI
                    st.rerun()
    
    # Display selected emojis in a visually appealing way
    if st.session_state.selected_emojis:
        st.markdown("---")
        st.markdown("### Your Selected Mood")
        
        # Create columns for selected emojis
        selected_cols = st.columns(len(st.session_state.selected_emojis))
        for idx, emoji_data in enumerate(st.session_state.selected_emojis):
            with selected_cols[idx]:
                st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; border-radius: 0.5rem; 
                                background-color: #f5f5f5; margin: 0.5rem 0;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{emoji_data['emoji']}</div>
                        <div style="font-size: 0.9rem; color: #666;">{emoji_data['name']}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    return st.session_state.selected_emojis