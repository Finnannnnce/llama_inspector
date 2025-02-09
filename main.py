import os
import json
import time
import yaml
from web3 import Web3
from dotenv import load_dotenv
from src.utils.contract_queries import ContractQueries
from src.utils.price_fetcher import PriceFetcher
from src.utils.formatters import format_token_amount, format_usd_amount
from colorama import init, Fore, Style
from typing import List, Dict, Any, Optional, TypedDict
from concurrent.futures import ThreadPoolExecutor
from web3.contract import Contract
from dataclasses import dataclass
from pathlib import Path

# Initialize colorama for colored output
init()

class TokenInfo(TypedDict):
    """Type definition for token information"""
    address: str
    name: str
    symbol: str
    decimals: int

class ControllerResult(TypedDict):
    """Type definition for controller analysis results"""
    address: str
    loans: List[Dict[str, Any]]
    total_borrowed: float
    total_collateral: float
    total_borrowed_usd: float
    total_collateral_usd: float
    borrowed_token: str
    collateral_token: str
    borrowed_price: float
    collateral_price: float

@dataclass
class AnalyzerStats:
    """Statistics for the analysis run"""
    total_controllers: int = 0
    total_loans: int = 0
    total_borrowed_usd: float = 0
    total_collateral_usd: float = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> float:
        """Calculate analysis duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

class LoanAnalyzer:
    """Main analyzer class for processing Ethereum loan data"""
    
    def __init__(self):
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.w3: Optional[Web3] = None
        self.queries: Optional[ContractQueries] = None
        self.price_fetcher: Optional[PriceFetcher] = None
        self.factory: Optional[Contract] = None
        self.stats = AnalyzerStats()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / 'config' / 'analyzer_config.yaml'
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")

    def initialize(self) -> None:
        """Initialize connections and utilities"""
        print("Initializing loan analyzer...")
        
        # Load environment variables
        load_dotenv()
        
        # Connect to Ethereum network
        self.w3 = self._setup_web3()
        if not self.w3:
            raise RuntimeError("Failed to connect to Ethereum network")
            
        # Initialize utilities
        cache_dir = Path(__file__).parent / '.cache'
        cache_dir.mkdir(exist_ok=True)
        
        self.queries = ContractQueries(self.w3, str(cache_dir))
        self.price_fetcher = PriceFetcher(str(cache_dir))
        
        print("Initialization complete")

    def _setup_web3(self) -> Optional[Web3]:
        """Setup Web3 connection with fallback endpoints"""
        for endpoint in self.config['rpc_endpoints']:
            try:
                w3 = Web3(Web3.HTTPProvider(endpoint))
                if w3.is_connected():
                    print(f"Connected to {endpoint}")
                    return w3
            except Exception as e:
                print(f"Failed to connect to {endpoint}: {str(e)}")
                continue
        return None

    def analyze_controller(self, factory: Contract, controller_address: str) -> Optional[ControllerResult]:
        """
        Analyze a single controller's loans and tokens
        
        Args:
            factory: Factory contract instance
            controller_address: Address of the controller to analyze
            
        Returns:
            Optional[ControllerResult]: Analysis results or None if analysis fails
        """
        try:
            print(f"\nAnalyzing controller {controller_address}")
            
            # Get admin contract
            admin = self.queries.get_admin_contract(factory, controller_address)
            if not admin:
                print(f"Could not get admin contract for controller {controller_address}")
                return None
            
            # Get token information
            token_info = self.queries.get_controller_tokens(admin, controller_address)
            if not token_info:
                print(f"Could not get token info for controller {controller_address}")
                return None
            
            borrowed_token = token_info['borrowed_token']['address']
            collateral_token = token_info['collateral_token']['address']
            
            # Get token prices
            borrowed_price = self.price_fetcher.get_token_price(borrowed_token)
            collateral_price = self.price_fetcher.get_token_price(collateral_token)
            
            # Get all loans
            loans = self._get_controller_loans(admin)
            if loans is None:
                return None
            
            # Calculate totals
            total_borrowed = sum(loan['debt'] for loan in loans)
            total_collateral = sum(loan['collateral'] for loan in loans)
            
            total_borrowed_usd = total_borrowed * (borrowed_price or 0)
            total_collateral_usd = total_collateral * (collateral_price or 0)
            
            return {
                'address': controller_address,
                'loans': loans,
                'total_borrowed': total_borrowed,
                'total_collateral': total_collateral,
                'total_borrowed_usd': total_borrowed_usd,
                'total_collateral_usd': total_collateral_usd,
                'borrowed_token': borrowed_token,
                'collateral_token': collateral_token,
                'borrowed_price': borrowed_price,
                'collateral_price': collateral_price
            }
            
        except Exception as e:
            print(f"Error analyzing controller {controller_address}: {str(e)}")
            return None

    def _get_controller_loans(self, admin: Contract) -> Optional[List[Dict[str, Any]]]:
        """
        Get all loans for a controller
        
        Args:
            admin: Admin contract instance
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of loan information or None if retrieval fails
        """
        loans = []
        user_addresses = []
        index = 0
        consecutive_errors = 0
        max_errors = self.config['error_limits']['max_consecutive_errors']
        
        # Collect all user addresses
        while consecutive_errors < max_errors:
            try:
                user_address = self.queries._retry_with_backoff(
                    admin.functions.loans(index).call
                )
                if not user_address or user_address == '0x' + '0' * 40:
                    consecutive_errors += 1
                else:
                    consecutive_errors = 0
                    user_addresses.append(user_address)
                
                index += 1
                
            except Exception as e:
                if self._is_rate_limit_error(str(e)):
                    print(f"Rate limit hit, stopping address collection at index {index}")
                    break
                elif 'execution reverted' in str(e).lower():
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        print(f"Stopping after {max_errors} consecutive errors")
                        break
                else:
                    print(f"Error getting loan at index {index}: {str(e)}")
                    break
        
        # Process loans in batches
        batch_size = self.config['batch_sizes']['loan_info']
        for i in range(0, len(user_addresses), batch_size):
            batch = user_addresses[i:i + batch_size]
            batch_loans = self.queries.get_multiple_loan_info(admin, batch)
            loans.extend(batch_loans)
        
        return loans

    def discover_controllers(self, factory_address: str) -> List[str]:
        """
        Discover all active controllers from factory
        
        Args:
            factory_address: Address of the factory contract
            
        Returns:
            List[str]: List of discovered controller addresses
        """
        print(f"\nDiscovering controllers from factory {factory_address}...")
        
        # Get factory contract
        self.factory = self.queries.get_factory(factory_address)
        if not self.factory:
            raise RuntimeError("Failed to get factory contract")
        
        # Load vault cache
        cache_file = Path(__file__).parent / '.cache' / 'vault_info_cache.json'
        vault_cache = self._load_vault_cache(cache_file)
        
        controllers = []
        index = 0
        consecutive_errors = 0
        max_errors = self.config['error_limits']['max_consecutive_errors']
        batch_size = self.config['batch_sizes']['controller_discovery']
        
        while consecutive_errors < max_errors:
            try:
                controllers.extend(
                    self._process_controller_batch(index, batch_size, vault_cache)
                )
                index += batch_size
                
            except Exception as e:
                if self._is_rate_limit_error(str(e)):
                    if self.queries._handle_rate_limit():
                        continue
                    else:
                        print(f"Rate limit hit, stopping controller discovery at index {index}")
                        break
                else:
                    print(f"Error discovering controllers: {str(e)}")
                    break
        
        print(f"\nFound {len(controllers)} active controllers")
        return controllers

    def _load_vault_cache(self, cache_file: Path) -> Dict[str, Any]:
        """Load vault cache from file"""
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text()).get('data', {})
            except Exception as e:
                print(f"Error loading vault cache: {str(e)}")
        return {}

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if an error is related to rate limiting"""
        rate_limit_indicators = ['429', 'rate', 'limit', 'unauthorized', '401', '403']
        return any(indicator in error_str.lower() for indicator in rate_limit_indicators)

    def _process_controller_batch(
        self, start_index: int, batch_size: int, vault_cache: Dict[str, Any]
    ) -> List[str]:
        """Process a batch of potential controllers"""
        batch_controllers = []
        
        # Prepare batch calls
        batch_calls = [
            self.factory.functions.controllers(start_index + i).call
            for i in range(batch_size)
        ]
        
        # Execute batch
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(call) for call in batch_calls]
            
            for i, future in enumerate(futures):
                try:
                    controller_address = future.result()
                    if self._is_valid_controller(controller_address, start_index + i, vault_cache):
                        batch_controllers.append(controller_address)
                except Exception as e:
                    if self._is_rate_limit_error(str(e)):
                        raise  # Re-raise to handle at higher level
                    print(f"Error getting controller at index {start_index + i}: {str(e)}")
        
        return batch_controllers

    def _is_valid_controller(
        self, address: str, index: int, vault_cache: Dict[str, Any]
    ) -> bool:
        """Check if a controller address is valid"""
        if not address or address == '0x' + '0' * 40:
            return False
            
        # Check vault cache first
        token_info = vault_cache.get(address)
        if token_info:
            print(f"\nFound controller {index}: {address}")
            print(f"Borrowed Token: {token_info['borrowed_token']['name']} "
                  f"({token_info['borrowed_token']['address']})")
            print(f"Collateral Token: {token_info['collateral_token']['name']} "
                  f"({token_info['collateral_token']['address']})")
            return True
            
        # Validate contract code exists
        code = self.queries._retry_with_backoff(self.w3.eth.get_code, address)
        return bool(code and code != '0x')

    def print_controller_summary(self, result: Optional[ControllerResult]) -> None:
        """Print summary for a single controller"""
        if not result:
            return
            
        print(f"\nController {result['address']}:")
        
        # Get cached token info
        token_info = self.queries._token_info_cache.get(result['address'])
        if token_info:
            print(f"Borrowed Token: {token_info['borrowed_token']['name']} ({result['borrowed_token']})")
            print(f"Collateral Token: {token_info['collateral_token']['name']} ({result['collateral_token']})")
        
        if result.get('borrowed_price'):
            print(f"Borrowed Token Price: ${result['borrowed_price']:.2f}")
        if result.get('collateral_price'):
            print(f"Collateral Token Price: ${result['collateral_price']:.2f}")
            
        print(f"\nActive Loans: {len(result.get('loans', []))}")
        print(f"Total Borrowed: {Fore.RED}{format_token_amount(result.get('total_borrowed', 0), '')}{Style.RESET_ALL}")
        print(f"Total Collateral: {Fore.GREEN}{format_token_amount(result.get('total_collateral', 0), '')}{Style.RESET_ALL}")
        print(f"Total Borrowed USD: {Fore.RED}{format_usd_amount(result.get('total_borrowed_usd', 0))}{Style.RESET_ALL}")
        print(f"Total Collateral USD: {Fore.GREEN}{format_usd_amount(result.get('total_collateral_usd', 0))}{Style.RESET_ALL}")

    def print_grand_totals(self) -> None:
        """Print grand totals and statistics"""
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        print(f"\nProcessed {self.stats.total_controllers} controllers")
        print(f"Found {self.stats.total_loans} active loans")
        print(f"\nGrand Totals:")
        print(f"Total Borrowed USD: {Fore.RED}{format_usd_amount(self.stats.total_borrowed_usd)}{Style.RESET_ALL}")
        print(f"Total Collateral USD: {Fore.GREEN}{format_usd_amount(self.stats.total_collateral_usd)}{Style.RESET_ALL}")
        print(f"\nAnalysis took {self.stats.duration:.2f} seconds")

    def run(self) -> None:
        """Main execution flow"""
        try:
            # Initialize
            self.initialize()
            
            # Start timing
            self.stats.start_time = time.time()
            
            # Get factory address from config
            factory_address = self.config['contracts']['factory']
            
            # Discover controllers
            controllers = self.discover_controllers(factory_address)
            self.stats.total_controllers = len(controllers)
            
            # Process controllers sequentially to avoid rate limits
            for controller in controllers:
                try:
                    result = self.analyze_controller(self.factory, controller)
                    if result:
                        self.print_controller_summary(result)
                        
                        # Update statistics
                        self.stats.total_loans += len(result.get('loans', []))
                        self.stats.total_borrowed_usd += result.get('total_borrowed_usd', 0)
                        self.stats.total_collateral_usd += result.get('total_collateral_usd', 0)
                        
                except Exception as e:
                    print(f"Error processing controller {controller}: {str(e)}")
                    continue
            
            # Record end time
            self.stats.end_time = time.time()
            
            # Print final summary
            self.print_grand_totals()
            
            # Save context if configured
            if self.config['output']['save_context']:
                self._save_analysis_context()
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            raise
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user")
            if self.stats.start_time:
                self.stats.end_time = time.time()
                self.print_grand_totals()

    def _save_analysis_context(self) -> None:
        """Save analysis context to file"""
        context = {
            'timestamp': time.time(),
            'stats': {
                'total_controllers': self.stats.total_controllers,
                'total_loans': self.stats.total_loans,
                'total_borrowed_usd': self.stats.total_borrowed_usd,
                'total_collateral_usd': self.stats.total_collateral_usd,
                'duration': self.stats.duration
            }
        }
        
        context_file = Path(__file__).parent / '.cache' / 'context.json'
        try:
            context_file.write_text(json.dumps(context, indent=2))
        except Exception as e:
            print(f"Error saving context: {str(e)}")

def main():
    """Entry point"""
    analyzer = LoanAnalyzer()
    analyzer.run()

if __name__ == '__main__':
    main()