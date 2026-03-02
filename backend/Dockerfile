FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Add gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Copy application
COPY . .

# Expose port (Cloud Run uses $PORT env var)
ENV PORT=8080
EXPOSE 8080

# Run with gunicorn (production-ready)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile - "main:app"
