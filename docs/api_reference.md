# Ethereum Loan Analytics API Reference

## Overview

API for querying Ethereum lending vault information. Provides endpoints for retrieving vault information, user positions, and loan statistics.

Base URL: `https://ethereum-analyzer-330135650610.us-east1.run.app`

## Root Endpoint

The root endpoint (`/`) automatically redirects to the API documentation.

```
GET /
```

#### Response

Redirects to `/api/docs`

## Authentication

Currently, no authentication is required.

## Endpoints

### List Vaults

Get a list of all vaults with their borrowed and collateral token information.

```
GET /api/v1/vaults
```

#### Response

```json
[
  {
    "address": "0x1E0165DbD2019441aB7927C018701f3138114D71",
    "borrowed_token": {
      "address": "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E",
      "name": "Curve.Fi USD Stablecoin",
      "symbol": "crvUSD",
      "decimals": 18
    },
    "collateral_token": {
      "address": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
      "name": "Wrapped liquid staked Ether 2.0",
      "symbol": "wstETH",
      "decimals": 18
    }
  }
]
```

### Get Vault Statistics

Get statistics for a specific vault including total debt, collateral, and number of active loans.

```
GET /api/v1/vaults/{vault_address}/stats
```

#### Parameters

- `vault_address`: Ethereum address of the vault

#### Response

```json
{
  "address": "0x1E0165DbD2019441aB7927C018701f3138114D71",
  "total_debt": "1000000000000000000",
  "total_collateral": "500000000000000000",
  "total_debt_usd": "1000.00",
  "total_collateral_usd": "1500.00",
  "active_loans": 24
}
```

### Get User Position

Get a user's position (debt and collateral) in a specific vault.

```
GET /api/v1/vaults/{vault_address}/users/{user_address}
```

#### Parameters

- `vault_address`: Ethereum address of the vault
- `user_address`: Ethereum address of the user

#### Response

```json
{
  "user_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "vault_address": "0x1E0165DbD2019441aB7927C018701f3138114D71",
  "debt": "1000000000000000000",
  "collateral": "500000000000000000",
  "debt_usd": "1000.00",
  "collateral_usd": "1500.00"
}
```

### List Vault Users

Get a list of all users with positions in a specific vault.

```
GET /api/v1/vaults/{vault_address}/users
```

#### Parameters

- `vault_address`: Ethereum address of the vault

#### Response

```json
[
  "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "0x8C2537F1a5b1b167A960A14B89f7860dd5F7cD68"
]
```

### Get User Positions

Get all positions for a specific user across all vaults.

```
GET /api/v1/users/{user_address}/positions
```

#### Parameters

- `user_address`: Ethereum address of the user

#### Response

```json
{
  "user_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "positions": [
    {
      "user_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
      "vault_address": "0x1E0165DbD2019441aB7927C018701f3138114D71",
      "debt": "1000000000000000000",
      "collateral": "500000000000000000",
      "debt_usd": "1000.00",
      "collateral_usd": "1500.00"
    }
  ],
  "total_debt_usd": "1000.00",
  "total_collateral_usd": "1500.00"
}
```

### List RPC Nodes

Get a list of available Ethereum RPC nodes with their status.

```
GET /api/v1/rpc-nodes
```

#### Response

```json
[
  {
    "name": "Local Ethereum Node",
    "url": "http://192.168.40.201:8545",
    "chain_id": 1,
    "is_active": true,
    "priority": 1
  },
  {
    "name": "Alchemy",
    "url": "https://eth-mainnet.alchemyapi.io/v2/",
    "chain_id": 1,
    "is_active": true,
    "priority": 2
  }
]
```

### Health Check

Get API health status.

```
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Error Responses

All endpoints can return the following error responses:

### 404 Not Found

```json
{
  "error": "Resource not found",
  "code": "NOT_FOUND",
  "details": {
    "resource": "vault",
    "id": "0x1234..."
  }
}
```

### 503 Service Unavailable

```json
{
  "error": "Service temporarily unavailable",
  "code": "SERVICE_UNAVAILABLE",
  "details": {
    "reason": "Failed to connect to Ethereum node"
  }
}
```

## Models

### TokenInfo

```typescript
{
  address: string;     // Ethereum address of the token
  name: string;        // Token name
  symbol: string;      // Token symbol
  decimals: number;    // Token decimals
}
```

### VaultInfo

```typescript
{
  address: string;           // Ethereum address of the vault
  borrowed_token: TokenInfo; // Borrowed token information
  collateral_token: TokenInfo; // Collateral token information
}
```

### VaultStats

```typescript
{
  address: string;           // Ethereum address of the vault
  total_debt: string;        // Total debt in token units
  total_collateral: string;  // Total collateral in token units
  total_debt_usd: string;    // Total debt in USD
  total_collateral_usd: string; // Total collateral in USD
  active_loans: number;      // Number of active loans
}
```

### UserPosition

```typescript
{
  user_address: string;      // Ethereum address of the user
  vault_address: string;     // Ethereum address of the vault
  debt: string;             // Debt in token units
  collateral: string;       // Collateral in token units
  debt_usd: string;         // Debt in USD
  collateral_usd: string;   // Collateral in USD
}
```

### UserVaultSummary

```typescript
{
  user_address: string;      // Ethereum address of the user
  positions: UserPosition[]; // Array of positions across vaults
  total_debt_usd: string;    // Total debt across all vaults in USD
  total_collateral_usd: string; // Total collateral across all vaults in USD
}
```

## Rate Limiting

Currently, there are no rate limits implemented on the API endpoints. However, the underlying web3 calls are rate-limited to prevent overloading the Ethereum node.

## Caching

The API uses SQLite-based caching for web3 calls with the following configuration:

- Cache Duration: 4 hours
- Cache Location: `.cache/web3_cache.db`
- Automatic cleanup of expired entries

## Development

To run the API server locally:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the server
python3 api.py
```

### Local Development

The server will start on `http://localhost:8000` with the following endpoints:
- Interactive API docs: http://localhost:8000/api/docs
- ReDoc documentation: http://localhost:8000/api/redoc
- OpenAPI schema: http://localhost:8000/api/openapi.json

### Production

The API is deployed on Google Cloud Run and available at:
- Base URL: https://ethereum-analyzer-330135650610.us-east1.run.app
- Interactive API docs: https://ethereum-analyzer-330135650610.us-east1.run.app/api/docs
- ReDoc documentation: https://ethereum-analyzer-330135650610.us-east1.run.app/api/redoc
- OpenAPI schema: https://ethereum-analyzer-330135650610.us-east1.run.app/api/openapi.json