#!/bin/bash

echo "Clearing local DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

echo -e "\nWaiting for cache clear to take effect..."
sleep 5

echo -e "\nTesting connection to Cloud Run service directly..."
curl -v https://swacktech-frontend-330135650610.us-central1.run.app/_stcore/health

echo -e "\nWaiting 5 seconds..."
sleep 5

echo -e "\nTesting connection through Cloudflare..."
curl -v --connect-timeout 10 https://swacktech.com/_stcore/health

echo -e "\nChecking SSL certificate details for Cloud Run..."
echo | openssl s_client -connect swacktech-frontend-330135650610.us-central1.run.app:443 -servername swacktech-frontend-330135650610.us-central1.run.app 2>/dev/null | openssl x509 -noout -text | grep "Subject:"

echo -e "\nChecking SSL certificate details for Cloudflare..."
echo | openssl s_client -connect swacktech.com:443 -servername swacktech.com 2>/dev/null | openssl x509 -noout -text | grep "Subject:"

echo -e "\nVerifying DNS records..."
echo "A Records:"
dig +short A swacktech.com
echo -e "\nAAAA Records:"
dig +short AAAA swacktech.com

echo -e "\nIf ERR_SSL_VERSION_OR_CIPHER_MISMATCH persists:"
echo "1. Verify Cloudflare SSL/TLS settings are set to 'Full' (not Full Strict)"
echo "2. Ensure TLS 1.2 is set as minimum version"
echo "3. Clear browser cache and try in incognito mode"
echo "4. Wait 5-10 minutes for SSL changes to propagate"