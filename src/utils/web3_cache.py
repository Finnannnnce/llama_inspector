import os
import json
import time
import requests
from typing import Any, Dict, Optional
from web3 import Web3

class CachedWeb3Calls:
    def __init__(self, w3: Web3, cache_dir: str):
        self.w3 = w3
        self.cache_dir = cache_dir
        self.cache_duration = 12 * 3600  # 12 hours
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize or load cache
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load the Web3 calls cache from disk"""
        cache_file = os.path.join(self.cache_dir, 'web3_cache.json')
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
        return {'calls': {}}

    def _save_cache(self):
        """Save the Web3 calls cache to disk"""
        cache_file = os.path.join(self.cache_dir, 'web3_cache.json')
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached data is still valid"""
        return time.time() - timestamp < self.cache_duration

    def _get_cache_key(self, contract_address: str, function_name: str, *args) -> str:
        """Generate cache key for a contract call"""
        args_str = ':'.join(str(arg) for arg in args)
        return f"{contract_address.lower()}:{function_name}:{args_str}"

    def _get_cached_call(self, key: str) -> Optional[Any]:
        """Get result from cache if valid"""
        cache_data = self.cache['calls'].get(key)
        if cache_data and self._is_cache_valid(cache_data['timestamp']):
            return cache_data['result']
        return None

    def _cache_call(self, key: str, result: Any):
        """Cache a function call result"""
        self.cache['calls'][key] = {
            'result': result,
            'timestamp': time.time()
        }
        self._save_cache()

    def call_function(self, contract: Any, function_name: str, *args) -> Optional[Any]:
        """Call a contract function with caching"""
        # Create cache key
        key = self._get_cache_key(contract.address, function_name, *args)
        
        # Check cache first
        cached_result = self._get_cached_call(key)
        if cached_result is not None:
            return cached_result
            
        # Make the actual call if not in cache
        try:
            function = getattr(contract.functions, function_name)
            if args:
                result = function(*args).call()
            else:
                result = function().call()
            
            # Cache the result
            self._cache_call(key, result)
            
            return result
            
        except Exception as e:
            return None