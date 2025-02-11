#!/bin/bash

# Configuration
PROJECT_ID="homelab-424523"
REGION="us-east1"
SERVICE_NAME="swacktech-frontend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building and Deploying Streamlit Frontend"
echo "========================================"

# Build Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest -f Dockerfile.streamlit .

# Push to Google Container Registry
echo "Pushing to Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run services replace cloud-run-config-streamlit.yaml \
  --platform=managed \
  --region=${REGION}

# Wait for deployment to complete
echo "Waiting for service to be ready..."
sleep 30

# Create domain mapping
echo "Updating domain mapping..."
gcloud beta run domain-mappings delete --domain=swacktech.com --platform=managed --region=${REGION} --quiet || true
gcloud beta run domain-mappings create --service=${SERVICE_NAME} --domain=swacktech.com --platform=managed --region=${REGION}

echo "Deployment complete!"
echo "==================="
echo "Service URL: https://swacktech.com"
echo "Note: It may take a few minutes for DNS and certificates to propagate."