#!/bin/bash

echo "Setting up Direct DNS Resolution for Cloud Run"
echo "==========================================="

# 1. Remove domain mapping
echo "1. Removing existing domain mapping..."
gcloud beta run domain-mappings delete --domain=swacktech.com --platform=managed --region=us-east1 --quiet

# 2. Create new domain mapping
echo "2. Creating new domain mapping..."
gcloud beta run domain-mappings create --service=swacktech-frontend --domain=swacktech.com --platform=managed --region=us-east1 --force-override

# 3. Configure DNS Records
echo -e "\n3. DNS Records to Configure in Cloudflare:"
echo "a. Remove all existing A and AAAA records for swacktech.com"
echo "b. Add the following records with Proxy Status: DNS only (grey cloud):"
echo ""
echo "A Records:"
echo "- 216.239.32.21"
echo "- 216.239.34.21"
echo "- 216.239.36.21"
echo "- 216.239.38.21"
echo ""
echo "AAAA Records:"
echo "- 2001:4860:4802:32::15"
echo "- 2001:4860:4802:34::15"
echo "- 2001:4860:4802:36::15"
echo "- 2001:4860:4802:38::15"

# 4. SSL/TLS Configuration
echo -e "\n4. Cloudflare SSL/TLS Configuration:"
echo "a. Go to SSL/TLS > Overview"
echo "b. Set SSL/TLS encryption mode to 'Off (not secure)'"
echo "   This allows direct SSL handling by Cloud Run"
echo ""
echo "c. Under Edge Certificates:"
echo "   - Disable 'Always Use HTTPS'"
echo "   - Disable 'Automatic HTTPS Rewrites'"

# 5. Wait for propagation
echo -e "\n5. After making these changes:"
echo "   - Wait 5-10 minutes for DNS propagation"
echo "   - Wait for Cloud Run SSL certificate provisioning"
echo "   - Clear DNS cache if needed:"
echo "     sudo dscacheutil -flushcache"
echo "     sudo killall -HUP mDNSResponder"

# 6. Verify setup
echo -e "\n6. Verify DNS resolution:"
dig swacktech.com

echo -e "\nSetup complete! Please make the DNS and SSL/TLS changes in Cloudflare as shown above."