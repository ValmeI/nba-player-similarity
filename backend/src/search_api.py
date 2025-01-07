from fastapi import FastAPI, HTTPException
from shared.config import settings
from backend.src.qdrant_wrapper import QdrantClientWrapper
from shared.utils.app_logger import logger
from backend.utils.search_results import (
    format_logger_search_result,
    remove_same_player,
    format_search_result,
)
from backend.src.player_real_name import get_real_player_name

app = FastAPI()
client = QdrantClientWrapper(
    host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=settings.QDRANT_COLLECTION_NAME
)


@app.get("/")
def get_root():
    return {"message": "Service is up and running."}


def generate_similar_players_search_query_vector(player_name: str):
    try:
        query_vector = client.search_players_embeddings_by_name(player_name.lower())
        return query_vector
    except Exception as e:
        logger.error(f"Error searching for player {player_name} in Qdrant: {e}")
        return None


@app.get("/search_similar_players/")
def search_similar_players(player_name: str):
    player_name = player_name.lower()
    player_result = get_real_player_name(player_name)

    if player_result.get("error"):
        return {
            "searched_player": {"target": player_result["target"], "player_name": player_name},
            "error": player_result["error"],
            "matches": player_result["matches"],
        }

    real_player_name = player_result["player_name"]
    logger.info(f"Received search query for real player name: {real_player_name} from user input: {player_name}")

    query_vector = generate_similar_players_search_query_vector(real_player_name)
    if not query_vector:
        raise HTTPException(status_code=500, detail=f"Could not generate query vector for player '{real_player_name}'")

    search_result = client.search_similar_players(query_vector)
    search_result = remove_same_player(search_result, real_player_name)
    # search_result = filter_search_result(search_result, settings.QDRANT_VECTOR_SEARCH_SCORE_THRESHOLD)

    if search_result:
        format_logger_search_result(search_result)
        logger.debug(f"Found results: {format_logger_search_result(search_result)}")
        return format_search_result(player_name, player_result, search_result)
    else:
        logger.error(
            f"No results found for player '{real_player_name}' in collection '{client.collection_name}' from user input '{player_name}'"
        )
        return {"searched_player": {"target": real_player_name, "player_name": player_name}, "similar_players": []}
