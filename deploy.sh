#!/bin/bash
# Cortex Deployment Script — Bash (Linux/Mac/Cloud Shell)
# Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

set -e

echo "============================================="
echo "Cortex Deployment — Cloud Run"
echo "============================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate required env vars
required_vars=("PROJECT_ID" "REGION" "DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set. Copy .env.example to .env and fill in values."
        exit 1
    fi
done

PROJECT_ID=${PROJECT_ID}
REGION=${REGION:-europe-west1}
SERVICE_NAME=cortex-agent
IMAGE_URI=gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Step 1: Build container image using Cloud Build
echo ""
echo "Step 1: Building Docker image..."
gcloud builds submit --tag ${IMAGE_URI} --project=${PROJECT_ID} .

# Step 2: Deploy to Cloud Run
echo ""
echo "Step 2: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_URI} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="DB_HOST=${DB_HOST},DB_PORT=${DB_PORT},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},PROJECT_ID=${PROJECT_ID},FLASK_ENV=production" \
    --project=${PROJECT_ID}

# Step 3: Get the service URL
echo ""
echo "Step 3: Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${REGION} --format='value(status.url)')
echo ""
echo "============================================="
echo "✅ Cortex deployed successfully!"
echo "🌐 URL: $SERVICE_URL"
echo "📋 API: $SERVICE_URL/api/query"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Set up Cloud SQL PostgreSQL database and run schema.sql + seed.sql"
echo "2. Configure Google OAuth for Gmail/Calendar APIs"
echo "3. Submit your project at: https://vision.hack2skill.com/event/apac-genaiacademy"
