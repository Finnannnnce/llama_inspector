#!/bin/bash

# Configuration
DOMAIN="ethereum.swacktech.com"
TARGET="ghs.googlehosted.com"

echo "DNS and HTTPS Verification for Google Hosting"
echo "==========================================="

echo "Required DNS Configuration:"
echo "-------------------------"
echo "In Cloudflare Dashboard:"
echo "Type: CNAME"
echo "Name: ethereum"
echo "Target: $TARGET"
echo "Proxy status: Proxied (orange cloud)"
echo

while true; do
    echo "Checking at $(date):"
    echo "------------------"
    
    # Check CNAME record
    echo "CNAME lookup:"
    dig CNAME $DOMAIN
    
    # Check A record resolution
    echo -e "\nA record lookup:"
    dig A $DOMAIN
    
    # Try HTTPS connection
    echo -e "\nHTTPS check:"
    curl -sI https://$DOMAIN/health
    
    echo -e "\nWaiting 30 seconds for next check..."
    echo "----------------------------------------"
    sleep 30
done