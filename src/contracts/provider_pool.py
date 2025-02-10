import asyncio
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from web3 import Web3
from web3.types import RPCEndpoint

from ..utils.rate_limiter import retry_forever


class Web3ProviderPool:
    """Pool of Web3 providers with weighted round-robin selection"""
    
    def __init__(self, rpc_configs: List[Dict], verbose: bool = False):
        """Initialize provider pool
        
        Args:
            rpc_configs: List of RPC node configs with format:
                [{"name": str, "url": str, "weight": int}, ...]
            verbose: Enable verbose logging
        """
        self.providers: List[Web3] = []
        self.provider_names: List[str] = []  # For logging
        self.provider_urls: List[str] = []  # For identifying providers
        self.current_provider = 0
        self.verbose = verbose
        self._lock = threading.Lock()  # Thread-safe provider selection
        self._disabled_providers: Set[str] = set()  # Track disabled provider URLs
        self._last_switch_time = time.time()  # Track last provider switch time
        self._requests_with_current = 0  # Track requests with current provider
        self.MAX_REQUESTS_PER_PROVIDER = 10  # Switch provider after this many requests
        
        if self.verbose:
            print("Initializing Web3 provider pool...")
        
        # Initialize providers from config
        for rpc in rpc_configs:
            try:
                if self.verbose:
                    print(f"Attempting to connect to {rpc['name']} ({rpc['url']})...")
                
                provider = Web3(Web3.HTTPProvider(
                    rpc['url'],
                    request_kwargs={'timeout': 30}  # Increased timeout to 30 seconds
                ))
                
                # Test connection with retries
                retries = 3
                connected = False
                for attempt in range(retries):
                    try:
                        if provider.is_connected():
                            connected = True
                            break
                        else:
                            if self.verbose:
                                print(f"Connection test failed for {rpc['name']}, attempt {attempt + 1}/{retries}")
                    except Exception as e:
                        if self.verbose:
                            print(f"Connection test error for {rpc['name']}: {str(e)}")
                
                if connected:
                    self.providers.append(provider)
                    self.provider_names.append(rpc['name'])
                    self.provider_urls.append(rpc['url'])
                    if self.verbose:
                        print(f"Successfully connected to {rpc['name']}")
                else:
                    if self.verbose:
                        print(f"Failed to connect to {rpc['name']} after {retries} attempts")
                    
            except Exception as e:
                if self.verbose:
                    print(f"Error initializing provider {rpc['name']}: {str(e)}")
                continue
        
        if not self.providers:
            raise Exception("No working RPC providers available")
        
        if self.verbose:
            print(f"Initialized provider pool with {len(self.providers)} providers")
            for name, url in zip(self.provider_names, self.provider_urls):
                print(f"- {name}: {url}")
    
    def get_provider(self) -> Optional[Tuple[Web3, str, str]]:
        """Get next available provider using thread-safe round-robin selection
        
        Returns:
            Tuple of (provider, name, url) or None if no providers available
        """
        with self._lock:
            # Get list of active providers
            active_providers = [
                (p, n, u) for p, n, u in zip(self.providers, self.provider_names, self.provider_urls)
                if u not in self._disabled_providers
            ]
            
            if not active_providers:
                if self.verbose:
                    print("No available providers")
                return None
            
            # Check if we should switch providers
            now = time.time()
            if self._requests_with_current >= self.MAX_REQUESTS_PER_PROVIDER:
                self.current_provider = (self.current_provider + 1) % len(active_providers)
                self._requests_with_current = 0
                self._last_switch_time = now
            
            # Get current provider
            provider, name, url = active_providers[self.current_provider % len(active_providers)]
            self._requests_with_current += 1
            
            if self.verbose and self._requests_with_current == 1:
                print(f"Using provider: {name}", flush=True)
            return provider, name, url
    
    def disable_provider(self, url: str):
        """Disable a provider by its URL
        
        Args:
            url: Provider URL to disable
        """
        with self._lock:
            if url not in self._disabled_providers:
                self._disabled_providers.add(url)
                if self.verbose:
                    print(f"Disabled provider: {url}")
                # Log remaining active providers
                active_count = len(self.provider_urls) - len(self._disabled_providers)
                if self.verbose:
                    print(f"Remaining active providers: {active_count}")
                # Reset request count when disabling current provider
                self._requests_with_current = 0
    
    @retry_forever
    async def batch_call_contract(self, calls: List[object], verbose: bool = False) -> List[Optional[Any]]:
        """Make multiple contract calls in a single batch request
        
        Args:
            calls: List of contract function objects to call
            verbose: Enable verbose logging
            
        Returns:
            List of results or None for failed calls
        """
        if not calls:
            return []
        
        start_time = asyncio.get_event_loop().time()
        attempt = 0
        last_error = None
        
        while True:
            provider_info = self.get_provider()
            if not provider_info:
                if verbose:
                    print("No available providers")
                return [None] * len(calls)
            
            provider, name, url = provider_info
            
            try:
                # Add delay between batches
                await asyncio.sleep(1.0)  # 1 second delay
                
                # Make individual calls since batch not supported
                results = []
                for call in calls:
                    try:
                        result = call.call()
                        results.append(result)
                    except Exception as e:
                        if verbose:
                            print(f"Error in call: {str(e)}")
                        results.append(None)
                    # Add small delay between calls
                    await asyncio.sleep(0.2)
                
                return results
                
            except Exception as e:
                last_error = e
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Check if total time exceeds timeout
                REQUEST_TIMEOUT = 300  # 5 minutes
                if elapsed >= REQUEST_TIMEOUT:
                    if verbose:
                        print(f"Request timed out after {REQUEST_TIMEOUT} seconds: {str(last_error)}")
                    return [None] * len(calls)
                
                # Disable provider if rate limited
                if "429" in str(e):
                    if verbose:
                        print(f"Provider {name} rate limited, disabling")
                    self.disable_provider(url)
                    continue  # Try next provider immediately
                
                # Exponential backoff with 30 second cap
                delay = min(30, 1 * (2 ** attempt))
                if verbose:
                    print(f"Error with provider: {str(e)}")
                    print(f"Retrying with next provider in {delay} seconds...")
                await asyncio.sleep(delay)
                attempt += 1
    
    @retry_forever
    async def call_contract(self, contract_function: object, verbose: bool = False) -> Optional[object]:
        """Make single contract call (fallback for non-batchable calls)
        
        Args:
            contract_function: Web3 contract function to call
            verbose: Enable verbose logging
            
        Returns:
            Contract call result or None if call fails
        """
        results = await self.batch_call_contract([contract_function], verbose)
        return results[0] if results else None