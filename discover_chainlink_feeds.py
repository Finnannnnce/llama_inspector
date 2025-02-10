import asyncio
from src.utils.price_fetcher import PriceFetcher

# Token addresses to check
TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "FRAX": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
    "LUSD": "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WSTETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
    "RPL": "0xD33526068D116cE69F19A9ee46F0bd304F21A51f",
    "LDO": "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "MKR": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
    "SNX": "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
    "CRV": "0xD533a949740bb3306d119CC777fa900bA034cd52",
    "CVX": "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B",
    "APE": "0x4d224452801ACEd8B2F0aebE155379bb5D594381",
    "SAND": "0x3845badAde8e6dFF049820680d1F14bD3903a5d0",
    "MANA": "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942",
    "OP": "0x4200000000000000000000000000000000000042",
    "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    "MATIC": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0"
}

async def discover_feeds():
    """Discover which tokens have Chainlink price feeds"""
    
    # Initialize price fetcher
    fetcher = PriceFetcher('.cache')
    
    print("\nDiscovering Chainlink price feeds...")
    print("-" * 80)
    print(f"{'Token':<10} {'Address':<42} {'Price':<15} {'Source':<10}")
    print("-" * 80)
    
    chainlink_count = 0
    coingecko_count = 0
    no_price_count = 0
    
    # Check each token
    for name, address in TOKENS.items():
        # First try to get price from Chainlink
        price = await fetcher.price_feed.get_raw_price(address, verbose=False)
        source = "Chainlink"
        if price is not None:
            chainlink_count += 1
        
        # If no Chainlink price, try CoinGecko
        if price is None:
            price = await fetcher.price_feed.fallback.get_raw_price(address, verbose=False)
            source = "CoinGecko" if price is not None else "None"
            if price is not None:
                coingecko_count += 1
            else:
                no_price_count += 1
        
        price_str = f"${float(price):.2f}" if price is not None else "Not available"
        print(f"{name:<10} {address:<42} {price_str:<15} {source:<10}")
    
    print("-" * 80)
    print(f"\nSummary:")
    print(f"Total tokens checked: {len(TOKENS)}")
    print(f"Chainlink feeds available: {chainlink_count}")
    print(f"CoinGecko fallback used: {coingecko_count}")
    print(f"No price available: {no_price_count}")

if __name__ == "__main__":
    asyncio.run(discover_feeds())