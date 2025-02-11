# SwackTech Analytics API

API for querying blockchain lending vault information.

## API Documentation

The API is deployed at:
- Base URL: https://swacktech-api-330135650610.us-central1.run.app
- Swagger UI: https://swacktech-api-330135650610.us-central1.run.app/api/v1/docs
- OpenAPI Schema: https://swacktech-api-330135650610.us-central1.run.app/api/v1/openapi.json

## Endpoints

### Health Check
- `GET /health`: Check API health status

### API v1 Endpoints
- `GET /api/v1/rpc-nodes`: List available Ethereum RPC nodes
- `GET /api/v1/vaults`: List all vaults with token information
- `GET /api/v1/vaults/{vault_address}/stats`: Get statistics for a specific vault
- `GET /api/v1/vaults/{vault_address}/users`: List users with positions in a vault
- `GET /api/v1/vaults/{vault_address}/users/{user_address}`: Get user's position in a vault
- `GET /api/v1/users/{user_address}/positions`: Get all positions for a user across vaults

## Development

### Local Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run development server:
```bash
uvicorn src.api.app:app --reload --port 8000
```

### Docker Build
```bash
docker build -f deployment/Dockerfile.api -t swacktech-api .
```

### Deployment
Deploy to Google Cloud Run:
```bash
./scripts/deploy_api.sh
```

## Architecture

The API is built with:
- FastAPI for the web framework
- Python 3.9 for the runtime
- Docker for containerization
- Google Cloud Run for serverless deployment

Key features:
- API versioning with /api/v1 prefix
- Interactive Swagger UI documentation
- OpenAPI schema generation
- Health check endpoint for monitoring
- CORS middleware for cross-origin requests
- Error handling middleware
- Request validation
- Response serialization