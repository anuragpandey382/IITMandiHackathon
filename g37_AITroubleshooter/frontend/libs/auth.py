import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:5000/"  # Update this if needed

def save_login_token(user_id):
    st.query_params["user_id"] = user_id

def load_login_token():
    return st.query_params.get("user_id", None)

def clear_login_token():
    st.query_params.clear()

def is_logged_in():
    return st.session_state.get("logged_in", False)

def check_auth():
    if "logged_in" not in st.session_state:
        user_id = load_login_token()
        if user_id:
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
        else:
            st.session_state.logged_in = False

def login():
    st.title("🔐 Login / Sign Up")

    auth_mode = st.radio("Select mode", ["Login", "Sign Up", "Admin"], horizontal=True)

    with st.form("auth_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(auth_mode)

        if submitted:
            if auth_mode == "Admin":
                # Temporary hardcoded admin credentials
                ADMIN_USERNAME = "abc"
                ADMIN_PASSWORD = "pqr"

                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    # Clear session state and initialize for admin
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.session_state.logged_in = True
                    st.session_state.user_id = "admin"
                    st.session_state.is_admin = True
                    save_login_token("admin")
                    st.success("Admin login successful!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials.")
            else:
                endpoint = "/auth" if auth_mode == "Login" else "/signup"
                try:
                    res = requests.post(f"{BACKEND_URL}{endpoint}", json={"username": username, "password": password})
                    res_json = res.json()

                    if res.status_code == 200 and res_json.get("status") == "success":
                        user_id = res_json["user_id"]
                        # Clear session state and initialize for the new user
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        save_login_token(user_id)
                        st.success(f"{auth_mode} successful!")
                        st.rerun()
                    else:
                        st.error(res_json.get("message", "Something went wrong"))
                except requests.exceptions.RequestException as e:
                    st.error("Connection error.")
                    st.exception(e)
