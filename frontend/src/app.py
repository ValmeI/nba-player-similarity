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
st.set_page_config(layout="wide")  # Enables wide screen mode


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": settings.STREAMLIT_INITIAL_MESSAGE}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""


def display_chat_messages():
    # enumerate to get unique key for each message by combining the role
    for i, msg in enumerate(st.session_state["messages"]):
        if msg.get("type") == "html":
            # Render HTML messages safely
            st.markdown(msg["content"], unsafe_allow_html=True)
        else:
            # Render plain text messages
            message(msg["content"], is_user=(msg["role"] == "user"), key=f"{msg['role']}_{i}")


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


def get_user_input_stats(user_input):
    user_stats_result = fetch_user_input_player_stats(user_input)
    logger.debug(f"User stats result: {user_stats_result} for user input: {user_input}")
    if "error" in user_stats_result:
        return {"error": user_stats_result["error"]}
    else:
        user_stats_result_player = user_stats_result[0]
        return [
            {
                "player_name": user_stats_result_player["searched_player"]["player_name"],
                "points_per_game": round(user_stats_result_player["points_per_game"], 1),
                "assists_per_game": round(
                    user_stats_result_player["assists_per_game"],
                ),
                "rebounds_per_game": round(user_stats_result_player["rebounds_per_game"]),
                "blocks_per_game": round(user_stats_result_player["blocks_per_game"]),
                "steals_per_game": round(user_stats_result_player["steals_per_game"]),
                "true_shooting_percentage": user_stats_result_player["true_shooting_percentage"],
                "field_goal_percentage": user_stats_result_player["field_goal_percentage"],
                "three_point_percentage": user_stats_result_player["three_point_percentage"],
                "free_throw_percentage": user_stats_result_player["free_throw_percentage"],
                "last_played_season": user_stats_result_player["last_played_season"],
                "last_played_age": user_stats_result_player["last_played_age"],
                "total_seasons": user_stats_result_player["total_seasons"],
            }
        ]


def get_similar_player_stats(user_stats):
    similar_players_result = fetch_similar_players(user_stats[0]["player_name"])
    logger.debug(f"Similar players result: {similar_players_result} for player: {user_stats[0]['player_name']}")
    if "error" in similar_players_result:
        return {"error": similar_players_result["error"]}
    else:
        return [
            {
                "player_name": player["player_name"],
                "points_per_game": round(player["points_per_game"], 1),
                "assists_per_game": round(
                    player["assists_per_game"],
                ),
                "rebounds_per_game": round(player["rebounds_per_game"]),
                "blocks_per_game": round(player["blocks_per_game"]),
                "steals_per_game": round(player["steals_per_game"]),
                "true_shooting_percentage": player["true_shooting_percentage"],
                "field_goal_percentage": player["field_goal_percentage"],
                "three_point_percentage": player["three_point_percentage"],
                "free_throw_percentage": player["free_throw_percentage"],
                "last_played_season": player["last_played_season"],
                "last_played_age": player["last_played_age"],
                "total_seasons": player["total_seasons"],
                "similarity_score": player["similarity_score"] * 100,
            }
            for player in similar_players_result
        ]


def format_stats_for_display(user_stats, similar_player_stats):
    summary = f"{user_stats[0]['player_name']} shares similarities with {', '.join([player['player_name'] for player in similar_player_stats])} based on scoring and playing style."

    html_content = f"""
        <h2>Here are players similar to {user_stats[0]['player_name']}:</h2>
        <h3>User Input Player Stats:</h3>
        <table border='1'>
            <tr>
                <th>Player</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting Percentage</th>
                <th>Field Goal Percentage</th>
                <th>3 Point Percentage</th>
                <th>Free Throw Percentage</th>
                <th>Last Played Season</th>
                <th>Last Played Age</th>
                <th>Total Seasons</th>
            </tr>
            {''.join([
                f'<tr><td>{player["player_name"]}</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.2f}%</td>'
                f'<td>{player["free_throw_percentage"]:.2f}%</td>'
                f'<td>{player["field_goal_percentage"]:.2f}%</td>'
                f'<td>{player["three_point_percentage"]:.2f}%</td>'
                f'<td>{player["last_played_season"]}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td></tr>'
                for player in user_stats
            ])}
        </table>
        <h3>Similar Players Stats:</h3>
        <table border='1'>
            <tr>
                <th>Player</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting Percentage</th>
                <th>Field Goal Percentage</th>
                <th>3 Point Percentage</th>
                <th>Free Throw Percentage</th>
                <th>Last Played Season</th>
                <th>Last Played Age</th>
                <th>Total Seasons</th>
                <th>Similarity Score</th>
            </tr>
            {''.join([
                f'<tr><td>{player["player_name"]}</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.2f}%</td>'
                f'<td>{player["field_goal_percentage"]:.2f}%</td>'
                f'<td>{player["three_point_percentage"]:.2f}%</td>'
                f'<td>{player["free_throw_percentage"]:.2f}%</td>'
                f'<td>{player["last_played_season"]}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td>'
                f'<td>{player["similarity_score"]:.2f}%</td></tr>'
                for player in similar_player_stats
            ])}
        </table>
        <h3>Summary:</h3>
        <p>{summary}</p>
    """
    return html_content


def handle_user_input():
    user_input = st.session_state.user_input.strip()
    logger.info(f"User input received: {user_input}")
    if user_input:
        # Add user message to the chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})

        user_stats = get_user_input_stats(user_input)
        similar_player_stats = get_similar_player_stats(user_stats)

        if "error" in user_stats or "error" in similar_player_stats:
            reply = user_stats["error"] if "error" in user_stats else similar_player_stats["error"]
            # Add plain text response for errors
            st.session_state["messages"].append({"role": "assistant", "content": reply})
        else:
            # Generate the detailed response
            html_reply = format_stats_for_display(user_stats, similar_player_stats)

            # Add HTML response
            st.session_state["messages"].append({"role": "assistant", "content": html_reply, "type": "html"})

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


if __name__ == "__main__":
    main()
