import pandas as pd
from sklearn.preprocessing import RobustScaler
from backend.utils.app_logger import logger
from backend.config import settings
import os
pd.set_option("future.no_silent_downcasting", True)


METADATA_COLUMNS = ["PLAYER_NAME", "PLAYER_ID", "LAST_PLAYED_SEASON"]

# Define the numeric columns for embedding
NUMERIC_COLUMNS = [
    "PTS_RESPONSIBILITY",  # Points responsibility
    "LAST_PLAYED_AGE",  # Age when the player last played
    "TOTAL_SEASONS",  # Total number of seasons played
    "GP",  # Games Played
    "GS",  # Games Started
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
]


# Define the normalized columns as we want to keep original columns also
NORMALIZED_COLUMN_PREFIX = "NORM_"
TO_NORMALIZED_COLUMNS = [f"{NORMALIZED_COLUMN_PREFIX}{col}" for col in NUMERIC_COLUMNS]


class PlayerEmbeddings:
    def __init__(self, players_stats_df: pd.DataFrame):
        self.players_stats_df = players_stats_df

    def fill_missing_values(self) -> pd.DataFrame:
        """
        Fill missing values in numeric columns with 0 as those are really old players
        """
        self.players_stats_df[NUMERIC_COLUMNS] = self.players_stats_df[NUMERIC_COLUMNS].fillna(0)
        return self.players_stats_df

    def normalize_features(self) -> pd.DataFrame:
        result_df = self.players_stats_df.copy()
        scaler = RobustScaler()

        normalized_data = scaler.fit_transform(self.players_stats_df[NUMERIC_COLUMNS])

        # Add all normalized columns at once using a new DataFrame
        normalized_df = pd.DataFrame(
            normalized_data, columns=[f"NORM_{col}" for col in NUMERIC_COLUMNS], index=self.players_stats_df.index
        )

        result_df = pd.concat([result_df, normalized_df], axis=1)

        logger.debug(f"Raw career stats before normalization:\n{self.players_stats_df[NUMERIC_COLUMNS]}")
        logger.debug(f"Normalized career stats:\n{result_df[[f'NORM_{col}' for col in NUMERIC_COLUMNS]]}")

        return result_df

    def create_players_embeddings(self) -> pd.DataFrame:
        logger.debug(f"Raw numeric data before normalization:\n{self.players_stats_df[NUMERIC_COLUMNS]}")
        missing_columns = [col for col in NUMERIC_COLUMNS if col not in self.players_stats_df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns for processing: {missing_columns}")

        self.fill_missing_values()
        self.players_stats_df = self.normalize_features()
        self.players_stats_df["embeddings"] = self.players_stats_df[TO_NORMALIZED_COLUMNS].apply(
            lambda row: row.to_numpy().tolist(), axis=1
        )
        logger.debug(f"Created embeddings for players list of length {len(self.players_stats_df)}")
        os.makedirs(settings.EMBEDDED_NBA_DATA_PATH, exist_ok=True)
        self.players_stats_df.to_parquet(f"{settings.EMBEDDED_NBA_DATA_PATH}/all_players_embeddings.parquet")
        return self.players_stats_df[METADATA_COLUMNS + ["embeddings"] + NUMERIC_COLUMNS + TO_NORMALIZED_COLUMNS]
