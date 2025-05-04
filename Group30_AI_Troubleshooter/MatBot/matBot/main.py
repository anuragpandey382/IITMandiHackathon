import asyncio
import nest_asyncio
from Img2Txt import process_image
# Apply nest_asyncio to handle nested event loops
try:
    nest_asyncio.apply()
except RuntimeError as e:
    print(f"⚠️ nest_asyncio error: {e}")

# Ensure an event loop is running
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import streamlit as st
import sys
import os
os.environ["STREAMLIT_DISABLE_WATCHDOG_WARNINGS"] = "true"
import time
import bcrypt
import json
from datetime import datetime

# Set page config as first Streamlit command
st.set_page_config(
    page_title="MATBOT - MATLAB Assistant",
    page_icon="/home/teaching/MatRag/MatBot/matBot/logo.png",  # Use absolute path
    layout="wide",
    initial_sidebar_state="expanded"
)


# Add path to import app.py
sys.path.append("/home/teaching/MatRag/MatBot/server")  # Use absolute path for reliability

# Now import other functions after the setup
from functions import (
    login_form, signup_form,
    save_user_data, get_timestamp, load_user_data
)
from app import load_embedding_model, load_mistral_model, generate_response

# Rest of your code remains the same

@st.cache_resource(show_spinner="Loading models...")
def init_models():
    """
    Initialize and cache the models.
    Returns:
        tuple: Embedding model, vectorstore, and model pipeline.
    """
    try:
        embedding_model, vectorstore = load_embedding_model()
        model_pipeline = load_mistral_model()
        return embedding_model, vectorstore, model_pipeline
    except RuntimeError as e:
        st.error(f"Model initialization failed: {e}")
        return None, None, None

# ------------- CONFIG & CONSTANTS ------------- 
USER_DB_PATH = "user_data.json"

# ------------- APP INITIALIZATION ------------- 
def initialize_app():
    """Initialize the application configuration and session state."""
    st.session_state.use_web = True
    # Initialize models_loaded flag
    if 'models_loaded' not in st.session_state:
        st.session_state.models_loaded = False

    # Load models during initialization
    if 'embedding_model' not in st.session_state or 'vectorstore' not in st.session_state or 'model_pipeline' not in st.session_state:
        with st.spinner("🔄 Loading models..."):
            st.session_state.embedding_model, st.session_state.vectorstore, st.session_state.model_pipeline = init_models()
            st.session_state.models_loaded = all([
                st.session_state.embedding_model,
                st.session_state.vectorstore,
                st.session_state.model_pipeline
            ])
    
    # load users
    if 'user_data' not in st.session_state:
        st.session_state.user_data = load_user_data()
    
    if 'theme' not in st.session_state:
        st.session_state.theme = "dark"

    # auth flags
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = "login"
        
    # per‐user sessions & settings
    if st.session_state.logged_in:
        user = st.session_state.username
        # load saved theme
        theme = st.session_state.user_data[user]["settings"].get("theme", "light")
        st.session_state.theme = theme
        # load saved chat sessions
        sessions = st.session_state.user_data[user].get("sessions", {"Chat 1": []})
        st.session_state.sessions = sessions
        # Set current session to the first one if not set
        if 'current_session' not in st.session_state:
            st.session_state.current_session = list(sessions.keys())[0]
    else:
        # Guest defaults
        if 'theme' not in st.session_state:
            st.session_state.theme = "light"
        if 'sessions' not in st.session_state:
            st.session_state.sessions = {"Chat 1": []}
        if 'current_session' not in st.session_state:
            st.session_state.current_session = "Chat 1"
    
    # Initialize chat history if not present
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    apply_matlab_theme(st.session_state.theme)

def get_bot_response(user_input):
    """Generate a response from the bot based on user input."""
    if not user_input:
        return "Please provide a question or input."
        
    # Check for model initialization
    if 'embedding_model' not in st.session_state or 'vectorstore' not in st.session_state or 'model_pipeline' not in st.session_state:
        try:
            st.session_state.embedding_model, st.session_state.vectorstore, st.session_state.model_pipeline = init_models()
            st.session_state.models_loaded = all([st.session_state.embedding_model, st.session_state.vectorstore, st.session_state.model_pipeline])
        except RuntimeError as e:
            st.error(f"Error initializing models: {e}")
            return f"I encountered an error initializing the models: {e}"
    
    if not st.session_state.models_loaded:
        return "Models failed to load. Please check the logs and try again."
        
    try:
         # Adding the NLP processing for the User input
    
        from nlp import GeminiQueryFormatter
        
        nlp1 = GeminiQueryFormatter()
        user_input = nlp1.format_query(user_input)

        # Generate response
        response,metaData = generate_response(
            user_query=user_input,
            embedding_model=st.session_state.embedding_model,
            vectorstore=st.session_state.vectorstore,
            model_pipeline=st.session_state.model_pipeline,
            use_web_search=st.session_state.use_web
        )
        print(metaData) #debug
        return response,metaData
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return f"I encountered an error: {str(e)}"

# ------------- UI COMPONENTS ------------- 
def render_sidebar():
    """Render GPT-like chat session list and controls, with delete support."""
    with st.sidebar:
        # Add MatBot logo and title at the top
        st.image("logo.png", width=150)
        st.markdown("## 💬 Chats")

        # Initialize chat_counter for unique chat naming
        if "chat_counter" not in st.session_state:
            st.session_state.chat_counter = 1

        # ➕ New Chat
        if st.button("➕ New Chat", use_container_width=True):
            # Generate a unique chat name
            while True:
                name = f"Chat {st.session_state.chat_counter}"
                if name not in st.session_state.sessions:
                    break
                st.session_state.chat_counter += 1

            # Create and switch to new session
            st.session_state.sessions[name] = []
            st.session_state.current_session = name
            st.session_state.chat_counter += 1

            # Persist if logged in
            if st.session_state.logged_in:
                user = st.session_state.username
                st.session_state.user_data[user]['sessions'] = st.session_state.sessions
                save_user_data(st.session_state.user_data)
            st.rerun()

        # Session selector
        sessions = list(st.session_state.sessions.keys())

        # Safety check for empty or invalid current session
        if not sessions:
            st.session_state.sessions["Chat 1"] = []
            st.session_state.current_session = "Chat 1"
            sessions = ["Chat 1"]
        elif st.session_state.current_session not in sessions:
            st.session_state.current_session = sessions[0]

        current_idx = sessions.index(st.session_state.current_session)
        sel = st.radio("Select a Chat", sessions, index=current_idx)

        if sel != st.session_state.current_session:
            st.session_state.current_session = sel
            st.rerun()

        # 🗑️ Delete Chat
        if st.button("🗑️ Delete Chat", use_container_width=True):
            if len(sessions) > 1:
                st.session_state.sessions.pop(st.session_state.current_session)
                st.session_state.current_session = list(st.session_state.sessions.keys())[0]
                if st.session_state.logged_in:
                    user = st.session_state.username
                    st.session_state.user_data[user]['sessions'] = st.session_state.sessions
                    save_user_data(st.session_state.user_data)
                st.rerun()
            else:
                st.warning("Cannot delete the only remaining chat.")
        
        

        # Other sidebar items
        st.markdown("## 📚 Resources")
        with st.expander("MATLAB Links", expanded=False):
            st.markdown("""
            - [Documentation](https://www.mathworks.com/help/matlab/)
            - [MATLAB Answers](https://www.mathworks.com/matlabcentral/answers/)
            """)
        st.markdown("---")
        st.caption("© 2025 MATBOT v1.0")

def render_navbar():
    """Render top navbar with theme toggle and profile dropdown."""
    import streamlit as st

    # Ensure session state has theme key
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    # Create columns for the navbar elements
    col1, col2, col3 = st.columns([1, 6, 3])

    with col3:
        cols = st.columns(2)

        # Column 1: Theme toggle
        with cols[0]:
            icon = "🌙" if st.session_state.theme == "light" else "☀️"
            if st.button(icon, key="theme_toggle"):
                new_theme = "dark" if st.session_state.theme == "light" else "light"
                st.session_state.theme = new_theme
                change_theme(new_theme)

        # Column 2: Avatar + Popover
        with cols[1]:
            if st.session_state.get("logged_in", False):
                username = st.session_state.username
                first_letter = username[0].upper()
                theme = st.session_state.get("theme", "light")
                bg_color = "#0076A8" if theme == "light" else "#0097E6"

                # CSS for avatar appearance
                st.markdown(f"""
                    <style>
                        .avatar-btn {{
                            background-color: {bg_color};
                            color: white;
                            font-weight: bold;
                            border-radius: 50%;
                            width: 32px;
                            height: 32px;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 16px;
                        }}
                    </style>
                """, unsafe_allow_html=True)

                # Popover trigger with plain text avatar (HTML not allowed here)
                with st.popover(label=first_letter):  # Only plain text works
                    st.markdown(f"**{username}**")
                    if st.button("Logout", key="logout_btn"):
                        st.session_state.logged_in = False
                        st.rerun()

def render_chat_interface():
    """Render the main chat interface for a logged in user."""
    st.markdown(f"""
    <div class="logo-container">
        <h1>Welcome, {st.session_state.username}! 👋</h1>
        <p>I'm your MATLAB Troubleshooter assistant. How can I help you today?</p>
    </div>
    """, unsafe_allow_html=True)

    render_chat_history()
        
    render_chat_input()

def render_auth_interface():
    """Render the authentication interface."""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)
    auth_col1, auth_col2 = st.columns([2, 3])
    with auth_col1:
        st.image("logo.png", width=150)
        st.markdown("### Welcome to MATBOT")
        st.markdown("""
        Your professional assistant for MATLAB:
        - Get instant help with syntax
        - Debug errors efficiently
        - Learn best practices
        - Optimize your code
        """)
    with auth_col2:
        if st.session_state.auth_page == "login":
            login_form()
        else:
            signup_form()
    st.markdown('</div>', unsafe_allow_html=True)



# =======================================================================================

# def render_chat_history():
    # """Render messages for the currently selected chat only, using Markdown for LLM response and metadata."""
    # import streamlit as st

    # current_session = st.session_state.current_session
    # messages = st.session_state.sessions.get(current_session, [])

    # with st.container():
    #     st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    #     # Show welcome message if this chat is empty
    #     if not messages:
    #         st.markdown(f"""
    #         <div class="chat-message bot-message">
    #             <div class="avatar bot-avatar">M</div>
    #             <div class="message-content">
    #                 <p>👋 Welcome to chat "{current_session}"! How can I help with your MATLAB questions?</p>
    #                 <div class="chat-timestamp">{get_timestamp()}</div>
    #             </div>
    #         </div>
    #         """, unsafe_allow_html=True)

    #     for message in messages:
    #         if message['role'] == 'user':
    #             # User message as before
    #             st.markdown(f"""
    #             <div class="chat-message user-message">
    #                 <div class="avatar user-avatar">U</div>
    #                 <div class="message-content">
    #                     <p>{message['content']}</p>
    #                     <div class="chat-timestamp">{message['timestamp']}</div>
    #                 </div>
    #             </div>
    #             """, unsafe_allow_html=True)
    #         else:
    #             # Bot response: Markdown rendering
    #             st.markdown(f"""
    #             <div class="chat-message bot-message">
    #                 <div class="avatar bot-avatar">M</div>
    #                 <div class="message-content">
    #                     <span style="font-weight: bold; color: {'#0076A8' if st.session_state.theme == 'light' else '#0097E6'};">🤖 Response:</span>
    #             """, unsafe_allow_html=True)

        #         # Render the LLM response as Markdown (preserves headings, code, etc.)
        #         st.markdown(message['content'], unsafe_allow_html=True)

        #         # Render metadata (sources, web results, etc.) as Markdown
        #         metadata_md = ""
        #         if 'metadata' in message and message['metadata']:
        #             metadata = message['metadata']
        #             metadata_md += "\n---\n**Sources & References:**\n"
        #             if isinstance(metadata, dict):
        #                 # Web results
        #                 if 'web_results' in metadata and metadata['web_results']:
        #                     metadata_md += "\n**Web Sources:**\n"
        #                     for result in metadata['web_results'][:3]:
        #                         if 'title' in result and 'link' in result:
        #                             metadata_md += f"- [{result['title']}]({result['link']})\n"
        #                 # Document sources
        #                 if 'doc_sources' in metadata and metadata['doc_sources']:
        #                     metadata_md += "\n**Document Sources:**\n"
        #                     for source in metadata['doc_sources'][:3]:
        #                         metadata_md += f"- {source}\n"
        #             elif isinstance(metadata, list):
        #                 # PDF/document metadata
        #                 seen_titles = set()
        #                 for doc in metadata[:5]:
        #                     if 'title' in doc and 'page' in doc and 'source' in doc:
        #                         title = doc['title']
        #                         if title not in seen_titles:
        #                             seen_titles.add(title)
        #                             metadata_md += f"- {title} (Page {doc['page']}, {doc['source']})\n"
        #             metadata_md += "\n"
        #         if metadata_md:
        #             st.markdown(metadata_md, unsafe_allow_html=True)

        #         # Timestamp
        #         st.markdown(f"""
        #                 <div class="chat-timestamp">{message['timestamp']}</div>
        #             </div>
        #         </div>
        #         """, unsafe_allow_html=True)

        # st.markdown('</div>', unsafe_allow_html=True)
        
# =======================================================================================


# def render_chat_history():
#     """Render messages for the currently selected chat only."""
#     current_session = st.session_state.current_session

#     # Get messages for this specific chat only
#     messages = st.session_state.sessions.get(current_session, [])

#     with st.container():
#         st.markdown('<div class="chat-container">', unsafe_allow_html=True)

#         # Show welcome message if this chat is empty
#         if not messages:
#             st.markdown(f"""
#             <div class="chat-message bot-message">
#                 <div class="avatar bot-avatar">M</div>
#                 <div class="message-content">
#                     <p>👋 Welcome to chat "{current_session}"! How can I help with your MATLAB questions?</p>
#                     <div class="chat-timestamp">{get_timestamp()}</div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)

#         # Display all messages for this chat
#         for message in messages:
#             if message['role'] == 'user':
#                 # Input text remains normal
#                 st.markdown(f"""
#                 <div class="chat-message user-message">
#                     <div class="avatar user-avatar">U</div>
#                     <div class="message-content">
#                         <p>{message['content']}</p>
#                         <div class="chat-timestamp">{message['timestamp']}</div>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
            
#             else:
#                 # Use the format_bot_response function if available
#                 if 'format_bot_response' in globals():
#                     formatted_response = (message['content'])
#                 else:
#                     # Fallback to manual formatting if the function isn't available
#                     formatted_response = message['content']
#                     if "```" in formatted_response:
#                         parts = formatted_response.split("```")
#                         formatted_response = ""
#                         for i, part in enumerate(parts):
#                             if i % 2 == 0:
#                                 formatted_response += f"<p>{part.strip()}</p>" if part.strip() else ""
#                             else:
#                                 formatted_response += f"<pre>{part.strip()}</pre>"
#                     else:
#                         formatted_response = f"<p>{formatted_response}</p>"
                
#                 # Add metadata section if available
#                 metadata_html = ""
#                 if 'metadata' in message and message['metadata']:
#                     metadata = message['metadata']
                    
#                     # Start of sources block
#                     metadata_html = """
#                     <div class='sources-block'>
#                         <div class='sources-header'>
#                             <span>📚 Sources</span>
#                             <span style='font-size: 0.8rem; opacity: 0.8;'>MATLAB Documentation</span>
#                         </div>
#                         <div class='sources-content'>
#                     """
                    
#                     if isinstance(metadata, dict):
#                         # Handle web search results
#                         if 'web_results' in metadata and metadata['web_results']:
#                             metadata_html += "<div style='margin-bottom:8px;'>Web Sources:</div>"
#                             for i, result in enumerate(metadata['web_results'][:3]):
#                                 if 'title' in result and 'link' in result:
#                                     metadata_html += f"<div class='source-item'><a href='{result['link']}' target='_blank'>{result['title']}</a></div>"
#                             metadata_html += "<div style='margin-top:6px;'></div>"
                        
#                         # Handle document sources
#                         if 'doc_sources' in metadata and metadata['doc_sources']:
#                             metadata_html += "<div style='margin-bottom:8px;'>Document Sources:</div>"
#                             for i, source in enumerate(metadata['doc_sources'][:3]):
#                                 metadata_html += f"<div class='source-item'>{source}</div>"
                            
#                     # Handle PDF documents metadata array
#                     elif isinstance(metadata, list):
#                         seen_titles = set()
#                         for i, doc in enumerate(metadata[:5]):
#                             if 'title' in doc and 'page' in doc and 'source' in doc:
#                                 title = doc['title']
#                                 if title not in seen_titles:
#                                     seen_titles.add(title)
#                                     metadata_html += f"<div class='source-item'>{title} (Page {doc['page']}, {doc['source']})</div>"
                    
#                     # Close the sources block
#                     metadata_html += """
#                         </div>
#                     </div>
#                     """

#                 st.markdown(f"""
#                 <div class="chat-message bot-message">
#                     <div class="avatar bot-avatar">M</div>
#                     <div class="message-content">
#                         <p style="font-weight: bold; color: {'#0076A8' if st.session_state.theme == 'light' else '#0097E6'};">🤖 Response:</p>
#                         <p>{formatted_response}
#                         {metadata_html}</p>
#                         <div class="chat-timestamp">{message['timestamp']}</div>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
                
        
#         # Close the chat container
#         st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================

def render_chat_history():
    """Render messages for the currently selected chat only, with special formatting for MATLAB code."""
    current_session = st.session_state.current_session
    messages = st.session_state.sessions.get(current_session, [])

    # Add MATLAB code block CSS and copy button JS only once
    matlab_css = """
    <style>
    .matlab-code-container {
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-color);
        background-color: var(--matlab-code-bg);
    }
    .matlab-code-header {
        background-color: var(--matlab-blue);
        color: white;
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: bold;
    }
    .copy-button {
        background-color: rgba(255, 255, 255, 0.2);
        border: none;
        border-radius: 4px;
        color: white;
        padding: 4px 8px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .copy-button:hover {
        background-color: rgba(255, 255, 255, 0.3);
    }
    .language-matlab {
        background-color: var(--matlab-code-bg) !important;
        padding: 12px !important;
        margin: 0 !important;
        color: var(--code-text) !important;
        font-family: 'Consolas', 'Courier New', monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        border-radius: 0 !important;
        border-top: none !important;
    }
    </style>
    """
    copy_script = """
    <script>
    function copyToClipboard(button) {
        const container = button.closest('.matlab-code-container');
        const codeElement = container.querySelector('pre code');
        const codeText = codeElement.innerText;
        navigator.clipboard.writeText(codeText).then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    }
    </script>
    """

    with st.container():
        st.markdown(matlab_css + copy_script, unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Show welcome message if this chat is empty
        if not messages:
            st.markdown(f"""
            <div class="chat-message bot-message">
                <div class="avatar bot-avatar">M</div>
                <div class="message-content">
                    <p>👋 Welcome to chat "{current_session}"! How can I help with your MATLAB questions?</p>
                    <div class="chat-timestamp">{get_timestamp()}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Display all messages for this chat
        for message in messages:
            if message['role'] == 'user':
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="avatar user-avatar">U</div>
                    <div class="message-content">
                        <p>{message['content']}</p>
                        <div class="chat-timestamp">{message['timestamp']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Format the bot response content
                content = message['content']
                formatted_content = ""

                # Handle code blocks, with special formatting for MATLAB
                if "```" in content:
                    parts = content.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 0:  # Regular text
                            if part.strip():
                                formatted_content += f"{part.strip()}"
                        else:  # Code block
                            code_lines = part.strip().split('\n')
                            if code_lines and not code_lines[0].startswith(' '):
                                language = code_lines[0].lower()
                                code = '\n'.join(code_lines[1:])
                                if language == 'matlab':
                                    formatted_content += f'''
                                    <div class="matlab-code-container">
                                        <div class="matlab-code-header">
                                            <span>MATLAB Code</span>
                                            <button class="copy-button" onclick="copyToClipboard(this)">Copy</button>
                                        </div>
                                        <pre class="language-matlab"><code>{code}</code></pre>
                                    </div>
                                    '''
                                else:
                                    formatted_content += f'<pre class="code-block language-{language}">{code}</pre>'
                            else:
                                # Try to auto-detect MATLAB code by keywords
                                code = part.strip()
                                if any(kw in code for kw in ['function', 'end', 'for', 'while', 'if', 'plot(', 'figure(', '%']):
                                    formatted_content += f'''
                                    <div class="matlab-code-container">
                                        <div class="matlab-code-header">
                                            <span>MATLAB Code</span>
                                            <button class="copy-button" onclick="copyToClipboard(this)">Copy</button>
                                        </div>
                                        <pre class="language-matlab"><code>{code}</code></pre>
                                    </div>
                                    '''
                                else:
                                    formatted_content += f'<pre class="code-block">{code}</pre>'
                else:
                    formatted_content = content

                # Format metadata if present
                metadata_html = ""
                if 'metadata' in message and message['metadata']:
                    metadata = message['metadata']
                    metadata_html = '<div class="sources-block">'
                    metadata_html += '<div class="sources-header">'
                    metadata_html += '<span>📚 Sources</span>'
                    metadata_html += '<span style="font-size: 0.8rem; opacity: 0.8;">MATLAB Documentation</span>'
                    metadata_html += '</div>'
                    metadata_html += '<div class="sources-content">'
                    has_content = False
                    if isinstance(metadata, dict):
                        # Web search results
                        if 'web_results' in metadata and metadata['web_results']:
                            has_content = True
                            metadata_html += '<div class="source-category">Web Sources:</div>'
                            for i, result in enumerate(metadata['web_results'][:3]):
                                if 'title' in result and 'link' in result:
                                    metadata_html += f'<div class="source-item"><a href="{result["link"]}" target="_blank">{result["title"]}</a></div>'
                        # Document sources
                        if 'doc_sources' in metadata and metadata['doc_sources']:
                            has_content = True
                            if 'web_results' in metadata and metadata['web_results']:
                                metadata_html += '<div style="margin-top: 10px;"></div>'
                            metadata_html += '<div class="source-category">Document Sources:</div>'
                            for i, source in enumerate(metadata['doc_sources'][:3]):
                                metadata_html += f'<div class="source-item">{source}</div>'
                    # Handle PDF documents metadata array
                    elif isinstance(metadata, list) and len(metadata) > 0:
                        has_content = True
                        seen_titles = set()
                        for doc in metadata[:5]:
                            if 'title' in doc and 'page' in doc and 'source' in doc:
                                title = doc['title']
                                if title not in seen_titles:
                                    seen_titles.add(title)
                                    metadata_html += f'<div class="source-item">{title} (Page {doc["page"]}, {doc["source"]})</div>'
                    metadata_html += '</div></div>'
                    if not has_content:
                        metadata_html = ""

                # Render the complete bot message with cleaner HTML structure
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <div class="avatar bot-avatar">M</div>
                    <div class="message-content">
                        <div class="response-header" style="font-weight: bold; color: {'#0076A8' if st.session_state.theme == 'light' else '#0097E6'};">🤖 MatBot:</div>
                        <div class="response-content">{formatted_content}
                        {metadata_html}</div>
                        <div class="chat-timestamp">{message['timestamp']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Close the chat container
        st.markdown('</div>', unsafe_allow_html=True)

# # =======================================================================================

# ==========================================================================================
 
def process_uploaded_file(uploaded_file):
    """Process an uploaded file and extract text/context from it."""
    if uploaded_file is None:
        return None
        
    # Create a temp directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Process based on file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext in ['.png', '.jpg', '.jpeg']:
        # Process image with OCR
        ocr_text = process_image(file_path)
        explanation = ocr_text
        result = f"IMAGE CONTENT:\n{ocr_text}\n\nINTERPRETATION:\n{explanation}"
    elif file_ext in ['.m', '.mat']:
        # Read MATLAB file content
        with open(file_path, 'r') as f:
            try:
                content = f.read()
                result = f"MATLAB FILE CONTENT:\n{content}"
            except UnicodeDecodeError:
                result = "Unable to read binary MATLAB file content."
    else:
        result = "Unsupported file type."
    
    # Clean up
    os.remove(file_path)
    
    return result

def render_chat_input():
    """Render the chat input area using a Streamlit form."""
    st.markdown("### Ask Your Question")

    # Web Search toggle (moved outside the form)
    st.session_state.use_web = st.toggle("🌐 Web Search", value=st.session_state.use_web)
    
    # Add border to toggle
    st.markdown(f"""
    <style>
        [data-testid="stToggleButton"] > div {{
            border: 2px solid {'#0076A8' if st.session_state.theme == 'light' else '#0097E6'};
            border-radius: 28px;
            padding: 2px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Initialize file_content in session state
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your MATLAB question here:",
            key="user_input",
            placeholder="E.g., How do I solve linear equations in MATLAB?",
            height=100
        )

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Attach image or MATLAB file", 
                type=["jpeg", "png", "jpg", "m", "mat"]
            )

        with col3:
            # Create a large styled button using HTML and CSS
            submit_btn = st.form_submit_button(
                label="Send",
                use_container_width=True  # Uses full width of column
            )
            st.markdown(
                f"""
                <style>
                    div.stButton > button:first-child {{
                        background-color: {'#0076A8' if st.session_state.theme == 'light' else '#0097E6'} !important;
                        color: white !important;
                        font-weight: bold;
                        border: none !important;
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )

    # Process uploaded file outside the form
    if uploaded_file is not None:
        with st.spinner("Processing uploaded file..."):
            st.session_state.file_content = process_uploaded_file(uploaded_file)
            if st.session_state.file_content:
                st.success(f"File '{uploaded_file.name}' processed successfully!")
                # Show a preview of the extracted content
                with st.expander("View extracted content", expanded=False):
                    st.markdown(st.session_state.file_content)

    # Handle submit with file context
    if submit_btn and (user_input.strip() or st.session_state.file_content):
        combined_input = user_input
        
        # Append file content if available
        if st.session_state.file_content:
            combined_input += f"\n\nContext from uploaded file:\n{st.session_state.file_content}"
            # Reset file content after sending
            st.session_state.file_content = None
            
        # Process the combined input
        process_user_input(combined_input)

# ------------- STYLING FUNCTIONS ------------- 
def apply_matlab_theme(theme_mode):
    """Apply MATLAB-inspired theme with dark/light mode support."""

    if theme_mode == "dark":
        matlab_theme_css = """
        <style>
            :root {
                --matlab-blue: #0097E6;
                --matlab-orange: #FF8C42;
                --matlab-dark: #1E1E1E;
                --matlab-light: #333333;
                --matlab-code-bg: #2D2D2D;
                --text-color: #E0E0E0;
                --text-secondary: #B0B0B0;
                --border-color: #444444;
                --user-message-bg: #2C3E50;
                --bot-message-bg: #343434;
                --hover-color: #005685;
                --header-bg: #212121;
                --input-bg: #3D3D3D;
                --input-text: #FFFFFF;
                --text-input: #FFFFFF;
                --input-border: #555555;
                --button-bg: #0097E6;
                --button-hover: #00B4F0;
                --navbar-bg: #151515;
                --sidebar-bg: #1E1E1E;
                --sidebar-text: #FFFFFF;
                --main-bg: #252525;
                --spinner-bg: #1E1E1E;
                --code-bg: #2D2D2D;
                --code-text: #E0E0E0;
            }
        </style>
        """
    else:
        matlab_theme_css = """
        <style>
            :root {
                --matlab-blue: #0076A8;
                --matlab-orange: #E76500;
                --matlab-dark: #FFFFFFF;
                --matlab-light: #F7F7F7;
                --matlab-code-bg: #EEF2F6;
                --text-color: #1C1C1C;
                --text-secondary: #444444;
                --border-color: #CCCCCC;
                --user-message-bg: #DCEFFF;
                --bot-message-bg: #F7F9FC;
                --hover-color: #005685;
                --header-bg: #F0F0F0;
                --input-bg: #FFFFFF;
                --input-text: #222222;
                --text-input: #222222;
                --input-border: #BBBBBB;
                --button-bg: #0076A8;
                --button-hover: #0096D6;
                --navbar-bg: #F0F0F0;
                --sidebar-bg: #F0F0F0;
                --sidebar-text: #333333;
                --main-bg: #FFFFFF;
                --spinner-bg: #FFFFFF;
                --code-bg: #F7F7F7;
                --code-text: #1C1C1C;
            }
        </style>
        """

    # Common CSS using the selected variables
    common_css = """
    <style>
        .chat-timestamp {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-align: right;
            margin-top: 0.5rem;
            font-style: italic;
            display: block;
            width: 100%;
        }
        .message-content {
            position: relative;
            width: 100%;
        }
        .sources-block {
            background-color: var(--matlab-code-bg);
            border-radius: 8px;
            border-left: 4px solid var(--matlab-orange);
            margin-top: 16px;
            margin-bottom: 8px;
            overflow: hidden;
        }

        .sources-header {
            background-color: var(--matlab-blue);
            color: white;
            padding: 8px 12px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.9rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .sources-content {
            padding: 12px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .source-item {
            margin: 4px 0;
            padding-left: 15px;
            position: relative;
        }

        .source-item:before {
            content: "•";
            position: absolute;
            left: 0;
            color: var(--matlab-orange);
        }
        .metadata-section {
            margin-top: 10px;
            font-size: 0.9rem;
            color: var(--text-secondary);
            border-top: 1px dashed var(--border-color);
            padding-top: 8px;
        }

        .metadata-section a {
            color: var(--matlab-blue);
            text-decoration: none;
            border-bottom: 1px dotted;
        }

        .metadata-section a:hover {
            color: var(--button-hover);
            border-bottom: 1px solid;
        }
        .chat-container {
            background-color: var(--main-bg);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .chat-message {
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: flex-start;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            animation: fadeIn 0.3s ease-in;
            overflow: hidden; 
            max-width: 80%; /* Limit the width of the message box */
            word-wrap: break-word; /* Ensure long words wrap */
            overflow-wrap: break-word; /* Handle long words */
        }

        .user-message, .bot-message {
            max-width: 70%; /* Limit the width of the message box */
            overflow: hidden; 
            word-wrap: break-word; /* Ensure long words wrap */
            overflow-wrap: break-word; /* Handle long words */
            padding: 1rem; 
            border-radius: 10px; 
        }

        .user-message {
            background-color: var(--user-message-bg);
            border-left: 6px solid var(--matlab-blue);
            color: var(--text-color);
            margin-left: auto;
            text-align: right;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .bot-message pre {
            white-space: pre-wrap; /* Ensure code blocks wrap */
            word-wrap: break-word; /* Ensure long words wrap */
            overflow-wrap: break-word; /* Handle long words */
            overflow-x: auto;
        }
        .bot-message {
            border-left: 6px solid var(--matlab-orange);
            background-color: var(--bot-message-bg);
        }

        .message-content {
            flex-grow: 1;
            font-size: 1rem;
            line-height: 1.6; 
            word-wrap: break-word;
            overflow-wrap: break-word;
            overflow:hidden
        }

        .message-content p {
            margin: 0;
            word-wrap: break-word; 
            overflow-wrap: break-word;
        }

        .message-content pre {
            background-color: var(--matlab-code-bg);
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Consolas', 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            color: var(--text-color);
            margin-top: 1rem;
        }

        .chat-timestamp {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-align: right;
            margin-top: 0.5rem;
            font-style: italic;
        }

        .avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 1rem;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .user-avatar {
            background-color: var(--matlab-blue);
        }

        .bot-avatar {
            background-color: var(--matlab-orange);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stApp {
            background-color: var(--main-bg) !important;
        }

        [data-testid="stAppViewContainer"] > section[data-testid="stVerticalBlock"] {
            background-color: var(--main-bg);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--matlab-blue);
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 600;
        }

        .stMarkdown, p, span, div, label,
        .stTextInput label, .stTextArea label,
        .stSelectbox label, .stMultiselect label {
            color: var(--text-color);
        }

        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            padding: 2rem 1rem;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--matlab-blue);
        }

        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] label {
            color: var(--sidebar-text);
        }

        [data-testid="stSidebar"] div[style*="font-weight: bold; color: white"] {
            color: var(--sidebar-text) !important;
        }

        [data-testid="stSidebar"] div[style*="color: #cccccc"] {
            color: var(--text-secondary) !important;
        }

        pre {
            background-color: var(--code-bg);
            color: var(--code-text);
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Consolas', 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            margin-top: 1rem;
        }

        code {
            color: var(--matlab-orange);
            background-color: var(--matlab-code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.9em;
        }

        .stButton button {
            background-color: var(--button-bg);
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }

        .stButton button:hover {
            background-color: var(--button-hover);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }

        .stSpinner {
            background-color: var(--spinner-bg) !important;
            border-radius: 10px;
            padding: 1rem;
        }

        .stTextInput div[data-baseweb="input"],
        .stTextArea textarea {
            border-radius: 10px;
            border: 2px solid var(--input-border);
            background-color: var(--input-bg);
            transition: all 0.2s ease;
            color: var(--input-text);
        }
        .stTextInput div[data-baseweb="input"] svg {
            fill: var(--text-secondary) !important;
        }
        .stTextInput div[data-baseweb="input"] button {
            background-color: var(--input-bg) !important;
            border: none !important;
            box-shadow: none !important;
        }

        .stTextInput input {
            color: var(--input-text);
            background-color: var(--input-bg) !important;
        }

        .stRadio label {
            color: var(--text-color);
        }

        .logo-container {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background-color: var(--header-bg);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        .logo-container h1 {
            color: var(--matlab-blue);
        }

        .logo-container p {
            color: var(--text-color);
        }

        [data-testid="stFileUploadDropzone"] {
            background-color: var(--input-bg) !important;
            border-color: var(--input-border) !important;
        }
        # Add this to the end of the common_css string in apply_matlab_theme()

        /* Force override for Streamlit UI elements */
        button, [type="button"], [type="reset"], [type="submit"] {
            background-color: var(--button-bg) !important;
            color: white !important;
            border: none !important;
        }

        .stButton > button {
            background-color: var(--button-bg) !important;
            color: white !important;
        }

        [data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] {
            background-color: var(--input-bg) !important;
            border-color: var(--input-border) !important;
            color: var(--text-color) !important;
        }

        /* Ensure text inputs are visible */
        input[type="text"], textarea, [data-baseweb="input"] input {
            background-color: var(--input-bg) !important;
            color: var(--input-text) !important;
        }

        /* Fix avatar colors */
        .avatar-btn, [data-testid="baseButton-headerNoPadding"] {
            background-color: var(--matlab-blue) !important;
            color: white !important;
        }

        /* Fix form submit buttons */
        .stForm [data-testid="stFormSubmitButton"] button {
            background-color: var(--button-bg) !important;
            color: white !important;
        }


    </style>
    """

    st.markdown(matlab_theme_css + common_css, unsafe_allow_html=True)

# ------------- ACTION HANDLERS ------------- 

def new_chat():
    """Start a fresh chat, persist if logged-in."""
    idx = len(st.session_state.sessions) + 1
    name = f"Chat {idx}"
    st.session_state.sessions[name] = []
    st.session_state.current_session = name
    if st.session_state.logged_in:
        user = st.session_state.username
        st.session_state.user_data[user]['sessions'] = st.session_state.sessions
        save_user_data(st.session_state.user_data)
    st.rerun()

def clear_chat_history():
    """Clear current session's history, persist if logged-in."""
    st.session_state.sessions[st.session_state.current_session] = []
    if st.session_state.logged_in:
        user = st.session_state.username
        st.session_state.user_data[user]['sessions'] = st.session_state.sessions
        save_user_data(st.session_state.user_data)
    st.rerun()

def change_theme(theme):
    """Change theme and persist per-user preference."""
    st.session_state.theme = theme
    if st.session_state.logged_in:
        user = st.session_state.username
        st.session_state.user_data[user]["settings"]["theme"] = theme
        save_user_data(st.session_state.user_data)
    st.rerun()

def process_user_input(user_input):
    """Process user input and add to the CURRENT selected chat only."""
    # Get current chat
    current_session = st.session_state.current_session
    
    # Add message to the CURRENT chat only
    if current_session not in st.session_state.sessions:
        st.session_state.sessions[current_session] = []
    
    # Add user message - only show the first part of the input if it contains file content
    display_input = user_input.split("\n\nContext from uploaded file:")[0] if "\n\nContext from uploaded file:" in user_input else user_input
    
    st.session_state.sessions[current_session].append({
        'role': 'user',
        'content': display_input,
        'timestamp': get_timestamp()
    })
    
    # Generate bot response with the full context
    with st.spinner("MATBOT is thinking..."):
        bot_response, metadata = get_bot_response(user_input)
        
        # Add bot response with metadata
        st.session_state.sessions[current_session].append({
            'role': 'assistant',
            'content': bot_response,
            'timestamp': get_timestamp(),
            'metadata': metadata
        })
    
    # Save user data if logged in
    if st.session_state.logged_in:
        user = st.session_state.username
        st.session_state.user_data[user]['sessions'] = st.session_state.sessions
        save_user_data(st.session_state.user_data)
    
    st.rerun()

def logout_user():
    """Log out the current user."""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ------------- MAIN APP EXECUTION ------------- 
def main():
    """Main application entry point."""
    initialize_app()
    render_navbar()
    if not st.session_state.logged_in:
        render_auth_interface()
    else:
        render_chat_interface()
        render_sidebar()
        
    

if __name__ == "__main__":
    main()