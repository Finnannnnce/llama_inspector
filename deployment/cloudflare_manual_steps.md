# Cloudflare Manual Configuration Steps

## 1. DNS Record Configuration
1. Log in to Cloudflare Dashboard
2. Select swacktech.com domain
3. Go to DNS → Records
4. Click "Add record" and enter:
   - Type: CNAME
   - Name: ethereum
   - Target: ethereum-analyzer-oacz5ektba-ue.a.run.app
   - Proxy status: Proxied (orange cloud)
   - TTL: Auto

## 2. SSL/TLS Settings
1. Go to SSL/TLS
2. Under Overview:
   - Set SSL/TLS encryption mode to "Full (strict)"
3. Under Edge Certificates:
   - Enable "Always Use HTTPS"
   - Set Minimum TLS Version to 1.2
   - Enable "Opportunistic Encryption"
   - Enable "TLS 1.3"
   - Enable "Automatic HTTPS Rewrites"

## 3. Page Rules Configuration
1. Go to Rules → Page Rules
2. Create two new page rules:

### Cache Rule
Click "Create Page Rule" and enter:
- URL Pattern: ethereum.swacktech.com/*
Settings:
- Cache Level: Standard
- Edge Cache TTL: 2 hours
- Browser Cache TTL: 4 hours
Order: 1

### Security Rule
Click "Create Page Rule" and enter:
- URL Pattern: ethereum.swacktech.com/*
Settings:
- Security Level: High
- Browser Integrity Check: On
- Enable Bot Fight Mode
Order: 2

## 4. Verification Steps
After completing the configuration, run these commands to verify:

```bash
# Check DNS propagation
dig ethereum.swacktech.com

# Verify HTTPS and security headers
curl -v https://ethereum.swacktech.com/health

# Test API endpoints
curl https://ethereum.swacktech.com/api/v1/vaults

# View API documentation
open https://ethereum.swacktech.com/api/docs
```

Expected Results:
- DNS should resolve to Cloudflare IPs
- HTTPS should work without certificate errors
- Security headers should be present in response
- API endpoints should return proper responses

## 5. Troubleshooting

If DNS is not resolving:
1. Verify CNAME record is correct
2. Wait 5-10 minutes for propagation
3. Clear local DNS cache:
   ```bash
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   ```

If SSL errors occur:
1. Verify SSL/TLS mode is set to "Full (strict)"
2. Check certificate is valid in browser
3. Verify HTTPS is enforced

If security headers are missing:
1. Verify page rules are in correct order
2. Check security settings are enabled
3. Clear Cloudflare cache if needed