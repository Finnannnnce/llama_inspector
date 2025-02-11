#!/bin/bash

# Configuration
DOMAIN="swacktech.com"

echo "DNS and HTTPS Verification for Root Domain"
echo "========================================"

echo "Required DNS Configuration:"
echo "-------------------------"
echo "In Cloudflare Dashboard:"
echo "Type: A and AAAA records"
echo "Name: @ (root domain)"
echo "Values:"
echo "A Records:"
echo "- 216.239.32.21"
echo "- 216.239.34.21"
echo "- 216.239.36.21"
echo "- 216.239.38.21"
echo
echo "AAAA Records:"
echo "- 2001:4860:4802:32::15"
echo "- 2001:4860:4802:34::15"
echo "- 2001:4860:4802:36::15"
echo "- 2001:4860:4802:38::15"
echo "Proxy status: Proxied (orange cloud)"
echo

while true; do
    echo "Checking at $(date):"
    echo "------------------"
    
    # Check A records
    echo "A record lookup:"
    dig A $DOMAIN
    
    # Check AAAA records
    echo -e "\nAAAA record lookup:"
    dig AAAA $DOMAIN
    
    # Try HTTPS connection
    echo -e "\nHTTPS check:"
    curl -sI https://$DOMAIN/health
    
    echo -e "\nWaiting 30 seconds for next check..."
    echo "----------------------------------------"
    sleep 30
done