from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime
import pandas as pd
import numpy as np
from backend.config import settings
from backend.utils.fuzz_utils import find_top_matches
import os
from backend.utils.app_logger import logger
from tqdm import tqdm


def fill_missing_values(df: pd.DataFrame):
    categorization = {
        "numeric_columns": [
            "PLAYER_AGE",
            "GP",
            "GS",
            "MIN",
            "FGM",
            "FGA",
            "FG_PCT",
            "FG3M",
            "FG3A",
            "FG3_PCT",
            "FTM",
            "FTA",
            "FT_PCT",
            "OREB",
            "DREB",
            "REB",
            "AST",
            "STL",
            "BLK",
            "TOV",
            "PF",
            "PTS",
        ]
    }

    # Ensure all columns in numeric_columns are numeric
    for column in categorization["numeric_columns"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Handle missing values with fallback to 0 for columns with only NaN
    for column in categorization["numeric_columns"]:
        if df[column].isnull().all():
            df[column] = 0
        else:
            df[column] = df[column].fillna(df[column].median())

    return df


def get_player_stats_from_local_file(player_name: str, data_dir: str):
    all_files = os.listdir(data_dir)
    best_match_file_name = find_top_matches(player_name, all_files, settings.FUZZ_THRESHOLD)
    file_path = os.path.join(data_dir, best_match_file_name)
    return pd.read_parquet(file_path)


def add_all_player_metrics_to_parquet(df: pd.DataFrame, player_name: str, overwrite_all_metrics: bool = False):
    if df.empty:
        logger.warning(f"Empty DataFrame for {player_name}")
        return
    logger.info(f"Starting to add all player metrics to {player_name}")
    processed_file_path = f"{settings.PROCESSED_NBA_DATA_PATH}/{player_name}_full_player_stats.parquet"
    if not overwrite_all_metrics and os.path.exists(processed_file_path):
        logger.info(f"Processed NBA data for {player_name} already exists, skipping.")
        return
    df.insert(1, "PLAYER_NAME", player_name)
    logger.debug(f"Adding all player metrics to {player_name} with DataFrame: \n{df}")
    df = fill_missing_values(df)
    df = remove_multiple_seasons(df)
    merged_player_stats_df = pd.merge(
        df,
        calculate_season_stat_averages_per_game(df),
        how="left",
        on=["PLAYER_NAME", "SEASON_ID", "TEAM_ID"],
    )
    logger.debug(f"Adding advanced metrics to {player_name} with DataFrame: \n{merged_player_stats_df}")
    full_player_stats_df = add_advanced_metrics(merged_player_stats_df)
    os.makedirs(settings.PROCESSED_NBA_DATA_PATH, exist_ok=True)
    full_player_stats_df.to_parquet(f"{processed_file_path}", index=False)


def remove_multiple_seasons(df: pd.DataFrame):
    df = df.sort_values("SEASON_ID")
    df = df.drop_duplicates(subset=["PLAYER_ID", "SEASON_ID"], keep="last")
    return df


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


def add_advanced_metrics(df: pd.DataFrame):
    """
    Add advanced basketball metrics to the player stats DataFrame, handling division by zero.
    """
    # Safely calculate True Shooting Percentage (TS%)
    df["TS%"] = np.where((df["FGA"] + 0.44 * df["FTA"]) > 0, df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"])), 0)

    # Safely calculate Player Efficiency Rating (PER) Approximation
    df["PER"] = np.where(
        df["MIN"] > 0,
        (
            df["PTS"]
            + df["REB"]
            + df["AST"]
            + df["STL"]
            + df["BLK"]
            - (df["FGA"] - df["FGM"])
            - (df["FTA"] - df["FTM"])
            - df["TOV"]
        )
        / df["MIN"],
        0,
    )

    # Safely calculate Effective Field Goal Percentage (EFG%)
    df["EFG%"] = np.where(df["FGA"] > 0, (df["FGM"] + 0.5 * df["FG3M"]) / df["FGA"], 0)

    # Safely calculate Usage Rate (USG%)
    df["USG%"] = np.where(
        (df["GP"] * df["MIN"]) > 0,
        100 * (df["FGA"] + 0.44 * df["FTA"] + df["TOV"]) / (df["GP"] * df["MIN"]),
        0,
    )

    # Safely calculate Turnover Percentage (TOV%)
    df["TOV%"] = np.where(
        (df["FGA"] + 0.44 * df["FTA"] + df["TOV"]) > 0,
        100 * df["TOV"] / (df["FGA"] + 0.44 * df["FTA"] + df["TOV"]),
        0,
    )

    # Calculate Free Throw Rate (FTR)
    df["FTR"] = np.where(df["FGA"] > 0, df["FTA"] / df["FGA"], 0)

    # Calculate Offensive Rebound Percentage (ORB%)
    df["ORB%"] = np.where(
        (df["OREB"] + df["DREB"]) > 0,
        100 * df["OREB"] / (df["OREB"] + df["DREB"]),
        0,
    )

    # Calculate Defensive Rebound Percentage (DRB%)
    df["DRB%"] = np.where(
        (df["OREB"] + df["DREB"]) > 0,
        100 * df["DREB"] / (df["OREB"] + df["DREB"]),
        0,
    )

    # Calculate Win Shares per 48 Minutes (WS/48)
    df["WS/48"] = np.where(
        (df["GP"] > 0) & (df["MIN"] > 0),
        (
            (df["PTS"] + df["AST"] + df["STL"] + df["BLK"])
            - (df["FGA"] - df["FGM"])
            - (df["FTA"] - df["FTM"])
            - df["TOV"]
        )
        / (48 * df["GP"]),
        0,
    )

    # Calculate Points Responsibility
    average_points_per_assist = 2.5  # Assumption
    df["PTS Responsibility"] = df["PTS"] + (df["AST"] * average_points_per_assist)

    return df


def process_player_metrics_in_threads(overwrite_all_metrics: bool = False):
    start_time = time.perf_counter()
    logger.info(
        f"Starting to process all players metrics on {datetime.now()} and add them to folder {settings.PROCESSED_NBA_DATA_PATH}"
    )

    all_raw_files = os.listdir(settings.RAW_NBA_DATA_PATH)

    def process_player_file(file):
        try:
            file_path = os.path.join(settings.RAW_NBA_DATA_PATH, file)
            player_name = file.split("_career_stats.parquet")[0].replace("_", " ")  # Temporary fix
            df = pd.read_parquet(file_path)
            add_all_player_metrics_to_parquet(df, player_name, overwrite_all_metrics=overwrite_all_metrics)
        except Exception as e:
            logger.error(f"Error processing file {file}: {e}")

    with ThreadPoolExecutor(max_workers=settings.MAX_THREADING_WORKERS) as executor:
        futures = {
            executor.submit(process_player_file, file): file
            for file in all_raw_files
        }
        # Wrap the `as_completed` loop with tqdm for progress tracking
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Players", unit="player"):
            file = futures[future]
            try:
                future.result()  # Raise exceptions if they occurred during thread execution
                logger.info(f"Successfully processed file: {file}")
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")

    logger.info(
        f"Finished processing all players metrics on {datetime.now()} and it took {time.perf_counter() - start_time:.2f} seconds"
    )
