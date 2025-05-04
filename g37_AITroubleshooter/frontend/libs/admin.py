import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt

BACKEND_URL = "http://127.0.0.1:5000/"  # Ensure this matches your Flask server URL

def admin():
    # Authentication check
    if not (st.session_state.get("logged_in") and st.session_state.get("is_admin")):
        st.error("⛔️ Admins only. Please login as admin.")
        st.stop()

    st.title("🛠️ Admin Dashboard")

    # 1) Fetch all users from the Flask API
    users_res = requests.get(f"{BACKEND_URL}/admin/users")
    if users_res.status_code != 200:
        st.error("Failed to fetch users.")
        st.stop()
    users = users_res.json().get("users", [])  # [{ "user_id": "...", "username": "..." }, …]

    # 2) Build a flat list of all sessions by calling /history/<user_id>
    sessions = []
    for u in users:
        hist_res = requests.get(f"{BACKEND_URL}/history/{u['user_id']}")
        if hist_res.status_code != 200:
            continue
        hist = hist_res.json()
        for doc in hist:
            for chat in doc.get("chat_history", []):
                messages = chat.get("messages", [])
                if messages:
                    sessions.append({
                        "user_id": u["user_id"],
                        "username": u["username"],
                        "chat_id": chat["chat_id"],
                        "chat_name": chat["chat_name"],
                        "timestamp": messages[-1]["timestamp"],
                        "turns": len(messages)
                    })

    df = pd.DataFrame(sessions)

    # 3) Global metrics
    st.subheader("Global Statistics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", len(users))
    c2.metric("Total Chat Sessions", len(df))
    avg = round(len(df) / len(users), 2) if users else 0
    c3.metric("Avg Sessions/User", avg)

    # 4) Sessions‑per‑day chart
    st.subheader("Sessions Over Time")
    if not df.empty:
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        ts = df.groupby("date").size().reset_index(name="count")
        fig, ax = plt.subplots()
        ax.plot(ts["date"], ts["count"])
        ax.set_xlabel("Date")
        ax.set_ylabel("Sessions")
        ax.tick_params(axis='x', labelrotation=90)  # :contentReference[oaicite:0]{index=0}
        st.pyplot(fig)
    else:
        st.info("No session data available to display.")
        
    # Bar chart of top users
    st.subheader("Top Users by # of Sessions")
    user_counts = df["username"].value_counts().head(10)
    fig2, ax2 = plt.subplots()
    ax2.bar(user_counts.index, user_counts.values)
    ax2.set_title("Top 10 Users") 
    ax2.set_xlabel("Username")
    ax2.set_ylabel("Session Count")
    ax2.tick_params(axis='x', labelrotation=90)  # rotate labels :contentReference[oaicite:2]{index=2}
    st.pyplot(fig2)
    

    # 5) Per‑user table & export
    st.subheader("Per‑User Summary")
    if not df.empty:
        user_stats = df.groupby("username").agg(
            sessions=("chat_id", "nunique"),
            last_activity=("date", "max")
        ).reset_index()
        st.dataframe(user_stats)
        csv = user_stats.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "user_stats.csv", "text/csv")
    else:
        st.info("No user statistics available.")

    # 6) Filter by user/date/keyword
    st.subheader("Filter Sessions")
    ufilter = st.selectbox("User", ["All"] + [u["username"] for u in users])
    if not df.empty:
         # Convert 'timestamp' column to datetime if not already
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        # Get date range from user input
        date_range = st.date_input("Date range", [df["date"].min(), df["date"].max()])
        key = st.text_input("Keyword in messages")

        # Convert date_range to Pandas Timestamps
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])

        filt = df.copy()
        if ufilter != "All":
            filt = filt[filt["username"] == ufilter]
        filt = filt[(filt["timestamp"] >= start_date) & (filt["timestamp"] <= end_date)]
        if key:
            filt = filt[filt.apply(lambda r: key.lower() in json.dumps(r, default=str).lower(), axis=1)]
        st.write(f"Showing {len(filt)} sessions")
        st.dataframe(filt)
    else:
        st.info("No sessions available for filtering.")

    # 7) Raw JSON download
    st.subheader("Download Raw Logs")
    raw_res = requests.get(f"{BACKEND_URL}/admin/raw_logs")
    if raw_res.status_code == 200:
        raw = raw_res.text
        st.download_button("Download JSON", raw, "logs.json", "application/json")
    else:
        st.error("Failed to fetch raw logs.")

    st.success("✅ Admin analytics loaded.")
    
    # 8) View individual chat sessions with Q&A expanders
    st.subheader("🔍 View Chat Session Details")

    if not df.empty:
        # 1) Select user
        selected_user = st.selectbox(
            "Select User", 
            df["username"].unique()
        )  # st.selectbox for choosing items :contentReference[oaicite:2]{index=2}

        # 2) Filter sessions for that user
        user_sessions = df[df["username"] == selected_user]

        if not user_sessions.empty:
            # 3) Select one of their sessions
            selected_session = st.selectbox(
                "Select Session", 
                user_sessions["chat_name"].tolist()
            )

            # 4) Look up chat_id & user_id
            row = user_sessions[user_sessions["chat_name"] == selected_session].iloc[0]
            chat_id = row["chat_id"]
            user_id = row["user_id"]

            # 5) Fetch full history once
            hist_res = requests.get(f"{BACKEND_URL}/hist/{user_id}")  # HTTP fetch :contentReference[oaicite:3]{index=3}
            if hist_res.status_code == 200:
                history = hist_res.json()  # parse JSON :contentReference[oaicite:4]{index=4}

                # 6) Find the matching chat_history entry
                for doc in history:
                    for chat in doc.get("chat_history", []):
                        if chat["chat_id"] == chat_id:
                            st.markdown(f"### Chat: {chat['chat_name']}")
                            
                            # 7) Show each turn’s Q & A in an expander
                            for i, msg in enumerate(chat.get("messages", []), start=1):  # enumerate turns :contentReference[oaicite:5]{index=5}
                                ts = msg.get("timestamp", "")
                                with st.expander(f"Turn {i} — {ts}"):              # st.expander usage :contentReference[oaicite:6]{index=6}
                                    st.markdown(f"**Question:** {msg.get('question','')}")  
                                    st.markdown(f"**Answer:** {msg.get('answer','')}")

            else:
                st.error("Failed to fetch chat history.")
        else:
            st.info("No sessions found for the selected user.")
    else:
        st.info("No session data available.")
