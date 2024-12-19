# CSV andmete töötlemine ja embeddingute loomine

import pandas as pd
from sentence_transformers import SentenceTransformer
from backend.utils.app_logger import logger
from backend.config import settings

IMPORTANT_COLUMNS = ["Date", "Description", "Amount", "Sender/receiver name"]


def load_and_process_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    df = df[IMPORTANT_COLUMNS]

    if IMPORTANT_COLUMNS != list(df.columns):
        raise Exception(f"Needed columns: {IMPORTANT_COLUMNS}. Found columns: {list(df.columns)}")

    model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
    df["embeddings"] = df["Description"].apply(lambda x: model.encode(str(x)).tolist())
    logger.info(f"Created embeddings for {len(df)} transactions")

    return df
