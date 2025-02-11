import argparse
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
)

import aiohttp
import yaml
from colorama import Fore, Style, init
from dotenv import load_dotenv
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.exceptions import ContractLogicError

from src.utils.contract_queries import ContractQueries
from src.utils.formatters import format_token_amount, format_usd_amount, get_token_decimals
from src.utils.price_fetcher import PriceFetcher

T = TypeVar('T')

try:
    from tqdm import tqdm as tqdm_sync
    from tqdm.asyncio import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable: Optional[Sequence[T]], **kwargs) -> Iterator[T]:
        if iterable is not None:
            return iter(iterable)
        return iter([])
    tqdm_sync = tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.cache/analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize colorama for colored output
init()

class TokenInfo(TypedDict):
    """Type definition for token information"""
    address: str
    name: str
    symbol: str
    decimals: int
    contract: Optional[AsyncContract]

class VaultResult(TypedDict):
    """Type definition for vault analysis results"""
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
    borrowed_decimals: int
    collateral_decimals: int

@dataclass
class AnalyzerStats:
    """Statistics for the analysis run"""
    total_vaults: int = 0
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

    @property
    def collateralization_ratio(self) -> float:
        """Calculate collateralization ratio"""
        if self.total_borrowed_usd == 0:
            return 0.0
        return (self.total_collateral_usd / self.total_borrowed_usd) * 100

class LoanAnalyzer:
    """Main analyzer class for processing Ethereum loan data"""
    
    def __init__(self, show_progress: bool = True):
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.w3: Optional[AsyncWeb3] = None
        self.queries: Optional[ContractQueries] = None
        self.price_fetcher: Optional[PriceFetcher] = None
        self.factory: Optional[AsyncContract] = None
        self.stats = AnalyzerStats()
        self.show_progress = show_progress
        
        # Track empty responses
        self.empty_responses = 0
        self.max_empty_responses = 10  # Stop after 10 empty responses

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path('config/analyzer_config.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise RuntimeError(f"Failed to load config: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        pass

    async def initialize(self) -> None:
        """Initialize connections and utilities"""
        logger.info("Initializing loan analyzer...")
        
        try:
            # Load environment variables
            load_dotenv()
            
            # Connect to Ethereum network
            self.w3 = await self._setup_web3()
            if not self.w3:
                raise RuntimeError("Failed to connect to Ethereum network")
                
            # Initialize utilities
            cache_dir = Path('.cache')  # Changed to use project root
            cache_dir.mkdir(exist_ok=True)
            
            self.queries = ContractQueries(self.w3, str(cache_dir))
            self.price_fetcher = PriceFetcher(str(cache_dir))
            
            logger.info("Initialization complete")
            
        except Exception as e:
            await self.cleanup()
            raise

    def _is_running_on_gcp(self) -> bool:
        """Check if running on Google Cloud Platform"""
        try:
            import requests

            # Try to access GCP metadata server
            response = requests.get(
                'http://metadata.google.internal',
                headers={'Metadata-Flavor': 'Google'},
                timeout=1
            )
            return response.status_code == 200
        except:
            return False

    def _get_rpc_endpoints(self) -> List[str]:
        """Get RPC endpoints based on environment"""
        is_gcp = self._is_running_on_gcp()
        env_key = 'gcp' if is_gcp else 'default'
        endpoints = self.config['rpc_endpoints'].get(env_key, [])
        
        # Substitute environment variables in endpoints
        processed_endpoints = []
        for endpoint in endpoints:
            try:
                # Replace ${VAR} with environment variable values
                import os
                import re
                processed = re.sub(
                    r'\${([^}]+)}',
                    lambda m: os.environ.get(m.group(1), ''),
                    endpoint
                )
                if '${' not in processed:  # Only add if all vars were substituted
                    processed_endpoints.append(processed)
                else:
                    logger.warning(f"Skipping endpoint {endpoint} due to missing environment variables")
            except Exception as e:
                logger.warning(f"Error processing endpoint {endpoint}: {str(e)}")
                continue
                
        if not processed_endpoints:
            logger.error(f"No valid RPC endpoints found for environment: {env_key}")
            return []
            
        return processed_endpoints

    async def _setup_web3(self) -> Optional[AsyncWeb3]:
        """Setup Web3 connection with fallback endpoints"""
        endpoints = self._get_rpc_endpoints()
        if not endpoints:
            return None
            
        for endpoint in endpoints:
            try:
                w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(endpoint))
                if await w3.is_connected():
                    logger.info(f"Connected to {endpoint}")
                    return w3
            except Exception as e:
                logger.warning(f"Failed to connect to {endpoint}: {str(e)}")
                continue
        return None

    async def get_token_prices(self, tokens: List[str]) -> Dict[str, float]:
        """Get prices for multiple tokens concurrently"""
        if not self.price_fetcher:
            return {}
        return await self.price_fetcher.get_multiple_prices_async(tokens)

    async def _get_vault_loans(self, vault: 'AsyncContract') -> AsyncGenerator[Dict[str, Any], None]:
        """Get all loans for a vault using async generator"""
        if not self.queries:
            logger.error("Queries not initialized")
            return
            
        index = 0
        consecutive_errors = 0
        max_errors = self.config['error_limits']['max_consecutive_errors']
        
        while consecutive_errors < max_errors:
            try:
                user_address = await self.queries._retry_with_backoff_async(
                    vault.functions.loans(index).call
                )
                if not user_address or user_address == '0x' + '0' * 40:
                    consecutive_errors += 1
                else:
                    consecutive_errors = 0
                    loan_info = await self.queries.get_loan_info_async(vault, user_address)
                    if loan_info:
                        yield loan_info
                
                index += 1
                
            except Exception as e:
                if 'rate limit' in str(e).lower():
                    logger.warning(f"Rate limit hit at index {index}")
                    break
                elif 'execution reverted' in str(e).lower():
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        logger.info(f"Stopping after {max_errors} consecutive errors")
                        break
                else:
                    logger.error(f"Error getting loan at index {index}: {str(e)}")
                    break

    async def analyze_vault(
        self, factory: Optional['AsyncContract'], vault_address: str
    ) -> Optional[VaultResult]:
        """Analyze a single vault's loans and tokens"""
        if not factory:
            logger.error("Factory contract not provided")
            return None
            
        try:
            logger.info(f"Analyzing vault {vault_address}")
            
            if not self.queries:
                logger.error("Queries not initialized")
                return None

            # Get vault contract
            vault = await self.queries.get_vault_async(factory, vault_address)
            if not vault:
                logger.warning(f"Could not get vault contract for {vault_address}")
                return None
            
            # Get token information
            token_info = await self.queries.get_vault_tokens_async(vault, vault_address)
            if not token_info:
                logger.warning(f"Could not get token info for vault {vault_address}")
                return None
            
            borrowed_token = token_info['borrowed_token']['address']
            collateral_token = token_info['collateral_token']['address']
            
            # Get token decimals
            borrowed_decimals = get_token_decimals(token_info['borrowed_token'].get('contract'))
            collateral_decimals = get_token_decimals(token_info['collateral_token'].get('contract'))
            
            # Get token prices concurrently
            prices = await self.get_token_prices([borrowed_token, collateral_token])
            borrowed_price = prices.get(borrowed_token, 1.0)  # Default to 1.0 for stablecoins
            collateral_price = prices.get(collateral_token, 0.0)  # Default to 0.0 for unknown tokens
            
            # Process loans using async generator
            total_borrowed = 0
            total_collateral = 0
            loans = []
            
            async for loan in self._get_vault_loans(vault):
                total_borrowed += loan['debt']
                total_collateral += loan['collateral']
                loans.append(loan)
            
            total_borrowed_usd = total_borrowed * borrowed_price
            total_collateral_usd = total_collateral * collateral_price
            
            return {
                'address': vault_address,
                'loans': loans,
                'total_borrowed': total_borrowed,
                'total_collateral': total_collateral,
                'total_borrowed_usd': total_borrowed_usd,
                'total_collateral_usd': total_collateral_usd,
                'borrowed_token': borrowed_token,
                'collateral_token': collateral_token,
                'borrowed_price': borrowed_price,
                'collateral_price': collateral_price,
                'borrowed_decimals': borrowed_decimals,
                'collateral_decimals': collateral_decimals
            }
            
        except Exception as e:
            logger.error(f"Error analyzing vault {vault_address}: {str(e)}")
            return None

    async def discover_vaults(self, factory_address: str) -> List[str]:
        """Discover all active vaults from factory"""
        logger.info(f"Discovering vaults from factory {factory_address}...")
        
        if not self.queries:
            logger.error("Queries not initialized")
            return []
            
        try:
            # Load and parse factory ABI from config
            factory_abi = self.config['contracts'].get('factory_abi')
            if not factory_abi:
                logger.error("Factory ABI not found in config")
                return []
                
            try:
                # Check if contract exists
                if not self.w3:
                    logger.error("Web3 not initialized")
                    return []
                
                checksum_address = self.w3.to_checksum_address(factory_address)
                code = await self.w3.eth.get_code(checksum_address)
                if not code or code == '0x':
                    logger.error(f"No contract found at address {factory_address}")
                    return []
                    
                factory_abi = json.loads(factory_abi)
                logger.info(f"Using factory ABI with {len(factory_abi)} functions")
                
                factory = await self.queries.get_factory_async(factory_address, factory_abi)
                
                if not factory:
                    logger.error("Failed to initialize factory contract")
                    return []
                    
                # Get total number of vaults
                try:
                    market_count = await factory.functions.market_count().call()
                    logger.info(f"Found {market_count} markets")
                    
                    # Get all vault addresses with progress bar
                    vaults = []
                    if self.show_progress:
                        print(f"\nDiscovering vaults (0/{market_count})\r\n", end="")
                    
                    for i in range(market_count):
                        vault = await factory.functions.controllers(i).call()
                        if vault != '0x' + '0' * 40:
                            vaults.append(vault)
                        if self.show_progress:
                            print(f"\rDiscovering vaults ({i+1}/{market_count})\r\n", end="")
                            
                    if self.show_progress:
                        print("\n")
                            
                    logger.info(f"Found {len(vaults)} active vaults")
                    self.factory = factory
                    return vaults
                        
                except ContractLogicError as e:
                    logger.error(f"Contract logic error: {e}")
                    return []
                except Exception as e:
                    logger.error(f"Failed to get vaults: {e}")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse factory ABI: {e}")
                return []
            except Exception as e:
                logger.error(f"Error initializing factory contract: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get factory contract: {str(e)}")
            return []

    def print_vault_summary(self, result: Optional[VaultResult]) -> None:
        """Print summary for a single vault"""
        if not result:
            return
            
        print(f"\n{Fore.CYAN}Vault {result['address']}{Style.RESET_ALL}")
        print("=" * 80)
        
        # Get cached token info if available
        if self.queries:
            token_info = getattr(self.queries, '_token_info_cache', {}).get(result['address'])
            if token_info:
                print(f"Borrowed Token:    {token_info['borrowed_token']['name']}")
                print(f"                   {Fore.BLUE}{result['borrowed_token']}{Style.RESET_ALL}")
                print(f"Collateral Token:  {token_info['collateral_token']['name']}")
                print(f"                   {Fore.BLUE}{result['collateral_token']}{Style.RESET_ALL}")
        
        print("\nPrices:")
        if result.get('borrowed_price'):
            print(f"Borrowed Price:    ${result['borrowed_price']:.2f}")
        if result.get('collateral_price'):
            print(f"Collateral Price:  ${result['collateral_price']:.2f}")
            
        print("\nLoan Statistics:")
        print(f"Active Loans:      {Fore.YELLOW}{len(result.get('loans', []))}{Style.RESET_ALL}")
        print(f"Total Borrowed:    {Fore.RED}{format_token_amount(result.get('total_borrowed', 0), result['borrowed_decimals'])}{Style.RESET_ALL}")
        print(f"Total Collateral:  {Fore.GREEN}{format_token_amount(result.get('total_collateral', 0), result['collateral_decimals'])}{Style.RESET_ALL}")
        print(f"Borrowed USD:      {Fore.RED}{format_usd_amount(result.get('total_borrowed_usd', 0))}{Style.RESET_ALL}")
        print(f"Collateral USD:    {Fore.GREEN}{format_usd_amount(result.get('total_collateral_usd', 0))}{Style.RESET_ALL}")

    def print_grand_totals(self) -> None:
        """Print grand totals and statistics"""
        print("\n" + "="*80)
        print(f"{Fore.CYAN}ANALYSIS COMPLETE{Style.RESET_ALL}")
        print("="*80)
        
        print("\nSummary:")
        print(f"Vaults:            {Fore.YELLOW}{self.stats.total_vaults}{Style.RESET_ALL}")
        print(f"Active Loans:      {Fore.YELLOW}{self.stats.total_loans}{Style.RESET_ALL}")
        
        print("\nGrand Totals:")
        print(f"Total Borrowed:    {Fore.RED}{format_usd_amount(self.stats.total_borrowed_usd)}{Style.RESET_ALL}")
        print(f"Total Collateral:  {Fore.GREEN}{format_usd_amount(self.stats.total_collateral_usd)}{Style.RESET_ALL}")
        print(f"Collateral Ratio:  {Fore.BLUE}{self.stats.collateralization_ratio:.2f}%{Style.RESET_ALL}")
        
        print(f"\nDuration:         {Fore.BLUE}{self.stats.duration:.2f} seconds{Style.RESET_ALL}")

    async def run(self) -> None:
        """Main execution flow"""
        try:
            await self.initialize()
            self.stats.start_time = time.time()
            
            factory_address = self.config['contracts']['factory']
            vaults = await self.discover_vaults(factory_address)
            self.stats.total_vaults = len(vaults)
            
            # Process vaults
            if not self.factory:
                logger.error("Factory contract not initialized")
                return
                
            if self.show_progress:
                print(f"\nAnalyzing vaults (0/{len(vaults)})\r\n", end="")
                
            for i, vault in enumerate(vaults, 1):
                try:
                    logger.info(f"Analyzing vault {i}/{len(vaults)}: {vault}")
                    result = await self.analyze_vault(self.factory, vault)
                    if result:
                        self.print_vault_summary(result)
                        
                        # Update statistics
                        self.stats.total_loans += len(result.get('loans', []))
                        self.stats.total_borrowed_usd += result.get('total_borrowed_usd', 0)
                        self.stats.total_collateral_usd += result.get('total_collateral_usd', 0)
                    if self.show_progress:
                        print(f"\rAnalyzing vaults ({i}/{len(vaults)})\r\n", end="")
                except Exception as e:
                    logger.error(f"Error processing vault {vault}: {str(e)}")
                    continue
            
            self.stats.end_time = time.time()
            self.print_grand_totals()
            
            if self.config['output']['save_context']:
                await self._save_analysis_context()
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise
        except KeyboardInterrupt:
            logger.info("Analysis interrupted by user")
            if self.stats.start_time:
                self.stats.end_time = time.time()
                self.print_grand_totals()

    async def _save_analysis_context(self) -> None:
        """Save analysis context to file"""
        context = {
            'timestamp': time.time(),
            'stats': {
                'total_vaults': self.stats.total_vaults,
                'total_loans': self.stats.total_loans,
                'total_borrowed_usd': self.stats.total_borrowed_usd,
                'total_collateral_usd': self.stats.total_collateral_usd,
                'collateralization_ratio': self.stats.collateralization_ratio,
                'duration': self.stats.duration
            }
        }
        
        context_file = Path('.cache') / 'context.json'  # Changed to use project root
        try:
            context_file.write_text(json.dumps(context, indent=2))
            logger.info("Analysis context saved successfully")
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Ethereum Loan Analytics")
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    return parser.parse_args()

async def main():
    """Entry point"""
    args = parse_args()
    try:
        async with LoanAnalyzer(show_progress=not args.no_progress) as analyzer:
            await analyzer.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise