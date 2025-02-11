# Google Cloud Domain Verification Guide

## 1. Get Verification Details
```bash
gcloud domains verify ethereum.swacktech.com
```
This will open the Search Console to get the verification record.

## 2. Add TXT Record in Cloudflare
1. Log into Cloudflare Dashboard
2. Select swacktech.com domain
3. Go to DNS → Records
4. Add new record:
   - Type: TXT
   - Name: ethereum
   - Content: [verification string from Google Search Console]
   - TTL: Auto
   - Proxy status: DNS only (gray cloud)

## 3. Wait for Propagation
- Wait 5-10 minutes for DNS propagation
- Verify TXT record:
  ```bash
  dig TXT ethereum.swacktech.com
  ```

## 4. Complete Verification
1. Return to Google Search Console
2. Click "Verify" button
3. Wait for verification to complete

## 5. Create Domain Mapping
After verification is complete:
```bash
gcloud beta run domain-mappings create \
  --service=ethereum-analyzer \
  --domain=ethereum.swacktech.com \
  --platform=managed \
  --region=us-east1
```

## 6. Update Cloudflare DNS
1. Update CNAME record:
   - Type: CNAME
   - Name: ethereum
   - Target: ghs.googlehosted.com
   - Proxy status: Proxied (orange cloud)

## 7. Verify Setup
```bash
# Check domain mapping
gcloud beta run domain-mappings describe \
  --domain=ethereum.swacktech.com \
  --platform=managed \
  --region=us-east1

# Test HTTPS
curl -v https://ethereum.swacktech.com/health
```

## Troubleshooting

If verification fails:
1. Check TXT record is correct
2. Ensure TXT record is not proxied
3. Clear DNS cache:
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```
4. Wait longer for DNS propagation
5. Try verification again