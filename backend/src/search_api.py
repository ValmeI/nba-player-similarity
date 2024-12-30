from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from backend.config import settings
from backend.utils.app_logger import logger
from data.process_data import fetch_all_players_from_local_files
from backend.utils.search_results import (
    remove_same_player,
    filter_search_result,
    format_logger_search_result,
    format_search_result,
)
from data.process_data import fetch_player_stats_from_local_file


app = FastAPI()
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def prepare_input_query_vector(player_name: str) -> list:
    """
    Fetch user input player stats and prepare the query vector for similarity search.

    Args:
        player_name (str): Name of the input player.

    Returns:
        list: Query vector representing the player's career trajectory.
    """
    try:
        player_stats_df = fetch_all_players_from_local_files(settings.EMBEDDED_NBA_DATA_PATH)
        print(player_stats_df)
        logger.debug(f"Player stats for {player_name}: \n{player_stats_df}")
        player_embedding = fetch_all_players_from_local_files(settings.EMBEDDED_NBA_DATA_PATH).query(
            f"PLAYER_NAME.str.lower() == '{player_name}'"
        )
        logger.debug(f"Player embedding for {player_name}: \n{player_embedding}")
        query_vector = player_embedding["embeddings"].tolist()
        return query_vector
    except Exception as e:
        logger.error(f"Error processing player stats for {player_name}: {e}")
        return None

@app.post("/search/")
def search_player_trajectory(player_name: str):
    player_name = player_name.lower()
    logger.info(f'Received search query for player: "{player_name}"')

    query_vector = prepare_input_query_vector(player_name)

    search_result = client.search(
        collection_name="player_career_trajectory",
        query_vector=query_vector,
        limit=settings.VECTOR_SEARCH_LIMIT,
        with_payload=True,
    )

    # search_result = remove_same_player(search_result, player_name)
    # search_result = filter_search_result(search_result, settings.VECTOR_SEARCH_SCORE_THRESHOLD)

    logger.info(f"Found results: {format_logger_search_result(search_result)}")
    return format_search_result(search_result)
