# Setting up Custom Domain with Cloudflare and Cloud Run

## Prerequisites
- Domain registered and managed by Cloudflare (swacktech.com)
- Google Cloud project with Cloud Run service deployed
- Access to both Cloudflare and Google Cloud Console

## 1. Verify Domain Ownership

1. In Google Cloud Console, go to Cloud Run > Domain Mappings
2. Click "Add Domain Mapping"
3. Enter domain: `ethereum.swacktech.com`
4. Note the verification records provided by Google

## 2. Configure Cloudflare DNS

1. Log in to Cloudflare dashboard
2. Select swacktech.com domain
3. Go to DNS settings
4. Add the following records:

```
# TXT record for domain verification
Type: TXT
Name: ethereum
Content: [Google verification string]

# CNAME record for the service
Type: CNAME
Name: ethereum
Target: ghs.googlehosted.com
Proxy status: Proxied
```

## 3. Configure Cloudflare SSL/TLS

1. Go to SSL/TLS settings
2. Set SSL/TLS encryption mode to "Full (strict)"
3. Under Edge Certificates:
   - Enable "Always Use HTTPS"
   - Set Minimum TLS Version to 1.2
   - Enable Automatic HTTPS Rewrites

## 4. Configure Cloud Run Domain Mapping

```bash
# Apply the domain mapping configuration
gcloud run domain-mappings create \
  --service=ethereum-analyzer \
  --domain=ethereum.swacktech.com \
  --region=us-east1 \
  --platform=managed

# Verify the mapping status
gcloud run domain-mappings describe \
  --domain=ethereum.swacktech.com \
  --region=us-east1 \
  --platform=managed
```

## 5. Configure Cloudflare Page Rules

Create the following page rules:

1. Cache Rule:
```
URL Pattern: ethereum.swacktech.com/*
Settings:
- Cache Level: Standard
- Edge Cache TTL: 2 hours
- Browser Cache TTL: 4 hours
```

2. Security Rule:
```
URL Pattern: ethereum.swacktech.com/*
Settings:
- Security Level: High
- Browser Integrity Check: On
- Enable Bot Fight Mode
```

## 6. Update Application Configuration

1. Update the Cloud Run service to handle the custom domain:
```bash
gcloud run services update ethereum-analyzer \
  --platform=managed \
  --region=us-east1 \
  --ingress=all
```

2. Configure CORS in the application to allow the custom domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ethereum.swacktech.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 7. Verify Setup

1. Test the domain:
```bash
# Test HTTPS access
curl https://ethereum.swacktech.com/health

# Test API endpoints
curl https://ethereum.swacktech.com/api/v1/vaults
```

2. Verify SSL certificate:
```bash
# Check SSL configuration
openssl s_client -connect ethereum.swacktech.com:443 -servername ethereum.swacktech.com
```

## 8. Monitoring and Maintenance

### Cloudflare Analytics
Monitor through Cloudflare dashboard:
- Traffic analytics
- Cache performance
- Security events
- SSL/TLS encryption stats

### Cloud Run Monitoring
Monitor through Google Cloud Console:
- Request latency
- Error rates
- Instance count
- Resource utilization

### Health Checks
- Cloud Run health checks configured in cloud-run-config.yaml
- Cloudflare monitors SSL/TLS status
- Regular certificate renewal handled automatically

## Troubleshooting

### Common Issues

1. DNS Resolution
```bash
# Verify DNS propagation
dig ethereum.swacktech.com
dig ethereum.swacktech.com +trace
```

2. SSL/TLS Issues
```bash
# Test SSL configuration
openssl s_client -connect ethereum.swacktech.com:443 -servername ethereum.swacktech.com

# Verify certificate chain
curl -vI https://ethereum.swacktech.com
```

3. Cloud Run Mapping
```bash
# Check mapping status
gcloud run domain-mappings describe \
  --domain=ethereum.swacktech.com \
  --region=us-east1
```

### Support Resources
- Cloudflare Support: https://support.cloudflare.com
- Cloud Run Documentation: https://cloud.google.com/run/docs
- Custom Domain Mapping: https://cloud.google.com/run/docs/mapping-custom-domains