#!/bin/bash

# Configuration
DOMAIN="swacktech.com"

echo "Updating DNS records for $DOMAIN in Cloudflare..."

# A Records for Cloud Run
A_RECORDS=(
    "216.239.32.21"
    "216.239.34.21"
    "216.239.36.21"
    "216.239.38.21"
)

# AAAA Records for Cloud Run
AAAA_RECORDS=(
    "2001:4860:4802:32::15"
    "2001:4860:4802:34::15"
    "2001:4860:4802:36::15"
    "2001:4860:4802:38::15"
)

echo "Please update your Cloudflare DNS records with the following:"
echo ""
echo "1. Remove any existing A and AAAA records for $DOMAIN"
echo ""
echo "2. Add the following A records:"
for ip in "${A_RECORDS[@]}"; do
    echo "   Type: A"
    echo "   Name: @"
    echo "   Content: $ip"
    echo "   Proxy status: DNS only (grey cloud)"
    echo ""
done

echo "3. Add the following AAAA records:"
for ip in "${AAAA_RECORDS[@]}"; do
    echo "   Type: AAAA"
    echo "   Name: @"
    echo "   Content: $ip"
    echo "   Proxy status: DNS only (grey cloud)"
    echo ""
done

echo "4. After adding records:"
echo "   - Wait 5-10 minutes for DNS propagation"
echo "   - Certificate provisioning will begin automatically"
echo "   - Run 'verify_dns_records.sh' to monitor the status"