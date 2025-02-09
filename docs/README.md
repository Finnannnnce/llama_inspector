# Ethereum Loan Query Tool

A Python tool for querying lending controller information from Ethereum smart contracts with optimized RPC handling and caching.

## Latest Analysis Results (2025-02-09)

- Total Controllers Analyzed: 25
- Active Loans: 345
- Total Value Borrowed: $16.73T USD
- Total Collateral Value: $21.81T USD
- Analysis Duration: 573.21 seconds

## Current Capabilities

- Query factory contract for active controllers
- Get borrowed and collateral token information for each controller
- Calculate USD values using current token prices
- Support multiple RPC endpoints with fallback
- Handle rate limiting with exponential backoff
- Support both snake_case and camelCase function names
- Efficient caching system for token and loan information
- Batch processing for loan queries
- Automatic RPC endpoint switching on rate limits

## Architecture

### RPC Configuration
The system uses multiple reliable public RPC endpoints with automatic failover:
- eth.llamarpc.com
- rpc.ankr.com/eth
- eth-mainnet.public.blastapi.io
- ethereum.publicnode.com
- 1rpc.io/eth
- rpc.mevblocker.io
- cloudflare-eth.com

### Optimization Parameters
- Controller Discovery Batch Size: 3
- Loan Info Batch Size: 5
- Max Consecutive Errors: 10
- Token Info Cache TTL: 12 hours
- Loan Info Cache TTL: 4 hours

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your configuration:
```
# Optional: Add custom RPC endpoints
ETH_RPC_URL=https://your-eth-node.com
```

## Docker Support

Build and run using Docker:

```bash
# Build the image
docker build -t eth-loan-query .

# Run the container
docker run -v $(pwd)/cache:/app/cache eth-loan-query
```

## Usage

Run the main script to query all controllers:

```bash
python main.py
```

The script will:
1. Connect to Ethereum network
2. Query the factory contract for all controllers
3. For each controller:
   - Get borrowed and collateral token information
   - Calculate USD values using current token prices
4. Display a summary for each controller and grand totals
5. Save analysis context to context.json

## Contract Interfaces

### Factory Contract
- Address: `0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0`
- Functions:
  - `controllers(uint256)`: Get controller address by index

### Controller Contract
Functions:
- `borrowed_token()` / `borrowedToken()`: Get borrowed token address
- `collateral_token()` / `collateralToken()`: Get collateral token address
- `user_state(address)`: Get user loan state (collateral, debt)
- `loans(uint256)`: Get loan addresses by index

## Error Handling

The tool includes:
- Exponential backoff for rate limiting
- Multiple RPC endpoint fallbacks
- Support for different function naming conventions
- Graceful handling of contract errors
- Consecutive error detection
- Automatic endpoint switching on rate limits

## Output Format

The tool provides colored output showing:
- Controller information
- Token addresses and prices
- Controller summaries
- Grand totals in USD

Example output:
```
Controller 0x1234...
Borrowed Token: Token A (0xabcd...)
Collateral Token: Token B (0xefgh...)
Borrowed Token Price: $1.00
Collateral Token Price: $2653.34

Active Loans: 42
Total Borrowed: 5.17T TOKEN_A
Total Collateral: 3.26T TOKEN_B
Total Borrowed USD: $5.17T
Total Collateral USD: $8.67T
```

## Caching System

The tool implements a multi-level caching system:
- Token Information: 12-hour TTL
- Loan Information: 4-hour TTL
- Web3 Call Results: Request-level caching
- Controller Data: Session-level caching

## Next Steps

To enhance the tool's capabilities:
1. Implement event-based loan tracking
2. Add support for proxy contract patterns
3. Include historical loan data analysis
4. Add more detailed token analytics
5. Implement WebSocket support for real-time updates
6. Add support for more price feed sources

## Contributing

Feel free to contribute by:
1. Adding support for more contract patterns
2. Implementing additional data sources
3. Improving error handling and recovery
4. Adding new analytics features
5. Optimizing RPC usage patterns
6. Enhancing caching strategies