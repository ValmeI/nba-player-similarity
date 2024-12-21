from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from nba_api.stats.static import players
import os
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from backend.utils.fuzz_utils import find_top_matches
from backend.config import settings
from backend.utils.app_logger import logger


def save_parquet_file_locally(df: pd.DataFrame, file_path: str):
    df.to_parquet(file_path, index=False)


def remove_multiple_seasons(df: pd.DataFrame):
    df = df.sort_values("SEASON_ID")
    df = df.drop_duplicates(subset=["PLAYER_ID", "SEASON_ID"], keep="last")
    return df


def fill_missing_values(df: pd.DataFrame):
    numeric_columns = df.select_dtypes(include=["number"]).columns
    medians = df[numeric_columns].median()
    df[numeric_columns] = df[numeric_columns].fillna(medians)
    return df


def get_player_stats_from_local_file(player_name: str, data_dir: str = "data/players_parquet"):
    all_files = os.listdir(data_dir)
    best_match_file_name = find_top_matches(player_name, all_files, settings.FUZZ_THRESHOLD)
    file_path = os.path.join(data_dir, best_match_file_name)
    return pd.read_parquet(file_path)


def fetch_and_save_player_stats(player_name: str, data_dir: str = "data/players_parquet", max_workers: int = 10):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        logger.info(f"Player '{player_name}' not found.")
        return None
    player_id = player_dict[0]["id"]

    file_path = os.path.join(data_dir, f'{player_name.replace(" ", "_")}_career_stats.parquet')

    def fetch_data_worker():
        logger.info(f"Fetching data for {player_name} from NBA API.")
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        player_stats_df = career.get_data_frames()[0]
        player_stats_df.insert(1, "PLAYER_NAME", player_name)
        player_stats_df = fill_missing_values(player_stats_df)
        player_stats_df = remove_multiple_seasons(player_stats_df)
        full_player_stats_df = pd.merge(
            player_stats_df,
            calculate_season_stat_averages_per_game(player_stats_df),
            how="left",
            on=["PLAYER_NAME", "SEASON_ID", "TEAM_ID"],
        )
        save_parquet_file_locally(full_player_stats_df, file_path)
        logger.info(f"Data for {player_name} saved to {file_path}.")
    
    if os.path.exists(file_path):
        logger.info(f"Data for {player_name} already exists, continuing with next player.")
        return None
    else:
        logger.info(f"Starting thread to fetch data for {player_name} from NBA API.")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future = executor.submit(fetch_data_worker)
            
            for future in as_completed([future]):
                try:
                    future.result()
                    logger.info(f"Successfully fetched data for {player_name} with thread {threading.get_ident()}.")
                except Exception as e:
                    logger.error(f"Error fetching data for {player_name} with thread {threading.get_ident()}: {e}")
                    
    logger.info(f"Finished thread to fetch data for {player_name}.")
    


def calculate_season_stat_averages_per_game(player_stats_df: pd.DataFrame):
    stat_columns = ["PTS", "REB", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PF", "GP"]
    if "GP" not in player_stats_df.columns:
        raise ValueError("The 'GP' column (Games Played) is required to calculate per-game averages.")

    per_game_stats = player_stats_df.copy()
    for stat in stat_columns:
        per_game_stats[f"{stat}_PER_GAME"] = round(per_game_stats[stat] / per_game_stats["GP"], 1)

    per_game_stats = per_game_stats[
        ["SEASON_ID", "PLAYER_NAME", "TEAM_ID"] + [f"{stat}_PER_GAME" for stat in stat_columns if stat != "GP"]
    ]
    return per_game_stats


def fetch_all_players_stats():
    all_players = players.get_players()
    logger.info(f"Found {len(all_players)} players in NBA. Fetching data for {len(all_players)} players...")
    for index, player in enumerate(all_players):
        logger.info(f"Processing player {index + 1}/{len(all_players)}: {player['full_name']}")
        try:
            fetch_and_save_player_stats(player["full_name"])
        except Exception as e:
            logger.error(f"Error processing player {player['full_name']}: {e}")


if __name__ == "__main__":
    start_time = pd.Timestamp.now()
    logger.info(f"Starting data fetching process on {start_time}")
    fetch_all_players_stats()
    # get_player_stats_from_local_file("Charles Nash")
    # fetch_and_save_player_stats("Shareef Abdur-Rahim")
    logger.info(f"Finished data fetching process on {pd.Timestamp.now()} and it took {pd.Timestamp.now() - start_time}")
