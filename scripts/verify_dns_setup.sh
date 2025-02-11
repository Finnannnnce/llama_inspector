#!/bin/bash

echo "DNS Record Verification for Cloud Run"
echo "=================================="

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

echo "1. Current A Records:"
echo "Current:"
dig +short A swacktech.com | sort
echo -e "\nExpected:"
printf '%s\n' "${A_RECORDS[@]}" | sort

echo -e "\n2. Current AAAA Records:"
echo "Current:"
dig +short AAAA swacktech.com | sort
echo -e "\nExpected:"
printf '%s\n' "${AAAA_RECORDS[@]}" | sort

echo -e "\n3. Steps to Fix in Cloudflare:"
echo "a. Go to DNS settings for swacktech.com"
echo "b. Remove any existing A and AAAA records"
echo "c. Add these A records (all with DNS only - grey cloud):"
for ip in "${A_RECORDS[@]}"; do
    echo "   - Type: A"
    echo "   - Name: @"
    echo "   - Content: $ip"
    echo "   - Proxy: DNS only (grey cloud)"
    echo "   - TTL: Auto"
    echo ""
done

echo "d. Add these AAAA records (all with DNS only - grey cloud):"
for ip in "${AAAA_RECORDS[@]}"; do
    echo "   - Type: AAAA"
    echo "   - Name: @"
    echo "   - Content: $ip"
    echo "   - Proxy: DNS only (grey cloud)"
    echo "   - TTL: Auto"
    echo ""
done

echo "4. SSL/TLS Settings:"
echo "   - Set SSL/TLS encryption mode to 'Off (not secure)'"
echo "   - Disable 'Always Use HTTPS'"
echo "   - Disable 'Automatic HTTPS Rewrites'"

echo -e "\n5. After making changes:"
echo "   - Wait 5-10 minutes for DNS propagation"
echo "   - Wait for Cloud Run certificate provisioning"
echo "   - Run this script again to verify records"