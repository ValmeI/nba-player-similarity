import sys
from pathlib import Path
import requests
import streamlit as st
from streamlit_chat import message


project_root = Path(__file__).resolve().parent.parent.parent

# Add project root to PYTHONPATH
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.config import settings
from shared.utils.app_logger import logger


REQUEST_TIMEOUT = 10  # Timeout for API requests
INITIAL_MESSAGE = "Hi! Type an NBA player's name to find similar players and press Enter..."
API_URL = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}/search_similar_players/"
TITLE = "NBA Player Similarity Chat"
INPUT_PLACEHOLDER = "Type a NBA player's name and press Enter..."


def initialize_session_state():
    """Initialize session state for chat history and user input."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": INITIAL_MESSAGE}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""

def display_chat_messages():
    for msg in st.session_state["messages"]:
        message(msg["content"], is_user=(msg["role"] == "user"))

def fetch_similar_players(player_name):
    logger.info('Fetching similar players for: %s', player_name)
    try:
        with st.spinner("Searching for similar players..."):
            response = requests.post(API_URL, json={"player_name": player_name}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the server: {e}"}

def handle_user_input():
    user_input = st.session_state.user_input.strip()
    logger.info('User input received: %s', user_input)
    if user_input:
        # Add user message to the chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Call the API with the player's name
        result = fetch_similar_players(user_input)

        if "error" in result:
            reply = result["error"]
        else:
            similar_players = "\n".join(
                [f"- {player['player_name']} (Similarity Score: {player['similarity_score']:.2f})" for player in result]
            )
            reply = f"Here are players similar to '{user_input}':\n{similar_players}"

        # Add the assistant's response to the chat history
        st.session_state["messages"].append({"role": "assistant", "content": reply})

        # Clear the input field
        st.session_state["user_input"] = ""

def main():
    """Main function."""
    logger.info('Starting the application')
    st.title(TITLE)
    initialize_session_state()
    display_chat_messages()

    user_input = st.text_input(
        "Your message:",
        key="user_input",
        placeholder=INPUT_PLACEHOLDER,
        on_change=handle_user_input
    )

    # Trigger the function manually if new input is detected
    if user_input and st.session_state["user_input"] != user_input:
        handle_user_input()

if __name__ == "__main__":
    main()
