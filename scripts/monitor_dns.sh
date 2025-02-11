#!/bin/bash

# Configuration
DOMAIN="swacktech.com"
CHECK_INTERVAL=30  # seconds between checks
PROGRESS_BAR_WIDTH=50

# Expected records
A_RECORDS=(
    "216.239.32.21"
    "216.239.34.21"
    "216.239.36.21"
    "216.239.38.21"
)

AAAA_RECORDS=(
    "2001:4860:4802:32::15"
    "2001:4860:4802:34::15"
    "2001:4860:4802:36::15"
    "2001:4860:4802:38::15"
)

# Function to draw progress bar
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=$3
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\rWaiting: ["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' ' '
    printf "] %d%%" $percentage
}

echo "DNS Record Verification for Cloud Run Domain Mapping"
echo "=================================================="

check_number=1
while true; do
    echo -e "\nCheck #$check_number at $(date):"
    echo "------------------"
    
    # Check A records
    echo "A Records:"
    echo "Expected:"
    printf '%s\n' "${A_RECORDS[@]}" | sed 's/^/- /'
    echo -e "\nActual:"
    dig +short A $DOMAIN | sed 's/^/- /'
    
    # Check AAAA records
    echo -e "\nAAAA Records:"
    echo "Expected:"
    printf '%s\n' "${AAAA_RECORDS[@]}" | sed 's/^/- /'
    echo -e "\nActual:"
    dig +short AAAA $DOMAIN | sed 's/^/- /'
    
    # Check certificate status
    echo -e "\nCertificate Status:"
    cert_status=$(gcloud beta run domain-mappings describe \
        --domain=${DOMAIN} \
        --platform=managed \
        --format="get(status.conditions[?(@.type=='CertificateProvisioned')].status)")
    
    cert_message=$(gcloud beta run domain-mappings describe \
        --domain=${DOMAIN} \
        --platform=managed \
        --format="get(status.conditions[?(@.type=='CertificateProvisioned')].message)")
    
    if [[ "$cert_status" == "True" ]]; then
        echo "✅ Certificate provisioned successfully"
        echo "DNS propagation complete and certificate is ready"
        echo "You can now re-enable Cloudflare proxy (orange cloud)"
        exit 0
    else
        echo "⏳ Certificate pending: $cert_message"
    fi
    
    # Check if DNS matches expected configuration
    current_records=($(dig +short A $DOMAIN))
    if [[ ${#current_records[@]} -eq ${#A_RECORDS[@]} ]]; then
        match=true
        for record in "${current_records[@]}"; do
            if [[ ! " ${A_RECORDS[@]} " =~ " ${record} " ]]; then
                match=false
                break
            fi
        done
        if [[ "$match" == "true" ]]; then
            echo "✅ A records match expected configuration"
        else
            echo "❌ A records do not match expected configuration"
        fi
    else
        echo "❌ A records do not match expected configuration"
    fi
    
    echo -e "\nWaiting for next check..."
    for ((i=1; i<=CHECK_INTERVAL; i++)); do
        draw_progress_bar $i $CHECK_INTERVAL $PROGRESS_BAR_WIDTH
        sleep 1
    done
    echo -e "\n----------------------------------------"
    
    ((check_number++))
done