import json


def filter_search_result(search_result: list, score_threshold: float):
    return [result for result in search_result if result.score > score_threshold]


def format_search_result(search_result: list):
    return [
        {
            "player_name": result.payload["player_name"],
            "season_id": result.payload["season_id"],
            "points_per_game": result.payload.get("points_per_game"),
            "offensive_rebounds_per_game": result.payload.get("offensive_rebounds_per_game"),
            "defensive_rebounds_per_game": result.payload.get("defensive_rebounds_per_game"),
            "steals_per_game": result.payload.get("steals_per_game"),
            "assists_per_game": result.payload.get("assists_per_game"),
            "blocks_per_game": result.payload.get("blocks_per_game"),
            "turnovers_per_game": result.payload.get("turnovers_per_game"),
            "personal_fouls_per_game": result.payload.get("personal_fouls_per_game"),
            "similarity_score": result.score,
        }
        for result in search_result
    ]


def format_logger_search_result(search_result: list):
    logger_results = [
        {**result.payload, "similarity_score": result.score}
        for result in search_result
    ]
    return json.dumps(logger_results, indent=1)


def remove_duplicates(search_results: list):
    seen_combinations = set()
    unique_results = []
    for result in search_results:
        key = (result.payload["player_name"], result.payload["season_id"])
        if key not in seen_combinations:
            unique_results.append(result)
            seen_combinations.add(key)
    return unique_results


def remove_same_player(search_results: list, player_name: str):
    return [result for result in search_results if result.payload["player_name"].lower() != player_name]
