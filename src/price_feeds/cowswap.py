import asyncio
import aiohttp
from decimal import Decimal
from typing import Optional
from web3 import Web3
from .base import PriceFeed
from ..utils.cache import Cache

class CowswapPriceFeed(PriceFeed):
    """Price feed using Cowswap's USDC pairs"""
    
    def __init__(self, cache: Cache):
        """Initialize Cowswap price feed
        
        Args:
            cache: Cache instance for price caching
        """
        super().__init__(cache)
        self.eth_cache_key = 'eth_price_cowswap'
        self.eth_cache_duration = 300  # Cache ETH price for 5 minutes
        self.USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        self.WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        self.base_url = 'https://api.cow.fi/mainnet'
    
    async def get_eth_price(self, verbose: bool = False) -> Optional[Decimal]:
        """Get ETH price in USD using USDC pair
        
        Args:
            verbose: Enable verbose logging
            
        Returns:
            ETH price in USD or None if unavailable
        """
        # Check cache first
        eth_price = self.cache.get(self.eth_cache_key)
        if eth_price is not None:
            if verbose:
                print(f"Using cached ETH price: ${float(eth_price):.2f}")
            return eth_price
        
        try:
            if verbose:
                print("Getting ETH price from Cowswap USDC pair")
            
            # Get price from API
            url = f"{self.base_url}/api/v1/quote"
            params = {
                'sellToken': self.WETH_ADDRESS,
                'buyToken': self.USDC_ADDRESS,
                'sellAmountBeforeFee': str(Web3.to_wei(1, 'ether')),  # 1 ETH
                'kind': 'sell',
                'from': '0x0000000000000000000000000000000000000000'  # Required by API
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'buyAmount' in data:
                            # Convert from USDC (6 decimals) to USD
                            eth_price = Decimal(data['buyAmount']) / Decimal('1000000')
                            if verbose:
                                print(f"ETH price: ${float(eth_price):.2f}")
                            self.cache.set(self.eth_cache_key, eth_price, self.eth_cache_duration)
                            return eth_price
                    elif verbose:
                        print(f"Cowswap API error: {response.status}")
            return None
            
        except Exception as e:
            if verbose:
                print(f"Error getting ETH price: {str(e)}")
            return None
    
    async def get_raw_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price in USD using Cowswap
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        try:
            if verbose:
                print(f"Getting price from Cowswap for token: {token_address}")
            
            # Get ETH price first
            eth_price = await self.get_eth_price(verbose)
            if not eth_price or eth_price <= 0:
                if verbose:
                    print("No valid ETH price available")
                return None
            
            # Get token/ETH price
            if token_address.lower() == self.WETH_ADDRESS.lower():
                token_eth_price = Decimal('1.0')
            else:
                # Get price from API
                url = f"{self.base_url}/api/v1/quote"
                params = {
                    'sellToken': token_address,
                    'buyToken': self.WETH_ADDRESS,
                    'sellAmountBeforeFee': str(Web3.to_wei(1, 'ether')),  # 1 token
                    'kind': 'sell',
                    'from': '0x0000000000000000000000000000000000000000'  # Required by API
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'buyAmount' in data:
                                # Convert from ETH (18 decimals) to ETH
                                token_eth_price = Decimal(data['buyAmount']) / Decimal('1000000000000000000')
                            else:
                                return None
                        else:
                            if verbose:
                                print(f"Cowswap API error: {response.status}")
                            return None
            
            if verbose:
                print(f"Token price in ETH: {float(token_eth_price):.6f}")
                print(f"ETH price in USD: ${float(eth_price):.2f}")
            
            # Calculate USD price
            if token_eth_price and token_eth_price > 0:
                usd_price = token_eth_price * eth_price
                if verbose:
                    print(f"Token price in USD: ${float(usd_price):.2f}")
                return usd_price
            
            return None
            
        except Exception as e:
            if verbose:
                print(f"Error getting Cowswap price: {str(e)}")
            return None