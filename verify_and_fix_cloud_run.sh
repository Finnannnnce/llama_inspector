#!/bin/bash

echo "Cloud Run Domain and SSL Verification/Fix Script"
echo "=============================================="

# 1. Verify/Create Domain Mapping
echo "1. Checking Cloud Run Domain Mapping..."
gcloud beta run domain-mappings delete --domain=swacktech.com --platform=managed --region=us-east1 --quiet
gcloud beta run domain-mappings create --service=swacktech-frontend --domain=swacktech.com --platform=managed --region=us-east1

# 2. Get Current DNS Records
echo -e "\n2. Current DNS Records:"
dig swacktech.com

# 3. Expected DNS Configuration
echo -e "\n3. Expected DNS Configuration:"
echo "A Records should point to:"
echo "- 216.239.32.21"
echo "- 216.239.34.21"
echo "- 216.239.36.21"
echo "- 216.239.38.21"
echo ""
echo "AAAA Records should point to:"
echo "- 2001:4860:4802:32::15"
echo "- 2001:4860:4802:34::15"
echo "- 2001:4860:4802:36::15"
echo "- 2001:4860:4802:38::15"

# 4. Cloudflare Configuration Steps
echo -e "\n4. Cloudflare Configuration Required:"
echo "a. DNS Settings:"
echo "   - Remove all existing A and AAAA records for swacktech.com"
echo "   - Add new A and AAAA records with above IPs"
echo "   - Set DNS only (grey cloud) for all records"
echo ""
echo "b. SSL/TLS Settings:"
echo "   - Set SSL/TLS encryption mode to 'Flexible'"
echo "   - Enable 'Always Use HTTPS'"
echo "   - Set Minimum TLS Version to 1.2"
echo "   - Enable 'Automatic HTTPS Rewrites'"

# 5. Verify Service Access
echo -e "\n5. Verifying direct Cloud Run access:"
gcloud run services describe swacktech-frontend --platform=managed --region=us-east1 --format="get(status.url)"

# 6. IAM Policy Check
echo -e "\n6. Verifying IAM Policy:"
gcloud run services get-iam-policy swacktech-frontend --platform=managed --region=us-east1

echo -e "\nAfter making these changes:"
echo "1. Wait 5-10 minutes for DNS propagation"
echo "2. Clear DNS cache:"
echo "   sudo dscacheutil -flushcache"
echo "   sudo killall -HUP mDNSResponder"
echo "3. Test the site: https://swacktech.com"