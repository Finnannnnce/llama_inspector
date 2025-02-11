#!/bin/bash

# Configuration
DOMAIN="swacktech.com"
CLOUDFLARE_DNS="1.1.1.1"
CLOUD_RUN_URL="swacktech-frontend-330135650610.us-central1.run.app"

echo "DNS and HTTPS Verification for Root Domain"
echo "========================================"

# Function to check A records
check_a_records() {
    echo "Checking A records..."
    dig @$CLOUDFLARE_DNS $DOMAIN A +short
}

# Function to check AAAA records
check_aaaa_records() {
    echo "Checking AAAA records..."
    dig @$CLOUDFLARE_DNS $DOMAIN AAAA +short
}

# Function to check HTTPS
check_https() {
    echo "Testing HTTPS connection..."
    curl -sI https://$DOMAIN
}

# Function to check Cloud Run
check_cloud_run() {
    echo "Testing Cloud Run service..."
    curl -sI https://$CLOUD_RUN_URL
}

# Function to check SSL certificate
check_ssl() {
    echo "Checking SSL certificate..."
    echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -text | grep "Subject:"
}

# Main verification
echo -e "\nRunning checks at $(date)"
echo "-------------------------"

# Check A records
A_RECORDS=$(check_a_records)
if [ -z "$A_RECORDS" ]; then
    echo "❌ A records not found"
    echo "Required A records in Cloudflare:"
    echo "216.239.32.21"
    echo "216.239.34.21"
    echo "216.239.36.21"
    echo "216.239.38.21"
else
    echo "✅ A records found:"
    echo "$A_RECORDS"
fi

# Check AAAA records
AAAA_RECORDS=$(check_aaaa_records)
if [ -z "$AAAA_RECORDS" ]; then
    echo "❌ AAAA records not found"
    echo "Required AAAA records in Cloudflare:"
    echo "2001:4860:4802:32::15"
    echo "2001:4860:4802:34::15"
    echo "2001:4860:4802:36::15"
    echo "2001:4860:4802:38::15"
else
    echo "✅ AAAA records found:"
    echo "$AAAA_RECORDS"
fi

# Check HTTPS
if curl -s https://$DOMAIN > /dev/null; then
    echo "✅ HTTPS connection successful"
    check_ssl
else
    echo "❌ HTTPS connection failed"
    echo "Verify Cloudflare SSL/TLS settings:"
    echo "1. SSL/TLS encryption mode: Full (strict)"
    echo "2. Always Use HTTPS: Enabled"
    echo "3. Minimum TLS Version: 1.2"
    echo "4. Automatic HTTPS Rewrites: Enabled"
fi

# Check Cloud Run
if curl -s https://$CLOUD_RUN_URL > /dev/null; then
    echo "✅ Cloud Run service is accessible"
else
    echo "❌ Cloud Run service is not accessible"
fi

echo -e "\nVerification complete. If issues persist:"
echo "1. Ensure all DNS records are proxied (orange cloud) in Cloudflare"
echo "2. Check Cloudflare SSL/TLS settings"
echo "3. Wait for DNS propagation (5-10 minutes)"
echo "4. Verify domain mapping status:"
echo "   gcloud beta run domain-mappings describe --domain $DOMAIN --platform managed --region us-central1"