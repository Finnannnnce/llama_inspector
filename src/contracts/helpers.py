import os
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.contract import Contract
from ..utils.rate_limiter import retry_forever, RateLimiter
from ..utils.cache import ContractCache
from .provider_pool import Web3ProviderPool

class ContractHelper:
    """Helper class for contract interactions"""
    
    def __init__(self, provider_pool: Web3ProviderPool, contract_cache: ContractCache, 
                 rate_limiter: RateLimiter, verbose: bool = False):
        """Initialize contract helper
        
        Args:
            provider_pool: Web3 provider pool for RPC calls
            contract_cache: Cache for contract call results
            rate_limiter: Rate limiter for RPC calls
            verbose: Enable verbose logging
        """
        self.provider_pool = provider_pool
        self.contract_cache = contract_cache
        self.rate_limiter = rate_limiter
        self.verbose = verbose
    
    async def get_contract_abi(self, name: str) -> Optional[list]:
        """Load contract ABI from file
        
        Args:
            name: Contract name (e.g., 'vault', 'controller', 'erc20')
            
        Returns:
            Contract ABI or None if loading fails
        """
        try:
            filepath = os.path.join(os.getcwd(), 'contracts', 'interfaces', f'{name}.json')
            if self.verbose:
                print(f"Loading ABI from: {filepath}")
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data['abi']
        except Exception as e:
            if self.verbose:
                print(f"Error loading ABI for {name}: {str(e)}")
            return None
    
    def get_contract(self, address: str, abi: list) -> Contract:
        """Create Web3 contract instance
        
        Args:
            address: Contract address
            abi: Contract ABI
            
        Returns:
            Web3 contract instance
        """
        provider_info = self.provider_pool.get_provider()
        if not provider_info:
            raise Exception("No available providers")
        provider, _, _ = provider_info
        
        # Ensure address is a string
        if isinstance(address, dict) and 'value' in address:
            address = address['value']
        
        return provider.eth.contract(address=address, abi=abi)
    
    @retry_forever
    async def call_contract_function(self, contract_function: object, 
                                   cache_key: Optional[str] = None) -> Any:
        """Call contract function with caching and rate limiting
        
        Args:
            contract_function: Web3 contract function to call
            cache_key: Optional cache key for result
            
        Returns:
            Contract call result or None if call fails
        """
        if cache_key:
            # Check cache first
            cached_result = self.contract_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Make the call using provider pool
        await self.rate_limiter.wait()
        result = await self.provider_pool.call_contract(contract_function, self.verbose)
        
        # Cache successful result
        if cache_key and result is not None:
            self.contract_cache.set(cache_key, result)
        
        return result
    
    @retry_forever
    async def batch_call_contract_functions(self, functions: List[object], 
                                          cache_keys: Optional[List[str]] = None) -> List[Any]:
        """Call multiple contract functions in batch with caching and rate limiting
        
        Args:
            functions: List of Web3 contract functions to call
            cache_keys: Optional list of cache keys for results
            
        Returns:
            List of contract call results or None for failed calls
        """
        if not functions:
            return []
        
        # Check cache first
        results = []
        uncached_indices = []
        uncached_functions = []
        
        if cache_keys:
            for i, (func, key) in enumerate(zip(functions, cache_keys)):
                if key:
                    cached_result = self.contract_cache.get(key)
                    if cached_result is not None:
                        results.append(cached_result)
                        continue
                uncached_indices.append(i)
                uncached_functions.append(func)
                results.append(None)
        else:
            uncached_indices = list(range(len(functions)))
            uncached_functions = functions
            results = [None] * len(functions)
        
        if uncached_functions:
            # Make the batch call using provider pool
            await self.rate_limiter.wait()
            batch_results = await self.provider_pool.batch_call_contract(
                uncached_functions, self.verbose
            )
            
            # Update results and cache
            for i, (result, idx) in enumerate(zip(batch_results, uncached_indices)):
                results[idx] = result
                if cache_keys and result is not None:
                    key = cache_keys[idx]
                    if key:
                        self.contract_cache.set(key, result)
        
        return results
    
    async def get_token_info(self, token_addresses: List[str], erc20_abi: list) -> List[Tuple[str, int]]:
        """Get token names and decimals
        
        Args:
            token_addresses: List of token contract addresses
            erc20_abi: ERC20 contract ABI
            
        Returns:
            List of tuples (token name, decimals)
        """
        results = []
        for addr in token_addresses:
            try:
                # Get cached values first
                name_key = f"token_name_{addr}"
                decimals_key = f"token_decimals_{addr}"
                
                name = self.contract_cache.get(name_key)
                decimals = self.contract_cache.get(decimals_key)
                
                if name is None or decimals is None:
                    # Create contract instance
                    token = self.get_contract(addr, erc20_abi)
                    
                    # Get name if not cached
                    if name is None:
                        name = await self.call_contract_function(
                            token.functions.name(),
                            cache_key=name_key
                        )
                    
                    # Get decimals if not cached
                    if decimals is None:
                        decimals = await self.call_contract_function(
                            token.functions.decimals(),
                            cache_key=decimals_key
                        )
                
                if name is not None and decimals is not None:
                    results.append((name, decimals))
                else:
                    if self.verbose:
                        print(f"Missing token info for {addr}")
                    results.append((None, None))
                
                # Add delay between tokens
                await asyncio.sleep(0.2)
                
            except Exception as e:
                if self.verbose:
                    print(f"Error getting token info for {addr}: {str(e)}")
                results.append((None, None))
        
        return results
    
    def format_token_amount(self, amount: int, decimals: int) -> Decimal:
        """Format raw token amount using decimals
        
        Args:
            amount: Raw token amount
            decimals: Token decimals
            
        Returns:
            Formatted amount as Decimal
        """
        return Decimal(amount) / Decimal(10**decimals)