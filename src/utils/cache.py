import json
import os
import time
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class Cache:
    """Simple file-based cache with atomic writes and expiration"""
    
    def __init__(self, cache_dir: str, filename: str):
        """Initialize cache
        
        Args:
            cache_dir: Directory to store cache files
            filename: Cache filename
        """
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / filename
        self.data: Dict[str, Tuple[Any, float]] = {}  # (value, expiration_time)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load existing cache
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    raw_data = json.load(f)
                    # Filter out expired entries during load
                    current_time = time.time()
                    self.data = {
                        k: (v[0], v[1]) for k, v in raw_data.items()
                        if v[1] == 0 or v[1] > current_time  # Keep if no expiration or not expired
                    }
            except Exception:
                self.data = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.data:
            return None
            
        value, expiration = self.data[key]
        if expiration > 0 and time.time() > expiration:
            # Remove expired entry
            del self.data[key]
            self._save()
            return None
            
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        expiration = time.time() + ttl if ttl is not None else 0
        self.data[key] = (value, expiration)
        self._save()
    
    def _save(self) -> None:
        """Save cache to disk"""
        # Write to temporary file first
        tmp_file = self.cache_file.with_suffix('.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(self.data, f, cls=DecimalEncoder)
            
            # Atomic rename
            os.replace(tmp_file, self.cache_file)
            
        except Exception as e:
            # Clean up temp file
            if tmp_file.exists():
                try:
                    os.unlink(tmp_file)
                except Exception:
                    pass
            raise e

class ContractCache(Cache):
    """Cache for contract call results"""
    
    def __init__(self, cache_dir: str):
        """Initialize contract cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        super().__init__(cache_dir, 'contracts_cache.json')