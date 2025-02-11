# SwackTech API Platform

## Overview

SwackTech provides enterprise-grade blockchain analytics APIs and tools. Our platform consists of:

1. Ethereum Loan Analytics API (ethereum.swacktech.com)
   - Real-time lending protocol analytics
   - Vault statistics and monitoring
   - User position tracking
   - Multi-token support

2. API Hub Frontend (swacktech.net)
   - Central access point for API documentation
   - Integration guides and examples
   - Real-time API status monitoring

## Architecture

### Components

1. Backend Services
   - FastAPI-based REST API
   - Multi-source price feeds (Chainlink/CoinGecko)
   - SQLite and Redis caching
   - Cloud Run deployment

2. Frontend Interface
   - Streamlit-based web application
   - Clean, modern UI
   - Documentation integration
   - Quick-start guides

3. Infrastructure
   - Google Cloud Run
   - Cloudflare DNS/CDN
   - Automated deployments
   - Health monitoring

## Documentation

- [API Reference](docs/api_reference.md) - Complete API documentation
- [Frontend Guide](docs/frontend.md) - Frontend implementation details
- [Architecture Overview](ai_context/architecture.md) - System architecture
- [Configuration Guide](ai_context/configuration.md) - System configuration
- [System Context](ai_context/system_context.md) - Comprehensive system context
- [Custom Domain Setup](docs/custom_domain_setup.md) - Domain configuration

## Deployment

### Backend API
```bash
# Deploy API service
gcloud run services replace cloud-run-config.yaml
```

### Frontend
```bash
# Deploy frontend
./deploy_frontend.sh
```

## Development

### Prerequisites
- Python 3.9+
- Google Cloud SDK
- Docker
- Access to required API keys

### Local Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API
python api.py

# Run frontend
streamlit run app.py
```

## Infrastructure

### Domains
- ethereum.swacktech.com - API service
- swacktech.net - Frontend interface

### Cloud Resources
- Cloud Run services
- Container Registry
- Secret Manager
- Cloud Monitoring

### Security
- SSL/TLS encryption
- Cloudflare protection
- Regular security updates
- Automated health checks

## Monitoring

### Health Checks
- API endpoint: /health
- Frontend: /_stcore/health
- Automated monitoring

### Metrics
- Request latency
- Error rates
- Instance count
- Resource utilization

## Support

For technical support or inquiries:
1. Review the [API Documentation](docs/api_reference.md)
2. Check [Frontend Guide](docs/frontend.md)
3. Visit the API Hub at [swacktech.net](https://swacktech.net)

## License

Copyright © 2025 SwackTech. All rights reserved.