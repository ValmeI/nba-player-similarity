
def remove_duplicates(search_results: list):
    seen_combinations = set()
    unique_results = []
    for result in search_results:
        key = (result.payload["player_name"], result.payload["season_id"])
        if key not in seen_combinations:
            unique_results.append(result)
            seen_combinations.add(key)
    return unique_results


def remove_same_players(search_results: list):
    # TODO: Implement
    pass