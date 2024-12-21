import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.utils.app_logger import logger

pd.set_option("future.no_silent_downcasting", True)

# Define the numeric columns for embedding
NUMERIC_COLUMNS = [
    "PTS_PER_GAME",
    "AST_PER_GAME",
    "STL_PER_GAME",
    "BLK_PER_GAME",
    "TOV_PER_GAME",
    "PF_PER_GAME",
    "OREB_PER_GAME",
    "DREB_PER_GAME",
]

NEW_NORMALIZED_COLUMNS = [f"NORM_{col}" for col in NUMERIC_COLUMNS]

METADATA_COLUMNS = ["SEASON_ID", "PLAYER_NAME"]


def fill_missing_values(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing values in numeric columns with 0 as those are really old players
    """
    player_stats_df[NUMERIC_COLUMNS] = player_stats_df[NUMERIC_COLUMNS].fillna(0).infer_objects(copy=False)
    return player_stats_df


def normalize_features(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    scaler = StandardScaler()
    # to keep original columns aslo, so we could return those to user after
    player_stats_df[NEW_NORMALIZED_COLUMNS] = scaler.fit_transform(player_stats_df[NUMERIC_COLUMNS])
    return player_stats_df


def create_season_embeddings(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in NUMERIC_COLUMNS if col not in player_stats_df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns for processing: {missing_columns}")

    player_stats_df = fill_missing_values(player_stats_df)
    player_stats_df = normalize_features(player_stats_df)
    player_stats_df["embeddings"] = player_stats_df[NEW_NORMALIZED_COLUMNS].apply(
        lambda row: row.to_numpy().tolist(), axis=1
    )
    logger.info(
        f"Created embeddings for {len(player_stats_df)} seasons for player: {player_stats_df['PLAYER_NAME'].iloc[0]}"
    )
    return player_stats_df[METADATA_COLUMNS + ["embeddings"] + NUMERIC_COLUMNS]
