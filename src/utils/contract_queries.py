import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, TypedDict, Callable, Awaitable, cast, Union
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.exceptions import ContractLogicError
from eth_typing import ChecksumAddress

from .rate_limiter import RateLimiter
from .web3_cache import CachedWeb3Calls

class TokenInfo(TypedDict):
    """Type definition for token information"""
    address: str
    name: str
    symbol: str
    decimals: int

class ContractQueries:
    """Handles Web3 contract interactions with caching and retries"""

    def __init__(self, w3: AsyncWeb3, cache_dir: str):
        self.w3 = w3
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize caches
        self._token_info_cache: Dict[str, Dict[str, TokenInfo]] = {}
        self._vault_cache: Dict[str, AsyncContract] = {}
        self._admin_cache: Dict[str, AsyncContract] = {}
        self._factory_cache: Dict[str, AsyncContract] = {}
        
        # Initialize Web3 caching
        self.web3_cache = CachedWeb3Calls(w3, str(self.cache_dir))
        
        # Rate limiting
        self.rate_limiter = RateLimiter(calls_per_second=50)
        
        # Load contract ABIs
        self.factory_abi = self._load_abi('factory')
        self.vault_abi = self._load_abi('vault')
        self.admin_abi = self._load_abi('admin')
        self.erc20_abi = self._load_abi('erc20')

    def _load_abi(self, name: str) -> List[Dict[str, Any]]:
        """Load contract ABI from JSON file"""
        abi_path = Path(__file__).parent.parent.parent / 'contracts' / 'interfaces' / f'{name}.json'
        with open(abi_path) as f:
            return json.load(f)['abi']

    async def _retry_with_backoff_async(
        self, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """Execute async function with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return await func(*args)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

    async def get_factory_async(self, address: str, abi: Optional[List[Dict[str, Any]]] = None) -> Optional[AsyncContract]:
        """Get factory contract instance with caching"""
        if address in self._factory_cache:
            return self._factory_cache[address]
            
        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(address),
                abi=abi if abi is not None else self.factory_abi
            )
            self._factory_cache[address] = factory
            return factory
        except Exception as e:
            print(f"Error getting factory contract: {str(e)}")
            return None

    async def get_vault_async(
        self, factory: AsyncContract, vault_address: str
    ) -> Optional[AsyncContract]:
        """Get vault contract instance with caching"""
        if vault_address in self._vault_cache:
            return self._vault_cache[vault_address]
            
        try:
            vault = self.w3.eth.contract(
                address=self.w3.to_checksum_address(vault_address),
                abi=self.vault_abi
            )
            self._vault_cache[vault_address] = vault
            return vault
        except Exception as e:
            print(f"Error getting vault contract: {str(e)}")
            return None

    async def get_admin_async(
        self, vault: AsyncContract, vault_address: str
    ) -> Optional[AsyncContract]:
        """Get admin contract instance with caching"""
        if vault_address in self._admin_cache:
            return self._admin_cache[vault_address]
            
        try:
            # Get admin address from vault using cached call
            admin_address = await self.web3_cache.call_function(vault, 'admin')
            if not admin_address:
                return None
                
            admin = self.w3.eth.contract(
                address=self.w3.to_checksum_address(admin_address),
                abi=self.admin_abi
            )
            self._admin_cache[vault_address] = admin
            return admin
        except Exception as e:
            print(f"Error getting admin contract: {str(e)}")
            return None

    async def get_vault_tokens_async(
        self, vault: AsyncContract, vault_address: str
    ) -> Optional[Dict[str, TokenInfo]]:
        """Get borrowed and collateral token information with caching"""
        if vault_address in self._token_info_cache:
            return self._token_info_cache[vault_address]
            
        try:
            # Get token addresses using fallback function names with caching
            borrowed_token = None
            try:
                borrowed_token = await self.web3_cache.call_function(vault, 'borrowed_token')
            except Exception:
                try:
                    borrowed_token = await self.web3_cache.call_function(vault, 'borrowedToken')
                except Exception as e:
                    print(f"Error getting borrowed token: {str(e)}")
                    return None
                
            collateral_token = None
            try:
                collateral_token = await self.web3_cache.call_function(vault, 'collateral_token')
            except Exception:
                try:
                    collateral_token = await self.web3_cache.call_function(vault, 'collateralToken')
                except Exception as e:
                    print(f"Error getting collateral token: {str(e)}")
                    return None
            
            if not borrowed_token or not collateral_token:
                return None
            
            # Get token details
            borrowed_info = await self._get_token_info_async(borrowed_token)
            collateral_info = await self._get_token_info_async(collateral_token)
            
            if not borrowed_info or not collateral_info:
                return None
                
            result = {
                'borrowed_token': cast(TokenInfo, borrowed_info),
                'collateral_token': cast(TokenInfo, collateral_info)
            }
            
            self._token_info_cache[vault_address] = result
            return result
            
        except Exception as e:
            print(f"Error getting vault tokens: {str(e)}")
            return None

    async def _get_token_info_async(self, token_address: str) -> Optional[TokenInfo]:
        """Get ERC20 token information with caching"""
        try:
            token = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            # Get token details using cached calls
            name = await self.web3_cache.call_function(token, 'name')
            symbol = await self.web3_cache.call_function(token, 'symbol')
            decimals_raw = await self.web3_cache.call_function(token, 'decimals')
            
            if not all([name, symbol, decimals_raw is not None]):
                return None
                
            # Safely convert decimals to int
            try:
                decimals = int(decimals_raw) if decimals_raw is not None else 18  # Default to 18 if conversion fails
            except (ValueError, TypeError):
                decimals = 18  # Default to 18 if conversion fails
                
            return {
                'address': token_address,
                'name': str(name),
                'symbol': str(symbol),
                'decimals': decimals
            }
            
        except Exception as e:
            print(f"Error getting token info: {str(e)}")
            return None

    async def get_loan_info_async(
        self, vault: AsyncContract, user_address: str
    ) -> Optional[Dict[str, Any]]:
        """Get loan information for a user with caching"""
        try:
            # Try different function names for user state with caching
            state = None
            try:
                state = await self.web3_cache.call_function(vault, 'user_state', user_address)
            except Exception:
                try:
                    # Try getting collateral and debt separately with caching
                    collateral = await self.web3_cache.call_function(vault, 'collateral', user_address)
                    debt = await self.web3_cache.call_function(vault, 'debt', user_address)
                    if collateral is not None and debt is not None:
                        state = [collateral, debt, 0]
                except Exception as e:
                    print(f"Error getting loan state: {str(e)}")
                    return None
            
            if not state:
                return None
                
            return {
                'user': user_address,
                'collateral': state[0],
                'debt': state[1]
            }
            
        except ContractLogicError:
            return None
        except Exception as e:
            print(f"Error getting loan info: {str(e)}")
            return None

    async def _handle_rate_limit_async(self) -> bool:
        """Handle rate limit error with fallback RPC endpoints"""
        # Implementation depends on specific RPC setup
        return False