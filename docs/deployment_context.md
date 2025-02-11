# Deployment Context Summary

## Cloud Run Deployment

1. Docker Configuration
   - Main Dockerfile configured for amd64 architecture
   - Streamlit Dockerfile configured for amd64 architecture
   - Both using --platform linux/amd64 for builds

2. Cloud Run Service Configuration
   - Service: swacktech-frontend
   - Region: us-central1
   - Memory: 1Gi
   - CPU: 1 core
   - Auto-scaling: 0-10 instances
   - Health checks configured on /_stcore/health
   - Environment variables:
     * BASE_URL=https://swacktech.com

3. Domain Mapping
   - Domain: swacktech.com
   - Mapped to: swacktech-frontend service
   - SSL certificate provisioning enabled
   - Required DNS records:
     * A Records:
       - 216.239.32.21
       - 216.239.34.21
       - 216.239.36.21
       - 216.239.38.21
     * AAAA Records:
       - 2001:4860:4802:32::15
       - 2001:4860:4802:34::15
       - 2001:4860:4802:36::15
       - 2001:4860:4802:38::15

## Cloudflare Configuration

1. DNS Settings
   - A and AAAA records pointing to Google Cloud Run IPs
   - Proxy status: DNS only (grey cloud) during setup, then proxied (orange cloud)
   - TTL: Auto

2. SSL/TLS Configuration
   - Mode: Full (not Full Strict)
   - TLS 1.3: Enabled
   - Minimum TLS Version: 1.2
   - Always Use HTTPS: Enabled
   - Automatic HTTPS Rewrites: Enabled

3. Page Rules
   - URL Pattern: swacktech.com/*
   - Settings:
     * SSL: Full
     * Cache Level: Standard
     * Edge Cache TTL: 2 hours
     * Browser Cache TTL: 4 hours

## Deployment Scripts

1. Cloud Run Deployment
   ```bash
   ./scripts/deploy_to_cloud_run.sh
   ```
   - Builds Docker image with amd64 platform
   - Pushes to Container Registry
   - Deploys to Cloud Run

2. DNS Verification
   ```bash
   ./scripts/verify_root_dns.sh
   ```
   - Checks A and AAAA records
   - Verifies SSL certificates
   - Tests Cloud Run health endpoint

3. SSL Verification
   ```bash
   ./scripts/verify_ssl_fix.sh
   ```
   - Tests direct Cloud Run connection
   - Tests Cloudflare proxied connection
   - Verifies SSL certificates
   - Checks DNS resolution

## Troubleshooting Documents

1. SSL Configuration
   - cloudflare_ssl_fix.txt: Initial SSL configuration
   - cloudflare_ssl_fix_v2.txt: Updated SSL fix with step-by-step guide
   - cloudflare_root_update.txt: Root domain configuration

2. Verification Steps
   ```bash
   # Check domain mapping
   gcloud beta run domain-mappings describe --domain swacktech.com --platform managed --region us-central1

   # Test direct Cloud Run
   curl -v https://swacktech-frontend-330135650610.us-central1.run.app/_stcore/health

   # Test through Cloudflare
   curl -v https://swacktech.com/_stcore/health
   ```

## Important Notes

1. SSL Setup Order
   - Disable Cloudflare proxy initially
   - Configure SSL/TLS settings
   - Enable features gradually
   - Re-enable proxy after SSL works

2. DNS Propagation
   - Wait 5-10 minutes after DNS changes
   - Clear local DNS cache if needed
   - Verify with dig commands

3. Certificate Provisioning
   - Cloud Run manages its own certificates
   - Cloudflare provides edge certificates
   - Use "Full" mode to avoid certificate conflicts