import json
from decimal import Decimal
from typing import Optional, Dict, cast
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from eth_typing import Address, ChecksumAddress
from pathlib import Path
from .base import PriceFeed
from .coingecko import CoinGeckoPriceFeed
from ..utils.cache import Cache

class ChainlinkPriceFeed(PriceFeed):
    """Price feed using Chainlink price oracles with fallback to CoinGecko"""
    
    # Chainlink Feed Registry on Ethereum Mainnet
    FEED_REGISTRY: ChecksumAddress = AsyncWeb3.to_checksum_address('0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf')
    
    # Base/Quote pairs for price lookup
    ETH_USD_FEED: ChecksumAddress = AsyncWeb3.to_checksum_address('0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419')
    
    # WETH address
    WETH_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
    
    # USD address in Chainlink registry
    USD_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address('0x0000000000000000000000000000000000000348')
    
    # Zero address
    ZERO_ADDRESS: str = '0x0000000000000000000000000000000000000000'
    
    def __init__(self, cache: Cache, w3: AsyncWeb3):
        """Initialize Chainlink price feed
        
        Args:
            cache: Cache instance for price caching
            w3: AsyncWeb3 instance
        """
        super().__init__(cache)
        self.w3 = w3
        
        # Load Chainlink aggregator ABI
        aggregator_path = Path(__file__).parent.parent.parent / 'contracts' / 'interfaces' / 'chainlink_aggregator.json'
        with open(aggregator_path) as f:
            self.aggregator_abi = json.load(f)['abi']
            
        # Initialize fallback price feed
        self.fallback = CoinGeckoPriceFeed(cache)
        
        # Cache for feed addresses
        self.feed_cache_prefix = 'chainlink_feed_'
        self.SEVEN_DAYS = 7 * 24 * 60 * 60  # 7 days in seconds
        
    def _get_feed_cache_key(self, token_address: str) -> str:
        """Get cache key for feed address"""
        return f"{self.feed_cache_prefix}_{str(token_address).lower()}"
        
    async def _get_feed_address(self, token_address: str, verbose: bool = False) -> Optional[ChecksumAddress]:
        """Get Chainlink price feed address for token
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Price feed address or None if not found
        """
        cache_key = self._get_feed_cache_key(token_address)
        
        # Check cache first
        feed_address = self.cache.get(cache_key)
        if feed_address:
            if verbose:
                print(f"Using cached feed address for {token_address}")
            return AsyncWeb3.to_checksum_address(str(feed_address))
            
        # Special case for ETH/USD
        token_checksum = AsyncWeb3.to_checksum_address(token_address)
        if str(token_checksum).lower() == str(self.WETH_ADDRESS).lower():
            self.cache.set(cache_key, str(self.ETH_USD_FEED), ttl=self.SEVEN_DAYS)
            return self.ETH_USD_FEED
            
        try:
            # Try to find feed in registry
            registry = self.w3.eth.contract(address=self.FEED_REGISTRY, abi=[{
                "inputs": [
                    {"internalType": "address", "name": "base", "type": "address"},
                    {"internalType": "address", "name": "quote", "type": "address"}
                ],
                "name": "getFeed",
                "outputs": [{"internalType": "address", "name": "feed", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }])
            
            # Get feed for token/USD pair
            feed_address = await registry.functions.getFeed(
                token_checksum,
                self.USD_ADDRESS
            ).call()
            
            if feed_address and feed_address != self.ZERO_ADDRESS:
                feed_checksum = AsyncWeb3.to_checksum_address(feed_address)
                if verbose:
                    print(f"Found Chainlink feed for {token_address}: {feed_checksum}")
                self.cache.set(cache_key, str(feed_checksum), ttl=self.SEVEN_DAYS)
                return feed_checksum
                
        except Exception as e:
            if verbose:
                print(f"Error getting feed address: {str(e)}")
        
        return None
        
    async def get_raw_price(self, token_address: str, verbose: bool = False) -> Optional[Decimal]:
        """Get token price from Chainlink oracle with fallback to CoinGecko
        
        Args:
            token_address: Token contract address
            verbose: Enable verbose logging
            
        Returns:
            Token price in USD or None if unavailable
        """
        try:
            # Get feed address
            feed_address = await self._get_feed_address(token_address, verbose)
            if not feed_address:
                if verbose:
                    print(f"No Chainlink feed found for {token_address}, falling back to CoinGecko")
                return await self.fallback.get_raw_price(token_address, verbose)
                
            # Get latest price from feed
            feed = self.w3.eth.contract(address=feed_address, abi=self.aggregator_abi)
            decimals = await feed.functions.decimals().call()
            latest = await feed.functions.latestRoundData().call()
            
            if latest and latest[1] > 0:  # Check answer > 0
                price = Decimal(latest[1]) / Decimal(10 ** decimals)
                if verbose:
                    print(f"Got price from Chainlink: ${float(price):.2f}")
                return price
                
            if verbose:
                print("Invalid price from Chainlink feed, falling back to CoinGecko")
            return await self.fallback.get_raw_price(token_address, verbose)
            
        except Exception as e:
            if verbose:
                print(f"Error getting Chainlink price: {str(e)}")
            if verbose:
                print("Falling back to CoinGecko due to error")
            return await self.fallback.get_raw_price(token_address, verbose)