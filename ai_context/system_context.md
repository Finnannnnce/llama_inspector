# Ethereum Analytics Platform Context

## System Overview

This is an Ethereum analytics platform designed to query and analyze lending vault information from smart contracts. The system provides a FastAPI-based REST API with sophisticated caching, error handling, and multi-source price feeds.

## Core Components

### 1. API Layer (src/api/)
- FastAPI implementation with async endpoints
- Pydantic models for request/response validation
- Comprehensive error handling
- Endpoints:
  * /api/v1/rpc-nodes - List available Ethereum RPC nodes
  * /api/v1/vaults - List all vaults and tokens
  * /api/v1/vaults/{vault_address}/stats - Get vault statistics
  * /api/v1/vaults/{vault_address}/users/{user_address} - Get user position
  * /api/v1/vaults/{vault_address}/users - List vault users
  * /api/v1/users/{user_address}/positions - Get all user positions

### 2. Price Feed System (src/price_feeds/)
#### Architecture
- Abstract base class (PriceFeed) defining common interface
- Primary implementation (ChainlinkPriceFeed)
- Fallback implementation (CoinGeckoPriceFeed)
- Shared caching layer

#### Price Sources Hierarchy
1. Chainlink Oracles (Primary)
   - Uses Feed Registry contract
   - Handles ETH/USD special case
   - 7-day cache for feed addresses
   - Validates price data

2. CoinGecko API (Fallback)
   - Configurable token mappings
   - Stablecoin price overrides
   - Rate limiting (0.2s delay)
   - Two-step price calculation:
     * Get ETH/USD price
     * Get token/ETH price
     * Calculate token/USD price

### 3. Contract Interaction Layer (src/contracts/)
- Async Web3 implementation
- Multiple RPC endpoint support
- Rate limiting and retry mechanisms
- Smart contract interface caching
- Error handling with fallbacks

### 4. Caching System
#### SQLite Implementation
- Thread-safe and reliable
- 4-hour expiration for Web3 calls
- Automatic cache cleanup
- JSON serialization for complex data types
- Cache structure:
  * Key: contract_address:function_name:args
  * Value: JSON-serialized result
  * Timestamp: Last update time

#### Benefits
- Reduced RPC calls
- Faster response times
- Lower network usage
- Better rate limit management

### 5. Data Models
#### Core Models
1. TokenInfo
   - Token contract address
   - Name
   - Symbol
   - Decimals

2. VaultInfo
   - Vault contract address
   - Borrowed token info
   - Collateral token info

3. VaultStats
   - Total debt amount
   - Total collateral amount
   - USD values
   - Active loans count

4. UserPosition
   - User address
   - Vault address
   - Debt amount
   - Collateral amount
   - USD values

5. UserVaultSummary
   - User positions across vaults
   - Total debt USD
   - Total collateral USD

## Integration Points

### 1. External Services
- Chainlink Feed Registry
- CoinGecko API
- Multiple RPC providers:
  * Local Ethereum node
  * Alchemy
  * Infura
  * Ankr

### 2. Smart Contracts
- Factory contract
- Vault contracts
- Token contracts
- Price feed contracts

### 3. Configuration
- YAML-based configuration
- Environment variables
- Token mappings
- RPC endpoints
- Cache settings

## Key Features

### 1. Reliability
- Multiple price sources
- RPC endpoint fallbacks
- Comprehensive error handling
- Rate limit management
- Type-safe implementations

### 2. Performance
- Multi-layer caching
- Batch processing
- Async operations
- Connection pooling
- Request throttling

### 3. Maintainability
- Modular architecture
- Clear separation of concerns
- Comprehensive documentation
- Type hints throughout
- Consistent error handling

### 4. Scalability
- Containerized deployment
- Cloud Run ready
- Configurable instances
- Memory/CPU optimization
- Auto-scaling support

## Latest Analysis Results (2025-02-10)
- Total Vaults Analyzed: 28
- Active Loans: 456
- Total Value Borrowed: $306.79T USD
- Total Collateral Value: $18.58Q USD
- Analysis Duration: 211.23 seconds
- Collateralization Ratio: 6056.85%

## Deployment

### Local Development
```bash
pip3 install -r requirements.txt
python3 api.py
```

### Docker
```bash
docker build -t ethereum-analytics .
docker run -p 8080:8080 ethereum-analytics
```

### Cloud Run and Custom Domain
- Primary domain: https://ethereum.swacktech.com
- Cloud Run service: ethereum-analyzer-oacz5ektba-ue.a.run.app
- Auto-scaling configuration
- Secret management for API keys
- IAM role configuration
- Health check endpoints

### Domain Infrastructure
- DNS Provider: Cloudflare
- Edge IPs: 104.21.81.184, 172.67.163.97
- SSL/TLS: Full (strict) mode
- Automatic HTTPS enforcement
- Edge caching and security rules

### Security Features
- Cloudflare DDoS protection
- Browser integrity checks
- Security headers:
  * Strict-Transport-Security
  * Content-Security-Policy
  * X-Frame-Options
  * X-Content-Type-Options
  * X-XSS-Protection
- Rate limiting and bot protection

### Monitoring and Verification
- DNS propagation monitoring
- HTTPS connection verification
- Certificate validation
- Edge caching performance
- Security event tracking
- Health check monitoring

## Documentation
- Interactive API docs: /api/docs
- ReDoc documentation: /api/redoc
- OpenAPI schema: /api/openapi.json
- Full API reference: docs/api_reference.md