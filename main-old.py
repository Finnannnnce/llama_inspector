import os
import time
import yaml
import json
import argparse
from decimal import Decimal
from web3 import Web3
from functools import wraps
from src.utils.cache import Cache, ContractCache
from src.contracts.provider_pool import Web3ProviderPool

# Initialize cache
cache = ContractCache('cache')

# Factory contract address
FACTORY_ADDRESS = Web3.to_checksum_address("0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0")

def get_contract_abi(name, verbose=False, is_interface=True):
    """Load contract ABI from file"""
    try:
        # Interface ABIs are in contracts/interfaces, others in contracts
        if is_interface:
            filepath = os.path.join(os.getcwd(), 'contracts', 'interfaces', f'{name}.json')
        else:
            filepath = os.path.join(os.getcwd(), 'contracts', f'{name}.json')
            
        if verbose:
            print(f"Loading ABI from: {filepath}")
        with open(filepath, 'r') as f:
            data = json.load(f)['abi']
            return data['abi']
    except Exception as e:
        if verbose:
            print(f"Error loading ABI for {name}: {str(e)}")
        return None

def get_contract_call_result(contract_function, cache_key=None, verbose=False):
    """Call contract function with caching"""
    if cache_key:
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
    
    # Make the call
    try:
        result = contract_function.call()
        
        # Cache successful result
        if cache_key and result is not None:
            cache.set(cache_key, result)
        
        return result
    except Exception as e:
        if verbose:
            print(f"Error calling contract: {str(e)}")
        return None

def retry_forever(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {str(e)}")
                print("Retrying...")
                time.sleep(1)
    return wrapper

def format_token(amount, token_name=None):
    """Format token amount with appropriate precision"""
    if amount == 0:
        return "0.00"
    abs_amount = abs(float(amount))
    if abs_amount < 0.01:
        return f"{float(amount):.6f}"
    elif abs_amount < 1:
        return f"{float(amount):.4f}"
    else:
        return f"{float(amount):.2f}"

def format_usd(amount):
    """Format USD amount with $ symbol and commas"""
    return f"${amount:,.2f}"

def get_token_info(token_address, w3, erc20_abi, config, verbose=False):
    """Get token name, decimals, and price"""
    try:
        # Convert address to checksum format
        token_address = Web3.to_checksum_address(token_address)
        
        # Create token contract
        token = w3.eth.contract(address=token_address, abi=erc20_abi)
        
        # Get token name and decimals
        name = get_contract_call_result(
            token.functions.name(),
            cache_key=f"token_name_{token_address}",
            verbose=verbose
        )
        decimals = get_contract_call_result(
            token.functions.decimals(),
            cache_key=f"token_decimals_{token_address}",
            verbose=verbose
        )
        
        # Get price from config
        price = None
        if token_address.lower() in config.get('stable_tokens', {}):
            price = config['stable_tokens'][token_address.lower()]
        else:
            for symbol, addr in config.get('tokens', {}).items():
                if addr.lower() == token_address.lower() and symbol in config.get('default_prices', {}):
                    price = config['default_prices'][symbol]
                    break
        
        return name, decimals, price
        
    except Exception as e:
        if verbose:
            print(f"Error getting token info: {str(e)}")
        return None, None, None

def verify_vault(factory_contract, vault_address, controller_address, verbose=False):
    """Verify vault and controller addresses through factory contract"""
    try:
        # Get total number of markets
        market_count = get_contract_call_result(
            factory_contract.functions.market_count(),
            cache_key="market_count",
            verbose=verbose
        )
        
        if not market_count:
            if verbose:
                print("Failed to get market count")
            return False
            
        # Check each market
        for i in range(market_count):
            vault = get_contract_call_result(
                factory_contract.functions.vaults(i),
                cache_key=f"vault_{i}",
                verbose=verbose
            )
            if vault and vault.lower() == vault_address.lower():
                controller = get_contract_call_result(
                    factory_contract.functions.controllers(i),
                    cache_key=f"controller_{i}",
                    verbose=verbose
                )
                if controller and controller.lower() == controller_address.lower():
                    if verbose:
                        print(f"Verified vault {vault_address} and controller {controller_address}")
                    return True
                    
        if verbose:
            print(f"Could not verify vault {vault_address} and controller {controller_address}")
        return False
        
    except Exception as e:
        if verbose:
            print(f"Error verifying vault: {str(e)}")
        return False

def get_active_loans(controller_contract, borrowed_decimals, borrowed_price, verbose=False):
    """Get all active loans from a controller"""
    try:
        active_loans = []
        loan_index = 0
        zero_address = "0x0000000000000000000000000000000000000000"
        
        while True:
            try:
                # Get loan address
                loan_address = get_contract_call_result(
                    controller_contract.functions.loans(loan_index),
                    cache_key=f"loan_{controller_contract.address}_{loan_index}",
                    verbose=verbose
                )
                
                # Stop if we get zero address or error
                if not loan_address or loan_address == zero_address:
                    break
                    
                # Check if loan exists (is active)
                loan_exists = get_contract_call_result(
                    controller_contract.functions.loan_exists(loan_address),
                    cache_key=f"loan_exists_{loan_address}",
                    verbose=verbose
                )
                
                if loan_exists:
                    # Get debt amount
                    debt = get_contract_call_result(
                        controller_contract.functions.debt(loan_address),
                        cache_key=f"debt_{loan_address}",
                        verbose=verbose
                    )
                    
                    if debt:
                        debt_amount = Decimal(debt) / Decimal(10**borrowed_decimals)
                        debt_value = debt_amount * Decimal(str(borrowed_price or 0))
                        
                        active_loans.append({
                            'address': loan_address,
                            'debt_amount': debt_amount,
                            'debt_value': debt_value
                        })
                
                loan_index += 1
                
            except Exception as e:
                if verbose:
                    print(f"Error getting loan {loan_index}: {str(e)}")
                break
                
        return active_loans
        
    except Exception as e:
        if verbose:
            print(f"Error getting active loans: {str(e)}")
        return []

@retry_forever
def get_vault_info(vault_name, vault_data, w3, factory_contract, vault_abi, controller_abi, erc20_abi, user_address, config, verbose=False):
    """Get information for a single vault with caching"""
    try:
        print(f"Processing {vault_name}...", flush=True)
        
        # Create cache directory if it doesn't exist
        os.makedirs('cache', exist_ok=True)
        
        # Convert addresses to checksum format
        vault_address = Web3.to_checksum_address(vault_data['address'])
        controller_address = Web3.to_checksum_address(vault_data['controller'])
        collateral_token = Web3.to_checksum_address(vault_data['collateral_token'])
        borrowed_token = Web3.to_checksum_address(vault_data['borrowed_token'])
        
        # Verify vault through factory
        print("  - Verifying vault...", flush=True)
        if not verify_vault(factory_contract, vault_address, controller_address, verbose):
            print("  - Failed to verify vault", flush=True)
            return None
        
        # Create controller contract
        controller_contract = w3.eth.contract(address=controller_address, abi=controller_abi)
        print("  - Created controller contract", flush=True)
        
        # Get token information
        print("  - Getting collateral token info...", flush=True)
        collateral_name, collateral_decimals, collateral_price = get_token_info(
            collateral_token, w3, erc20_abi, config, verbose
        )
        
        print("  - Getting borrowed token info...", flush=True)
        borrowed_name, borrowed_decimals, borrowed_price = get_token_info(
            borrowed_token, w3, erc20_abi, config, verbose
        )
        
        # Get all active loans
        print("  - Getting active loans...", flush=True)
        active_loans = get_active_loans(
            controller_contract,
            borrowed_decimals,
            borrowed_price,
            verbose
        )
        
        if active_loans:
            print(f"  - Found {len(active_loans)} active loans")
        else:
            print("  - No active loans found")
        
        # Check user position if address provided
        user_position = None
        if user_address:
            print("  - Checking user position...", flush=True)
            # Check if user has any active loans
            for loan in active_loans:
                if loan['address'].lower() == user_address.lower():
                    user_position = loan
                    break
        
        print("  - Vault processing complete", flush=True)
        
        return {
            'name': vault_name,
            'collateral_name': collateral_name,
            'borrowed_name': borrowed_name,
            'active_loans': active_loans,
            'user_position': user_position
        }
    except Exception as e:
        print(f"Error processing vault {vault_name}: {str(e)}", flush=True)
        return None

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Query vault information')
        parser.add_argument('-a', '--address', help='Optional: Ethereum address to query for positions', default=None)
        parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
        args = parser.parse_args()
        
        print("Starting vault query...", flush=True)
        
        # Load config first
        config_file = os.path.join(os.getcwd(), 'config.yaml')
        print(f"Loading config from: {config_file}", flush=True)
        
        if not os.path.exists(config_file):
            print(f"Error: Config file not found at {config_file}")
            return
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print("Config loaded", flush=True)
        
        # Initialize provider pool
        provider_pool = Web3ProviderPool(config['rpc_nodes'], args.verbose)
        print("Provider pool initialized", flush=True)
        
        # Initialize Web3 with first provider
        provider_info = provider_pool.get_provider()
        if not provider_info:
            print("Error: No available providers")
            return
        w3 = provider_info[0]  # Get the Web3 instance from the tuple
        print("Web3 initialized", flush=True)
        
        # Load ABIs
        factory_abi = get_contract_abi('factory', args.verbose, is_interface=False)
        vault_abi = get_contract_abi('vault', args.verbose)
        controller_abi = get_contract_abi('controller', args.verbose)
        erc20_abi = get_contract_abi('erc20', args.verbose)
        
        if not factory_abi or not vault_abi or not controller_abi or not erc20_abi:
            print("Failed to load ABIs")
            return
        
        print("ABIs loaded", flush=True)
        
        # Create factory contract
        factory_contract = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
        print("Factory contract initialized", flush=True)
        
        # Process each vault
        user_positions = []
        all_borrowers = set()  # Track unique borrowers across all vaults
        
        for vault_name, vault_data in config['vaults'].items():
            if vault_name != 'base_contract':
                try:
                    info = get_vault_info(
                        vault_name, vault_data, w3, factory_contract, vault_abi, 
                        controller_abi, erc20_abi, args.address, config, args.verbose
                    )
                    
                    if info:
                        # Print active loans for this vault
                        if info['active_loans']:
                            print(f"\nActive loans in {info['name']}:")
                            for loan in info['active_loans']:
                                print(f"\n  Address: {loan['address']}")
                                print(f"  Debt: {format_token(loan['debt_amount'])} {info['borrowed_name']} ({format_usd(float(loan['debt_value']))})")
                                all_borrowers.add(loan['address'])
                        
                        # Track user position if found
                        if info['user_position']:
                            user_positions.append({
                                'name': info['name'],
                                'collateral_name': info['collateral_name'],
                                'borrowed_name': info['borrowed_name'],
                                'position': info['user_position']
                            })
                    
                    # Add delay between vault processing
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error processing vault {vault_name}: {str(e)}")
                    # Continue with next vault even if one fails
                    continue
        
        # Print summary
        print(f"\nSummary:")
        print(f"Total Unique Borrowers Across All Vaults: {len(all_borrowers)}")
        
        # Print user positions if found
        if args.address:
            if user_positions:
                print(f"\nPositions for {args.address}:")
                for pos in user_positions:
                    print(f"\n{pos['name']}:")
                    print(f"  Debt: {format_token(pos['position']['debt_amount'])} {pos['borrowed_name']} ({format_usd(float(pos['position']['debt_value']))})")
            else:
                print(f"\nNo positions found for {args.address}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            print(traceback.format_exc())

if __name__ == '__main__':
    main()
