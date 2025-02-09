from typing import Optional, Dict, Any, List, Tuple
import os
import json
import time
from web3 import Web3
from web3.contract import Contract
from concurrent.futures import ThreadPoolExecutor, as_completed
from .web3_cache import CachedWeb3Calls

# Add user_state ABI
USER_STATE_ABI = {
    "inputs": [{"internalType": "address", "name": "_user", "type": "address"}],
    "name": "user_state",
    "outputs": [
        {"internalType": "uint256", "name": "", "type": "uint256"},
        {"internalType": "uint256", "name": "", "type": "uint256"},
        {"internalType": "uint256", "name": "", "type": "uint256"}
    ],
    "stateMutability": "view",
    "type": "function",
    "type": "function",
    "selector": "0xec74c0a8"
}

class ContractQueries:
    def __init__(self, w3: Web3, cache_dir: str):
        self.w3 = w3
        self.cache = CachedWeb3Calls(w3, cache_dir)
        self.cache_dir = cache_dir
        
        # Load common ABIs
        self.factory_abi = self._load_abi('factory.json')
        self.erc20_abi = self._load_abi('erc20.json')
        self.controller_abi = self._load_abi('controller.json')
        self.amm_abi = self._load_abi('amm.json')
        
        # Contract instances cache
        self._contract_instances: Dict[str, Contract] = {}
        
        # Token info cache
        self._token_info_cache: Dict[str, Dict[str, Any]] = {}
        self._load_token_cache()
        
        # Loan info cache
        self._loan_info_cache: Dict[str, Dict[str, Any]] = {}
        self._load_loan_cache()
        
        # Configure batch sizes
        self.batch_size = 30  # Increased batch size for parallel requests
        
        # Configure retry settings
        self.max_retries = 3
        self.retry_delay = 2
        self.rate_limit_cooldown = 60  # 1 minute cooldown for rate limits
        
        # Store reference to RPC endpoints from main.py
        if not hasattr(w3, '_rpc_endpoints'):
            self._initialize_rpc_endpoints()

    def _load_token_cache(self):
        """Load token cache from file"""
        cache_file = os.path.join(self.cache_dir, 'controller_tokens_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Check if cache is still valid (12 hours)
                    if cache_data.get('timestamp', 0) + (12 * 3600) > time.time():
                        self._token_info_cache = cache_data.get('data', {})
                    else:
                        # Cache expired, create new
                        self._token_info_cache = {}
            except Exception as e:
                print(f"Error loading token cache: {str(e)}")
                self._token_info_cache = {}
        else:
            self._token_info_cache = {}

    def _save_token_cache(self):
        """Save token cache to file"""
        cache_file = os.path.join(self.cache_dir, 'controller_tokens_cache.json')
        try:
            cache_data = {
                'timestamp': time.time(),
                'data': self._token_info_cache
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving token cache: {str(e)}")

    def _load_loan_cache(self):
        """Load loan cache from file"""
        cache_file = os.path.join(self.cache_dir, 'loan_info_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Check if cache is still valid (4 hours)
                    if cache_data.get('timestamp', 0) + (4 * 3600) > time.time():
                        self._loan_info_cache = cache_data.get('data', {})
                    else:
                        # Cache expired, create new
                        self._loan_info_cache = {}
            except Exception as e:
                print(f"Error loading loan cache: {str(e)}")
                self._loan_info_cache = {}
        else:
            self._loan_info_cache = {}

    def _save_loan_cache(self):
        """Save loan cache to file"""
        cache_file = os.path.join(self.cache_dir, 'loan_info_cache.json')
        try:
            cache_data = {
                'timestamp': time.time(),
                'data': self._loan_info_cache
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving loan cache: {str(e)}")

    def _initialize_rpc_endpoints(self):
        """Initialize default RPC endpoints if not provided"""
        from datetime import datetime, timedelta
        
        class RPCEndpoint:
            def __init__(self, url: str, cooldown_minutes: int = 5):
                self.url = url
                self.last_used = None
                self.cooldown = timedelta(minutes=cooldown_minutes)
                self.is_active = True
                self.error_count = 0
                self.last_error = None
            
            def can_use(self) -> bool:
                if not self.is_active or self.error_count >= 3:
                    return False
                if self.last_used is None:
                    return True
                return datetime.now() - self.last_used >= self.cooldown
            
            def mark_used(self):
                self.last_used = datetime.now()
            
            def mark_error(self, error: Exception):
                self.error_count += 1
                self.last_error = error
                if self.error_count >= 3:
                    self.is_active = False
            
            def reset_errors(self):
                self.error_count = 0
                self.last_error = None
                self.is_active = True
            
            def check_cooldown(self) -> bool:
                if not self.is_active and self.last_used is not None:
                    if datetime.now() - self.last_used >= self.cooldown:
                        self.reset_errors()
                        return True
                return False
        
        # Initialize with reliable public RPC endpoints
        self.w3._rpc_endpoints = [
            RPCEndpoint('https://eth.llamarpc.com'),
            RPCEndpoint('https://rpc.ankr.com/eth'),
            RPCEndpoint('https://eth-mainnet.public.blastapi.io'),
            RPCEndpoint('https://ethereum.publicnode.com'),
            RPCEndpoint('https://1rpc.io/eth'),
            RPCEndpoint('https://rpc.mevblocker.io'),
            RPCEndpoint('https://cloudflare-eth.com'),
            RPCEndpoint('https://eth-rpc.gateway.pokt.network'),
            RPCEndpoint('https://api.mycryptoapi.com/eth'),
            RPCEndpoint('https://nodes.mewapi.io/rpc/eth')
        ]

    def _load_abi(self, filename: str) -> Optional[list]:
        """Load ABI from interfaces directory with error handling"""
        try:
            interfaces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'contracts', 'interfaces')
            with open(os.path.join(interfaces_dir, filename), 'r') as f:
                return json.load(f)['abi']
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            return None

    def _get_contract_instance(self, address: str, abi: list) -> Optional[Contract]:
        """Get or create contract instance with caching"""
        cache_key = f"{address}_{hash(str(abi))}"
        if cache_key not in self._contract_instances:
            try:
                contract = self.w3.eth.contract(address=address, abi=abi)
                self._contract_instances[cache_key] = contract
            except Exception as e:
                print(f"Error creating contract instance for {address}: {str(e)}")
                return None
        return self._contract_instances[cache_key]

    def _handle_rate_limit(self) -> bool:
        """Handle rate limit by switching RPC endpoint"""
        current_url = self.w3.provider.endpoint_uri
        
        # Mark current endpoint as rate limited
        for endpoint in self.w3._rpc_endpoints:
            if endpoint.url == current_url:
                endpoint.mark_error(Exception("Rate limited"))
                break
        
        # Try to find available endpoint
        for endpoint in self.w3._rpc_endpoints:
            if endpoint.url != current_url and endpoint.can_use():
                try:
                    self.w3.provider = Web3.HTTPProvider(endpoint.url)
                    if self.w3.is_connected():
                        endpoint.mark_used()
                        print(f"Switched to {endpoint.url}")
                        return True
                except Exception as e:
                    endpoint.mark_error(e)
                    continue
        
        # If no endpoints available, wait for cooldown
        print(f"No RPC endpoints available, waiting {self.rate_limit_cooldown}s...")
        time.sleep(self.rate_limit_cooldown)
        
        # Try endpoints again after cooldown
        for endpoint in self.w3._rpc_endpoints:
            if endpoint.check_cooldown():
                try:
                    self.w3.provider = Web3.HTTPProvider(endpoint.url)
                    if self.w3.is_connected():
                        endpoint.mark_used()
                        print(f"Switched to {endpoint.url} after cooldown")
                        return True
                except Exception as e:
                    endpoint.mark_error(e)
                    continue
        
        return False

    def _retry_with_backoff(self, func: callable, *args, **kwargs) -> Any:
        """Execute function with retry logic and exponential backoff"""
        attempt = 0
        while attempt < self.max_retries:
            try:
                result = func(*args, **kwargs)
                # Handle Web3 calls that return HexBytes
                if hasattr(result, 'hex'):
                    return result.hex()
                return result
            except Exception as e:
                if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401']):
                    if self._handle_rate_limit():
                        continue
                    else:
                        raise
                
                attempt += 1
                if attempt >= self.max_retries:
                    raise
                
                delay = self.retry_delay * (2 ** attempt)
                print(f"Retry {attempt}/{self.max_retries} after {delay}s: {str(e)}")
                time.sleep(delay)

    def _try_call_function(self, contract: Contract, function_names: List[str], *args) -> Optional[Any]:
        """Try multiple function names and return first successful result"""
        last_error = None
        for name in function_names:
            try:
                if hasattr(contract.functions, name):
                    if args:
                        result = getattr(contract.functions, name)(*args).call()
                    else:
                        result = getattr(contract.functions, name)().call()
                    # Handle Web3 calls that return HexBytes
                    if hasattr(result, 'hex'):
                        return result.hex()
                    return result
            except Exception as e:
                last_error = e
                if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401']):
                    if self._handle_rate_limit():
                        continue
                    else:
                        print(f"Rate limit error calling {name}: {str(e)}")
                        return None
                continue
        
        if last_error:
            print(f"Error calling functions {function_names}: {str(last_error)}")
        return None

    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get ERC20 token information with retries"""
        try:
            if not self.erc20_abi:
                print("No ERC20 ABI loaded")
                return None
            
            token = self._get_contract_instance(token_address, self.erc20_abi)
            if not token:
                return None
            
            # Get token info with retries
            name = self._retry_with_backoff(self.cache.call_function, token, 'name')
            symbol = self._retry_with_backoff(self.cache.call_function, token, 'symbol')
            decimals = self._retry_with_backoff(self.cache.call_function, token, 'decimals')
            
            if not all([name, symbol, decimals]):
                print(f"Failed to get complete token info for {token_address}")
                return None
            
            return {
                'address': token_address,
                'name': name,
                'symbol': symbol,
                'decimals': decimals
            }
            
        except Exception as e:
            print(f"Error getting token info for {token_address}: {str(e)}")
            return None

    def get_multiple_token_info(self, token_addresses: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get information for multiple tokens in parallel"""
        results = {}
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            future_to_address = {
                executor.submit(self.get_token_info, addr): addr
                for addr in token_addresses
            }
            for future in as_completed(future_to_address):
                addr = future_to_address[future]
                try:
                    results[addr] = future.result()
                except Exception as e:
                    print(f"Error getting info for {addr}: {str(e)}")
                    results[addr] = None
        return results

    def get_admin_contract(self, factory: Contract, controller_address: str) -> Optional[Contract]:
        """Get admin contract for a controller from factory"""
        try:
            print(f"\nGetting admin contract for controller {controller_address}...")
            
            # The controller itself is the admin contract
            code = self._retry_with_backoff(self.w3.eth.get_code, controller_address)
            if not code or code == '0x':
                print(f"No contract at controller address {controller_address}")
                return None
            
            return self._get_contract_instance(controller_address, self.controller_abi)
            
        except Exception as e:
            print(f"Error getting admin contract for {controller_address}: {str(e)}")
            return None

    def get_loan_info(self, admin: Contract, user_address: str) -> Optional[Dict[str, Any]]:
        """Get loan information for a user with retries"""
        try:
            print(f"Getting loan info from contract {admin.address} for user {user_address}")
            
            # Check loan cache first
            cache_key = f"{admin.address}_{user_address}"
            if cache_key in self._loan_info_cache:
                return self._loan_info_cache[cache_key]
            
            # Create temporary contract with user_state ABI
            temp_contract = self.w3.eth.contract(
                address=admin.address,
                abi=[USER_STATE_ABI]
            )
            
            # Call user_state function
            try:
                result = self._retry_with_backoff(
                    temp_contract.functions.user_state(user_address).call
                )
                
                if not result or len(result) < 3:
                    return None
                
                # First element is collateral, third is debt
                collateral = result[0]
                debt = result[2]
                
                if debt == 0:
                    return None
                
                loan_info = {
                    'user_address': user_address,
                    'debt': debt,
                    'collateral': collateral,
                    'is_liquidated': False
                }
                
                # Cache the result
                self._loan_info_cache[cache_key] = loan_info
                self._save_loan_cache()
                
                return loan_info
                
            except Exception as e:
                print(f"Error calling user_state for {user_address}: {str(e)}")
                return None
            
        except Exception as e:
            print(f"Error getting loan info for {user_address}: {str(e)}")
            return None

    def get_multiple_loan_info(self, admin: Contract, user_addresses: List[str]) -> List[Dict[str, Any]]:
        """Get loan information for multiple users in parallel"""
        loans = []
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            future_to_address = {
                executor.submit(self.get_loan_info, admin, addr): addr
                for addr in user_addresses
            }
            for future in as_completed(future_to_address):
                addr = future_to_address[future]
                try:
                    loan_info = future.result()
                    if loan_info and loan_info['debt'] > 0:
                        loans.append(loan_info)
                except Exception as e:
                    print(f"Error getting loan info for {addr}: {str(e)}")
                    continue
        return loans

    def get_controller_tokens(self, admin: Contract, controller_address: str) -> Optional[Dict[str, Any]]:
        """Get controller token information with caching"""
        if controller_address in self._token_info_cache:
            return self._token_info_cache[controller_address]
            
        try:
            # Get token addresses
            borrowed_token = self._try_call_function(
                admin,
                ['borrowed_token', 'borrowedToken']
            )
            collateral_token = self._try_call_function(
                admin,
                ['collateral_token', 'collateralToken']
            )
            
            if not borrowed_token or not collateral_token:
                return None
            
            # Get token info
            borrowed_info = self.get_token_info(borrowed_token)
            collateral_info = self.get_token_info(collateral_token)
            
            if not borrowed_info or not collateral_info:
                return None
            
            result = {
                'borrowed_token': borrowed_info,
                'collateral_token': collateral_info
            }
            
            # Cache the result
            self._token_info_cache[controller_address] = result
            self._save_token_cache()
            
            return result
            
        except Exception as e:
            print(f"Error getting controller tokens for {controller_address}: {str(e)}")
            return None

    def get_loans(self, factory: Contract, controller_address: str) -> List[Dict[str, Any]]:
        """Get all loans from controller with parallel processing"""
        try:
            # Get admin contract first (controller is the admin)
            admin = self.get_admin_contract(factory, controller_address)
            if not admin:
                print(f"Could not get admin contract for controller {controller_address}")
                return []
            
            # Get token info from cache or fetch new
            token_info = self.get_controller_tokens(admin, controller_address)
            if not token_info:
                return []
            
            # Get all loans
            loans = []
            user_addresses = []
            index = 0
            
            # First collect all user addresses
            while True:
                try:
                    user_address = self._retry_with_backoff(
                        admin.functions.loans(index).call
                    )
                    if not user_address or user_address == '0x' + '0' * 40:
                        break
                    
                    user_addresses.append(user_address)
                    index += 1
                    
                except Exception as e:
                    if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401']):
                        # Rate limit hit, stop collecting addresses
                        print(f"Rate limit hit, stopping address collection at index {index}")
                        break
                    print(f"Error getting loan at index {index}: {str(e)}")
                    break
            
            # Process loans in batches
            for i in range(0, len(user_addresses), self.batch_size):
                batch = user_addresses[i:i + self.batch_size]
                batch_loans = self.get_multiple_loan_info(admin, batch)
                loans.extend(batch_loans)
            
            return loans
            
        except Exception as e:
            print(f"Error getting loans for controller {controller_address}: {str(e)}")
            return []

    def get_factory(self, factory_address: str) -> Optional[Contract]:
        """Get factory contract instance with validation"""
        try:
            if not self.factory_abi:
                print("No factory ABI loaded")
                return None
            
            # Validate contract
            code = self._retry_with_backoff(self.w3.eth.get_code, factory_address)
            if not code or code == '0x':
                print(f"No contract at {factory_address}")
                return None
            
            return self._get_contract_instance(factory_address, self.factory_abi)
            
        except Exception as e:
            print(f"Error getting factory {factory_address}: {str(e)}")
            return None