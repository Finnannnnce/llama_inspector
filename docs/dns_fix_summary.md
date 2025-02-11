# DNS Configuration Fix for swacktech.com

## Current Issue
- DNS records are pointing to Cloudflare proxy IPs
- SSL certificate cannot be provisioned by Google Cloud Run
- Domain verification challenge failing

## Current Configuration
A Records (incorrect):
- 104.21.81.184
- 172.67.163.97

AAAA Records (incorrect):
- 2606:4700:3034::ac43:a361
- 2606:4700:3032::6815:51b8

## Required Configuration
A Records:
- 216.239.32.21
- 216.239.34.21
- 216.239.36.21
- 216.239.38.21

AAAA Records:
- 2001:4860:4802:32::15
- 2001:4860:4802:34::15
- 2001:4860:4802:36::15
- 2001:4860:4802:38::15

## Steps to Fix

1. Cloudflare DNS Settings
   - Go to Cloudflare Dashboard
   - Select swacktech.com
   - Navigate to DNS settings
   - Remove all existing A and AAAA records for the root domain

2. Add New Records
   - Add all A records listed above
   - Add all AAAA records listed above
   - Set Proxy status to DNS only (gray cloud) temporarily
   - Set TTL to Auto

3. Wait for Certificate
   - Allow 5-10 minutes for DNS propagation
   - Wait for Google Cloud Run to provision SSL certificate
   - Monitor status with: `./fix_dns.sh`

4. Re-enable Cloudflare Proxy
   - Once certificate is provisioned
   - Change DNS records back to proxied (orange cloud)
   - Verify HTTPS is working

## Verification Commands
```bash
# Check DNS propagation
dig +short swacktech.com
dig +short AAAA swacktech.com

# Check domain mapping status
gcloud beta run domain-mappings describe \
  --domain=swacktech.com \
  --platform=managed
```

## Expected Outcome
1. DNS records will point to Google Cloud Run IPs
2. SSL certificate will be provisioned
3. Domain will serve content from Cloud Run
4. HTTPS will work properly