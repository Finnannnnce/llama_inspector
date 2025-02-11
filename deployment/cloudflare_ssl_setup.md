# Cloudflare SSL/TLS Configuration Guide

## 1. Log into Cloudflare Dashboard
1. Go to https://dash.cloudflare.com
2. Log in with your account
3. Select the domain: swacktech.com

## 2. Configure SSL/TLS Settings
1. Click on "SSL/TLS" in the left sidebar
2. Under "Overview" tab:
   - Set SSL/TLS encryption mode to "Full (strict)"

3. Under "Edge Certificates" tab:
   - Enable "Always Use HTTPS"
   - Set Minimum TLS Version to 1.2
   - Enable "Automatic HTTPS Rewrites"

## 3. Verify DNS Settings
1. Click on "DNS" in the left sidebar
2. Verify CNAME record:
   - Type: CNAME
   - Name: ethereum
   - Target: ethereum-analyzer-oacz5ektba-ue.a.run.app
   - Proxy status: Proxied (orange cloud icon)

## 4. Add Page Rules
1. Click on "Rules" in the left sidebar
2. Click "Create Page Rule"
3. Add rule for caching:
   - URL pattern: ethereum.swacktech.com/*
   - Settings:
     * Cache Level: Standard
     * Edge Cache TTL: 2 hours
     * Browser Cache TTL: 4 hours

## 5. Expected Results
After configuring:
1. SSL/TLS status should show as "Active"
2. DNS record should show orange cloud (proxied)
3. HTTPS should be enforced automatically
4. Certificate should be issued by Cloudflare

## 6. Troubleshooting
If HTTPS still fails after configuration:
1. Verify SSL/TLS mode is "Full (strict)"
2. Check that DNS is proxied (orange cloud)
3. Wait 5-10 minutes for SSL certificate to be issued
4. Clear browser cache and DNS cache:
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

## 7. Verification Commands
```bash
# Check DNS resolution
dig ethereum.swacktech.com

# Test HTTPS connection
curl -v https://ethereum.swacktech.com/health

# View certificate details
openssl s_client -connect ethereum.swacktech.com:443 -servername ethereum.swacktech.com