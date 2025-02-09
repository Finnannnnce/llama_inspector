from decimal import Decimal
from typing import Dict, List, Optional
from .base import PriceFeed
from .oneinch import OneInchPriceFeed
from .cowswap import CowswapPriceFeed
from .coingecko import CoinGeckoPriceFeed
from ..utils.cache import Cache

class PriceFeedAggregator:
    """Aggregates multiple price feeds with fallback logic"""
    
    def __init__(self, cache: Cache, default_prices: Dict[str, float]):
        """Initialize price feed aggregator
        
        Args:
            cache: Cache instance for price caching
            default_prices: Dictionary mapping token symbols to default prices (unused)
        """
        self.cache = cache
        
        # Initialize price feeds in priority order
        self.price_feeds: List[PriceFeed] = [
            OneInchPriceFeed(cache),  # Try 1inch first (fastest, most accurate)
            CowswapPriceFeed(cache),  # Cowswap as backup
            CoinGeckoPriceFeed(cache) # CoinGecko as final fallback
        ]
    
    async def get_price(self, token_address: str, token_symbol: Optional[str] = None, 
                       verbose: bool = False) -> Optional[Decimal]:
        """Get token price from available price feeds with fallback
        
        Args:
            token_address: Token contract address
            token_symbol: Optional token symbol (unused)
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if all price feeds fail
        """
        # Check cache first
        cached_price = self.cache.get(token_address)
        if cached_price is not None:
            if verbose:
                print(f"Using cached price for {token_address}")
            return cached_price
        
        # Try each price feed in order
        for feed in self.price_feeds:
            try:
                price = await feed.get_price(token_address, verbose)
                if price is not None and price > 0:
                    # Cache successful result
                    self.cache.set(token_address, price)
                    return price
            except Exception as e:
                if verbose:
                    print(f"Error getting price from {feed.__class__.__name__}: {str(e)}")
                continue
        
        if verbose:
            print(f"All price feeds failed for {token_address}")
        return None