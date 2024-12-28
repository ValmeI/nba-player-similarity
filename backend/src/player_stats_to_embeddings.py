import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.utils.app_logger import logger

pd.set_option("future.no_silent_downcasting", True)


METADATA_COLUMNS = ["PLAYER_NAME", "PLAYER_ID"]

# Define the numeric columns for embedding
NUMERIC_COLUMNS = [
    "PTS_PER_GAME",  # Points per game
    "REB_PER_GAME",  # Rebounds per game
    "AST_PER_GAME",  # Assists per game
    "STL_PER_GAME",  # Steals per game
    "BLK_PER_GAME",  # Blocks per game
    "TOV_PER_GAME",  # Turnovers per game
    "MIN_PER_GAME",  # Minutes per game
    "TS%",  # True shooting percentage
    "EFG%",  # Effective field goal percentage
    "FG%",  # Field goal percentage
    "FT%",  # Free throw percentage
    "PER",  # Player efficiency rating
    "WS/48",  # Win shares per 48 minutes
    "USG%",  # Usage rate
    "PTS_PER_36",  # Points per 36 minutes
    "AST_TO_RATIO",  # Assist-to-turnover ratio
    "STL%",  # Steal percentage
    "BLK%",  # Block percentage
    "PTS_RESPONSIBILITY",  # Points responsibility
]


# Define the normalized columns as we want to keep original columns aslo
NORMALIZED_COLUMN_PREFIX = "NORM_"
TO_NORMALIZED_COLUMNS = [f"{NORMALIZED_COLUMN_PREFIX}{col}" for col in NUMERIC_COLUMNS]


def fill_missing_values(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing values in numeric columns with 0 as those are really old players
    """
    player_stats_df[NUMERIC_COLUMNS] = player_stats_df[NUMERIC_COLUMNS].fillna(0)
    return player_stats_df


def normalize_features(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    scaler = StandardScaler()
    # to keep original columns aslo, so we could return those to user after
    player_stats_df[TO_NORMALIZED_COLUMNS] = scaler.fit_transform(player_stats_df[NUMERIC_COLUMNS])
    logger.debug(f"Normalized numeric data:\n{player_stats_df[TO_NORMALIZED_COLUMNS]}")
    return player_stats_df


def create_player_embeddings(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    logger.debug(f"Raw numeric data before normalization:\n{player_stats_df[NUMERIC_COLUMNS]}")
    missing_columns = [col for col in NUMERIC_COLUMNS if col not in player_stats_df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns for processing: {missing_columns}")

    player_stats_df = fill_missing_values(player_stats_df)
    player_stats_df = normalize_features(player_stats_df)
    player_stats_df["embeddings"] = player_stats_df[TO_NORMALIZED_COLUMNS].apply(
        lambda row: row.to_numpy().tolist(), axis=1
    )
    logger.debug(f"Created embeddings for player {player_stats_df.iloc[0]['PLAYER_NAME']} with data: {player_stats_df}")
    return player_stats_df[METADATA_COLUMNS + ["embeddings"] + NUMERIC_COLUMNS]
