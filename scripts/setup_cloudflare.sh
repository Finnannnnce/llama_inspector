#!/bin/bash

# Cloud Run URL
CLOUD_RUN_URL="ethereum-analyzer-oacz5ektba-ue.a.run.app"
DOMAIN="ethereum.swacktech.com"

echo "Cloudflare Configuration Steps for $DOMAIN"
echo "=========================================="
echo
echo "1. DNS Configuration"
echo "-------------------"
echo "Add the following DNS record in Cloudflare:"
echo "Type: CNAME"
echo "Name: ethereum"
echo "Target: $CLOUD_RUN_URL"
echo "Proxy status: Proxied (orange cloud)"
echo
echo "2. SSL/TLS Configuration"
echo "----------------------"
echo "Set the following in Cloudflare SSL/TLS settings:"
echo "- SSL/TLS encryption mode: Full (strict)"
echo "- Always Use HTTPS: On"
echo "- Min TLS Version: 1.2"
echo "- Opportunistic Encryption: On"
echo "- TLS 1.3: On"
echo "- Automatic HTTPS Rewrites: On"
echo
echo "3. Page Rules"
echo "------------"
echo "Create the following page rules:"
echo
echo "Rule 1 - Cache Configuration:"
echo "URL Pattern: $DOMAIN/*"
echo "Settings:"
echo "- Cache Level: Standard"
echo "- Edge Cache TTL: 2 hours"
echo "- Browser Cache TTL: 4 hours"
echo
echo "Rule 2 - Security Settings:"
echo "URL Pattern: $DOMAIN/*"
echo "Settings:"
echo "- Security Level: High"
echo "- Browser Integrity Check: On"
echo "- Enable Bot Fight Mode"
echo
echo "4. Verification Steps"
echo "------------------"
echo "After configuration, run these commands to verify:"
echo
echo "1. Check DNS propagation:"
echo "   dig $DOMAIN"
echo
echo "2. Verify HTTPS:"
echo "   curl -v https://$DOMAIN/health"
echo
echo "3. Check SSL configuration:"
echo "   openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
echo
echo "5. Testing Commands"
echo "-----------------"
echo "# Test health endpoint"
echo "curl https://$DOMAIN/health"
echo
echo "# Test API endpoints"
echo "curl https://$DOMAIN/api/v1/vaults"
echo
echo "# View API documentation"
echo "open https://$DOMAIN/api/docs"