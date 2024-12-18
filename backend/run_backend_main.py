from .src.store_data import store_embeddings_to_qdrant


if __name__ == "__main__":
    data_path = "data/transactions.csv"
    collection_name = "transactions"
    store_embeddings_to_qdrant(collection_name, data_path)
