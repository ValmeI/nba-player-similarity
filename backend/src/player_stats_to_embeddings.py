import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.utils.app_logger import logger

pd.set_option("future.no_silent_downcasting", True)

# Define the numeric columns for embedding
NUMERIC_COLUMNS = [
    "PTS_PER_GAME",  # Points per game
    "AST_PER_GAME",  # Assists per game
    "STL_PER_GAME",  # Steals per game
    "BLK_PER_GAME",  # Blocks per game
    "TOV_PER_GAME",  # Turnovers per game
    "PF_PER_GAME",  # Personal fouls per game
    "OREB_PER_GAME",  # Offensive rebounds per game
    "DREB_PER_GAME",  # Defensive rebounds per game
    "TS%",  # True shooting percentage
    "EFG%",  # Effective field goal percentage
    "PER",  # Player efficiency rating
    "USG%",  # Usage rate
    "TOV%",  # Turnover rate
    "WS/48",  # Win shares per 48 minutes
    "FTR",  # Free throw rate
    "ORB%",  # Offensive rebound percentage
    "DRB%",  # Defensive rebound percentage
    "PTS Responsibility",  # Points responsibility
]

# Define the normalized columns as we want to keep original columns aslo
NORMALIZED_COLUMN_PREFIX = "NORM_"
TO_NORMALIZED_COLUMNS = [f"{NORMALIZED_COLUMN_PREFIX}{col}" for col in NUMERIC_COLUMNS]

METADATA_COLUMNS = ["SEASON_ID", "PLAYER_NAME"]


COLUMN_WEIGHTS = {
    "PTS_PER_GAME": 3,  # Emphasize scoring
    "TS%": 2,  # Shooting efficiency
    "PER": 2,  # Player efficiency rating
    "WS/48": 2,  # Win shares per 48 minutes
    "AST_PER_GAME": 1.5,  # Playmaking
    "STL_PER_GAME": 1.5,  # Defense
    "BLK_PER_GAME": 1.5,  # Defense
}


# TODO: check if those two are needed
def apply_weights(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add weights to only the normalized columns and not the original ones
    as we want to keep the original columns for user return, for examples and reference
    """
    for column, weight in COLUMN_WEIGHTS.items():
        new_normalized_column = f"{NORMALIZED_COLUMN_PREFIX}{column}"
        if new_normalized_column in player_stats_df.columns:
            player_stats_df[new_normalized_column] *= weight
    return player_stats_df


def remove_weight(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    for column, weight in COLUMN_WEIGHTS.items():
        new_normalized_column = f"{NORMALIZED_COLUMN_PREFIX}{column}"
        if new_normalized_column in player_stats_df.columns:
            player_stats_df[new_normalized_column] /= weight
    return player_stats_df


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
    return player_stats_df


def create_season_embeddings(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in NUMERIC_COLUMNS if col not in player_stats_df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns for processing: {missing_columns}")

    player_stats_df = fill_missing_values(player_stats_df)
    player_stats_df = apply_weights(player_stats_df)
    player_stats_df = normalize_features(player_stats_df)
    player_stats_df["embeddings"] = player_stats_df[TO_NORMALIZED_COLUMNS].apply(
        lambda row: row.to_numpy().tolist(), axis=1
    )
    logger.info(
        f"Created embeddings for {len(player_stats_df)} seasons for player: {player_stats_df['PLAYER_NAME'].iloc[0]}"
    )
    return player_stats_df[METADATA_COLUMNS + ["embeddings"] + NUMERIC_COLUMNS]
