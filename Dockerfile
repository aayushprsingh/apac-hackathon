# Cortex Dockerfile — Cloud Run
# Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install app dependencies
COPY app/requirements.txt ./app/
RUN pip install --no-cache-dir -r app/requirements.txt

# Copy application code
COPY app/ ./app/
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY db/ ./db/

# Set environment
ENV PORT=8080
ENV FLASK_ENV=production
ENV DEMO_MODE=false

# Expose port
EXPOSE 8080

# Run
CMD ["python", "app/app.py"]
