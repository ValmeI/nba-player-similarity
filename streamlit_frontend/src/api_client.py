import requests
import streamlit as st

from shared.config import settings
from shared.utils.app_logger import logger

API_BASE_URL = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}"


@st.cache_data
def fetch_similar_players(requested_player_name: str, position: str | None = None, era: str | None = None) -> dict | list:
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
def fetch_user_input_player_stats(requested_player_name: str) -> dict | list:
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


@st.cache_data(ttl=30)
def fetch_recent_searches(limit: int = 8) -> list[dict]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/recent_searches/",
            params={"limit": limit},
            timeout=settings.API_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("recent_searches", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch recent searches: {e}")
        return []


def get_user_input_stats(user_input: str) -> dict | list[dict]:
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
            "height_inches": user_stats_result_player.get("height_inches", 0),
            "weight": user_stats_result_player.get("weight", 0),
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


def get_similar_player_stats(user_stats: dict | list[dict], position: str | None = None, era: str | None = None) -> dict | list[dict]:
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
                "height_inches": player.get("height_inches", 0),
                "weight": player.get("weight", 0),
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
