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
from streamlit_frontend.src.llm import generate_analysis
from streamlit_frontend.src.intent_parser import parse_user_intent
from streamlit_frontend.src.utils import fetch_versions, get_client_ip, get_geolocation

API_BASE_URL = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}"
st.set_page_config(layout="wide")  # Enables wide screen mode


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": settings.STREAMLIT_INITIAL_MESSAGE}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""

    if "client_ip" not in st.session_state:
        st.session_state["client_ip"] = get_client_ip()

    if "client_geolocation" not in st.session_state:
        st.session_state["client_geolocation"] = get_geolocation(st.session_state["client_ip"])

    geolocation = st.session_state["client_geolocation"]
    log_message = (
        f"🌍 User Location Info: "
        f" - 🏷️ IP Address: {st.session_state['client_ip']} "
        f" - 🌍 Country: {geolocation.get('country', 'Unknown')} "
        f" - 🏙️ City: {geolocation.get('city', 'Unknown')} "
        f" - 📍 Region: {geolocation.get('region', 'Unknown')} "
        f" - 🌐 ISP: {geolocation.get('isp', 'Unknown')} "
        f" - 🗺️ Coordinates: {geolocation.get('latitude', 'Unknown')}, {geolocation.get('longitude', 'Unknown')} "
        f" - 🌍 Continent: {geolocation.get('continent', 'Unknown')} "
        f" - 🕒 Timezone: {geolocation.get('timezone', 'Unknown')} "
        f" - 💱 Currency: {geolocation.get('currency', 'Unknown')} "
        f" - 🏢 Organization: {geolocation.get('org', 'Unknown')}"
    )
    logger.info(log_message)


def display_chat_messages():
    # enumerate to get unique key for each message by combining the role
    for i, msg in enumerate(st.session_state["messages"]):
        if msg.get("type") == "html":
            # Render HTML messages safely
            st.markdown(msg["content"], unsafe_allow_html=True)
        else:
            # Render plain text messages
            message(msg["content"], is_user=(msg["role"] == "user"), key=f"{msg['role']}_{i}")


@st.cache_data
def fetch_similar_players(requested_player_name, position=None, era=None):
    # Capitalize the player name
    requested_player_name = requested_player_name.title()
    logger.info(f"Fetching similar players for: {requested_player_name} (position={position}, era={era})")
    try:
        with st.spinner("Searching for similar players..."):
            params = {"player_name": requested_player_name}
            if position:
                params["position"] = position
            if era:
                params["era"] = era
            response = requests.get(
                f"{API_BASE_URL}/search_similar_players/",
                params=params,
                timeout=settings.API_REQUEST_TIMEOUT,
            )
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the server: {e}"}


@st.cache_data
def fetch_user_input_player_stats(requested_player_name):
    # Capitalize the player name
    requested_player_name = requested_player_name.title()
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
                "player_name": user_stats_result_player["searched_player"]["player_name"].title(),
                "points_per_game": user_stats_result_player["points_per_game"],
                "assists_per_game": user_stats_result_player["assists_per_game"],
                "rebounds_per_game": user_stats_result_player["rebounds_per_game"],
                "blocks_per_game": user_stats_result_player["blocks_per_game"],
                "steals_per_game": user_stats_result_player["steals_per_game"],
                "true_shooting_percentage": user_stats_result_player["true_shooting_percentage"] * 100,
                "field_goal_percentage": user_stats_result_player["field_goal_percentage"],
                "three_point_percentage": user_stats_result_player["three_point_percentage"],
                "free_throw_percentage": user_stats_result_player["free_throw_percentage"],
                "last_played_season": user_stats_result_player["last_played_season"],
                "last_played_age": user_stats_result_player["last_played_age"],
                "total_seasons": user_stats_result_player["total_seasons"],
            }
        ]


def get_similar_player_stats(user_stats, position=None, era=None):
    if "error" in user_stats:
        return user_stats
    similar_players_result = fetch_similar_players(user_stats[0]["player_name"], position=position, era=era)
    logger.debug(f"Similar players result: {similar_players_result} for player: {user_stats[0]['player_name']}")
    if isinstance(similar_players_result, dict) or not similar_players_result:
        error_msg = similar_players_result.get("error") if isinstance(similar_players_result, dict) else None
        if not error_msg:
            active_filters = []
            if position:
                active_filters.append(f"position: {position}")
            if era:
                active_filters.append(f"era: {era}")
            filter_note = f" with filters ({', '.join(active_filters)})" if active_filters else ""
            error_msg = f"No similar players found{filter_note}. Try removing some filters or broadening your search."
        return {"error": error_msg}
    else:
        return [
            {
                "player_name": player["player_name"].title(),
                "points_per_game": player["points_per_game"],
                "assists_per_game": player["assists_per_game"],
                "rebounds_per_game": player["rebounds_per_game"],
                "blocks_per_game": player["blocks_per_game"],
                "steals_per_game": player["steals_per_game"],
                "true_shooting_percentage": player["true_shooting_percentage"] * 100,
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


def format_stats_for_display(user_stats, similar_player_stats, position=None, era=None):
    llm_summary = generate_analysis(user_stats, similar_player_stats)

    active_filters = []
    if position:
        active_filters.append(f"Position: {position}")
    if era:
        active_filters.append(f"Era: {era}")
    filter_html = f"<p><strong>Active Filters:</strong> {', '.join(active_filters)}</p>" if active_filters else ""

    html_content = f"""
        <h2>Here are players similar to {user_stats[0]['player_name']}:</h2>
        {filter_html}
        <h3>{user_stats[0]['player_name']} Career Stats:</h3>
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
                f'<td>{player["field_goal_percentage"]:.2f}%</td>'
                f'<td>{player["three_point_percentage"]:.2f}%</td>'
                f'<td>{player["free_throw_percentage"]:.2f}%</td>'
                f'<td>{player["last_played_season"]}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td></tr>'
                for player in user_stats
            ])}
        </table>
        <h3>Similar Career Players Stats:</h3>
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
        <h3>Summary by LLM:</h3>
        <p>{llm_summary}</p>
    """
    return html_content


def handle_user_input():
    user_input = st.session_state.user_input.strip()
    logger.info(f"User input received: {user_input}")
    if user_input:
        # Add user message to the chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Parse user intent using LLM
        intent = parse_user_intent(user_input)
        logger.info(f"Parsed intent: {intent}")

        # Handle edge case: no player name identified
        if not intent["player_name"]:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "Please provide a player name to find similar players.",
            })
            st.session_state["user_input"] = ""
            return

        # Handle edge case: multiple players mentioned
        if intent["multiple_players"]:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"Currently only single player comparison is supported. Showing results for {intent['player_name']}.",
            })

        player_name = intent["player_name"]
        position = intent["position"]
        era = intent["era"]

        user_stats = get_user_input_stats(player_name)
        similar_player_stats = get_similar_player_stats(user_stats, position=position, era=era)

        if "error" in user_stats or "error" in similar_player_stats:
            reply = user_stats["error"] if "error" in user_stats else similar_player_stats["error"]
            st.session_state["messages"].append({"role": "assistant", "content": reply})
        else:
            html_reply = format_stats_for_display(user_stats, similar_player_stats, position=position, era=era)
            st.session_state["messages"].append({"role": "assistant", "content": html_reply, "type": "html"})

        # Clear the input field
        st.session_state["user_input"] = ""


def display_versions():
    frontend_version, backend_version = fetch_versions()

    # Display versions in the header or footer
    header = f"""
        <div style="text-align: right; margin-bottom: 20px;">
            <p>Frontend Version: {frontend_version} | Backend Version: {backend_version}</p>
        </div>
        """
    st.markdown(header, unsafe_allow_html=True)


def main():
    """Main function."""
    logger.info("Starting the application")
    st.title(settings.STREAMLIT_TITLE)
    display_versions()
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
    # TODO: at some point move all to app/ dir for easier deployment on docker and config management with app/ dir
