import asyncio
import aiohttp
from decimal import Decimal
from typing import Optional
from .base import PriceFeed
from ..utils.cache import Cache

class OneInchPriceFeed(PriceFeed):
    """Price feed using 1inch API"""
    
    def __init__(self, cache: Cache):
        """Initialize 1inch price feed
        
        Args:
            cache: Cache instance for price caching
        """
        super().__init__(cache)
        self.api_key = 'kvhNUzLlCTMeCoV1IZfAd1dRNzoADHRr'  # Use provided API key
        self.enabled = True
        self.USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        self.base_url = 'https://api.1inch.dev'
    
    async def get_price_from_api(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price from 1inch API
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        url = f"{self.base_url}/swap/v5.2/1/quote"  # Use swap quote endpoint
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        params = {
            'src': token_address,
            'dst': self.USDC_ADDRESS,
            'amount': '1000000000000000000'  # 1 token in wei
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'toTokenAmount' in data:
                            # Convert from USDC (6 decimals) to USD
                            price = Decimal(data['toTokenAmount']) / Decimal('1000000')
                            if verbose:
                                print(f"Got price from 1inch: ${float(price):.2f}")
                            return price
                    elif verbose:
                        print(f"1inch API error: {response.status}")
            return None
            
        except Exception as e:
            if verbose:
                print(f"Error getting 1inch price: {str(e)}")
            return None
    
    async def get_raw_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price from 1inch
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        try:
            # Add delay to avoid rate limits
            await asyncio.sleep(0.2)
            
            # Get price from API
            return await self.get_price_from_api(token_address, verbose)
            
        except Exception as e:
            if verbose:
                print(f"Error getting 1inch price: {str(e)}")
            return None