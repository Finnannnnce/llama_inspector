# System Context Summary

## Components Overview

### 1. API Service (ethereum.swacktech.com)
- FastAPI-based REST API
- Dual price feed system (Chainlink/CoinGecko)
- Multi-layer caching (SQLite/Redis)
- Cloud Run deployment with Cloudflare DNS/security

### 2. Frontend Interface (swacktech.net)
- Streamlit-based web application
- Clean, modern interface
- API documentation integration
- Integration examples and guides

## Infrastructure

### Cloud Run Services
1. ethereum-analyzer
   - Container: us-east1-docker.pkg.dev/homelab-424523/ethereum-analyzer/analyzer:latest
   - Resources: 2Gi memory, 1 CPU
   - Health checks on /health endpoint

2. swacktech-frontend
   - Container: gcr.io/homelab-424523/swacktech-frontend:latest
   - Resources: 1Gi memory, 1 CPU
   - Health checks:
     * Path: /_stcore/health
     * Startup: 1s period, 1s timeout, 30 retries
     * Readiness: Immediate checks
     * Port: 8000

### Domain Configuration
1. ethereum.swacktech.com
   - Points to ethereum-analyzer service
   - SSL/TLS managed by Cloud Run
   - Cloudflare proxy enabled

2. swacktech.net
   - Points to swacktech-frontend service
   - SSL/TLS managed by Cloud Run
   - Cloudflare proxy enabled

## Configuration Files

### API Service
- app.py: Combined Streamlit frontend and FastAPI backend
- cloud-run-config.yaml: API service configuration
- domain-mapping.yaml: Domain mapping for ethereum.swacktech.com
- requirements.txt: Python dependencies

### Frontend
- cloud-run-config-streamlit.yaml: Frontend service configuration
- Dockerfile.streamlit: Container configuration for combined service

## Documentation
1. API Documentation
   - api_reference.md: Complete API documentation
   - custom_domain_setup.md: Domain configuration guide
   - architecture.md: System architecture details
   - configuration.md: Configuration reference
   - system_context.md: System context details

2. Frontend Documentation
   - frontend.md: Frontend implementation details
   - README.md: Project overview and setup guide

## Monitoring & Security

### Health Monitoring
1. API Service
   - /health endpoint
   - Resource monitoring
   - Error tracking

2. Frontend
   - /_stcore/health endpoint
   - Instance monitoring
   - Performance metrics

### Security Measures
1. SSL/TLS
   - Cloud Run managed certificates
   - Cloudflare SSL/TLS encryption
   - Automatic certificate renewal

2. Access Control
   - No sensitive information exposed
   - Public API endpoints
   - Documentation access controls

## Development Environment

### Local Setup
```bash
# API Service
# Combined frontend and API setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py  # Starts both Streamlit and FastAPI servers
# Access frontend at :8501 and API at :8000
```

### Deployment Process
1. API Service
   ```bash
   gcloud run services replace cloud-run-config.yaml
   ```

2. Frontend
   ```bash
   gcloud run services replace cloud-run-config-streamlit.yaml \
     --platform managed --region us-central1 --async
   ```

## Current Analysis Results (2025-02-10)
- Total Vaults: 28
- Active Loans: 456
- Total Value Borrowed: $306.79T USD
- Total Collateral Value: $18.58Q USD
- Analysis Duration: 211.23 seconds
- Collateralization Ratio: 6056.85%

## Required Environment Variables
1. API Service
   - ALCHEMY_API_KEY
   - INFURA_PROJECT_ID (pending)
   - ANKR_API_KEY (pending)

2. Frontend
   - BASE_URL=https://ethereum.swacktech.com