import sys
from pathlib import Path
import requests
import streamlit as st
from streamlit_chat import message


project_root = Path(__file__).resolve().parent.parent.parent

# Add project root to PYTHONPATH as streamlit wants to run as "streamlit runapp.py" and not module "python -m  runapp.py"
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from shared.config import settings
from shared.utils.app_logger import logger


API_BASE_URL = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}"


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": settings.STREAMLIT_INITIAL_MESSAGE}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""


def display_chat_messages():
    # enumerate to get unique key for each message by combining the role
    # To avoid StreamlitDuplicateElementId error
    for i, msg in enumerate(st.session_state["messages"]):
        message(msg["content"], is_user=(msg["role"] == "user"), key=f"{msg['role']}_{i}")


@st.cache_data
def fetch_similar_players(requested_player_name):
    logger.info(f"Fetching similar players for: {requested_player_name}")
    try:
        with st.spinner("Searching for similar players..."):
            url = f"{API_BASE_URL}/search_similar_players/?player_name={requested_player_name}"
            response = requests.get(url, timeout=settings.API_REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the server: {e}"}


def handle_user_input():
    user_input = st.session_state.user_input.strip()
    logger.info(f"User input received: {user_input}")
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
    logger.info("Starting the application")
    st.title(settings.STREAMLIT_TITLE)
    initialize_session_state()
    display_chat_messages()

    user_input = st.text_input(
        "Your message:", key="user_input", placeholder=settings.STREAMLIT_INPUT_PLACEHOLDER, on_change=handle_user_input
    )

    # Trigger the function manually if new input is detected
    if user_input and st.session_state["user_input"] != user_input:
        handle_user_input()

    # streamlit run /home/valme/git/nba-player-similarity/frontend/src/app.py --server.headless true


if __name__ == "__main__":
    main()
