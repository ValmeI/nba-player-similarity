# SpendSearch


### Known Issues


## Backend

### Running the Backend

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:

   ```bash
   uvicorn main:app --reload
   ```

3. **Test the API**:
   Open your browser and visit:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the FastAPI Swagger documentation.

---

## Frontend

# TODO: Add Streamlit logic

## Full Setup Using Docker

### Prerequisites

- Ensure Docker and Docker Compose are installed on your system.

### Steps

1. **Build and Start Services**:

   ```bash
   docker-compose up --build
   ```

2. **Access Services**:
   - **Frontend**: [http://localhost:8501](http://localhost:8501)
   - **Backend**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Qdrant**: [http://localhost:6333](http://localhost:6333)

3. **Stop Services**:

   ```bash
   docker-compose down
   ```

---

## To Do

1. Finalize the frontend interface.
2. Add examples to the API documentation.
3. Write integration tests for API and frontend.
4. Optimize Docker configuration for production.
