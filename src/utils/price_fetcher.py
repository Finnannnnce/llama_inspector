import json
import asyncio
import ssl
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from ..price_feeds.chainlink import ChainlinkPriceFeed
from .cache import Cache

class PriceFetcher:
    """Fetches token prices using Chainlink oracles with CoinGecko fallback"""

    def __init__(self, cache_dir: str):
        """Initialize price fetcher
        
        Args:
            cache_dir: Directory for caching
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize Web3 with SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Configure provider with SSL context
        provider = AsyncHTTPProvider(
            'https://rpc.ankr.com/eth',
            request_kwargs={
                'ssl': ssl_context,
                'timeout': 30
            }
        )
        self.w3 = AsyncWeb3(provider)
        
        # Initialize cache
        self.cache = Cache(str(self.cache_dir), 'price_cache.json')
        
        # Initialize price feed
        self.price_feed = ChainlinkPriceFeed(self.cache, self.w3)

    async def get_token_price_async(self, token_address: str, verbose: bool = False) -> Optional[float]:
        """Get token price
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        try:
            price = await self.price_feed.get_price(token_address, verbose)
            return float(price) if price is not None else None
            
        except Exception as e:
            if verbose:
                print(f"Error fetching price for {token_address}: {str(e)}")
            return None

    async def get_multiple_prices_async(self, token_addresses: list[str], verbose: bool = False) -> Dict[str, float]:
        """Get prices for multiple tokens concurrently
        
        Args:
            token_addresses: List of token addresses
            verbose: Enable verbose logging
            
        Returns:
            Dictionary of token addresses to prices
        """
        prices = {}
        async with asyncio.TaskGroup() as tg:
            for address in token_addresses:
                tg.create_task(self._get_price_task(address, prices, verbose))
        return prices

    async def _get_price_task(self, address: str, prices: Dict[str, float], verbose: bool) -> None:
        """Helper task for concurrent price fetching
        
        Args:
            address: Token address
            prices: Dictionary to store results
            verbose: Enable verbose logging
        """
        price = await self.get_token_price_async(address, verbose)
        if price is not None:
            prices[address] = price