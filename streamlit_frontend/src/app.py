import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent.parent

# Add project root to PYTHONPATH as streamlit wants to run as "streamlit runapp.py" and not module "python -m  runapp.py"
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from shared.config import settings
from shared.utils.app_logger import logger
from streamlit_frontend.src.api_client import get_user_input_stats, get_similar_player_stats
from streamlit_frontend.src.components import (
    display_chat_messages,
    format_stats_for_display,
    inject_nba_theme,
)
from streamlit_frontend.src.radar_chart import generate_radar_chart_html
from streamlit_frontend.src.intent_parser import parse_user_intent
from streamlit_frontend.src.llm import generate_analysis
from streamlit_frontend.src.session import initialize_session_state
from streamlit_frontend.src.utils import fetch_versions

st.set_page_config(layout="wide", page_title="NBA Player Similarity Finder", page_icon="\U0001f3c0")


def handle_user_input() -> None:
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
        chart_html = generate_radar_chart_html(user_stats, similar_player_stats)
        st.session_state["messages"].append({"role": "assistant", "content": html_reply, "type": "html", "chart": chart_html})

    # Clear the input field
    st.session_state["user_input"] = ""


def get_version_string() -> str:
    frontend_version, backend_version = fetch_versions()
    return f"v{frontend_version} | API v{backend_version}"


def main() -> None:
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
