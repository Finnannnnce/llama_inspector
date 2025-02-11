#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="homelab-424523"
REGION="us-central1"
IMAGE_NAME="swacktech-frontend"
GCR_HOSTNAME="gcr.io"

echo "Building Docker image for amd64..."
docker build --platform linux/amd64 -t $GCR_HOSTNAME/$PROJECT_ID/$IMAGE_NAME:latest -f deployment/Dockerfile.streamlit .

echo "Pushing to Container Registry..."
docker push $GCR_HOSTNAME/$PROJECT_ID/$IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run services replace config/cloud-run-config-streamlit.yaml \
  --platform managed \
  --region $REGION \
  --async

echo "Deployment initiated. Check status with:"
echo "gcloud run services describe swacktech-frontend --region $REGION"