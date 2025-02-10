import asyncio
import aiohttp
import ssl
from decimal import Decimal
from typing import Optional, Dict, Tuple
import yaml
from .base import PriceFeed
from ..utils.cache import Cache

class CoinGeckoPriceFeed(PriceFeed):
    """Price feed using CoinGecko API"""
    
    def __init__(self, cache: Cache):
        """Initialize CoinGecko price feed
        
        Args:
            cache: Cache instance for price caching
        """
        super().__init__(cache)
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Get token mappings from config
        self.token_id_map = {
            addr.lower(): ticker 
            for addr, ticker in config.get('coingecko_tickers', {}).items()
        }
        self.stable_tokens = {
            addr.lower(): Decimal(str(price))
            for addr, price in config.get('stable_tokens', {}).items()
        }
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        self.eth_cache_key = 'eth_price_coingecko'
        
        # Configure SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def get_eth_price(self, verbose: bool = False) -> Optional[Decimal]:
        """Get ETH price in USD
        
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
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': 'ethereum',
                'vs_currencies': 'usd'
            }
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'ethereum' in data and 'usd' in data['ethereum']:
                            price = Decimal(str(data['ethereum']['usd']))
                            if verbose:
                                print(f"Got ETH price from CoinGecko: ${float(price):.2f}")
                            self.cache.set(self.eth_cache_key, price)
                            return price
                    elif verbose:
                        print(f"CoinGecko API error: {response.status}")
            return None
            
        except Exception as e:
            if verbose:
                print(f"Error getting ETH price: {str(e)}")
            return None
    
    async def get_token_price_in_eth(self, token_id: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price in ETH
        
        Args:
            token_id: CoinGecko token ID
            verbose: Enable verbose logging
            
        Returns:
            Token price in ETH or None if unavailable
        """
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': token_id,
                'vs_currencies': 'eth'
            }
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and token_id in data and 'eth' in data[token_id]:
                            price = Decimal(str(data[token_id]['eth']))
                            if verbose:
                                print(f"Got token price in ETH: {float(price):.6f}")
                            return price
                    elif verbose:
                        print(f"CoinGecko API error: {response.status}")
            return None
            
        except Exception as e:
            if verbose:
                print(f"Error getting token price: {str(e)}")
            return None
    
    async def get_raw_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price from CoinGecko
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        try:
            # Check if it's a known stablecoin first
            token_lower = token_address.lower()
            if token_lower in self.stable_tokens:
                if verbose:
                    print(f"Using known stablecoin price: ${float(self.stable_tokens[token_lower]):.2f}")
                return self.stable_tokens[token_lower]
            
            # Get token ID from map (case-insensitive)
            token_id = self.token_id_map.get(token_lower)
            if not token_id:
                if verbose:
                    print(f"No CoinGecko ID mapping for {token_address}")
                return None
            
            # Add delay to avoid rate limits
            await asyncio.sleep(0.2)
            
            # Get ETH price first
            eth_price = await self.get_eth_price(verbose)
            if not eth_price:
                if verbose:
                    print("Failed to get ETH price")
                return None
            
            # Special case for WETH
            if token_lower == self.WETH_ADDRESS.lower():
                return eth_price
            
            # Get token price in ETH
            token_eth_price = await self.get_token_price_in_eth(token_id, verbose)
            if not token_eth_price:
                if verbose:
                    print("Failed to get token price in ETH")
                return None
            
            # Calculate USD price
            usd_price = token_eth_price * eth_price
            if verbose:
                print(f"Got price from CoinGecko: ${float(usd_price):.2f}")
            return usd_price
            
        except Exception as e:
            if verbose:
                print(f"Error getting CoinGecko price: {str(e)}")
            return None