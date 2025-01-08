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


@st.cache_data
def fetch_user_input_player_stats(requested_player_name):
    logger.info(f"Fetching career stats for: {requested_player_name}")
    try:
        with st.spinner("Fetching career stats..."):
            url = f"{API_BASE_URL}/user_requested_player_career_stats/?player_name={requested_player_name}"
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
        fetch_user_input_player_stats_result = fetch_user_input_player_stats(user_input)
        similar_players_result = fetch_similar_players(user_input)

        if "error" in similar_players_result or "error" in fetch_user_input_player_stats_result:
            reply = (
                similar_players_result["error"]
                if "error" in similar_players_result
                else fetch_user_input_player_stats_result["error"]
            )
        else:
            # Prepare data for the response
            similar_players = [
                {
                    "player_name": player["player_name"],
                    "points_per_game": player["points_per_game"],
                    "assists_per_game": player["assists_per_game"],
                    "rebounds_per_game": player["rebounds_per_game"],
                    "similarity_score": player["similarity_score"],
                }
                for player in similar_players_result
            ]

            summary = f"{user_input} shares similarities with {', '.join([player['player_name'] for player in similar_players])} based on scoring and playing style."

            # Generate the detailed response
            reply = generate_similar_players_response(user_input, similar_players, summary)

        # Add the assistant's response to the chat history
        st.session_state["messages"].append({"role": "assistant", "content": reply})

        # Clear the input field
        st.session_state["user_input"] = ""


def generate_similar_players_response(player_name, similar_players, summary):
    prompt = f"Here are players similar to {player_name}:\n\n"
    prompt += "Player Comparison:\n"
    prompt += "Player               Points/Game   Assists/Game   Rebounds/Game   Similarity\n"
    prompt += "---------------------------------------------------------------------------\n"

    for player in similar_players:
        prompt += f"{player['player_name']: <20} {player['points_per_game']: <15} {player['assists_per_game']: <15} {player['rebounds_per_game']: <15} {player['similarity_score']:.2f}%\n"

    prompt += "\nSummary:\n"
    prompt += summary

    return prompt


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
