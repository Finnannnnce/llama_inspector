#!/bin/bash

# Configuration
DOMAIN="ethereum.swacktech.com"
CLOUDFLARE_DNS="1.1.1.1"
CLOUD_RUN_URL="ethereum-analyzer-oacz5ektba-ue.a.run.app"

echo "DNS and HTTPS Verification"
echo "========================="

# Function to check DNS
check_dns() {
    echo "Checking DNS resolution..."
    dig @$CLOUDFLARE_DNS $DOMAIN +short
}

# Function to check HTTPS
check_https() {
    echo "Testing HTTPS connection..."
    curl -sI https://$DOMAIN/health
}

# Function to check Cloud Run
check_cloud_run() {
    echo "Testing Cloud Run service..."
    curl -sI https://$CLOUD_RUN_URL/health
}

# Main verification loop
while true; do
    echo -e "\nRunning checks at $(date)"
    echo "-------------------------"
    
    # Check DNS
    DNS_RESULT=$(check_dns)
    if [ -z "$DNS_RESULT" ]; then
        echo "❌ DNS record not found"
        echo "Add this CNAME record in Cloudflare:"
        echo "Type: CNAME"
        echo "Name: ethereum"
        echo "Target: $CLOUD_RUN_URL"
        echo "Proxy status: Proxied (orange cloud)"
    else
        echo "✅ DNS record found: $DNS_RESULT"
        
        # Check HTTPS
        if curl -s https://$DOMAIN/health > /dev/null; then
            echo "✅ HTTPS connection successful"
            echo "Service is ready at: https://$DOMAIN"
            exit 0
        else
            echo "❌ HTTPS connection failed"
        fi
    fi
    
    echo -e "\nWaiting 30 seconds before next check..."
    sleep 30
done