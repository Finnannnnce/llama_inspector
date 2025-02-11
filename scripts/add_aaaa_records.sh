#!/bin/bash

echo "Adding AAAA Records for Cloud Run SSL Certificate"
echo "=============================================="

echo "Current DNS Records:"
echo "A Records:"
dig +short A swacktech.com

echo -e "\nAAAA Records:"
dig +short AAAA swacktech.com

echo -e "\nRequired AAAA Records to Add in Cloudflare:"
echo "1. Add these AAAA records (all with DNS only - grey cloud):"
echo "   - Type: AAAA"
echo "   - Name: @"
echo "   - Content: 2001:4860:4802:32::15"
echo "   - Proxy: DNS only (grey cloud)"
echo "   - TTL: Auto"
echo ""
echo "   - Type: AAAA"
echo "   - Name: @"
echo "   - Content: 2001:4860:4802:34::15"
echo "   - Proxy: DNS only (grey cloud)"
echo "   - TTL: Auto"
echo ""
echo "   - Type: AAAA"
echo "   - Name: @"
echo "   - Content: 2001:4860:4802:36::15"
echo "   - Proxy: DNS only (grey cloud)"
echo "   - TTL: Auto"
echo ""
echo "   - Type: AAAA"
echo "   - Name: @"
echo "   - Content: 2001:4860:4802:38::15"
echo "   - Proxy: DNS only (grey cloud)"
echo "   - TTL: Auto"

echo -e "\nAfter adding records:"
echo "1. Wait 5-10 minutes for DNS propagation"
echo "2. Cloud Run will automatically detect the records"
echo "3. SSL certificate will be provisioned"
echo "4. Run this command to verify AAAA records:"
echo "   dig +short AAAA swacktech.com"