from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from ..utils.cache import Cache

class PriceFeed(ABC):
    """Base class for price feeds"""
    
    def __init__(self, cache: Cache):
        """Initialize price feed
        
        Args:
            cache: Cache instance for price caching
        """
        self.cache = cache
    
    @abstractmethod
    async def get_raw_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get raw token price from source
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if price not available
        """
        pass
    
    async def get_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price with caching
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if price not available
        """
        # Check cache first
        cached_price = self.cache.get(token_address)
        if cached_price is not None:
            if verbose:
                print(f"Using cached price for {token_address}")
            return cached_price
        
        try:
            # Get price from source
            price = await self.get_raw_price(token_address, verbose)
            if price is not None and price > 0:
                # Cache successful result
                self.cache.set(token_address, price)
                return price
            return None
        except Exception as e:
            if verbose:
                print(f"Error getting price from {self.__class__.__name__}: {str(e)}")
            return None