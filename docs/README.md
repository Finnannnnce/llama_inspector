# Ethereum Loan Query Tool

A Python tool for querying lending vault information from Ethereum smart contracts with optimized RPC handling and SQLite-based caching.

## Latest Analysis Results (2025-02-10)

- Total Vaults Analyzed: 28
- Active Loans: 456
- Total Value Borrowed: $306.79T USD
- Total Collateral Value: $18.58Q USD
- Analysis Duration: 211.23 seconds
- Collateralization Ratio: 6056.85%

## API Documentation

The project includes a FastAPI-based REST API for querying vault information:

### Running the API

#### Local Development
```bash
# Install dependencies
pip3 install -r requirements.txt

# Start the API server
python3 api.py
```

#### Docker
```bash
# Build the Docker image
docker build -t ethereum-analytics .

# Run the container
docker run -p 8080:8080 ethereum-analytics
```

#### Cloud Run Deployment
The API is deployed on Google Cloud Run and available at:
https://ethereum-analytics-330135650610.us-central1.run.app

To deploy to Cloud Run:
```bash
# Build and push the image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/ethereum-analytics-api

# Deploy to Cloud Run
gcloud run deploy ethereum-analytics \
  --image gcr.io/[PROJECT_ID]/ethereum-analytics-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### API Endpoints

- GET /api/v1/vaults - List all vaults and their tokens
- GET /api/v1/vaults/{vault_address}/stats - Get vault statistics
- GET /api/v1/vaults/{vault_address}/users/{user_address} - Get user position
- GET /api/v1/vaults/{vault_address}/users - List vault users
- GET /api/v1/users/{user_address}/positions - Get user positions

### Documentation

#### Local Development
- Interactive API docs: http://localhost:8000/api/docs
- ReDoc documentation: http://localhost:8000/api/redoc
- OpenAPI schema: http://localhost:8000/api/openapi.json

#### Production (Cloud Run)
- Interactive API docs: https://ethereum-analytics-330135650610.us-central1.run.app/api/docs
- ReDoc documentation: https://ethereum-analytics-330135650610.us-central1.run.app/api/redoc
- OpenAPI schema: https://ethereum-analytics-330135650610.us-central1.run.app/api/openapi.json
- Full API reference: [docs/api_reference.md](docs/api_reference.md)

## Features

- Query factory contract for active vaults
- Get borrowed and collateral token information
- Calculate USD values using current token prices
- Support multiple RPC endpoints with fallback
- Handle rate limiting with exponential backoff
- Support both snake_case and camelCase function names
- SQLite-based caching system for web3 calls
- Batch processing for loan queries
- Automatic RPC endpoint switching on rate limits
- Type-safe implementation with full type hints
- Configurable parameters via YAML
- Colored terminal output
- Context saving for analysis results
- REST API with Swagger documentation
- Docker containerization
- Cloud Run deployment

## Architecture

### Configuration

All configuration parameters are stored in `config/analyzer_config.yaml`:

```yaml
# RPC Configuration
rpc_endpoints:
  - http://192.168.40.201:8545  # Local Ethereum node

# Batch Processing
batch_sizes:
  vault_discovery: 10
  loan_processing: 50

# Error Handling
error_limits:
  max_consecutive_errors: 5
  max_retries: 3
  retry_delay: 1.0

# Cache Configuration
cache:
  enabled: true
  storage: "sqlite"
  location: ".cache/web3_cache.db"
  ttl: 14400  # 4 hours in seconds
  cleanup_interval: 3600  # Run cleanup every hour

# Output
output:
  save_context: true
```

### Directory Structure

```
.
├── api.py                # API server runner
├── config/              # Configuration files
│   └── analyzer_config.yaml
├── contracts/          # Contract interfaces and ABIs
│   └── interfaces/
├── docs/              # Documentation
│   └── api_reference.md
├── src/              # Source code
│   ├── api/         # API implementation
│   ├── utils/       # Utility modules
│   └── contracts/   # Contract interaction modules
├── .cache/           # Cache directory
├── main.py          # CLI entry point
├── Dockerfile       # Docker configuration
└── README.md        # Documentation
```

### Contract Interfaces

[Previous contract interfaces section remains the same...]

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Create a `.env` file with your configuration:
```
# Optional: Add custom RPC endpoints
ETH_RPC_URL=https://your-eth-node.com
```

## Usage

### CLI Tool

Run the main script to query all vaults:

```bash
python3 main.py
```

### API Server

Run the API server:

```bash
python3 api.py
```

The API will be available at:
- http://localhost:8000/api/docs (Swagger UI)
- http://localhost:8000/api/redoc (ReDoc)

## Error Handling

The tool includes sophisticated error handling:
- Exponential backoff for rate limiting
- Multiple RPC endpoint fallbacks
- Support for different function naming conventions
- Graceful handling of contract errors
- Consecutive error detection
- Automatic endpoint switching on rate limits
- Type-safe operations with runtime checks

## Caching System

The tool implements a SQLite-based caching system:
- Uses SQLite for reliable and thread-safe caching
- 4-hour expiration for all web3 calls
- Automatic cache cleanup for expired entries
- JSON serialization for complex data types
- Cache structure:
  * Key: contract_address:function_name:args
  * Value: JSON-serialized result
  * Timestamp: Last update time
- Benefits:
  * Reduced RPC calls
  * Faster response times
  * Lower network usage
  * Better rate limit management

## Contributing

Feel free to contribute by:
1. Adding support for more contract patterns
2. Implementing additional data sources
3. Improving error handling and recovery
4. Adding new analytics features
5. Optimizing RPC usage patterns
6. Enhancing caching strategies
7. Adding tests and improving type safety