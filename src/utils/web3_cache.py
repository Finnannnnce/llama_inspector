import os
import json
import time
import sqlite3
from typing import Any, Dict, Optional
from web3 import AsyncWeb3
from web3.contract import AsyncContract

class CachedWeb3Calls:
    def __init__(self, w3: AsyncWeb3, cache_dir: str):
        self.w3 = w3
        self.cache_dir = cache_dir
        self.cache_duration = 4 * 3600  # 4 hours
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize SQLite database
        self.db_path = os.path.join(cache_dir, 'web3_cache.db')
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and create table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS web3_cache (
                    key TEXT PRIMARY KEY,
                    result TEXT,
                    timestamp REAL
                )
            ''')
            conn.commit()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached data is still valid"""
        return time.time() - timestamp < self.cache_duration

    def _get_cache_key(self, contract_address: str, function_name: str, *args) -> str:
        """Generate cache key for a contract call"""
        args_str = ':'.join(str(arg) for arg in args)
        return f"{contract_address.lower()}:{function_name}:{args_str}"

    def _get_cached_call(self, key: str) -> Optional[Any]:
        """Get result from cache if valid"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT result, timestamp FROM web3_cache WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if row and self._is_cache_valid(row[1]):
                import json
                return json.loads(row[0])
        return None

    def _cache_call(self, key: str, result: Any):
        """Cache a function call result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            import json
            cursor.execute(
                'INSERT OR REPLACE INTO web3_cache (key, result, timestamp) VALUES (?, ?, ?)',
                (key, json.dumps(result), time.time())
            )
            conn.commit()

    async def call_function(self, contract: AsyncContract, function_name: str, *args) -> Optional[Any]:
        """Call a contract function with caching"""
        # Create cache key
        key = self._get_cache_key(contract.address, function_name, *args)
        
        # Check cache first
        cached_result = self._get_cached_call(key)
        if cached_result is not None:
            return cached_result
            
        # Make the actual call if not in cache or cache is expired
        try:
            function = getattr(contract.functions, function_name)
            if args:
                result = await function(*args).call()
            else:
                result = await function().call()
            
            # Cache the result
            self._cache_call(key, result)
            
            return result
            
        except Exception as e:
            print(f"Error calling function {function_name}: {str(e)}")
            return None

    def clear_expired_cache(self):
        """Clear expired cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM web3_cache WHERE ? - timestamp > ?',
                (time.time(), self.cache_duration)
            )
            conn.commit()