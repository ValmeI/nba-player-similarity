import html
import sys
from pathlib import Path
import requests
import streamlit as st

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
st.set_page_config(layout="wide", page_title="NBA Player Similarity Finder", page_icon="\U0001f3c0")


def initialize_session_state():
    if "messages" not in st.session_state:
        # Replace literal \n from env with markdown line breaks (two trailing spaces + newline)
        initial_message = settings.STREAMLIT_INITIAL_MESSAGE.replace("\\n", "  \n")
        st.session_state["messages"] = [{"role": "assistant", "content": initial_message}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "last_processed_input" not in st.session_state:
        st.session_state["last_processed_input"] = ""

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


def _render_avatar(role):
    """Return an HTML avatar circle for the given role."""
    if role == "user":
        return '''<div style="width:36px; height:36px; border-radius:50%; background:#C9082A;
                    display:flex; align-items:center; justify-content:center; flex-shrink:0;
                    font-size:16px; box-shadow:0 1px 4px rgba(0,0,0,0.12);">\U0001f464</div>'''
    else:
        return '''<div style="width:36px; height:36px; border-radius:50%; background:#17408B;
                    display:flex; align-items:center; justify-content:center; flex-shrink:0;
                    font-size:16px; box-shadow:0 1px 4px rgba(0,0,0,0.12);">\U0001f3c0</div>'''


def display_chat_messages():
    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg["content"]
        is_html = msg.get("type") == "html"

        if is_html:
            # HTML results render full-width via st.html (no tag stripping)
            st.html(content)
        else:
            # Render text messages as styled chat bubbles with avatars
            escaped = html.escape(content)
            escaped = escaped.replace("\n", "<br>")
            avatar = _render_avatar(role)

            if role == "user":
                bubble_html = f'''
                <div style="display:flex; justify-content:flex-end; align-items:flex-start; gap:10px; margin:0.6rem 0;">
                    <div style="background:#17408B; color:#fff; border-radius:16px 4px 16px 16px;
                                padding:0.8rem 1.1rem; max-width:70%; font-size:0.95rem;
                                box-shadow:0 2px 8px rgba(23,64,139,0.2); line-height:1.5;">
                        {escaped}
                    </div>
                    {avatar}
                </div>'''
            else:
                bubble_html = f'''
                <div style="display:flex; justify-content:flex-start; align-items:flex-start; gap:10px; margin:0.6rem 0;">
                    {avatar}
                    <div style="background:#ffffff; color:#1a202c; border:1px solid #e2e8f0;
                                border-radius:4px 16px 16px 16px; padding:0.8rem 1.1rem;
                                max-width:70%; font-size:0.95rem;
                                box-shadow:0 1px 4px rgba(0,0,0,0.05); line-height:1.5;">
                        {escaped}
                    </div>
                </div>'''

            st.markdown(bubble_html, unsafe_allow_html=True)


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
            response = requests.get(
                f"{API_BASE_URL}/user_requested_player_career_stats/",
                params={"player_name": requested_player_name},
                timeout=settings.API_REQUEST_TIMEOUT,
            )
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the server: {e}"}


def get_user_input_stats(user_input):
    user_stats_result = fetch_user_input_player_stats(user_input)
    logger.debug(f"User stats result: {user_stats_result} for user input: {user_input}")
    if "error" in user_stats_result:
        return {"error": user_stats_result["error"]}
    if not user_stats_result:
        return {"error": "No stats found for the requested player."}
    user_stats_result_player = user_stats_result[0]
    return [
        {
            "player_name": user_stats_result_player["searched_player"]["player_name"].title(),
            "position": user_stats_result_player.get("position", "Unknown"),
            "points_per_game": user_stats_result_player["points_per_game"],
            "assists_per_game": user_stats_result_player["assists_per_game"],
            "rebounds_per_game": user_stats_result_player["rebounds_per_game"],
            "blocks_per_game": user_stats_result_player["blocks_per_game"],
            "steals_per_game": user_stats_result_player["steals_per_game"],
            "true_shooting_percentage": (user_stats_result_player["true_shooting_percentage"] or 0) * 100,
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
                "position": player.get("position", "Unknown"),
                "points_per_game": player["points_per_game"],
                "assists_per_game": player["assists_per_game"],
                "rebounds_per_game": player["rebounds_per_game"],
                "blocks_per_game": player["blocks_per_game"],
                "steals_per_game": player["steals_per_game"],
                "true_shooting_percentage": (player["true_shooting_percentage"] or 0) * 100,
                "field_goal_percentage": player["field_goal_percentage"],
                "three_point_percentage": player["three_point_percentage"],
                "free_throw_percentage": player["free_throw_percentage"],
                "last_played_season": player["last_played_season"],
                "last_played_age": player["last_played_age"],
                "total_seasons": player["total_seasons"],
                "similarity_score": (player["similarity_score"] or 0) * 100,
            }
            for player in similar_players_result
        ]


def format_stats_for_display(user_stats, similar_player_stats, llm_summary, position=None, era=None):
    active_filters = []
    if position:
        active_filters.append(f"Position: {position}")
    if era:
        active_filters.append(f"Era: {era}")

    def similarity_class(score):
        return "nba-similarity-high" if score >= 98 else "nba-similarity-mid"

    filter_badges = ''.join(
        f'<span class="nba-filter-badge">{html.escape(f)}</span>' for f in active_filters
    ) if active_filters else ""
    filter_html_styled = f"<p>{filter_badges}</p>" if filter_badges else ""

    escaped_heading_name = html.escape(user_stats[0]['player_name'])
    escaped_llm_summary = html.escape(llm_summary)

    html_content = f"""
        <div class="nba-results-card">
        <h2>Players similar to {escaped_heading_name}</h2>
        {filter_html_styled}
        <h3>{escaped_heading_name} Career Stats</h3>
        <table class="nba-table">
            <tr>
                <th>Player</th>
                <th>Position</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting %</th>
                <th>Field Goal %</th>
                <th>3 Point %</th>
                <th>Free Throw %</th>
                <th>Last Season</th>
                <th>Last Age</th>
                <th>Total Seasons</th>
            </tr>
            {''.join([
                f'<tr><td>{html.escape(str(player["player_name"]))}</td>'
                f'<td>{html.escape(str(player["position"]))}</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.1f}%</td>'
                f'<td>{player["field_goal_percentage"]:.1f}%</td>'
                f'<td>{player["three_point_percentage"]:.1f}%</td>'
                f'<td>{player["free_throw_percentage"]:.1f}%</td>'
                f'<td>{html.escape(str(player["last_played_season"]))}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td></tr>'
                for player in user_stats
            ])}
        </table>
        <h3>Similar Players</h3>
        <table class="nba-table">
            <tr>
                <th>Player</th>
                <th>Position</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting %</th>
                <th>Field Goal %</th>
                <th>3 Point %</th>
                <th>Free Throw %</th>
                <th>Last Season</th>
                <th>Last Age</th>
                <th>Total Seasons</th>
                <th>Similarity</th>
            </tr>
            {''.join([
                f'<tr><td>{html.escape(str(player["player_name"]))}</td>'
                f'<td>{html.escape(str(player["position"]))}</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.1f}%</td>'
                f'<td>{player["field_goal_percentage"]:.1f}%</td>'
                f'<td>{player["three_point_percentage"]:.1f}%</td>'
                f'<td>{player["free_throw_percentage"]:.1f}%</td>'
                f'<td>{html.escape(str(player["last_played_season"]))}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td>'
                f'<td class="{similarity_class(player["similarity_score"])}">{player["similarity_score"]:.1f}%</td></tr>'
                for player in similar_player_stats
            ])}
        </table>
        <h3>Analysis</h3>
        <div class="nba-summary">{escaped_llm_summary}</div>
        </div>
    """
    return html_content


def handle_user_input():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return

    # Guard against double-firing: skip if this input was already processed
    if st.session_state["last_processed_input"] == user_input:
        return
    st.session_state["last_processed_input"] = user_input

    logger.info(f"User input received: {user_input}")

    # Add user message to the chat history
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Parse user intent using LLM
    with st.spinner("Understanding your request..."):
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
        with st.spinner("Generating analysis..."):
            llm_summary = generate_analysis(user_stats, similar_player_stats)
        html_reply = format_stats_for_display(user_stats, similar_player_stats, llm_summary, position=position, era=era)
        st.session_state["messages"].append({"role": "assistant", "content": html_reply, "type": "html"})

    # Clear the input field
    st.session_state["user_input"] = ""


def get_version_string():
    frontend_version, backend_version = fetch_versions()
    return f"v{frontend_version} | API v{backend_version}"


def inject_nba_theme():
    """Inject global NBA-themed CSS."""
    st.markdown("""
    <style>
        /* === Font === */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* === Page background === */
        .stApp {
            background-color: #f4f4f4;
        }
        .block-container {
            padding-top: 1rem !important;
        }

        /* === Header banner === */
        .nba-header {
            background: linear-gradient(135deg, #17408B 0%, #1a4fa0 50%, #17408B 100%);
            padding: 2rem 1.5rem 1.2rem 1.5rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px rgba(23, 64, 139, 0.35);
        }
        .nba-header h1 {
            color: #ffffff !important;
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .nba-header .nba-subtitle {
            color: rgba(255, 255, 255, 0.85) !important;
            font-size: 1rem;
            margin: 0.3rem 0 0 0;
        }
        .nba-header .nba-version {
            color: rgba(255, 255, 255, 0.45) !important;
            font-size: 0.72rem;
            margin: 0.6rem 0 0 0;
        }


        /* === Input styling === */
        .stTextInput label {
            font-weight: 600;
            color: #17408B;
        }
        .stTextInput input {
            border: 2px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            background: #ffffff !important;
        }
        .stTextInput input:focus {
            border-color: #17408B !important;
            box-shadow: 0 0 0 3px rgba(23, 64, 139, 0.12) !important;
        }
        /* Kill Streamlit's default focus wrapper border */
        .stTextInput div[data-baseweb] {
            border: none !important;
            box-shadow: none !important;
        }
        .stTextInput input::placeholder {
            color: #a0aec0;
        }

        /* === Scrollbar === */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #17408B; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #C9082A; }

        /* === Footer === */
        .nba-footer {
            text-align: center;
            color: #a0aec0;
            font-size: 0.78rem;
            padding: 1.5rem 0 0.5rem 0;
            border-top: 1px solid #e2e8f0;
            margin-top: 2rem;
        }

        /* === Hide Streamlit chrome === */
        #MainMenu, .stDeployButton, [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
            display: none !important;
        }
        header[data-testid="stHeader"] { display: none !important; }
        footer { visibility: hidden; }

        /* === NBA Results Card (used by format_stats_for_display) === */
        .nba-results-card { background:#fff; border-radius:12px; padding:24px 28px; box-shadow:0 2px 12px rgba(0,0,0,0.07); }
        .nba-results-card h2 { color:#17408B; font-size:1.5rem; font-weight:700; margin:0 0 4px 0; border-bottom:3px solid #C9082A; padding-bottom:10px; display:inline-block; }
        .nba-results-card h3 { color:#2d3748; font-size:1.1rem; font-weight:600; margin:20px 0 8px 0; }
        .nba-table { border-collapse:collapse; width:100%; font-size:13px; margin:8px 0 16px 0; box-shadow:0 1px 6px rgba(0,0,0,0.06); border-radius:8px; overflow:hidden; }
        .nba-table th { background:linear-gradient(180deg,#C9082A 0%,#a8061f 100%); color:#fff; padding:10px; text-align:center; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.3px; border:none; white-space:nowrap; }
        .nba-table td { padding:9px 10px; text-align:center; border-bottom:1px solid #edf2f7; color:#2d3748; }
        .nba-table tr:nth-child(even) { background:#fafbfc; }
        .nba-table tr:hover { background:#edf2f7; }
        .nba-table td:first-child { text-align:left; font-weight:600; color:#17408B; }
        .nba-filter-badge { display:inline-block; background:linear-gradient(135deg,#17408B,#1a4fa0); color:#fff; padding:4px 14px; border-radius:16px; font-size:12px; font-weight:500; margin:2px 4px; }
        .nba-similarity-high { color:#276749; font-weight:700; background:#f0fff4; padding:2px 8px; border-radius:10px; }
        .nba-similarity-mid { color:#C9082A; font-weight:600; background:#fff5f5; padding:2px 8px; border-radius:10px; }
        .nba-summary { background:linear-gradient(135deg,#f7fafc 0%,#edf2f7 100%); border-left:4px solid #17408B; padding:18px 20px; margin:16px 0 0 0; border-radius:0 10px 10px 0; line-height:1.7; font-size:14px; color:#2d3748; }
    </style>
    """, unsafe_allow_html=True)


def main():
    """Main function."""
    logger.info("Starting the application")
    inject_nba_theme()

    # Custom HTML header banner with integrated version
    version_str = get_version_string()
    st.markdown(f"""
    <div class="nba-header">
        <h1>\U0001f3c0 NBA Player Similarity Finder</h1>
        <p class="nba-subtitle">Find players with similar playing styles across eras</p>
        <p class="nba-version">{version_str}</p>
    </div>
    """, unsafe_allow_html=True)
    initialize_session_state()
    display_chat_messages()

    st.text_input(
        "Search for a player:", key="user_input", placeholder=settings.STREAMLIT_INPUT_PLACEHOLDER, on_change=handle_user_input
    )

    # Footer
    st.markdown('<div class="nba-footer">Powered by AI & NBA Stats</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
    # TODO: at some point move all to app/ dir for easier deployment on docker and config management with app/ dir
