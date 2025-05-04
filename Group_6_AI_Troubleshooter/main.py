import os
from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import base64

from dotenv import load_dotenv
import sys

# Import the Zep client - only importing what we know exists
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message, Session

from agents.orchestrator import Orchestrator

def setup_environment():
    """Setup environment variables and API keys"""
    # Load environment variables
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        
    # Validate OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        sys.exit(1)
        
    # Validate Zep API key
    if not os.getenv('ZEP_API_KEY'):
        print("Error: ZEP_API_KEY not found in environment variables.")
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
        print("-----------------------------------------------------\n")
        print(result)
        return result, None  # Return response and no documents for now
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error while processing your request. Please try again.", None

# Suppress torch RuntimeError related to __path__._path
try:
    setup_environment()
    orchestrator = Orchestrator(
        faiss_index_path="./faiss_index",
        model="gpt-4o-mini"
    )
    image_bytes = None
except RuntimeError as e:
    if "__path__._path" not in str(e):
        raise  # Re-raise if it's not the specific error we're suppressing

# Load environment variables
load_dotenv()

# Initialize Zep client
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
zep_client = AsyncZep(api_key=ZEP_API_KEY)

# Maximum message length for Zep memory API
MAX_ZEP_MESSAGE_LENGTH = 2400  # Slightly below the 2500 limit for safety

async def add_message_to_zep(session_id, role, role_type, content):
    """
    Add a message to Zep memory, handling large content appropriately
    """
    try:
        # Check if content exceeds the maximum length
        if len(content) > MAX_ZEP_MESSAGE_LENGTH:
            # Create a summary for memory
            summary = content[:MAX_ZEP_MESSAGE_LENGTH - 100] + "... [content truncated]"
            
            # Add the truncated version to memory with metadata indicating truncation
            memory_message = Message(
                role=role,
                role_type=role_type,
                content=summary,
                metadata={"timestamp": datetime.now().isoformat(), "truncated": True}
            )
            await zep_client.memory.add(session_id, messages=[memory_message])
            print(f"Added truncated message to session {session_id}")
            
        else:
            # Add regular sized message to memory
            memory_message = Message(
                role=role,
                role_type=role_type,
                content=content,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            await zep_client.memory.add(session_id, messages=[memory_message])
        
        return True
    except Exception as e:
        print(f"Warning: Failed to add message to Zep: {e}")
        return False

app = FastAPI(title="RAG Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update the ChatRequest model to support image data
class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    image_base64: Optional[str] = None  # For JSON-based image submission

# Add a new endpoint for form-based submission with file upload
@app.post("/chat/form")
async def chat_form_endpoint(
    prompt: str = Form(...),
    image: Union[UploadFile, None] = File(None),
    session_id: Optional[str] = Form(None)
):
    """Chat endpoint that accepts multipart form data with image upload"""
    
    # If no session ID provided, create a new one
    session_id = session_id if session_id else str(uuid.uuid4())
    
    # Ensure session exists in Zep
    if not session_id:
        try:
            # Create a new session
            session = Session(name=session_id)
            await zep_client.session.create(session)
        except Exception as e:
            print(f"Warning: Failed to create session in Zep: {e}")
    
    # Retrieve chat history
    chat_history = []
    try:
        memory = await zep_client.memory.get(session_id)
        if memory and hasattr(memory, 'messages'):
            for msg in memory.messages:
                chat_history.append({
                    "role": "user" if msg.role_type == "user" else "assistant",
                    "content": msg.content
                })
    except Exception as e:
        print(f"Warning: Failed to retrieve chat history from Zep: {e}")
    
    try:
        # Read image if provided
        image_bytes = None
        if image is not None:
            image_bytes = await image.read()
        
        # Call orchestration function with prompt, image bytes, and chat history
        print(prompt)
        result, retrieved_documents = generate_response(prompt, image_bytes, chat_history)
        print("-----------------------------------------------------\n")
        print(result)
        response_data = {
            "final_response": result.final_response,
            "reference_links": [
                {"title": ref.title, "url": ref.url} 
                for ref in result.reference_links
            ] if result.reference_links else [],
            "relevant_docs": [
                {
                    "score": doc.score,
                    "url": doc.url,
                    "content_preview": doc.content_preview
                } 
                for doc in sorted(result.relevant_docs, key=lambda x: x.score, reverse=True)
            ] if result.relevant_docs else []
        }
        
        # Store messages in Zep
        await add_message_to_zep(session_id, "user", "user", prompt)
        await add_message_to_zep(session_id, "assistant", "assistant", result.final_response)
        
        return response_data
        
    except Exception as e:
        print(f"Error in chat form endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Update the existing JSON-based chat endpoint to handle base64 encoded images
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    prompt = request.prompt
    
    # If no session ID provided, create a new one
    session_id = request.session_id if request.session_id else str(uuid.uuid4())
    
    # Ensure session exists in Zep
    if not request.session_id:
        try:
            # Create a new session
            session = Session(name=session_id)
            await zep_client.session.create(session)
        except Exception as e:
            print(f"Warning: Failed to create session in Zep: {e}")
    
    # Retrieve chat history for the session from Zep
    chat_history = []
    try:
        # Get memory for the session
        memory = await zep_client.memory.get(session_id)
        
        # Extract messages from memory
        if memory and hasattr(memory, 'messages'):
            for msg in memory.messages:
                chat_history.append({
                    "role": "user" if msg.role_type == "user" else "assistant",
                    "content": msg.content
                })
    except Exception as e:
        print(f"Warning: Failed to retrieve chat history from Zep: {e}")
    
    try:
        # Process image if provided in base64 format
        image_bytes = None
        if request.image_base64:
            try:
                image_bytes = base64.b64decode(request.image_base64)
            except Exception as e:
                print(f"Failed to decode base64 image: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Call orchestration function with prompt, image bytes, and chat history
        response, retrieved_documents = generate_response(prompt, image_bytes, chat_history)
        
        # Store the user message and AI response in Zep
        await add_message_to_zep(session_id, "user", "user", prompt)
        await add_message_to_zep(session_id, "assistant", "assistant", response)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            documents=retrieved_documents
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Retrieve chat history for a specific session"""
    try:
        # Get memory for the session
        memory = await zep_client.memory.get(session_id)
        
        # Format the response to match the expected structure
        formatted_history = []
        
        if memory and hasattr(memory, 'messages'):
            for msg in memory.messages:
                entry = {}
                if msg.role_type == "user":
                    entry["user_message"] = msg.content
                else:
                    entry["ai_response"] = msg.content
                
                # Check if the message was truncated
                if (hasattr(msg, 'metadata') and msg.metadata and 
                    msg.metadata.get('truncated', False)):
                    entry["truncated"] = True
                
                # Add timestamp from metadata if available
                if hasattr(msg, 'metadata') and msg.metadata and 'timestamp' in msg.metadata:
                    entry["timestamp"] = msg.metadata['timestamp']
                else:
                    entry["timestamp"] = datetime.now().isoformat()
                    
                formatted_history.append(entry)
        
        return formatted_history
    
    except Exception as e:
        print(f"Error in get_session_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)