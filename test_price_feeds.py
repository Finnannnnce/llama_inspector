import asyncio
from src.utils.price_fetcher import PriceFetcher

async def main():
    # Initialize price fetcher
    fetcher = PriceFetcher('.cache')
    
    # Test tokens
    tokens = {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    }
    
    print("\nFetching individual prices:")
    for name, address in tokens.items():
        price = await fetcher.get_token_price_async(address, verbose=True)
        print(f"{name}: ${price:.2f}" if price else f"{name}: Failed to get price")
        
    print("\nFetching all prices concurrently:")
    prices = await fetcher.get_multiple_prices_async(list(tokens.values()), verbose=True)
    for name, address in tokens.items():
        if address in prices:
            print(f"{name}: ${prices[address]:.2f}")
        else:
            print(f"{name}: Failed to get price")

if __name__ == "__main__":
    asyncio.run(main())