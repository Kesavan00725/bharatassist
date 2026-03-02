FROM python:3.9-slim

WORKDIR /app

# Copy requirements (from backend directory)
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Add gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Copy application (from backend directory)
COPY backend/ .

# Expose port (Cloud Run uses $PORT env var)
ENV PORT=8080
EXPOSE 8080

# Run with uvicorn directly (simpler and faster for FastAPI)
CMD exec uvicorn --host 0.0.0.0 --port $PORT --loop uvloop main:app
