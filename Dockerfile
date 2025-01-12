# Use an official Python runtime as a base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the project into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI and Streamlit ports
EXPOSE 8000
EXPOSE 8501

# Start both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn backend.run_backend_server_main:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_frontend/src/app.py --server.port=8501 --server.address=0.0.0.0 --server.headless true"]
