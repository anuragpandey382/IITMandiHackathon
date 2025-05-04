#ui/components/feedback_collector.py

import streamlit as st
import sys
import os

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def display_feedback_collector():
    """
    Display enhanced feedback collection UI
    
    Returns:
        Feedback data or None if not submitted
    """
    st.markdown("""
        <div style="background: linear-gradient(45deg, #f8f9fa, #e9ecef); 
                    border-radius: 1rem; padding: 2rem; margin: 2rem 0;">
            <h3 style="text-align: center; color: #495057;">💝 How did we do?</h3>
            <p style="text-align: center; color: #6c757d;">
                Your feedback helps us improve our movie recommendations
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'feedback_submitted' not in st.session_state:
        st.session_state.feedback_submitted = False
    
    # If feedback already submitted, show thank you message with animation
    if st.session_state.feedback_submitted:
        st.markdown("""
            <div style="text-align: center; padding: 2rem; background: #d4edda; 
                        border-radius: 1rem; color: #155724;">
                <h3>🎉 Thank you for your feedback!</h3>
                <p>Your input helps us make MoodFlixx better for everyone!</p>
            </div>
        """, unsafe_allow_html=True)
        return None
    
    # Rating with emoji feedback
    rating_labels = {
        1: "😟 Not relevant at all",
        2: "😕 Somewhat relevant",
        3: "😊 Relevant enough",
        4: "😃 Very relevant",
        5: "🌟 Perfectly relevant!"
    }
    
    st.markdown("### Rate Our Recommendations")
    rating = st.slider(
        "How relevant were the recommendations?",
        min_value=1,
        max_value=5,
        value=3,
        format="%d"
    )
    
    # Display emoji label for selected rating
    st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem; margin: 0.5rem 0; 
                    background: #e3f2fd; border-radius: 0.5rem;">
            <h4>{rating_labels.get(rating, '😊 Relevant enough')}</h4>
        </div>
    """, unsafe_allow_html=True)
    
    # Comments with enhanced styling
    st.markdown("### Additional Comments")
    comments = st.text_area(
        "What can we improve? Any specific feedback about the recommendations?",
        placeholder="Your feedback helps us improve MoodFlixx for everyone...",
        max_chars=500,
        height=100
    )
    
    # Submit button with enhanced styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Submit Feedback", type="primary", use_container_width=True):
            # In a real app, you would save this feedback to a database
            st.session_state.feedback_submitted = True
            
            feedback_data = {
                "rating": rating,
                "comments": comments
            }
            
            # Show success animation
            with st.spinner("Submitting your feedback..."):
                st.success("Thank you for helping us improve!")
            return feedback_data
    
    return None