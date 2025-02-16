from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from datetime import datetime
import pandas as pd
from shared.config import settings
from backend.utils.fuzz_utils import find_top_matches
import os
from shared.utils.app_logger import logger
from tqdm import tqdm
from icecream import ic


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

    for column in categorization["numeric_columns"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Handle missing values with fallback to 0 for columns with only NaN
    for column in categorization["numeric_columns"]:
        if df[column].isnull().all():
            df[column] = 0
        else:
            df[column] = df[column].fillna(df[column].median())

    return df


def fetch_player_stats_from_local_file(player_name: str, data_dir: str):
    logger.debug(f"Fetching player stats from {data_dir} for {player_name}")
    all_files = os.listdir(data_dir)
    best_match_file_name = find_top_matches(player_name, all_files, settings.FUZZ_THRESHOLD_LOCAL_STATS_FILE)
    file_path = os.path.join(data_dir, best_match_file_name)
    return pd.read_parquet(file_path)


def fetch_all_players_from_local_files(data_dir: str):
    all_files = [os.path.join(data_dir, file) for file in os.listdir(data_dir)]
    logger.info(f"Fetching all players from {data_dir} with {len(all_files)} files")
    # not using list comprehension because it's hard to debug which file is causing the errors
    players_stats_df_list = []
    try:
        for file_path in tqdm(all_files, desc="Processing files"):
            logger.debug(f"Reading file: {file_path}")
            players_stats_df_list.append(pd.read_parquet(file_path))

        all_players_df = pd.concat(players_stats_df_list)
        return all_players_df
    except Exception as e:
        logger.error(f"Error processing players files: {e}")
        return None


def calculate_career_averages(player_stats_df: pd.DataFrame):
    career_totals = player_stats_df.sum(numeric_only=True)
    total_games_played = career_totals["GP"]
    if total_games_played == 0:
        logger.warning(f"No games played for {player_stats_df['PLAYER_NAME'].iloc[0]}")
        return pd.DataFrame()

    # Core per-game stats
    career_averages = {
        "PLAYER_NAME": player_stats_df["PLAYER_NAME"].iloc[0],
        "PLAYER_ID": player_stats_df["PLAYER_ID"].iloc[0],
        "GP": total_games_played,
        "GS": career_totals["GS"],
        "LAST_PLAYED_AGE": player_stats_df["PLAYER_AGE"].iloc[-1],
        "LAST_PLAYED_SEASON": player_stats_df["SEASON_ID"].iloc[-1],
        "TOTAL_SEASONS": len(player_stats_df["SEASON_ID"].unique()),
        "PTS_PER_GAME": career_totals["PTS"] / total_games_played,
        "REB_PER_GAME": career_totals["REB"] / total_games_played,
        "AST_PER_GAME": career_totals["AST"] / total_games_played,
        "STL_PER_GAME": career_totals["STL"] / total_games_played,
        "BLK_PER_GAME": career_totals["BLK"] / total_games_played,
        "TOV_PER_GAME": career_totals["TOV"] / total_games_played,
        "MIN_PER_GAME": career_totals["MIN"] / total_games_played,
    }

    # Shooting percentages
    career_averages["FG%"] = (career_totals["FGM"] / career_totals["FGA"] * 100) if career_totals["FGA"] > 0 else 0
    career_averages["3P%"] = (career_totals["FG3M"] / career_totals["FG3A"] * 100) if career_totals["FG3A"] > 0 else 0
    career_averages["TS%"] = (
        career_totals["PTS"] / (2 * (career_totals["FGA"] + 0.44 * career_totals["FTA"]))
        if (career_totals["FGA"] + 0.44 * career_totals["FTA"]) > 0
        else 0
    )
    career_averages["FT%"] = (career_totals["FTM"] / career_totals["FTA"] * 100) if career_totals["FTA"] > 0 else 0

    # Advanced metrics
    career_averages["PER"] = (
        (
            career_totals["PTS"]
            + career_totals["REB"]
            + career_totals["AST"]
            + career_totals["STL"]
            + career_totals["BLK"]
            - (career_totals["FGA"] - career_totals["FGM"])
            - (career_totals["FTA"] - career_totals["FTM"])
            - career_totals["TOV"]
        )
        / career_totals["MIN"]
        if career_totals["MIN"] > 0
        else 0
    )
    career_averages["WS/48"] = (
        (
            (career_totals["PTS"] + career_totals["AST"] + career_totals["STL"] + career_totals["BLK"])
            - (career_totals["FGA"] - career_totals["FGM"])
            - (career_totals["FTA"] - career_totals["FTM"])
            - career_totals["TOV"]
        )
        / (48 * total_games_played)
        if total_games_played > 0
        else 0
    )
    career_averages["USG%"] = (
        100
        * (career_totals["FGA"] + 0.44 * career_totals["FTA"] + career_totals["TOV"])
        / (total_games_played * career_totals["MIN"])
        if career_totals["MIN"] > 0
        else 0
    )
    career_averages["EFG%"] = (
        (career_totals["FGM"] + 0.5 * career_totals["FG3M"]) / career_totals["FGA"] if career_totals["FGA"] > 0 else 0
    )

    career_averages["PTS_PER_36"] = (
        (career_totals["PTS"] / career_totals["MIN"]) * 36 if career_totals["MIN"] > 0 else 0
    )
    career_averages["AST_TO_RATIO"] = career_totals["AST"] / career_totals["TOV"] if career_totals["TOV"] > 0 else 0
    career_averages["STL%"] = (career_totals["STL"] * 100) / career_totals["MIN"] if career_totals["MIN"] > 0 else 0
    career_averages["BLK%"] = (career_totals["BLK"] * 100) / career_totals["MIN"] if career_totals["MIN"] > 0 else 0
    career_averages["PTS_RESPONSIBILITY"] = career_totals["PTS"] + (career_totals["AST"] * 2.5)

    return pd.DataFrame([career_averages])


def add_all_player_metrics_to_parquet(df: pd.DataFrame, player_name: str, overwrite_all_metrics: bool = False):
    if df.empty:
        logger.warning(f"Empty DataFrame for {player_name}")
        return
    processed_file_path = (
        f"{settings.PROCESSED_NBA_DATA_PATH}/{player_name.replace(' ', '_')}_full_player_stats.parquet"
    )
    if not overwrite_all_metrics and os.path.exists(processed_file_path):
        logger.info(f"Processed NBA data for {player_name} already exists, skipping.")
        return
    df.insert(1, "PLAYER_NAME", player_name)
    logger.debug(f"Adding all player metrics to {player_name} with DataFrame: \n{df}")
    df = fill_missing_values(df)
    df = remove_multiple_seasons(df)
    df_career_stats = calculate_career_averages(df)
    df_career_stats = round_career_averages(df_career_stats)
    logger.debug(f"rounded career stats:\n{df_career_stats}")
    if settings.LOG_LEVEL == "DEBUG":  # left in for debugging
        ic(df_career_stats.dtypes)
        for _, row in df_career_stats.iterrows():
            ic(row)
    os.makedirs(settings.PROCESSED_NBA_DATA_PATH, exist_ok=True)
    df_career_stats.to_parquet(f"{processed_file_path}", index=False)


def round_career_averages(df: pd.DataFrame) -> pd.DataFrame:
    pct_cols = [col for col in df.columns if "%" in col or "PER" == col or "RATIO" in col]
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.difference(pct_cols)
    df[numeric_cols] = df[numeric_cols].round(1)
    df[pct_cols] = df[pct_cols].astype(float).round(3)

    return df


def remove_multiple_seasons(df: pd.DataFrame):
    df = df.sort_values("SEASON_ID")
    df = df.drop_duplicates(subset=["PLAYER_ID", "SEASON_ID"], keep="last")
    return df


def process_player_file(file: str, overwrite_all_metrics: bool):
    try:
        file_path = os.path.join(settings.RAW_NBA_DATA_PATH, file)
        player_name = file.split("_career_stats.parquet")[0].replace("_", " ")
        df = pd.read_parquet(file_path)
        add_all_player_metrics_to_parquet(df, player_name, overwrite_all_metrics=overwrite_all_metrics)
    except Exception as e:
        logger.error(f"Error processing file {file}: {e}")
    return file


def process_player_metrics_in_processes(overwrite_all_metrics: bool = False):
    start_time = time.perf_counter()
    logger.info(
        f"Starting to process all players metrics on {datetime.now()} and add them to folder {settings.PROCESSED_NBA_DATA_PATH}"
    )

    all_raw_files = os.listdir(settings.RAW_NBA_DATA_PATH)

    with ProcessPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        futures = {executor.submit(process_player_file, file, overwrite_all_metrics): file for file in all_raw_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Players", unit="player"):
            file = futures[future]
            try:
                future.result()
                logger.debug(f"Successfully processed file: {file}")
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")

    logger.info(
        f"Finished processing all players metrics on {datetime.now()} and it took {round((time.perf_counter() - start_time) / 60, 2)} minutes"
    )
