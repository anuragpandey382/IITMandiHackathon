from datetime import datetime
import streamlit as st
import time
import bcrypt
import json
import os
USER_DB_PATH = "user_data.json"

# Function to get current timestamp
def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def get_bot_response(user_input):
    # This is a placeholder for your actual RAG implementation
    time.sleep(1)  # Simulate processing time
    
    return "hi ! i m runnning"

def handle_example_query(query):
    st.session_state.chat_history.append({
        'role': 'user',
        'content': query,
        'timestamp': get_timestamp()
    })
    
    bot_response = get_bot_response(query)
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': bot_response,
        'timestamp': get_timestamp()
    })
    
    st.rerun()

def login_form():
    st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
    
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    
    login_error = st.empty()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Login", use_container_width=True):
            if login_username in st.session_state.user_data:
                stored_hash = st.session_state.user_data[login_username]["password_hash"]
                if verify_password(stored_hash, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.rerun()
                else:
                    login_error.markdown('<p class="auth-error">❌ Invalid password. Please try again.</p>', unsafe_allow_html=True)
            else:
                login_error.markdown('<p class="auth-error">❌ Username not found. Please sign up.</p>', unsafe_allow_html=True)
    
    with col2:
        if st.button("Need an account? Sign up", use_container_width=True):
            st.session_state.auth_page = "signup"
            st.rerun()

def signup_form():
    st.markdown("<h2>Create Account</h2>", unsafe_allow_html=True)
    
    new_username = st.text_input("Choose Username", key="new_username")
    new_password = st.text_input("Create Password", type="password", key="new_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    
    signup_error = st.empty()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Create Account", use_container_width=True):
            if not new_username or not new_password:
                signup_error.markdown('<p class="auth-error">❌ Username and password are required.</p>', unsafe_allow_html=True)
            elif new_username in st.session_state.user_data:
                signup_error.markdown('<p class="auth-error">❌ Username already exists. Please choose another.</p>', unsafe_allow_html=True)
            elif new_password != confirm_password:
                signup_error.markdown('<p class="auth-error">❌ Passwords do not match.</p>', unsafe_allow_html=True)
            else:
                # Create new user
                hashed_pw = hash_password(new_password)
                st.session_state.user_data[new_username] = {
                    "password_hash": hashed_pw,
                    "created_at": datetime.now().isoformat(),
                    "settings": {"theme": st.session_state.theme}
                }
                save_user_data(st.session_state.user_data)
                
                # Auto-login
                st.session_state.logged_in = True
                st.session_state.username = new_username
                st.rerun()
    
    with col2:
        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()

def load_user_data():
    """Load user data from the database file"""
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_user_data(data):
    """Save user data to the database file"""
    with open(USER_DB_PATH, 'w') as file:
        json.dump(data, file)

def verify_password(stored_hash, password):
    """Verify if password matches stored hash"""
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

def hash_password(password):
    """Hash password for secure storage"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_timestamp():
    """Get current timestamp in HH:MM:SS format"""
    return datetime.now().strftime("%H:%M:%S")

