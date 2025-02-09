import json
import os
import tempfile
from decimal import Decimal
from typing import Any, Dict, Optional
from pathlib import Path

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class Cache:
    """Simple file-based cache with atomic writes"""
    
    def __init__(self, cache_dir: str, filename: str):
        """Initialize cache
        
        Args:
            cache_dir: Directory to store cache files
            filename: Cache filename
        """
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / filename
        self.data: Dict[str, Any] = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load existing cache
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        return self.data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.data[key] = value
        
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