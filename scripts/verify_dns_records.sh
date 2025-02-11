#!/bin/bash

# Configuration
DOMAIN="swacktech.com"

# Expected records
A_RECORDS=(
    "216.239.32.21"
    "216.239.34.21"
    "216.239.36.21"
    "216.239.38.21"
)

AAAA_RECORDS=(
    "2001:4860:4802:32::15"
    "2001:4860:4802:34::15"
    "2001:4860:4802:36::15"
    "2001:4860:4802:38::15"
)

echo "DNS Record Verification for Cloud Run Domain Mapping"
echo "=================================================="

while true; do
    echo "Checking at $(date):"
    echo "------------------"
    
    # Check A records
    echo "A Records:"
    echo "Expected:"
    printf '%s\n' "${A_RECORDS[@]}" | sed 's/^/- /'
    echo -e "\nActual:"
    dig +short A $DOMAIN | sed 's/^/- /'
    
    # Check AAAA records
    echo -e "\nAAAA Records:"
    echo "Expected:"
    printf '%s\n' "${AAAA_RECORDS[@]}" | sed 's/^/- /'
    echo -e "\nActual:"
    dig +short AAAA $DOMAIN | sed 's/^/- /'
    
    # Check HTTPS certificate
    echo -e "\nHTTPS Certificate Check:"
    curl -sI https://$DOMAIN | grep -i "HTTP\|SSL"
    
    echo -e "\nWaiting 30 seconds for next check..."
    echo "----------------------------------------"
    sleep 30
done