#!/bin/bash

# Configuration
DOMAIN="swacktech.com"
TARGET="ethereum.swacktech.com"

echo "URL Forwarding Verification"
echo "=========================="

while true; do
    echo "Checking at $(date):"
    echo "------------------"
    
    # Check CNAME record
    echo "CNAME lookup:"
    dig CNAME $DOMAIN
    
    # Check redirect
    echo -e "\nRedirect check:"
    curl -sI https://$DOMAIN | grep -i "location"
    
    # Check target accessibility
    echo -e "\nTarget check:"
    curl -sI https://$TARGET
    
    echo -e "\nWaiting 30 seconds for next check..."
    echo "----------------------------------------"
    sleep 30
done