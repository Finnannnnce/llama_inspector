#!/bin/bash

# Configuration
SUBDOMAIN="ethereum"
DOMAIN="swacktech.com"
TARGET="ethereum-analyzer-oacz5ektba-ue.a.run.app"

echo "DNS Setup Verification Script"
echo "==========================="
echo
echo "1. Add this CNAME record in Cloudflare:"
echo "--------------------------------------"
echo "Type: CNAME"
echo "Name: $SUBDOMAIN"
echo "Target: $TARGET"
echo "Proxy status: Proxied (orange cloud)"
echo "TTL: Auto"
echo
echo "2. Verify DNS Configuration:"
echo "--------------------------"
echo "Running DNS checks..."

# Check Cloudflare DNS servers
echo "Checking Cloudflare DNS (1.1.1.1)..."
dig @1.1.1.1 $SUBDOMAIN.$DOMAIN

echo
echo "Checking Cloudflare DNS (1.0.0.1)..."
dig @1.0.0.1 $SUBDOMAIN.$DOMAIN

echo
echo "3. Clear local DNS cache:"
echo "----------------------"
echo "Run these commands:"
echo "sudo dscacheutil -flushcache"
echo "sudo killall -HUP mDNSResponder"

echo
echo "4. Test HTTPS after DNS propagation:"
echo "--------------------------------"
echo "curl -v https://$SUBDOMAIN.$DOMAIN/health"

echo
echo "5. Expected Results:"
echo "-----------------"
echo "- DNS should show CNAME or A record"
echo "- HTTPS should return 200 OK"
echo "- Response should include security headers"