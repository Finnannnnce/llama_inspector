# System Configuration Reference

## Configuration Files

### 1. analyzer_config.yaml
Primary configuration file for the analytics system.

```yaml
# RPC Configuration
rpc_endpoints:
  - http://192.168.40.201:8545  # Local Ethereum node
  - https://eth-mainnet.alchemyapi.io/v2/${ALCHEMY_API_KEY}
  - https://mainnet.infura.io/v3/${INFURA_PROJECT_ID}
  - https://rpc.ankr.com/eth/${ANKR_API_KEY}

# Batch Processing
batch_sizes:
  vault_discovery: 10    # Number of vaults to process in parallel
  loan_processing: 50    # Number of loans to process in parallel

# Error Handling
error_limits:
  max_consecutive_errors: 5  # Max errors before switching RPC
  max_retries: 3            # Max retry attempts per call
  retry_delay: 1.0          # Base delay between retries (seconds)

# Cache Configuration
cache:
  enabled: true
  storage: "sqlite"
  location: ".cache/web3_cache.db"
  ttl: 14400              # 4 hours in seconds
  cleanup_interval: 3600  # Run cleanup every hour

# Output Configuration
output:
  save_context: true      # Save analysis context to file
```

### 2. Cloud Run Configuration (cloud-run-config.yaml)
Deployment configuration for Google Cloud Run.

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ethereum-analyzer
spec:
  template:
    spec:
      containers:
        - image: gcr.io/PROJECT_ID/ethereum-analyzer
          ports:
            - containerPort: 8080
          resources:
            limits:
              memory: "2Gi"
              cpu: "1"
          env:
            - name: ALCHEMY_API_KEY
              valueFrom:
                secretKeyRef:
                  name: rpc-credentials
                  key: alchemy
            - name: INFURA_PROJECT_ID
              valueFrom:
                secretKeyRef:
                  name: rpc-credentials
                  key: infura
            - name: ANKR_API_KEY
              valueFrom:
                secretKeyRef:
                  name: rpc-credentials
                  key: ankr
```

## Environment Variables

### Required Variables
- `ALCHEMY_API_KEY`: Alchemy API key for RPC access
- `INFURA_PROJECT_ID`: Infura project ID for RPC access
- `ANKR_API_KEY`: Ankr API key for RPC access

### Optional Variables
- `ETH_RPC_URL`: Custom Ethereum RPC endpoint
- `CACHE_TTL`: Override default cache TTL
- `LOG_LEVEL`: Set logging verbosity
- `PORT`: Override default API port

## Cache Configuration

### Web3 Cache
- Location: .cache/web3_cache.db
- Type: SQLite
- TTL: 4 hours
- Schema:
  ```sql
  CREATE TABLE web3_cache (
      key TEXT PRIMARY KEY,
      result TEXT,
      timestamp REAL
  )
  ```

### Price Cache
- Location: .cache/price_cache.json
- Type: JSON file
- TTL: 1 hour
- Format:
  ```json
  {
    "token_address": {
      "price": "decimal_string",
      "timestamp": "unix_timestamp"
    }
  }
  ```

## Rate Limiting

### RPC Calls
- Default: 50 calls per second
- Retry delay: 1.0 second base
- Exponential backoff: 2^attempt * base_delay
- Max retries: 3

### CoinGecko API
- Delay between calls: 0.2 seconds
- Cache duration: 1 hour
- Automatic fallback to cached data

## Security

### API Authentication
- Cloud Run IAM roles
- Secret Manager access
- Public endpoints (no auth required)

### RPC Security
- SSL verification
- API key rotation
- Rate limit monitoring
- Error tracking

## Monitoring

### Cloud Run Metrics
- Request latency
- Error rates
- Instance count
- Memory usage
- CPU utilization

### Custom Metrics
- Cache hit rates
- RPC endpoint health
- Price feed accuracy
- Analysis duration
- Active vaults/loans

## Error Handling

### RPC Errors
- Automatic endpoint switching
- Exponential backoff
- Error logging
- Status monitoring

### Price Feed Errors
- Chainlink → CoinGecko fallback
- Cache fallback
- Error reporting
- Alert thresholds

## Performance Tuning

### Cache Settings
- TTL optimization
- Storage type selection
- Cleanup frequency
- Key structure

### Batch Processing
- Vault discovery size
- Loan processing size
- Concurrent requests
- Memory limits

### RPC Optimization
- Endpoint prioritization
- Connection pooling
- Request batching
- Timeout configuration