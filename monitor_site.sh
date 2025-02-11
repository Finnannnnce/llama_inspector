#!/bin/bash

URL="https://swacktech.com"
CHECK_INTERVAL=30  # seconds between checks

echo "Monitoring $URL"
echo "Checking every $CHECK_INTERVAL seconds..."
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -n "[$timestamp] Checking $URL... "
    
    # Try to get HTTP status code and response time
    response=$(curl -o /dev/null -s -w "%{http_code},%{time_total},%{ssl_verify_result}" -k $URL)
    http_code=$(echo $response | cut -d',' -f1)
    time_taken=$(echo $response | cut -d',' -f2)
    ssl_result=$(echo $response | cut -d',' -f3)
    
    # Check response
    if [ "$http_code" = "200" ]; then
        echo -e "\033[32m✓ Site is UP\033[0m (Response: $http_code, Time: ${time_taken}s)"
        
        # Additional checks
        echo "  DNS Resolution:"
        dig +short A $URL | sed 's/^/    A: /'
        dig +short AAAA $URL | sed 's/^/    AAAA: /'
        
        echo "  SSL Certificate:"
        echo | openssl s_client -connect swacktech.com:443 2>/dev/null | openssl x509 -noout -dates | sed 's/^/    /'
        
        echo "----------------------------------------"
        exit 0
    elif [ "$http_code" = "000" ]; then
        echo -e "\033[31m✗ Connection failed\033[0m"
    elif [ "$http_code" = "525" ]; then
        echo -e "\033[31m✗ SSL Handshake failed\033[0m"
    else
        echo -e "\033[31m✗ Site is DOWN\033[0m (Response: $http_code)"
    fi
    
    # Check DNS
    echo "  Current DNS Records:"
    dig +short A $URL | sed 's/^/    A: /'
    dig +short AAAA $URL | sed 's/^/    AAAA: /'
    
    echo "----------------------------------------"
    sleep $CHECK_INTERVAL
done