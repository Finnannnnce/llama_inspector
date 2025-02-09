import os
import json
import time
from web3 import Web3
from src.utils.contract_queries import ContractQueries

def main():
    """Generate vault configuration cache"""
    print("Generating vault configuration cache...")
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
    if not w3.is_connected():
        raise Exception("Failed to connect to Ethereum network")
    
    # Initialize utilities
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    queries = ContractQueries(w3, cache_dir)
    
    # Factory contract address
    factory_address = '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0'
    
    # Get factory contract
    factory = queries.get_factory(factory_address)
    if not factory:
        raise Exception("Failed to get factory contract")
    
    # Discover and cache all controllers
    index = 0
    consecutive_none = 0
    vault_info = {}
    
    while consecutive_none < 3:  # Stop after 3 consecutive empty responses
        try:
            controller_address = queries._retry_with_backoff(
                factory.functions.controllers(index).call
            )
            
            if not controller_address or controller_address == '0x' + '0' * 40:
                consecutive_none += 1
            else:
                consecutive_none = 0
                
                # Get controller contract
                controller = queries.get_admin_contract(factory, controller_address)
                if controller:
                    # Get token info
                    token_info = queries.get_controller_tokens(controller, controller_address)
                    if token_info:
                        print(f"\nCached controller {index}: {controller_address}")
                        print(f"Borrowed Token: {token_info['borrowed_token']['name']} ({token_info['borrowed_token']['address']})")
                        print(f"Collateral Token: {token_info['collateral_token']['name']} ({token_info['collateral_token']['address']})")
                        
                        # Store in vault info
                        vault_info[controller_address] = token_info
            
            index += 1
            time.sleep(2)  # Rate limit delay
            
        except Exception as e:
            print(f"Error discovering controller at index {index}: {str(e)}")
            break
    
    # Save vault info cache
    cache_file = os.path.join(cache_dir, 'vault_info_cache.json')
    cache_data = {
        'timestamp': time.time(),
        'data': vault_info
    }
    
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print(f"\nCached {len(vault_info)} controllers")

if __name__ == '__main__':
    main()