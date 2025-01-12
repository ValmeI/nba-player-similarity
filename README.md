# NBA Player Similarity

## Description
This project analyzes and compares NBA players based on various performance metrics using advanced similarity algorithms to identify comparable players.

---

## Installation Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/nba-player-similarity.git
cd nba-player-similarity
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Usage locally without Docker

### Step 1: Load and Process NBA Data
Run the data loader to fetch and process NBA data:
```bash
python -m tasks.data_loading.data_load_main
```

### Step 2: Set Up Qdrant
Download and run Qdrant as a Docker container:
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Step 3: Ingest Data into Qdrant
Run the data ingestion script to populate Qdrant:
```bash
python -m tasks.data_ingesting.ingest_data
```

### Step 4: Start the Backend Server
Run the backend server using FastAPI:
```bash
python -m backend.run_backend_server_main
```

### Step 5: Start the Frontend Application
Launch the Streamlit frontend application:
```bash
streamlit run streamlit_frontend/src/app.py
```


## Usage with Docker

### Step 1: Build Docker Images
```bash
docker-compose build
```

### Step 2: Run Docker Compose
```bash
docker-compose up
```

### Step 1-2: Build and up together
```bash
docker-compose up --build
```

### Step 3: Access the Application frontend
Navigate to `http://localhost:8501` in your web browser to access the Streamlit frontend.
Note: Make sure to replace `8501` with the actual port number used by your Streamlit application.

### Step 4: Access the Backend API
Navigate to `http://localhost:8000` in your web browser to access the FastAPI backend.
Note: Make sure to replace `8000` with the actual port number used by your FastAPI server.

### Step 5: Qdrant setup
Download and run Qdrant as a Docker container:
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

# Check logs
```bash
docker-compose logs -f nba-app
```

---

## Project Structure Overview
```plaintext
nba_project/
├── backend/                      # Backend (FastAPI)
│   ├── src/                      # Backend core logic
│   ├── utils/                    # Backend utilities
│   ├── run_backend_server_main.py
│
├── general_ongoing_dev_scripts/  # Miscellaneous development scripts
│
├── logs/                         # Logs for monitoring/debugging
│
├── nba_data/                     # Data folder
│   ├── processed_parquet_files/  # Processed files for Qdrant/analysis
│   ├── raw_parquet_files/        # Raw data files
│
├── shared/                       # Shared utilities across backend/frontend
│   ├── utils/
│   ├── config.py
│
├── streamlit_frontend/           # Frontend (Streamlit)
│   ├── src/                      # Streamlit app core
│
├── tasks/                        # Scripts for one-off or periodic tasks
│   ├── data_ingesting/           # Data ingestion-related tasks
│   │   ├── ingest_data.py        # Main data ingestion script
│   ├── data_main.py              # Entry point for data tasks
│   ├── get_nba_data.py           # Raw data fetching
│
├── requirements.txt              # Project dependencies
```

---

## Features
- **Backend**: Built with FastAPI to handle data ingestion, processing, and API endpoints.
- **Frontend**: Interactive UI built with Streamlit for visualizing player similarity results.
- **Data Ingestion**: Automated scripts for fetching and processing NBA player data.
- **Qdrant Integration**: Stores and retrieves similarity vectors efficiently.
- **Logs**: Centralized logging for debugging and monitoring.

---


