import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.utils.app_logger import logger

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

METADATA_COLUMNS = ["SEASON_ID", "PLAYER_NAME"]


def normalize_features(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    scaler = StandardScaler()
    player_stats_df[NUMERIC_COLUMNS] = scaler.fit_transform(player_stats_df[NUMERIC_COLUMNS])
    return player_stats_df


def create_season_embeddings(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in NUMERIC_COLUMNS if col not in player_stats_df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns for processing: {missing_columns}")

    player_stats_df = normalize_features(player_stats_df)
    player_stats_df["embeddings"] = player_stats_df[NUMERIC_COLUMNS].apply(lambda row: row.to_numpy().tolist(), axis=1)
    logger.info(
        f"Created embeddings for {len(player_stats_df)} seasons for player: {player_stats_df['PLAYER_NAME'].iloc[0]}"
    )
    return player_stats_df[METADATA_COLUMNS + ["embeddings"]]
