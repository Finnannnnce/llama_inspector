#!/bin/bash

echo "Monitoring certificate status for swacktech.com..."
echo "Press Ctrl+C to stop monitoring"
echo "----------------------------------------"

while true; do
    echo -e "\nChecking at $(date)"
    gcloud beta run domain-mappings describe \
        --domain=swacktech.com \
        --platform=managed \
        --region=us-east1 | grep -A2 "CertificateProvisioned"
    
    # Check if certificate is provisioned
    if gcloud beta run domain-mappings describe \
        --domain=swacktech.com \
        --platform=managed \
        --region=us-east1 | grep -q "status: True.*type: CertificateProvisioned"; then
        echo -e "\n✅ Certificate has been provisioned!"
        break
    fi
    
    echo "Waiting 30 seconds before next check..."
    sleep 30
done