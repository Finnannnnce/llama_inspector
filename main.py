import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv
from src.utils.contract_queries import ContractQueries
from src.utils.price_fetcher import PriceFetcher
from src.utils.formatters import format_token_amount, format_usd_amount
from colorama import init, Fore, Back, Style
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from web3.contract import Contract

# Initialize colorama
init()

class LoanAnalyzer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Web3
        self.w3 = None
        self.queries = None
        self.price_fetcher = None
        self.factory = None
        
        # Statistics
        self.stats = {
            'total_controllers': 0,
            'total_loans': 0,
            'total_borrowed_usd': 0,
            'total_collateral_usd': 0,
            'start_time': None,
            'end_time': None
        }

    def initialize(self):
        """Initialize connections and utilities"""
        print("Initializing loan analyzer...")
        
        # Connect to Ethereum network
        self.w3 = self._setup_web3()
        if not self.w3:
            raise Exception("Failed to connect to Ethereum network")
            
        # Initialize utilities
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        self.queries = ContractQueries(self.w3, cache_dir)
        self.price_fetcher = PriceFetcher(cache_dir)
        
        print("Initialization complete")

    def _setup_web3(self) -> Optional[Web3]:
        """Setup Web3 connection with fallback endpoints"""
        # Default RPC endpoints
        endpoints = [
            'https://eth.llamarpc.com',
            'https://rpc.ankr.com/eth',
            'https://eth-mainnet.public.blastapi.io',
            'https://ethereum.publicnode.com',
            'https://1rpc.io/eth',
            'https://rpc.mevblocker.io',
            'https://cloudflare-eth.com'
        ]
        
        for endpoint in endpoints:
            try:
                w3 = Web3(Web3.HTTPProvider(endpoint))
                if w3.is_connected():
                    print(f"Connected to {endpoint}")
                    return w3
            except Exception as e:
                print(f"Failed to connect to {endpoint}: {str(e)}")
                continue
                
        return None

    def analyze_controller(self, factory: Contract, controller_address: str) -> Dict[str, Any]:
        """Analyze a single controller's loans and tokens"""
        try:
            print(f"\nAnalyzing controller {controller_address}")
            
            # Get admin contract first (controller is the admin)
            admin = self.queries.get_admin_contract(factory, controller_address)
            if not admin:
                print(f"Could not get admin contract for controller {controller_address}")
                return None
            
            # Get token addresses and info (cached)
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
            loans = []
            user_addresses = []
            index = 0
            consecutive_errors = 0
            max_consecutive_errors = 10  # Stop after 10 consecutive errors
            
            # First collect all user addresses
            while consecutive_errors < max_consecutive_errors:
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
                    if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401', '403']):
                        # Rate limit hit, stop collecting addresses
                        print(f"Rate limit hit, stopping address collection at index {index}")
                        break
                    elif 'execution reverted' in str(e).lower():
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"Stopping after {max_consecutive_errors} consecutive errors")
                            break
                    else:
                        print(f"Error getting loan at index {index}: {str(e)}")
                        break
            
            # Process loans in batches
            batch_size = 5  # Small batch size to avoid rate limits
            for i in range(0, len(user_addresses), batch_size):
                batch = user_addresses[i:i + batch_size]
                batch_loans = self.queries.get_multiple_loan_info(admin, batch)
                loans.extend(batch_loans)
            
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

    def discover_controllers(self, factory_address: str) -> List[str]:
        """Discover all active controllers from factory"""
        print(f"\nDiscovering controllers from factory {factory_address}...")
        
        # Get factory contract
        self.factory = self.queries.get_factory(factory_address)
        if not self.factory:
            raise Exception("Failed to get factory contract")
            
        # Load vault cache
        cache_file = os.path.join(os.path.dirname(__file__), 'cache', 'vault_info_cache.json')
        vault_cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    vault_cache = json.load(f).get('data', {})
            except Exception as e:
                print(f"Error loading vault cache: {str(e)}")
        
        controllers = []
        index = 0
        consecutive_errors = 0
        max_consecutive_errors = 10  # Stop after 10 consecutive errors
        batch_size = 3  # Small batch size
        
        while consecutive_errors < max_consecutive_errors:
            try:
                # Get batch of controllers
                batch_calls = []
                for i in range(batch_size):
                    batch_calls.append(
                        self.factory.functions.controllers(index + i).call
                    )
                
                # Execute batch
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = [executor.submit(call) for call in batch_calls]
                    
                    error_count = 0
                    for i, future in enumerate(futures):
                        try:
                            controller_address = future.result()
                            
                            if not controller_address or controller_address == '0x' + '0' * 40:
                                error_count += 1
                                if error_count >= batch_size:
                                    consecutive_errors += 1
                                    if consecutive_errors >= max_consecutive_errors:
                                        print(f"Stopping after {max_consecutive_errors} consecutive empty batches")
                                        break
                            else:
                                consecutive_errors = 0
                                # Check vault cache first
                                token_info = vault_cache.get(controller_address)
                                if token_info:
                                    print(f"\nFound controller {index + i}: {controller_address}")
                                    print(f"Borrowed Token: {token_info['borrowed_token']['name']} ({token_info['borrowed_token']['address']})")
                                    print(f"Collateral Token: {token_info['collateral_token']['name']} ({token_info['collateral_token']['address']})")
                                    controllers.append(controller_address)
                                else:
                                    # Only validate if not in cache
                                    code = self.queries._retry_with_backoff(self.w3.eth.get_code, controller_address)
                                    if code and code != '0x':
                                        controllers.append(controller_address)
                        except Exception as e:
                            if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401', '403']):
                                # Rate limit hit, try switching RPC endpoint
                                if self.queries._handle_rate_limit():
                                    continue
                                else:
                                    print(f"Rate limit hit, stopping controller discovery at index {index + i}")
                                    consecutive_errors = max_consecutive_errors
                                    break
                            elif 'execution reverted' in str(e).lower():
                                error_count += 1
                                if error_count >= batch_size:
                                    consecutive_errors += 1
                                    if consecutive_errors >= max_consecutive_errors:
                                        print(f"Stopping after {max_consecutive_errors} consecutive error batches")
                                        break
                            else:
                                print(f"Error getting controller at index {index + i}: {str(e)}")
                                continue
                
                index += batch_size
                
            except Exception as e:
                if any(err in str(e).lower() for err in ['429', 'rate', 'limit', 'unauthorized', '401', '403']):
                    # Rate limit hit, try switching RPC endpoint
                    if self.queries._handle_rate_limit():
                        continue
                    else:
                        print(f"Rate limit hit, stopping controller discovery at index {index}")
                        break
                elif 'execution reverted' in str(e).lower():
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"Stopping after {max_consecutive_errors} consecutive error batches")
                        break
                else:
                    print(f"Error discovering controllers: {str(e)}")
                    break
                
        print(f"\nFound {len(controllers)} active controllers")
        return controllers

    def print_controller_summary(self, result: Optional[Dict[str, Any]]):
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

    def print_grand_totals(self):
        """Print grand totals and statistics"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        print(f"\nProcessed {self.stats['total_controllers']} controllers")
        print(f"Found {self.stats['total_loans']} active loans")
        print(f"\nGrand Totals:")
        print(f"Total Borrowed USD: {Fore.RED}{format_usd_amount(self.stats['total_borrowed_usd'])}{Style.RESET_ALL}")
        print(f"Total Collateral USD: {Fore.GREEN}{format_usd_amount(self.stats['total_collateral_usd'])}{Style.RESET_ALL}")
        print(f"\nAnalysis took {duration:.2f} seconds")

    def run(self):
        """Main execution flow"""
        try:
            # Initialize
            self.initialize()
            
            # Start timing
            self.stats['start_time'] = time.time()
            
            # Factory contract address
            factory_address = '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0'
            
            # Discover controllers (not cached)
            controllers = self.discover_controllers(factory_address)
            self.stats['total_controllers'] = len(controllers)
            
            # Process controllers sequentially to avoid rate limits
            for controller in controllers:
                try:
                    result = self.analyze_controller(self.factory, controller)
                    if result:
                        self.print_controller_summary(result)
                        
                        # Update statistics
                        self.stats['total_loans'] += len(result.get('loans', []))
                        self.stats['total_borrowed_usd'] += result.get('total_borrowed_usd', 0)
                        self.stats['total_collateral_usd'] += result.get('total_collateral_usd', 0)
                        
                except Exception as e:
                    print(f"Error processing controller {controller}: {str(e)}")
                    continue
            
            # Record end time
            self.stats['end_time'] = time.time()
            
            # Print final summary
            self.print_grand_totals()
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            raise
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user")
            if self.stats['start_time']:
                self.stats['end_time'] = time.time()
                self.print_grand_totals()

def main():
    """Entry point"""
    analyzer = LoanAnalyzer()
    analyzer.run()

if __name__ == '__main__':
    main()