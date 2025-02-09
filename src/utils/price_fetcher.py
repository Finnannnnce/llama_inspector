import os
import json
import time
import requests
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Load environment variables
load_dotenv()

class PriceFetcher:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'price_cache.json')
        self.oneinch_api_key = os.getenv('ONEINCH_API_KEY')
        self.oneinch_enabled = True  # Will be set to False if API fails
        self.cache_duration = {
            'prices': 4 * 3600,  # 4 hours for prices
            'failed': 24 * 3600  # 24 hours for failed lookups
        }
        
        # Price source configurations
        self.price_sources = [
            {
                'name': '1inch',
                'method': self._get_price_from_1inch,
                'weight': 3,  # Higher weight as it's typically more reliable
                'enabled': True
            },
            {
                'name': 'coingecko',
                'method': self._get_price_from_coingecko,
                'weight': 2,
                'enabled': True
            }
        ]
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize or load cache
        self.cache = self._load_cache()
        
        # Clean expired cache entries on initialization
        self._clean_expired_cache()

    def _load_cache(self) -> Dict:
        """
        Load the price cache from disk.
        
        Returns:
            Dict: Cache data with prices and failed lookups
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Validate cache structure
                    if not isinstance(cache_data, dict) or \
                       not all(k in cache_data for k in ['prices', 'failed']):
                        print("Warning: Invalid cache structure, initializing new cache")
                        return {'prices': {}, 'failed': {}}
                    return cache_data
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
        return {'prices': {}, 'failed': {}}

    def _save_cache(self):
        """Save the price cache to disk with error handling."""
        try:
            # Create temp file
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.cache, f)
            
            # Atomic rename
            os.replace(temp_file, self.cache_file)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")
            # Try to remove temp file if it exists
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    def _clean_expired_cache(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        
        # Clean prices cache
        expired_prices = [
            addr for addr, data in self.cache['prices'].items()
            if not self._is_cache_valid(data['timestamp'], 'prices')
        ]
        for addr in expired_prices:
            del self.cache['prices'][addr]
            
        # Clean failed lookups cache
        expired_failed = [
            addr for addr, data in self.cache['failed'].items()
            if not self._is_cache_valid(data['timestamp'], 'failed')
        ]
        for addr in expired_failed:
            del self.cache['failed'][addr]
            
        if expired_prices or expired_failed:
            self._save_cache()

    def _is_cache_valid(self, timestamp: float, cache_type: str = 'prices') -> bool:
        """
        Check if cached data is still valid.
        
        Args:
            timestamp: Cache entry timestamp
            cache_type: Type of cache entry ('prices' or 'failed')
            
        Returns:
            bool: True if cache entry is still valid
        """
        return time.time() - timestamp < self.cache_duration[cache_type]

    def _get_cached_price(self, token_address: str) -> Optional[float]:
        """
        Get price from cache if valid.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optional[float]: Cached price if valid, None otherwise
        """
        cache_data = self.cache['prices'].get(token_address)
        if cache_data and self._is_cache_valid(cache_data['timestamp']):
            return cache_data['price']
        return None

    def _is_failed_lookup(self, token_address: str) -> bool:
        """
        Check if token is in failed lookups cache.
        
        Args:
            token_address: Token contract address
            
        Returns:
            bool: True if token lookup recently failed
        """
        failed_data = self.cache['failed'].get(token_address)
        return failed_data and self._is_cache_valid(failed_data['timestamp'], 'failed')

    def _cache_price(self, token_address: str, price: float, source: str):
        """
        Cache a successful price lookup.
        
        Args:
            token_address: Token contract address
            price: Token price in USD
            source: Name of price source
        """
        self.cache['prices'][token_address] = {
            'price': price,
            'timestamp': time.time(),
            'source': source
        }
        self._save_cache()

    def _cache_failed_lookup(self, token_address: str):
        """
        Cache a failed price lookup.
        
        Args:
            token_address: Token contract address
        """
        self.cache['failed'][token_address] = {
            'timestamp': time.time()
        }
        self._save_cache()

    def _get_price_from_1inch(self, token_address: str) -> Optional[Tuple[float, str]]:
        """
        Get token price from 1inch API.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optional[Tuple[float, str]]: (price, source) if successful
        """
        if not self.oneinch_enabled or not self.oneinch_api_key:
            return None

        try:
            url = f"https://api.1inch.dev/price/v1.1/1/{token_address}"
            headers = {"Authorization": f"Bearer {self.oneinch_api_key}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                price_data = response.json()
                if isinstance(price_data, dict) and 'price' in price_data:
                    return (float(price_data['price']), '1inch')
            elif response.status_code == 429:  # Rate limit
                print("1inch API rate limit reached")
                return None
            elif response.status_code >= 400:
                print(f"1inch API error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("1inch API timeout")
        except Exception as e:
            print(f"Warning: 1inch API failed, disabling for future requests. Error: {str(e)}")
            self.oneinch_enabled = False
        return None

    def _get_price_from_coingecko(self, token_address: str) -> Optional[Tuple[float, str]]:
        """
        Get token price from CoinGecko API.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optional[Tuple[float, str]]: (price, source) if successful
        """
        try:
            url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum"
            params = {
                'contract_addresses': token_address,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                price_data = response.json()
                if price_data and token_address.lower() in price_data:
                    return (float(price_data[token_address.lower()]['usd']), 'coingecko')
            elif response.status_code == 429:  # Rate limit
                print("CoinGecko API rate limit reached")
            elif response.status_code >= 400:
                print(f"CoinGecko API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("CoinGecko API timeout")
        except Exception as e:
            print(f"Error fetching price from CoinGecko: {str(e)}")
        return None

    def get_token_price(self, token_address: str) -> Optional[float]:
        """
        Get token price with caching and multiple API fallbacks.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optional[float]: Token price in USD or None if price cannot be fetched
        """
        # Normalize address
        token_address = token_address.lower()
        
        # Check cache first
        cached_price = self._get_cached_price(token_address)
        if cached_price is not None:
            return cached_price
            
        # Check if it's a failed lookup
        if self._is_failed_lookup(token_address):
            return None
            
        # Try all enabled price sources in parallel
        enabled_sources = [s for s in self.price_sources if s['enabled']]
        if not enabled_sources:
            print("No price sources available")
            return None
            
        with ThreadPoolExecutor(max_workers=len(enabled_sources)) as executor:
            future_to_source = {
                executor.submit(source['method'], token_address): source
                for source in enabled_sources
            }
            
            results = []
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    if result:
                        price, source_name = result
                        results.append((price, source_name, source['weight']))
                except Exception as e:
                    print(f"Error from {source['name']}: {str(e)}")
                    
        if results:
            # Calculate weighted average if multiple results
            if len(results) > 1:
                total_weight = sum(weight for _, _, weight in results)
                weighted_price = sum(price * weight for price, _, weight in results) / total_weight
                self._cache_price(token_address, weighted_price, 'weighted_average')
                return weighted_price
            else:
                # Single result
                price, source_name, _ = results[0]
                self._cache_price(token_address, price, source_name)
                return price
                
        # Cache failed lookup if no price found
        self._cache_failed_lookup(token_address)
        return None

    def get_multiple_token_prices(self, token_addresses: List[str]) -> Dict[str, Optional[float]]:
        """
        Get prices for multiple tokens in parallel.
        
        Args:
            token_addresses: List of token contract addresses
            
        Returns:
            Dict[str, Optional[float]]: Map of token addresses to prices
        """
        results = {}
        with ThreadPoolExecutor() as executor:
            future_to_address = {
                executor.submit(self.get_token_price, addr): addr 
                for addr in token_addresses
            }
            for future in as_completed(future_to_address):
                addr = future_to_address[future]
                try:
                    results[addr] = future.result()
                except Exception as e:
                    print(f"Error getting price for {addr}: {str(e)}")
                    results[addr] = None
        return results