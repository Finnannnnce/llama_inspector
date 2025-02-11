# SwackTech API Platform

## Overview

SwackTech provides enterprise-grade blockchain analytics APIs and tools. Our platform consists of:

1. Analytics API (swacktech.com)
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
   - Cloud Run deployment with zero-downtime updates

2. Frontend Interface
   - Streamlit-based web application
   - Clean, modern UI
   - Documentation integration
   - Quick-start guides

3. Infrastructure
   - Google Cloud Run with rolling updates
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
- [Deployment Context](docs/deployment_context.md) - Deployment and SSL configuration
- [Cloud Run DNS Setup](docs/cloud_run_dns_setup.md) - Cloud Run DNS configuration

## Deployment

### Backend API
```bash
# Deploy API service with rolling updates
gcloud run services replace cloud-run-config.yaml
```

### Frontend
```bash
# Deploy frontend with zero-downtime updates
gcloud run services replace cloud-run-config-streamlit.yaml --platform managed --region us-central1
```

### Domain Configuration
```bash
# Verify domain mapping
gcloud beta run domain-mappings describe --domain swacktech.com --platform managed --region us-central1

# Check DNS and SSL
./scripts/verify_root_dns.sh
./scripts/verify_ssl_fix.sh
```

## Development

### Prerequisites
- Python 3.9+
- Google Cloud SDK
- Docker (with amd64 platform support)
- Access to required API keys

### Local Setup
The project includes a start script that handles the development environment:
```bash
# Run the application (creates venv and installs dependencies if needed)
./start.sh
```

This will:
```bash
- Set up Python virtual environment
- Install all dependencies (including watchdog for better performance)
- Start both API (port 8000) and Frontend (port 8501) servers
```

## Infrastructure

### Domains
- swacktech.com - API service
- swacktech.net - Frontend interface

### Cloud Resources
- Cloud Run services with rolling updates
- Container Registry
- Secret Manager
- Cloud Monitoring

### Security
- SSL/TLS encryption (Cloudflare Full mode)
- Cloudflare protection
- Regular security updates
- Automated health checks
- TLS 1.2+ support

## Monitoring

### Health Checks
- API endpoint: http://localhost:8000/health
- Frontend: http://localhost:8501/_stcore/health
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