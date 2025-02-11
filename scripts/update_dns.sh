#!/bin/bash

# Configuration
DOMAIN="swacktech.com"

# Remove existing A and AAAA records
echo "Removing existing DNS records..."
gcloud beta run domain-mappings delete --domain=$DOMAIN --platform=managed --region=us-east1 --quiet || true

# Create new domain mapping
echo "Creating new domain mapping..."
gcloud beta run domain-mappings create --service=swacktech-frontend --domain=$DOMAIN --platform=managed --region=us-east1

# Wait for DNS records to be generated
echo "Waiting for DNS records to be generated..."
sleep 30

# Verify DNS records
echo "Verifying DNS records..."
gcloud beta run domain-mappings describe --domain=$DOMAIN --platform=managed --region=us-east1

echo "Done! Please update your DNS records in Cloudflare with the above values."