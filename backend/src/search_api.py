from fastapi import FastAPI, HTTPException, Request
from shared.config import settings
from backend.src.qdrant_wrapper import QdrantClientWrapper
from shared.utils.app_logger import logger
from backend.utils.search_results import (
    format_logger_search_result,
    remove_same_player,
    format_similar_players_search_result,
    format_user_requested_player_career_stats,
)
from backend.src.player_real_name import get_real_player_name
from geoip2.database import Reader
import os

# Load GeoIP database
geoip_db_path = os.getenv("GEOIP_DB_PATH", "backend/geo_db/GeoLite2-City.mmdb")
geoip_reader = Reader(geoip_db_path)

app = FastAPI()
client = QdrantClientWrapper(
    host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=settings.QDRANT_COLLECTION_NAME
)


@app.get("/")
def get_root():
    return {"message": "Service is up and running."}


@app.middleware("http")
async def log_user_geolocation(request: Request, call_next):
    
    client_ip = request.client.host

    if client_ip in ["127.0.0.1", "::1"] or client_ip.startswith("192.168.") or client_ip.startswith("10."):
        logger.info(f"Request from local environment (IP: {client_ip}). Assuming developer access.")
        country, city = "Local Environment", "Developer Machine"
    else:
        try:
            geoip_data = geoip_reader.city(client_ip)
            country = geoip_data.country.name
            city = geoip_data.city.name
        except Exception as e:
            logger.error(f"Failed to retrieve GeoIP data for {client_ip}: {e}")
            country, city = "Unknown", "Unknown"

    logger.info(f"Request from IP: {client_ip}, Country: {country}, City: {city}, Path: {request.url.path}")

    response = await call_next(request)
    return response


def generate_similar_players_search_query_vector(player_name: str):
    try:
        query_vector, _ = client.search_players_by_name(player_name.lower())
        return query_vector
    except Exception as e:
        logger.error(f"Error searching for player {player_name} embeddings in Qdrant: {e}")
        return None


# Just for simplicity, calling this code twice, one for emmbeddings and one for career stats
def fetch_user_input_player_stats(player_name: str):
    try:
        _, career_stats = client.search_players_by_name(player_name.lower())
        return career_stats
    except Exception as e:
        logger.error(f"Error searching for player {player_name} stats in Qdrant: {e}")
        return None


def handle_player_search_result(player_result, player_name):
    if player_result.get("error"):
        return {
            "searched_player": {"target": player_result["target"], "player_name": player_name},
            "error": player_result["error"],
        }

    real_player_name = player_result["player_name"]
    logger.info(f"Received search query for real player name: {real_player_name} from user input: {player_name}")
    return {
        "searched_player": {"player_name": real_player_name},
        "error": None,
    }


@app.get("/user_requested_player_career_stats/")
def user_requested_player_career_stats(player_name: str):
    logger.info(f"Received request for career stats for player: {player_name}")
    player_name = player_name.lower()
    player_result = get_real_player_name(player_name)

    result = handle_player_search_result(player_result, player_name)
    if result["error"]:
        return result

    real_player_name = result["searched_player"]["player_name"]
    career_stats = fetch_user_input_player_stats(real_player_name)
    if career_stats:
        logger.info(f"Retrieved career stats for player: {real_player_name}")
        logger.debug(f"Retrieved career stats: {career_stats}")
    else:
        logger.error(f"Failed to retrieve career stats for player: {real_player_name}")
    return format_user_requested_player_career_stats(player_result, career_stats)


@app.get("/search_similar_players/")
def search_similar_players(player_name: str):
    player_name = player_name.lower()
    player_result = get_real_player_name(player_name)

    result = handle_player_search_result(player_result, player_name)
    if result["error"]:
        return result

    real_player_name = result["searched_player"]["player_name"]
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
        return format_similar_players_search_result(player_result, search_result)
    else:
        logger.error(
            f"No results found for player '{real_player_name}' in collection '{client.collection_name}' from user input '{player_name}'"
        )
        return {"searched_player": {"target": real_player_name, "player_name": player_name}, "similar_players": []}
