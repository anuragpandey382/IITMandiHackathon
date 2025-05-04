from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import hashlib
import os
from bson import ObjectId
from bson.objectid import ObjectId
import random
import string
import uuid
from main import run_qna_workflow
from agents.imageQueryAgent import generate_query_from_image

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

# -------------------- Initialize Flask App --------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# -------------------- Connect to MongoDB --------------------
try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise e

db = client["troubleshooter"]
user_collection = db["user"]
global_collection = db["qna"]
user_credentials_collection = db["user_credentials"]

# -------------------- Routes --------------------

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    question = data.get("question")
    mode = data.get("mode", "Web Search")
    timestamp = datetime.utcnow()

    answer = run_qna_workflow(question)
    ques_id = str(uuid.uuid4())

    chat_entry = {
        "ques_id": ques_id,
        "question": question,
        "answer": answer,
        "mode": mode,
        "timestamp": timestamp
    }


    # Find the user, or initialize if not found
    user_doc = user_collection.find_one({"user_id": user_id})

    if not user_doc:
        # If the user does not exist, initialize their document
        user_collection.insert_one({
            "user_id": user_id,
            "chat_history": []  # Empty chat history for new user
        })
        user_doc = {"chat_history": []}  # Initialize chat history for new user

    chat_history = user_doc.get("chat_history", [])

    chat_found = False
    for chat in chat_history:
        if chat["chat_id"] == chat_id:
            chat["messages"].append(chat_entry)
            chat_found = True
            break

    if not chat_found:
        # Create a new chat if no chat with the given chat_id exists
        chat_name = "Welcome Chat"  # You can replace this with any default or generated chat name
        chat_history.append({
            "chat_id": chat_id,
            "chat_name": chat_name,
            "messages": [chat_entry]
        })

    # Update the user document with the new chat history
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"chat_history": chat_history}}
    )

    return jsonify({"status": "success", "answer": answer, "questionId": ques_id})



# Get all chats of a user

@app.route("/user/chats/<user_id>", methods=["GET"])
def get_user_chats(user_id):
    user_doc = user_collection.find_one({"user_id": user_id}, {"_id": 0, "chat_history": 1})
    if not user_doc or "chat_history" not in user_doc:
        return jsonify({"chats": []})

    chat_history = user_doc["chat_history"]
    chat_list = [{"chat_name": chat["chat_name"], "chat_id": chat["chat_id"]} for chat in chat_history]

    return jsonify({"chats": chat_list})


# get a specific chat

def convert_object_ids(obj):
    if isinstance(obj, list):
        return [convert_object_ids(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_object_ids(value) for key, value in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

@app.route("/user/chat/<user_id>/<chat_id>", methods=["GET"])
def get_chat_by_id(user_id, chat_id):
    try:
        user_doc = user_collection.find_one({"user_id": user_id}, {"_id": 0, "chat_history": 1})
        if not user_doc or "chat_history" not in user_doc:
            return jsonify({"error": "User or chat history not found"}), 404

        for chat in user_doc["chat_history"]:
            if chat.get("chat_id") == chat_id:
                chat_cleaned = convert_object_ids(chat)
                return jsonify({
                    "chat_id": chat_cleaned.get("chat_id"),
                    "chat_name": chat_cleaned.get("chat_name"),
                    "messages": chat_cleaned.get("messages", [])
                })

        return jsonify({"error": "Chat not found"}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# Create a new chat for a user

@app.route("/create-chat", methods=["POST"])
def create_new_chat():
    data = request.get_json()
    user_id = data.get("user_id")
    chat_name = data.get("chat_name", "Welcome Chat")
    chat_id = str(uuid.uuid4())

    user_doc = user_collection.find_one({"user_id": user_id})
    if not user_doc:
        return jsonify({"error": "User not found"}), 404

    new_chat = {
        "chat_id": chat_id,
        "chat_name": chat_name,
        "messages": []
    }

    user_collection.update_one(
        {"user_id": user_id},
        {"$push": {"chat_history": new_chat}}
    )

    return jsonify({"chat_id": chat_id, "chat_name": chat_name})


# delete a chat for a user

@app.route("/delete-chat", methods=["POST"])
def delete_chat():
    data = request.get_json()
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")

    user_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"chat_history": {"chat_id": chat_id}}}
    )

    return jsonify({"status": "success"})



# ----------------------------------------------------------

@app.route("/history/<user_id>", methods=["GET"])
def get_user_history(user_id):
    history = list(user_collection.find({"user_id": user_id}, {"_id": 0}))
    return jsonify(history)

@app.route("/qna/<ques_id>", methods=["GET"])
def get_answer_by_ques_id(ques_id):
    result = global_collection.find_one({"ques_id": ques_id}, {"_id": 0})
    if not result:
        return jsonify({"error": "Question ID not found"}), 404
    return jsonify(result)

@app.route("/user/questions/<user_id>", methods=["GET"])
def get_user_questions(user_id):
    user_doc = user_collection.find_one({"user_id": user_id}, {"_id": 0, "chat_history.question": 1})
    
    if not user_doc or "chat_history" not in user_doc:
        return jsonify({"error": "No history found for this user"}), 404

    questions = [entry["question"] for entry in user_doc["chat_history"] if "question" in entry]
    return jsonify({"user_id": user_id, "questions": questions})


# -------------------- User Authentication --------------------

@app.route("/auth", methods=["POST"])
def authenticate_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = user_credentials_collection.find_one({"username": username, "password": password})
    if user:
        return jsonify({"status": "success", "user_id": user["user_id"]})
    return jsonify({"status": "failure", "message": "Invalid credentials"}), 401

@app.route("/signup", methods=["POST"])
def signup_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "failure", "message": "Username and password required"}), 400

    # Check if username already exists
    existing_user = user_credentials_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"status": "failure", "message": "Username already exists"}), 409

    # Create new user with a unique user_id
    user_id = hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

    # Insert the user into the user_credentials collection
    user_credentials_collection.insert_one({
        "username": username,
        "password": password,
        "user_id": user_id
    })

    # Create the initial user document in the users collection with an initial chat ("Welcome Chat")
    chat_id = str(uuid.uuid4())  # New chat ID
    chat_name = "Welcome Chat"  # First chat for the user

    user_collection.insert_one({
        "user_id": user_id,
        "chat_history": [
            {
                "chat_id": chat_id,
                "chat_name": chat_name,
                "messages": []  # Empty messages for the welcome chat
            }
        ]
    })

    return jsonify({"status": "success", "user_id": user_id})





# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# route to get answer using question object id 
@app.route('/get-answer', methods=['GET'])
def get_answer_by_object_id():
    object_id = request.args.get("objectId")
    if not object_id:
        return jsonify({"error": "Missing objectId"}), 400

    result = global_collection.find_one({"_id": ObjectId(object_id)}, {"_id": 0})
    if not result:
        return jsonify({"error": "Object ID not found"}), 404

    return jsonify(result)


# endpoint to add question and answer to the database
def generate_ques_id(length=24):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@app.route('/add-qna', methods=['POST'])
def add_qna():
    # Get the input data (question and answer)
    data = request.json
    question = data.get('question')
    answer = data.get('answer')

    if not question or not answer:
        return jsonify({"error": "Missing question or answer"}), 400

    # Generate random ques_id
    ques_id = generate_ques_id()

    # Insert the new Q&A entry into the database
    new_qna = {
        "question": question,
        "answer": answer,
        "ques_id": ques_id
    }

    result = global_collection.insert_one(new_qna)

    # Return the ObjectId of the newly created document
    return jsonify({"objectId": str(result.inserted_id), "ques_id": ques_id}), 201


# ---------------Suggestion Generation------------------
from agents.autocompleteAgent import get_matlab_suggestions

@app.route("/suggest", methods=["GET"])
def suggest():
    query = request.args.get("q", "")
    # print("Query:", query)  # Debugging line to check the query value
    if not query:
        return jsonify(suggestions=[])
    
    suggestions = get_matlab_suggestions(query)
    return jsonify(suggestions=suggestions)



@app.route('/image-to-query', methods=['POST'])
def image_to_query():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    image_bytes = file.read()

    query = generate_query_from_image(image_bytes)
    
    if query.startswith("❌ Error"):
        return jsonify({'error': query}), 500
    
    return jsonify({'query': query})


# 1) List all users for admin
@app.route("/admin/users", methods=["GET"])
def get_all_users():
    try:
        users_cursor = user_credentials_collection.find({}, {"_id": 0, "user_id": 1, "username": 1})
        users = list(users_cursor)
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 2) Dump raw user_collection for admin download
@app.route("/admin/raw_logs", methods=["GET"])
def get_raw_logs():
    try:
        users_cursor = user_collection.find({}, {"_id": 0})
        users = list(users_cursor)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#3 Return full chat_history for one user ———
@app.route("/hist/<user_id>", methods=["GET"])
def get_user_history_chat(user_id):
    """
    Returns JSON array of documents matching user_id, e.g.
      [ { user_id, chat_history: [ { chat_id, chat_name, messages: […] }, … ] } ]
    """
    try:
        # find all docs for this user (should normally be one)
        docs = list(
            user_collection.find(
                {"user_id": user_id},
                {"_id": 0, "user_id": 1, "chat_history": 1}
            )
        )
        return jsonify(docs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)
