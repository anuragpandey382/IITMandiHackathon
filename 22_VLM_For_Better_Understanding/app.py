import os
import re
from flask import Flask, request, render_template, jsonify, session
from flask_cors import CORS 
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import torch

chat_history = []

MODEL_PATH = Path("./qwen-3-transformers-0.6b-v1")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model directory not found at {MODEL_PATH}. "
        "Please download the model and place it in the correct location, "
        "or update the MODEL_PATH variable."
    )

# --- Model Loading ---
print(f"Loading tokenizer from: {MODEL_PATH}")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    print("Tokenizer loaded successfully.")
except Exception as e:
    print(f"Error loading tokenizer: {e}")
    raise

print(f"Loading model from: {MODEL_PATH}")
try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype="auto",  
        device_map="auto"    
    )
    print(f"Model loaded successfully onto device: {model.device}")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.urandom(24)

# table_html = None
# try:
#     table_html = open('./vlmax/public/results.html', 'r', encoding='utf-8').read()
# except FileNotFoundError:
#     try :
#         table_html = open('./public/results.html', 'r', encoding='utf-8').read()
#     except FileNotFoundError:
#         print("HTML table file not found. Please ensure the file exists.")

# print("HTML table :", table_html[:1000])  # Print the first 1000 characters for brevity
def ask_qwen_model(question: str, table_html: str) -> str:

    system_prompt = (
        "You are a helpful AI assistant analyzing an HTML table. "
        f"The table is provided below:\n\n```html\n{table_html}\n```\n\n"
        "Prioritize answering questions based *only* on the information in this table. "
        "However, also pay attention to the entire conversation history. "
        "If the user asks a question not related to the table (e.g., asks you to remember their name or asks about previous turns), "
        "use the conversation history to answer. If the answer cannot be found in the table or the conversation history, say so politely."
    )

    # Construct messages for the model
    print(f"Chat history: {chat_history}")
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    messages.append({"role": "user", "content": question})

    # print("-" * 20)
    # print("Messages sent to model:")
    # for msg in messages:
    #     # Print truncated content for brevity in logs
    #     print(f"- {msg['role']}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
    # print("-" * 20)

    try:
        print(messages)
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=1024,
        )

        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]
        raw_response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()

        print(f"Model Raw Response: {raw_response}")

        cleaned_response = re.sub(r"<think>.*?</think>\s*", "", raw_response, flags=re.DOTALL).strip()

        print(f"Cleaned Response: {cleaned_response}")
        return cleaned_response 

    except Exception as e:
        print(f"Error during model generation: {e}")
        return None

# --- Flask Routes ---
from flask_cors import cross_origin


@app.route('/ask', methods=['POST'])
@cross_origin()
def ask():
    """Handles incoming questions, interacts with the model, and returns the answer."""
    if request.is_json:
        data = request.get_json()
        question = data.get('question')

    else : 
        question = request.form.get('question')

    table_html = None
    try:
        table_html = open('./vlmax/public/results.html', 'r', encoding='utf-8').read()
    except FileNotFoundError:
        try :
            table_html = open('./public/results.html', 'r', encoding='utf-8').read()
        except FileNotFoundError:
            print("HTML table file not found. Please ensure the file exists.")

    print(f"Chat history: {chat_history}")

    if not question:
        return jsonify({"error": "No question provided."}), 400
    if table_html is None:
        return jsonify({"error": "Please submit the HTML table first."}), 400
    if chat_history is None:
         return jsonify({"error": "Chat history not initialized. Please submit table again."}), 400

    print(f"Received question: {question}")

    answer = ask_qwen_model(question, table_html)

    if answer is None:
        return jsonify({"error": "Failed to get response from the model."}), 500

    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer}) # Store the cleaned answer
    print(f"Updated chat history: {chat_history}")
    # print(f"Sending answer: {answer}")
    return jsonify({"answer": answer}) 

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)