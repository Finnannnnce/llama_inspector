import asyncio
import json
import logging
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .utils.cache import Cache, ContractCache
from .utils.rate_limiter import RateLimiter
from .contracts.provider_pool import Web3ProviderPool
from .contracts.helpers import ContractHelper
from .contracts.vault import VaultManager
from .price_feeds.aggregator import PriceFeedAggregator

async def main():
    """Main entry point"""
    
    # Enable verbose logging if -v flag is passed
    verbose = '-v' in sys.argv
    if '-vv' in sys.argv:
        verbose = True
        print("Debug mode enabled - maximum verbosity")
    
    print("Starting vault query...")
    
    # Load config
    config_path = os.path.join(os.getcwd(), 'config.yaml')
    print(f"Loading config from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Config loaded")
    if verbose:
        print("Config contents:")
        print(yaml.dump(config))
    
    # Initialize caches
    print("Initializing caches...")
    cache_dir = os.path.join(os.getcwd(), 'cache')
    
    # Create cache instances
    contracts_cache = ContractCache(cache_dir)
    prices_cache = Cache(cache_dir, 'prices_cache.json')
    token_info_cache = Cache(cache_dir, 'token_info_cache.json')
    loan_info_cache = Cache(cache_dir, 'loan_info_cache.json')
    print("Caches initialized")
    
    # Initialize rate limiter
    rpc_rate_limit = config.get('rate_limits', {}).get('rpc_calls_per_second', 2)
    rate_limiter = RateLimiter(rpc_rate_limit)
    print(f"Rate limiter initialized with {rpc_rate_limit} requests/second")
    
    # Initialize provider pool
    provider_pool = Web3ProviderPool(config.get('rpc_nodes', []), verbose)
    print("Components initialized")
    
    # Initialize contract helper
    contract_helper = ContractHelper(
        provider_pool,
        contracts_cache,
        rate_limiter,
        verbose
    )
    
    # Initialize price feed
    price_feed = PriceFeedAggregator(
        prices_cache,
        config.get('default_prices', {})
    )
    
    # Initialize vault manager
    vault_manager = VaultManager(
        contract_helper,
        price_feed,
        loan_info_cache,
        verbose
    )
    
    print("Starting vault processing...")
    
    # Load contract ABIs
    print("Loading ABIs...")
    vault_abi = await contract_helper.get_contract_abi('vault')
    controller_abi = await contract_helper.get_contract_abi('controller')
    erc20_abi = await contract_helper.get_contract_abi('erc20')
    
    if not vault_abi or not controller_abi or not erc20_abi:
        print("Failed to load required ABIs")
        return
    print("ABIs loaded")
    
    print("Starting vault processing...")
    
    # Process each vault
    vaults = config.get('vaults', {})
    print(f"Creating task for vault: {', '.join(vaults.keys())}")
    
    tasks = []
    for name, info in vaults.items():
        task = asyncio.create_task(
            vault_manager.get_vault_info(
                name,
                info['address'],
                info['collateral_token'],
                info['borrowed_token'],
                vault_abi,
                controller_abi,
                erc20_abi
            )
        )
        tasks.append(task)
    
    print(f"Created {len(tasks)} vault tasks")
    
    # Wait for all tasks to complete
    results = []
    for task in tasks:
        try:
            result = await task
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error processing vault: {str(e)}")
    
    print(f"Completed processing {len(results)} vaults")
    
    # Print results
    print("\nProcessing complete. Printing results...\n")
    
    total_loans = 0
    total_providers = 0
    
    for vault in results:
        if vault.loans:
            print(f"\nActive loans in {vault.name}:\n")
            for loan in vault.loans:
                print(f"  Address: {loan['address']}")
                print(f"  Collateral: {loan['collateral_amount']} {vault.collateral_name} (${float(loan['collateral_value']):.2f})")
                print(f"  Debt: {loan['debt_amount']} {vault.borrowed_name} (${float(loan['debt_value']):.2f})")
                print()
            
            print(f"Liquidity providers in {vault.name}:")
            for provider in vault.liquidity_providers:
                print(f"  {provider}")
            print()
            
            total_loans += len(vault.loans)
            total_providers += len(vault.liquidity_providers)
    
    print("Summary:")
    print(f"Total Active Loans Across All Vaults: {total_loans}")
    print(f"Total Unique Liquidity Providers: {total_providers}")
    
    print("\nExecution complete.")

if __name__ == '__main__':
    try:
        import yaml
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        if '-v' in sys.argv or '-vv' in sys.argv:
            import traceback
            print("\nTraceback:")
            traceback.print_exc()