import streamlit as st
from streamlit_chat import message
import requests
import sys
from pathlib import Path

# Add the project root to PYTHONPATH, as Streamlit needs to run as "streamlit run app.py"
project_root = Path(__file__).resolve().parent.parent.parent  # Adjust to your project root
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.config import settings

REQUEST_TIMEOUT = 10

# Backend API URL
API_URL = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}/search_similar_players/"

st.title("NBA Player Similarity Chat")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! Type an NBA player's name to find similar players."}
    ]

# Display the chat messages
for msg in st.session_state["messages"]:
    message(msg["content"], is_user=(msg["role"] == "user"))

# Input for user to type the player's name
user_input = st.text_input("Your message:", key="user_input")

if st.button("Send"):
    if user_input.strip():
        # Add user message to the chat history
        st.session_state["messages"].append({"role": "user", "content": user_input.strip()})

        # Call the API with the player's name
        try:
            with st.spinner("Searching for similar players..."):  # Add spinner here
                response = requests.post(API_URL, json={"player_name": user_input.strip()}, timeout=REQUEST_TIMEOUT)
                
            if response.status_code == 200:
                # Successful response: add to chat history
                result = response.json()
                similar_players = "\n".join(
                    [f"- {player['player_name']} (Similarity Score: {player['similarity_score']:.2f})"
                     for player in result]
                )
                reply = f"Here are players similar to '{user_input}':\n{similar_players}"
            else:
                # Handle error response
                error_result = response.json()
                if "error" in error_result:
                    reply = error_result["error"]
                    if "matches" in error_result:
                        reply += "\nDid you mean:\n" + "\n".join(f"- {match}" for match in error_result["matches"])
                else:
                    reply = "Something went wrong. Please try again."
        except Exception as e:
            reply = f"Error connecting to the server: {e}"

        # Add the assistant's response to the chat history
        st.session_state["messages"].append({"role": "assistant", "content": reply})

        # Clear the input field for the next query
        st.rerun()