import streamlit as st
import requests
from uuid import uuid4
from libs.auth import clear_login_token
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:5000/"

def get_top_unique_links(links, limit=5):
    """
    Returns a list of unique links, limited to the specified number.
    """
    seen = set()
    unique_links = []
    for link in links:
        if isinstance(link,str) and link not in seen:
            seen.add(link)
            unique_links.append(link)
        if len(unique_links) >= limit:
            break
    return unique_links

# -------------------- Get Response from Backend --------------------
def get_bot_response(user_input):
    user_id = st.session_state.get("user_id")
    chat_id = st.session_state.current_chat_id
    mode = st.session_state.get("mode", "Web Search")

    payload = {
        "user_id": user_id,
        "chat_id": chat_id,
        "question": user_input,
        "mode": mode
    }

    try:
        res = requests.post(f"{BACKEND_URL}/ask", json=payload)
        if res.status_code == 200:
            return res.json().get("answer", "No answer returned.")
        else:
            st.error(f"❌ Failed to get response from backend. Status code: {res.status_code}")
            return "❌ Failed to get response from backend."
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend not reachable: {e}")
        return "❌ Backend not reachable."

# -------------------- Image to Query --------------------

def get_query_from_image(image_file):
    try:
        files = {'file': image_file}
        res = requests.post(f"{BACKEND_URL}/image-to-query", files=files)
        if res.status_code == 200:
            return res.json().get("query", "")
        else:
            st.error(f"Image processing failed: {res.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with image processing service: {e}")
        return ""

# -------------------- Autocomplete Suggestions --------------------

# def get_autocomplete_suggestions(query):
#     try:
#         res = requests.get(f"{BACKEND_URL}/suggest", params={"q": query})
#         if res.status_code == 200:
#             suggestions_string = res.json().get("suggestions", "")
#             return [s.strip() for s in suggestions_string.split("$") if s.strip()]
#         else:
#             return []
#     except requests.exceptions.RequestException:
#         return []

def get_autocomplete_suggestions(query):
    try:
        res = requests.get(f"{BACKEND_URL}/suggest", params={"q": query})
        if res.status_code == 200:
            suggestions_list = res.json().get("suggestions", [])
            # print("Q", query)
            if isinstance(suggestions_list, list):
                return [s.strip() for s in suggestions_list if isinstance(s, str) and s.strip()]
            else:
                return []
        else:
            return []
    except requests.exceptions.RequestException:
        return []





# -------------------- Main Chat --------------------
def chat():
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    user_id = st.session_state.get("user_id")

    # Initialize chat_sessions if not present
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}

        # Load existing chats for this user
        try:
            res = requests.get(f"{BACKEND_URL}/user/chats/{user_id}")
            if res.status_code == 200:
                chats = res.json().get("chats", [])
                for chat in chats:
                    chat_id = chat["chat_id"]
                    chat_name = chat["chat_name"]
                    st.session_state.chat_sessions[chat_id] = {"chat_name": chat_name, "messages": []}
            else:
                st.error(f"Failed to load chats: {res.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to server to load chats: {e}")
        



    if "current_chat_id" not in st.session_state or not st.session_state.chat_sessions:
        if st.session_state.chat_sessions:
            st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{st.session_state.current_chat_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning("Could not load messages for the required chat.")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading welcome chat messages.")
            st.rerun() # Rerun to display the welcome chat
        else:
            new_id = str(uuid4())
            st.session_state.chat_sessions[new_id] = {"chat_name": "Welcome Chat", "messages": []}
            st.session_state.current_chat_id = new_id
            # Immediately fetch messages for the default chat
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{new_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[new_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning("Could not load messages for the welcome chat.")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading welcome chat messages.")
            st.rerun() # Rerun to display the welcome chat



    # Initialize default mode if not set
    if "mode" not in st.session_state:
        st.session_state.mode = "MATLAB Troubleshooting"




    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.title("🧠 Chats")

        chat_names = {chat_id: chat_info["chat_name"] for chat_id, chat_info in st.session_state.chat_sessions.items()}
        current_chat_name = st.session_state.chat_sessions[st.session_state.current_chat_id]["chat_name"]
        selected_chat_name = st.radio("Select a chat", list(chat_names.values()), index=list(chat_names.values()).index(current_chat_name))

        selected_chat_id = [
            chat_id for chat_id, chat_name in chat_names.items()
            if chat_name == selected_chat_name
        ][0]


        if selected_chat_id != st.session_state.current_chat_id:
            st.session_state.current_chat_id = selected_chat_id
            # Fetch messages for the selected chat
            try:
                res = requests.get(f"{BACKEND_URL}/user/chat/{user_id}/{selected_chat_id}")
                if res.status_code == 200:
                    st.session_state.chat_sessions[selected_chat_id]["messages"] = res.json().get("messages", [])
                else:
                    st.warning(f"Could not load messages for chat ID: {selected_chat_id}")
            except requests.exceptions.RequestException:
                st.warning("Server unreachable while loading chat messages.")
            st.rerun()

        # Rethink button in sidebar to toggle mode
        rethink_button = st.button("🔄 Rethink Mode")
        if rethink_button:
            # Toggle between Web Search and MATLAB Troubleshooting mode
            if st.session_state.mode == "Web Search":
                st.session_state.mode = "MATLAB Troubleshooting"
            else:
                st.session_state.mode = "Web Search"

        # Display current mode
        st.markdown(f"<p style='text-align: center; color: gray;'>Current mode: <strong>{st.session_state.mode}</strong></p>", unsafe_allow_html=True)


        if st.button("➕ New Chat"):
            try:
                chat_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                res = requests.post(f"{BACKEND_URL}/create-chat", json={
                    "user_id": user_id,
                    "chat_name": chat_name
                })
                if res.status_code == 200:
                    chat_data = res.json()
                    new_id = chat_data["chat_id"]
                    st.session_state.chat_sessions[new_id] = {
                        "chat_name": chat_data["chat_name"],
                        "messages": []
                    }
                    st.session_state.current_chat_id = new_id
                    st.rerun()
                else:
                    st.error("Failed to create new chat.")
            except requests.exceptions.RequestException:
                st.error("Could not reach server to create new chat.")

        if st.button("📊 Image Troubleshooting"):
            st.session_state.page = "image_upload"
            st.rerun()


        if st.button("🗑️ Delete Chat"):
            chat_id = st.session_state.current_chat_id
            try:
                res = requests.post(f"{BACKEND_URL}/delete-chat", json={
                    "user_id": user_id,
                    "chat_id": chat_id
                })
                if res.status_code == 200:
                    del st.session_state.chat_sessions[chat_id]
                    if st.session_state.chat_sessions:
                        st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
                        st.rerun() # Rerun to update the selected chat
                    else:
                        # Create default if no chats left
                        new_id = str(uuid4())
                        st.session_state.chat_sessions[new_id] = {"chat_name": "Welcome Chat", "messages": []}
                        st.session_state.current_chat_id = new_id
                        st.rerun()
                else:
                    st.error("Failed to delete chat.")
            except requests.exceptions.RequestException:
                st.error("Server unreachable while deleting chat.")

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            clear_login_token()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if st.session_state.page == "image_upload":
        st.title("🧮 MATLAB Image Troubleshooting")

        uploaded_file = st.file_uploader("Upload an image of the MATLAB error or code", type=["png", "jpg", "jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded image", use_column_width=True)

            if st.button("Generate Answer from Image"):
                query = get_query_from_image(uploaded_file)
                if query:
                    with st.expander("🔍 Extracted Query", expanded=True):
                        st.code(query)

                    response = get_bot_response(query)

                    # Show Answer
                    st.subheader("🧠 Assistant's Answer")
                    st.info(response["answer"])  # Boxed answer

                    # Show Contributing Links
                    st.subheader("🔗 References")
                    if response["contributing_links"]:
                        links = get_top_unique_links(response["contributing_links"], 5)
                        for link in links:
                            st.markdown(f"- [{link}]({link})")
                    else:
                        st.warning("No references available.")


        st.button("🔙 Back to Chat", on_click=lambda: st.session_state.update({"page": "chat"}))
        st.stop()  # ⛔ Prevents the chat UI from rendering below


    # ---------------- Main Chat Display ----------------
    current_chat_id = st.session_state.current_chat_id
    chat_info = st.session_state.chat_sessions[current_chat_id]
    chat_history = chat_info.get("messages", [])

    for msg in chat_history:
        if "question" in msg and "answer" in msg:
            # User message
            with st.chat_message("user"):
                st.markdown(f"**You:** {msg['question']}")

            # Assistant message
            with st.chat_message("assistant"):
                # st.subheader("🧠 Assistant's Answer")
                if isinstance(msg["answer"], dict):
                    st.info(msg["answer"]["answer"])
                    links = msg["answer"].get("contributing_links", [])
                    if links:
                        st.subheader("🔗 References")
                        links = get_top_unique_links(links, 5)
                        for link in links:
                            st.markdown(f"- [{link}]({link})")
                    else:
                        pass
                else:
                    # Fallback in case answer is a plain string
                    st.info(msg["answer"])

    # --- Chat Input ---
    user_input = st.chat_input("Type your message...")

    if user_input:
    # Append user message
        st.session_state.chat_sessions[current_chat_id]["messages"].append({
            "question": user_input
        })

        with st.chat_message("user"):
            st.markdown(f"**You:** {user_input}")

        # Get and display bot response
        response = get_bot_response(user_input)
        st.session_state.chat_sessions[current_chat_id]["messages"][-1]["answer"] = response

        with st.chat_message("assistant"):
            # Display answer
            st.markdown("**Answer:**")
            st.info(response["answer"])  # Boxed answer

            # Display contributing links
            if response["contributing_links"]:
                st.markdown("**References:**")
                links = get_top_unique_links(response["contributing_links"], 5)
                for link in links:
                    st.markdown(f"- [{link}]({link})")
            else:
                pass