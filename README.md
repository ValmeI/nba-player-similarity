# NBA Player Similarity

Find NBA players with similar career profiles using vector search and natural language queries.

**Live at [valme.xyz](http://valme.xyz)**

## Features

- **Natural language search** — ask things like "guards similar to Kobe from the 90s" (LLM intent parsing)
- **Position & era filters** — narrow results by guard/forward/center and decade
- **Radar chart comparisons** — visual overlay of player stat profiles
- **Recent searches** — clickable pills showing what others have searched
- **LLM-generated analysis** — short AI summary explaining why players are similar

## Tech Stack

FastAPI · Streamlit · Qdrant · OpenAI · Docker

## Quick Start — Local

Requires Python 3.12, [uv](https://github.com/astral-sh/uv), and Docker.

```bash
make venv               # create venv and install deps
make run-qdrant         # start Qdrant in Docker
make data-load-local    # fetch and process NBA data
make data-ingest-local  # ingest vectors into Qdrant
make run-backend        # start FastAPI server
make run-frontend       # start Streamlit UI
```

Backend runs on `localhost:8000`, frontend on `localhost:8501`.

## Quick Start — Docker

```bash
docker-compose up --build
```

Then load and ingest data inside the container:

```bash
make data-load
make data-ingest
```

## Deploy to NAS

The `deploy.sh` script handles git-based deployment to a Synology NAS:

```bash
./deploy.sh                    # pull + rebuild containers
./deploy.sh --ingest           # also re-ingest data
./deploy.sh --skip-build       # pull only, no rebuild
./deploy.sh -n                 # dry run
```

Run `./deploy.sh --help` for full options.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/version` | Frontend & backend versions |
| GET | `/user_requested_player_career_stats/` | Career stats for a player |
| GET | `/search_similar_players/` | Find similar players (with optional filters) |
| POST | `/record_search/` | Record a search for analytics |
| GET | `/recent_searches/` | Retrieve recent searches |

## Configuration

Copy `.env_EXAMPLE` to `.env` and fill in your values. Key sections:

- **Qdrant** — host, port, collection name, vector settings
- **FastAPI** — host, port, worker count
- **LLM** — API key, model, temperature, intent parsing settings
- **Recent Searches** — enabled flag, display limit, TTL

For Docker deployments, the compose file uses `.env_docker`.

## Project Structure

```
├── backend/
│   ├── src/                    # API routes, Qdrant wrapper, embeddings, recent searches
│   ├── utils/                  # fuzzy matching, search result formatting
│   └── run_backend_server_main.py
├── streamlit_frontend/
│   └── src/                    # app, components, intent parser, LLM, radar chart
├── shared/
│   ├── config.py               # env-based configuration
│   └── utils/                  # logging
├── tasks/
│   ├── data_loading/           # fetch and process NBA data
│   └── data_ingesting/         # ingest vectors into Qdrant
├── nba_data/                   # raw and processed parquet files
├── deploy.sh                   # NAS deployment script
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── requirements.txt
```
