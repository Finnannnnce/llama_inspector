import os
import json
from web3 import Web3
from dotenv import load_dotenv
import yaml
from decimal import Decimal
from pathlib import Path

# Load environment variables
load_dotenv()

import time

# Cache settings
VAULT_CACHE_FILE = Path(__file__).parent / '.vault_cache.json'
VAULT_CACHE_DURATION = 4 * 60 * 60  # 4 hours in seconds

# Factory contract address
FACTORY_ADDRESS = Web3.to_checksum_address("0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0")  # crvUSD factory

def load_vault_cache():
    """Load cached vault data"""
    if VAULT_CACHE_FILE.exists():
        try:
            with open(VAULT_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                cache_age = time.time() - cache_data.get('timestamp', 0)
                time_left = VAULT_CACHE_DURATION - cache_age
                if cache_age < VAULT_CACHE_DURATION:
                    print(f"Using cached vault data (expires in {time_left/60:.1f} minutes)")
                    return cache_data.get('data')
                else:
                    print(f"Cache expired {-time_left/60:.1f} minutes ago")
        except Exception as e:
            print(f"Error loading vault cache: {str(e)}")
    return None

def save_vault_cache(data):
    """Save vault data to cache"""
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        with open(VAULT_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Error saving vault cache: {str(e)}")
RPC_URLS = [
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum.publicnode.com",
    "https://1rpc.io/eth",
    "https://eth.api.onfinality.io/public",
    "https://eth.rpc.blxrbdn.com",
    "https://rpc.payload.de",
    "https://virginia.rpc.blxrbdn.com",
    "https://uk.rpc.blxrbdn.com",
    "https://singapore.rpc.blxrbdn.com"
]

def get_working_web3():
    """Try different RPC URLs until we find one that works"""
    while True:
        for url in RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(url))
                if w3.is_connected():
                    print(f"Connected to {url}")
                    return w3, url
            except Exception as e:
                print(f"Failed to connect to {url}: {str(e)}")
                continue
        print("All RPC endpoints failed, retrying after 1 second...")
        time.sleep(1)

def handle_rate_limit(current_url):
    """Switch to a different RPC URL when rate limited"""
    print(f"Rate limited on {current_url}, switching RPC...")
    time.sleep(1)  # Wait before trying new URL
    w3, url = get_working_web3()
    while url == current_url:  # Keep trying until we get a different URL
        w3, url = get_working_web3()
    return w3, url

def get_token_name(w3, token_address, current_url):
    """Get token name and symbol from contract"""
    try:
        # Load ERC20 ABI
        with open('contracts/interfaces/erc20.json', 'r') as f:
            erc20_abi = json.load(f)['abi']
            
        token = w3.eth.contract(address=token_address, abi=erc20_abi)
        
        while True:
            try:
                name = token.functions.name().call()
                time.sleep(0.1)  # Small delay between calls
                symbol = token.functions.symbol().call()
                return f"{name} ({symbol})"
            except Exception as e:
                if "429" in str(e):
                    w3, current_url = handle_rate_limit(current_url)
                    token = w3.eth.contract(address=token_address, abi=erc20_abi)
                else:
                    raise
    except Exception as e:
        print(f"Error getting token name for {token_address}: {str(e)}")
        return f"Unknown ({token_address})"

def clear_cache():
    """Clear all cache files"""
    try:
        if VAULT_CACHE_FILE.exists():
            VAULT_CACHE_FILE.unlink()
            print("Cleared vault cache")
        cache_file = Path(__file__).parent / '.cache.json'
        if cache_file.exists():
            cache_file.unlink()
            print("Cleared network call cache")
    except Exception as e:
        print(f"Error clearing cache: {str(e)}")

def generate_vault_config(clear_cache_first=False):
    """Generate llama_vault_contracts.yaml by querying the factory contract"""
    
    if clear_cache_first:
        clear_cache()
    
    # Check cache first
    cached_data = load_vault_cache()
    if cached_data:
        # Write cached data to YAML file
        with open('llama_vault_contracts.yaml', 'w') as f:
            yaml.dump(cached_data, f, default_flow_style=False, sort_keys=False)
        print("Generated llama_vault_contracts.yaml from cache")
        return
    
    try:
        # Initialize web3 with a working RPC
        w3, current_url = get_working_web3()
        
        # Load factory ABI
        with open('contracts/factory.json', 'r') as f:
            factory_abi = json.load(f)['abi']
            
        # Create factory contract instance
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
        
        # Get total number of markets
        while True:
            try:
                market_count = factory.functions.market_count().call()
                break
            except Exception as e:
                if "429" in str(e):
                    w3, current_url = handle_rate_limit(current_url)
                    factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
                else:
                    raise
        
        print(f"Found {market_count} markets")
        
        # Initialize config and tracking sets
        config = {
            'base_contract': FACTORY_ADDRESS
        }
        seen_addresses = set()
        name_counts = {}
        
        # Query each market
        for i in range(market_count):
            while True:
                try:
                    # Get vault and token addresses and convert to checksum
                    vault_address = Web3.to_checksum_address(factory.functions.vaults(i).call())
                    
                    # Check for duplicate vault address
                    if vault_address in seen_addresses:
                        print(f"Warning: Duplicate vault address found: {vault_address}")
                        break
                    seen_addresses.add(vault_address)
                    
                    time.sleep(0.1)  # Small delay between calls
                    controller_address = Web3.to_checksum_address(factory.functions.controllers(i).call())
                    time.sleep(0.1)
                    borrowed_token = Web3.to_checksum_address(factory.functions.borrowed_tokens(i).call())
                    time.sleep(0.1)
                    collateral_token = Web3.to_checksum_address(factory.functions.collateral_tokens(i).call())
                    time.sleep(0.1)
                    
                    # Get token name to use as key
                    base_name = get_token_name(w3, collateral_token, current_url)
                    
                    # Handle duplicate names by appending a counter
                    if base_name in config:
                        name_counts[base_name] = name_counts.get(base_name, 1) + 1
                        token_name = f"{base_name} #{name_counts[base_name]}"
                    else:
                        token_name = base_name
                        
                    print(f"Processing market {i}: {token_name}")
                    
                    # Add to config
                    config[token_name] = {
                        'address': vault_address,
                        'controller': controller_address,
                        'borrowed_token': borrowed_token,
                        'collateral_token': collateral_token
                    }
                    break
                    
                except Exception as e:
                    if "429" in str(e):
                        w3, current_url = handle_rate_limit(current_url)
                        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=factory_abi)
                    else:
                        print(f"Error processing market {i}: {str(e)}")
                        break
        
        # Save to cache
        save_vault_cache(config)
        
        # Write to YAML file
        with open('llama_vault_contracts.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print("Generated llama_vault_contracts.yaml")
        
    except Exception as e:
        print(f"Error generating vault config: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate vault configuration')
    parser.add_argument('--clear-cache', action='store_true', help='Clear cache before generating config')
    args = parser.parse_args()
    
    generate_vault_config(clear_cache_first=args.clear_cache)