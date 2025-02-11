# SwackTech Frontend Documentation

## Overview

The SwackTech frontend (swacktech.net) provides a clean, user-friendly interface to access our API documentation and services. Built with Streamlit, it serves as the root page for our API hub.

## Architecture

### Components
1. Streamlit Application
   - Location: app.py
   - Purpose: Root page interface
   - Features: API overview, documentation links, integration examples

2. Container Infrastructure
   - Dockerfile.streamlit: Container definition
   - Base image: python:3.9-slim
   - Exposed port: 8501

3. Cloud Run Configuration
   - Service name: swacktech-frontend
   - Configuration: cloud-run-config-streamlit.yaml
   - Memory: 1Gi
   - CPU: 1 core
   - Auto-scaling: enabled (max 10 instances)

### Domain Setup
- Primary domain: swacktech.net
- SSL/TLS: Managed by Cloud Run
- DNS: Cloudflare managed

## Deployment

### Prerequisites
- Google Cloud SDK installed
- Docker installed
- Access to Google Cloud project
- Cloudflare DNS access

### Deployment Process
```bash
# Deploy frontend
./deploy_frontend.sh
```

The script handles:
1. Building Docker image
2. Pushing to Container Registry
3. Deploying to Cloud Run
4. Setting up domain mapping

### Environment Variables
- BASE_URL: https://ethereum.swacktech.com

## Development

### Local Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

### Directory Structure
```
├── app.py                         # Main Streamlit application
├── Dockerfile.streamlit           # Container configuration
├── cloud-run-config-streamlit.yaml # Cloud Run service config
├── deploy_frontend.sh            # Deployment script
└── requirements.txt              # Python dependencies
```

## Integration with API

The frontend integrates with the Ethereum Loan Analytics API by:
1. Providing direct links to API documentation
2. Showing integration examples
3. Displaying API status
4. Offering quick-start guides

## Security Considerations

1. Information Disclosure
   - No sensitive endpoints exposed
   - No internal URLs displayed
   - No configuration details revealed

2. Infrastructure Security
   - Cloud Run managed SSL/TLS
   - Cloudflare protection
   - Regular security updates

## Monitoring

1. Health Checks
   - Path: /_stcore/health
   - Port: 8501
   - Initial delay: 10s

2. Cloud Run Metrics
   - Request latency
   - Instance count
   - Memory usage
   - CPU utilization

## Maintenance

### Regular Tasks
1. Update dependencies
2. Check for security advisories
3. Monitor resource usage
4. Review access logs

### Update Process
1. Test changes locally
2. Build and test Docker image
3. Deploy using deploy_frontend.sh
4. Verify deployment success

## Troubleshooting

### Common Issues
1. Streamlit not starting
   - Check virtual environment
   - Verify dependencies
   - Check port availability

2. Deployment failures
   - Verify gcloud configuration
   - Check Docker build process
   - Validate YAML configurations

### Logs Access
```bash
# View Cloud Run logs
gcloud run services logs read swacktech-frontend