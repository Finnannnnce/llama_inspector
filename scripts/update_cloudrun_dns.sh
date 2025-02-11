#!/bin/bash

echo "Updating DNS Records for Cloud Run Domain Mapping"
echo "=============================================="

# A Records
echo "Adding A Records:"
echo "Type: A, Name: @, Content: 216.239.32.21, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: A, Name: @, Content: 216.239.34.21, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: A, Name: @, Content: 216.239.36.21, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: A, Name: @, Content: 216.239.38.21, Proxy: Proxied (orange cloud), TTL: Auto"

# AAAA Records
echo -e "\nAdding AAAA Records:"
echo "Type: AAAA, Name: @, Content: 2001:4860:4802:32::15, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: AAAA, Name: @, Content: 2001:4860:4802:34::15, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: AAAA, Name: @, Content: 2001:4860:4802:36::15, Proxy: Proxied (orange cloud), TTL: Auto"
echo "Type: AAAA, Name: @, Content: 2001:4860:4802:38::15, Proxy: Proxied (orange cloud), TTL: Auto"

echo -e "\nCloudflare SSL/TLS Settings:"
echo "1. Set SSL/TLS encryption mode to 'Full (strict)'"
echo "2. Enable 'Always Use HTTPS'"
echo "3. Set Minimum TLS Version to 1.2"
echo "4. Enable 'Automatic HTTPS Rewrites'"

echo -e "\nAdd Page Rules:"
echo "1. URL Pattern: swacktech.com/*"
echo "   Settings:"
echo "   - Cache Level: Standard"
echo "   - Edge Cache TTL: 2 hours"
echo "   - Browser Cache TTL: 4 hours"

echo -e "\nAfter updating records in Cloudflare:"
echo "1. Ensure all DNS records are proxied (orange cloud)"
echo "2. Wait 5-10 minutes for DNS propagation"
echo "3. Cloud Run will automatically detect the records"
echo "4. SSL certificate will be provisioned"
echo "5. Verify DNS and SSL:"
echo "   dig +short A swacktech.com"
echo "   dig +short AAAA swacktech.com"
echo "   curl -v https://swacktech.com/health"
echo "6. Check domain mapping status:"
echo "   gcloud beta run domain-mappings describe --domain swacktech.com --platform managed --region us-central1"