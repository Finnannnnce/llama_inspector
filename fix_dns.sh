#!/bin/bash

# Configuration
DOMAIN="swacktech.com"

echo "Fixing DNS Configuration for ${DOMAIN}"
echo "======================================"

# 1. Check current Cloud Run domain mappings
echo "Checking Cloud Run domain mappings..."
gcloud beta run domain-mappings list --platform managed

# 2. Verify Google Cloud Run DNS records
echo -e "\nRequired Google Cloud Run DNS records:"
echo "A Records:"
echo "- 216.239.32.21"
echo "- 216.239.34.21"
echo "- 216.239.36.21"
echo "- 216.239.38.21"

echo -e "\nAAAA Records:"
echo "- 2001:4860:4802:32::15"
echo "- 2001:4860:4802:34::15"
echo "- 2001:4860:4802:36::15"
echo "- 2001:4860:4802:38::15"

# 3. Check current DNS configuration
echo -e "\nCurrent DNS Configuration:"
echo "A Records:"
dig +short ${DOMAIN}
echo -e "\nAAAA Records:"
dig +short AAAA ${DOMAIN}

# 4. Instructions for fixing
echo -e "\nTo fix the DNS configuration:"
echo "1. Go to Cloudflare Dashboard"
echo "2. Select domain: ${DOMAIN}"
echo "3. Go to DNS settings"
echo "4. Remove existing A and AAAA records"
echo "5. Add new records:"
echo "   A Records (Proxy status: DNS only - gray cloud temporarily):"
echo "   - 216.239.32.21"
echo "   - 216.239.34.21"
echo "   - 216.239.36.21"
echo "   - 216.239.38.21"
echo "   AAAA Records (Proxy status: DNS only - gray cloud temporarily):"
echo "   - 2001:4860:4802:32::15"
echo "   - 2001:4860:4802:34::15"
echo "   - 2001:4860:4802:36::15"
echo "   - 2001:4860:4802:38::15"

# 5. Check domain mapping status
echo -e "\nChecking domain mapping status..."
gcloud beta run domain-mappings describe \
  --domain=${DOMAIN} \
  --platform=managed

echo -e "\nAfter updating DNS records:"
echo "1. Wait for DNS propagation (5-10 minutes)"
echo "2. Wait for SSL certificate provisioning"
echo "3. Re-enable Cloudflare proxy (orange cloud) once certificate is provisioned"
echo "4. Run this script again to verify changes"