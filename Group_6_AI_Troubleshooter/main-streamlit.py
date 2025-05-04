import streamlit as st
import time
import random
import uuid
from datetime import datetime
import os
import torch
import tempfile
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import soundfile as sf
import numpy as np
from tqdm import tqdm
import sounddevice as sd
from langchain.memory import ConversationBufferMemory
import streamlit.components.v1 as com
import warnings

# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

# Set page config
st.set_page_config(
    page_title="MATFix-AI",
    page_icon="💬",
    layout="centered"
)

col1, col2 = st.columns([1, 3])

# Display Lottie animation in the first column
with col1:
    com.html("<div style='height: 360px; width: 950px; background: transparent;'></div>", height=360, width=950)


# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f7f7f8;
    }
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.8rem; 
        margin-bottom: 1rem; 
        height: 100%;
        align-items: center;
        display: flex;
    }
    .chat-message.user {
        background-color: #f0f2f6;
    }
    .chat-message.bot {
        background-color: white;
    }
    .chat-message .avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 1rem;
    }
    .chat-message .message {
        flex-grow: 1;
    }
    .sidebar .sidebar-content {
        background-color: #f7f7f8;
    }
    .stTextInput>div>div>input {
        border-radius: 0.8rem;
        padding: 1rem;
        font-size: 1.1rem;
    }
    .stButton>button {
        background-color: #10a37f;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 1.1rem;
        border: none;
        width: 100%;
        text-align: left;
    }
    .stButton>button:hover {
        background-color: #0d8a6c;
    }
    .input-container {
        position: fixed;
        bottom: 40px;
        left: 0;
        width: 100%;
        padding: 10px;
        background-color: #f7f7f8;
        z-index: 100;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        font-size: 0.8rem;
        color: #888;
        padding: 0.5rem;
        background: transparent;
        z-index: 99;
    }
    .session-id {
        background-color: #e9f7f2;
        border-radius: 4px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        border-left: 3px solid #10a37f;
    }
    .main .block-container {
        padding-bottom: 100px;
    }
</style>
""", unsafe_allow_html=True)

def load_model(model_size="small"):
    """Load the Whisper model and processor"""
    print("Loading Whisper model...")
    model_name = f"openai/whisper-{model_size}"
    
    processor = WhisperProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name)
    
    # Use GPU if available
    if torch.cuda.is_available():
        model = model.cuda()
        print("Using GPU for inference")
    else:
        print("Using CPU for inference (this might be slow)")
    
    return processor, model

# Track all sessions and messages
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "all_messages" not in st.session_state:
    st.session_state.all_messages = {}

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "thinking" not in st.session_state:
    st.session_state.thinking = False

if "memories" not in st.session_state:
    st.session_state.memories = {}

if "whisper_model" not in st.session_state:
    with st.spinner("Loading Whisper model... This may take a moment."):
        processor, model = load_model("small")
        st.session_state.whisper_processor = processor
        st.session_state.whisper_model = model
        st.success("Model loaded successfully!")

RESULT_FILE = "transcription_result.txt"

def record_audio(duration=5, sample_rate=16000):
    """Record audio from the microphone"""
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"recording_{int(time.time())}.wav")
    
    # Find an input device
    input_device_index = None
    for i, device in enumerate(sd.query_devices()):
        if device['max_input_channels'] > 0:
            input_device_index = i
            print(f"Using microphone: {device['name']}")
            break

    if input_device_index is None:
        print("Error: No microphone found")
        return None
    
    print(f"Recording for {duration} seconds...")
    
    try:
        # Record audio
        audio = sd.rec(int(duration * sample_rate),
                      samplerate=sample_rate,
                      channels=1,
                      dtype='int16',
                      device=input_device_index)
        
        # Simple progress bar
        for _ in tqdm(range(duration)):
            time.sleep(1)
        
        sd.wait()  # Wait until recording is finished
        print("Recording finished")
        
        # Save the audio to a temporary file
        sf.write(output_file, audio, sample_rate)
        return output_file
    
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None
    
def transcribe_audio(file_path, processor, model):
    """Transcribe an audio file"""
    print(f"Transcribing audio...")
    
    try:
        # Load audio
        audio, sampling_rate = sf.read(file_path)
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Ensure audio is in float32 format
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize audio
        if np.abs(audio).max() > 1.0:
            audio = audio / np.abs(audio).max()
        
        # Process audio
        input_features = processor(audio, sampling_rate=sampling_rate, return_tensors="pt").input_features
        
        # Move to GPU if available
        if torch.cuda.is_available():
            input_features = input_features.cuda()
        
        # Generate tokens
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
        predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
        
        # Decode to text
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return transcription
    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""
    
def voice_to_text():
    """Main function to record and transcribe audio"""
    # Set recording duration (in seconds)
    duration = 5
    
    # Load the model
    processor, model = load_model("small")
    
    # Record audio from microphone
    audio_file = record_audio(duration=duration)
    
    if not audio_file:
        print("Failed to record audio")
        return
    
    # Transcribe the audio
    transcription = transcribe_audio(audio_file, processor, model)
    
    # Save the transcription to a file that the main app can read
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        f.write(transcription)
    
    print("\nTranscription:")
    print(transcription)
    print(f"\nTranscription saved to {RESULT_FILE}")
    
    # Clean up the temporary audio file
    try:
        os.remove(audio_file)
    except:
        pass

# Function to simulate the AI thinking and generating response
def generate_response(prompt, image_bytes=None, conversation_history=None):
    print("-----------------------------------------------------\n")
    print(prompt)
    print("-----------------------------------------------------\n")
    
    # Handle empty or None prompt
    if not prompt:
        return "I didn't receive any input. Please try again with a question or message."
    
    try:
        # Pass conversation history to orchestrator if available
        result = orchestrator.run(prompt, image_bytes, conversation_history)
        return print_result(result)
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error while processing your request. Please try again."

def create_new_session():
    new_session_id = str(uuid.uuid4())
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save new session info
    st.session_state.chat_sessions[new_session_id] = {
        "last_updated": current_time
    }
    
    # Initialize messages for new session
    st.session_state.all_messages[new_session_id] = []
    
    # Initialize LangChain memory for this session
    st.session_state.memories[new_session_id] = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    return new_session_id

def format_conversation_history(memory):
    """Format conversation history from memory buffer for the LLM"""
    if not memory or not hasattr(memory, 'chat_memory') or not hasattr(memory.chat_memory, 'messages'):
        return []
    
    formatted_history = []
    for message in memory.chat_memory.messages:
        if hasattr(message, 'type') and hasattr(message, 'content'):
            role = 'user' if message.type == 'human' else 'assistant'
            formatted_history.append({
                'role': role,
                'content': message.content
            })
    
    return formatted_history

# -----------------------------------------------------main app-----------------------------------------------------
from dotenv import load_dotenv
import google.generativeai as genai
import sys

from agents.orchestrator import Orchestrator

def setup_environment():
    """Setup environment variables and API keys"""
    # Load environment variables
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

    # Configure Google API
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        genai.configure(api_key=google_api_key)
    else:
        print("Warning: GOOGLE_API_KEY not found in environment variables.")
        
    # Validate OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        sys.exit(1)

def print_result(result):
    # Handle None result case
    if not result:
        return "I couldn't generate a proper response. Please try again."
    
    # Build the output as a string
    final_output_string = "\n--- Final Output ---\n"

    final_output_string += f"\nResponse:\n{result.final_response}\n"

    # Add reference links
    if hasattr(result, 'reference_links') and result.reference_links:
        final_output_string += "\nReference Links:\n"
        for ref in result.reference_links:
            final_output_string += f"- {ref.title}: {ref.url}\n"
    else:
        final_output_string += "\nReference Links: None\n"

    # Add relevant documents
    if hasattr(result, 'relevant_docs') and result.relevant_docs:
        final_output_string += "\nRelevant Documents:\n"
        for i, doc in enumerate(sorted(result.relevant_docs, key=lambda x: x.score if hasattr(x, 'score') else 0, reverse=True)):
            final_output_string += f"\n[{i+1}] Score: {getattr(doc, 'score', 0):.2f}\n"
            final_output_string += f"URL: {getattr(doc, 'url', 'N/A')}\n"
            final_output_string += f"Preview: {getattr(doc, 'content_preview', 'N/A')}\n"
    else:
        final_output_string += "\nRelevant Documents: None\n"
    return final_output_string

# Suppress torch RuntimeError related to __path__._path
try:
    setup_environment()
    orchestrator = Orchestrator(
        faiss_index_path="./faiss_index/faiss_index",
        model="gpt-4o-mini"
    )
    image_bytes = None
except RuntimeError as e:
    if "__path__._path" not in str(e):
        raise  # Re-raise if it's not the specific error we're suppressing

chat_container = st.container()
# Sidebar for new chat and settings
with st.sidebar:
    # New chat button
    if st.button("New Chat"):
        st.session_state.session_id = None
        st.rerun()
    
    # Previous sessions section (optional - shows 5 most recent)
    # Show recent sessions
    if len(st.session_state.chat_sessions) > 0:
        st.divider()
        st.subheader("Recent Chats")

        sorted_sessions = sorted(
            st.session_state.chat_sessions.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True
        )

        count = 0
        for session_id, _ in sorted_sessions:
            col1, col2 = st.columns([4, 1])  # Create two columns for session label and delete button
            with col1:
                label = f"Session {session_id[:8]}..."
                if st.button(label, key=f"session_{session_id}"):
                    print(f"[DEBUG] Selected session: {session_id}")
                    st.session_state.session_id = session_id
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}"):  # Add a delete button
                    # Delete the session and its history
                    del st.session_state.chat_sessions[session_id]
                    del st.session_state.all_messages[session_id]
                    if session_id in st.session_state.memories:
                        del st.session_state.memories[session_id]
                    if st.session_state.session_id == session_id:
                        st.session_state.session_id = None  # Reset current session if it was deleted
                    st.rerun()  # Reload the page after deletion
            count += 1
            if count >= 5:
                break
    
    st.divider()

with chat_container:
    if st.session_state.session_id is None:
        # Show the welcome message when no session is active
        with st.chat_message("bot"):
            st.markdown("Hello! I'm your AI assistant. How can I help you today?")
    else:
        if st.session_state.session_id and st.session_state.session_id in st.session_state.all_messages:
            messages = st.session_state.all_messages[st.session_state.session_id]
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

# st.markdown("<div class='input-container'>", unsafe_allow_html=True)
# Replace the voice button and chat input section with this:
st.session_state.prompt=None
if "voice_text" in st.session_state and st.session_state.voice_text:
    # If we have transcribed voice text, display it above the chat input
    st.info(f"Voice input: {st.session_state.voice_text}")
    
    # Add buttons to use the voice text or clear it
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Use this text"):
            st.session_state.prompt = st.session_state.voice_text
            st.session_state.voice_text = ""  # Clear after use
            
            # Process the prompt just like regular text input
            if st.session_state.session_id is None:
                # Create a new session
                new_session_id = str(uuid.uuid4())
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save new session info
                st.session_state.chat_sessions[new_session_id] = {
                    "last_updated": current_time
                }
                
                # Set current session
                st.session_state.session_id = new_session_id

                # Initialize messages for new session
                st.session_state.all_messages[new_session_id] = []
            
            session_id = st.session_state.session_id
            st.session_state.all_messages[session_id].append({"role": "user", "content": st.session_state.get("prompt")})
            
            # Update last modified
            st.session_state.chat_sessions[session_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.session_state.thinking = True
            st.rerun()
    with col2:
        if st.button("Clear"):
            st.session_state.voice_text = ""
            st.rerun()
else:
    # Normal chat input and voice button layout
    col1, col2 = st.columns([9, 1])  # Create two columns: one for the text input and one for the voice button

    with col1:
        st.session_state.prompt = st.chat_input("Ask something...")
    print("##############################",st.session_state.get("prompt"))
    with col2:
        if st.button("🎤"):
            with st.spinner("Recording..."):
                # Directly use the functions with the pre-loaded model
                audio_file = record_audio(duration=5)
                
                if audio_file:
                    with st.spinner("Transcribing..."):
                        # Use the models from session state
                        transcribed_text = transcribe_audio(
                            audio_file, 
                            st.session_state.whisper_processor, 
                            st.session_state.whisper_model
                        )
                        
                        # Clean up the temporary audio file
                        try:
                            os.remove(audio_file)
                        except:
                            pass
                        
                        # If transcription was successful, store it in session state
                        if transcribed_text:
                            st.session_state.voice_text = transcribed_text
                            st.rerun()
                else:
                    st.error("Failed to record audio. Please check your microphone.")

st.markdown("</div>", unsafe_allow_html=True)
print("##############################",st.session_state.get("prompt"))

if st.session_state.get("prompt"):
    if st.session_state.session_id is None:
        # Create a new session
        st.session_state.session_id = create_new_session()
    
    session_id = st.session_state.session_id
    
    # Validate prompt is not None or empty before processing
    if st.session_state.get("prompt") and st.session_state.get("prompt").strip():
        st.session_state.all_messages[session_id].append({"role": "user", "content": st.session_state.get("prompt")})
        
        st.session_state.memories[session_id].chat_memory.add_user_message(st.session_state.get("prompt"))

        # Update last modified
        st.session_state.chat_sessions[session_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.session_state.thinking = True
        st.rerun()

# print("##############################",prompt)

if st.session_state.thinking:
    session_id = st.session_state.session_id
    user_input = st.session_state.all_messages[session_id][-1]["content"]
    
    # Get conversation history from memory
    memory = st.session_state.memories[session_id]
    
    # Format conversation history for the LLM
    conversation_history = format_conversation_history(memory)
    
    # Make sure user_input is valid before processing
    if user_input and user_input.strip():
        response = generate_response(user_input, image_bytes, conversation_history)
    else:
        response = "I didn't receive any input. Please try again with a question or message."
    
    st.session_state.prompt = None  # Clear the prompt after processing
    st.session_state.voice_text = ""  # Clear the voice text after processing
    st.session_state.all_messages[st.session_state.session_id].append({"role": "bot", "content": response})
    st.session_state.memories[session_id].chat_memory.add_ai_message(response)
    st.session_state.chat_sessions[st.session_state.session_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with chat_container:
        # Display just the newly generated response
        with st.chat_message("bot"):
            st.markdown(response)

    st.session_state.thinking = False
    st.rerun()

st.markdown("""
<div class="footer">
    © 2025 Demo App
</div>
""", unsafe_allow_html=True)