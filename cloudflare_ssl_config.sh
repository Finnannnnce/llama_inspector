#!/bin/bash

echo "Cloudflare SSL Configuration for Cloud Run"
echo "========================================"

echo "1. Current Configuration:"
echo "   - SSL is being handled by both Cloudflare and Cloud Run"
echo "   - This causes SSL handshake failures"

echo -e "\n2. Required Changes in Cloudflare:"
echo "   a. SSL/TLS Settings:"
echo "      - Go to SSL/TLS > Overview"
echo "      - Set SSL/TLS encryption mode to 'Full (strict)'"
echo "      - This allows Cloudflare to trust Cloud Run's certificate"
echo ""
echo "   b. DNS Settings:"
echo "      - Keep all A and AAAA records with Proxy Status: ON (orange cloud)"
echo "      - This enables Cloudflare's proxy while respecting Cloud Run's SSL"

echo -e "\n3. Expected Flow:"
echo "   Client -> Cloudflare (SSL) -> Cloud Run (SSL)"
echo "   - Cloudflare handles SSL between client and Cloudflare"
echo "   - Cloud Run handles SSL between Cloudflare and Cloud Run"

echo -e "\n4. After making changes:"
echo "   - Wait 5-10 minutes for changes to propagate"
echo "   - Clear browser cache and DNS cache"
echo "   - Test with: curl -v https://swacktech.com"