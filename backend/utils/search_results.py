import json
from shared.utils.app_logger import logger


def filter_search_result(search_result: list, score_threshold: float):
    return [result for result in search_result if result.score > score_threshold]


def format_search_result(user_player_input: str, search_player_name, search_result: list):
    return [
        {
            "target": user_player_input,
            "searched_player": search_player_name,
            "player_name": result.payload["PLAYER_NAME"],
            "games_played": result.payload.get("GP"),
            "games_started": result.payload.get("GS"),
            "last_played_age": result.payload.get("LAST_PLAYED_AGE"),
            "last_played_season": result.payload.get("LAST_PLAYED_SEASON"),
            "total_seasons": result.payload.get("TOTAL_SEASONS"),
            "points_per_game": result.payload.get("PTS_PER_GAME"),
            "rebounds_per_game": result.payload.get("REB_PER_GAME"),
            "assists_per_game": result.payload.get("AST_PER_GAME"),
            "steals_per_game": result.payload.get("STL_PER_GAME"),
            "blocks_per_game": result.payload.get("BLK_PER_GAME"),
            "turnovers_per_game": result.payload.get("TOV_PER_GAME"),
            "minutes_per_game": result.payload.get("MIN_PER_GAME"),
            "true_shooting_percentage": result.payload.get("TS%"),
            "effective_field_goal_percentage": result.payload.get("EFG%"),
            "player_efficiency_rating": result.payload.get("PER"),
            "win_shares_per_48": result.payload.get("WS/48"),
            "usage_rate": result.payload.get("USG%"),
            "points_per_36": result.payload.get("PTS_PER_36"),
            "assist_turnover_ratio": result.payload.get("AST_TO_RATIO"),
            "steal_percentage": result.payload.get("STL%"),
            "block_percentage": result.payload.get("BLK%"),
            "points_responsibility": result.payload.get("PTS_RESPONSIBILITY"),
            "similarity_score": result.score,
        }
        for result in search_result
    ]


def format_logger_search_result(search_result: list):
    logger_results = [{**result.payload, "similarity_score": result.score} for result in search_result]
    return json.dumps(logger_results, indent=1)


def remove_same_player(search_results: list, player_name: str):
    logger.debug(f"Removing same player: {player_name} from search results {search_results}")
    return [result for result in search_results if result.payload["PLAYER_NAME_LOWER_CASE"] != player_name.lower()]
