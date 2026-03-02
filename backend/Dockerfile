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

# Run with gunicorn using uvicorn worker (for ASGI/FastAPI compatibility)
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0 --access-logfile - --error-logfile - "main:app"
