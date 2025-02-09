from web3 import Web3
from eth_utils.currency import from_wei
import os
import yaml
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
import argparse
import time
import json

# Load environment variables
load_dotenv()

# Get environment variables
USER_ADDRESS = os.getenv("USER_ADDRESS")
ARCHIVE_RPC_URL = os.getenv("ARCHIVE_RPC_URL")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ARCHIVE_RPC_URL))

# Llama Vault ABI - more specific to these contracts
VAULT_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def load_vault_contracts():
    with open('llama_vault_contracts.yaml', 'r') as file:
        return yaml.safe_load(file)

def format_usd(amount):
    """Format amount in USD with commas and 2 decimal places"""
    return f"${amount:,.2f}"

def check_contract_deployed(address, block_number):
    """Check if contract was deployed at the given block number"""
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(address), block_identifier=block_number)
        return len(code) > 0
    except Exception as e:
        print(f"Error checking contract deployment: {str(e)}")
        return False

def get_block_by_date(target_date):
    """Find the closest block number to a given date"""
    print(f"Finding block number for date {target_date}...")
    
    # Get current block and timestamp
    current_block = w3.eth.get_block('latest')
    current_timestamp = current_block.timestamp
    current_block_number = current_block.number
    
    # Convert target date to timestamp
    target_timestamp = int(datetime.strptime(target_date, "%Y-%m-%d").timestamp())
    
    # Estimate blocks per day (assuming ~12 seconds per block)
    BLOCKS_PER_DAY = 7200
    
    # Estimate initial block number
    days_diff = (current_timestamp - target_timestamp) / (24 * 3600)
    estimated_block = current_block_number - int(days_diff * BLOCKS_PER_DAY)
    
    print(f"Estimated initial block: {estimated_block}")
    
    # Binary search to find the closest block
    left = max(1, estimated_block - BLOCKS_PER_DAY)
    right = estimated_block + BLOCKS_PER_DAY
    
    while left <= right:
        mid = (left + right) // 2
        try:
            block = w3.eth.get_block(mid)
            if block.timestamp == target_timestamp:
                return mid
            elif block.timestamp < target_timestamp:
                left = mid + 1
            else:
                right = mid - 1
            time.sleep(0.1)  # Add delay to avoid rate limiting
        except Exception as e:
            print(f"Error getting block {mid}: {str(e)}")
            time.sleep(1)  # Longer delay on error
            continue
    
    return right

def query_vault_info(vault_name, vault_data, block_number=None):
    """Query vault information at a specific block number"""
    print(f"\n=== {vault_name} Vault Information ===")
    print(f"Vault Address: {vault_data['address']}")
    
    try:
        # Check if contract was deployed at this block
        if block_number and not check_contract_deployed(vault_data['address'], block_number):
            print(f"Contract was not deployed at block {block_number}")
            return 0
        
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(vault_data['address']),
            abi=VAULT_ABI
        )
        
        try:
            # Add delay between requests
            time.sleep(0.2)
            
            block_identifier = block_number if block_number else 'latest'
            print(f"Querying block {block_identifier}...")
            
            # Get user's balance in Wei
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(USER_ADDRESS)
            ).call(block_identifier=block_identifier)
            
            print(f"Raw balance in Wei: {balance_wei}")
            
            # Convert Wei to USD directly
            eth_balance = Decimal(balance_wei) / Decimal(10**18)
            
            # Get price feed (assuming $1 for stablecoins, rough estimation for others)
            price_usd = 1.0  # Default to $1
            if vault_name == "CRV":
                price_usd = 0.50  # Example CRV price
            elif vault_name in ["WBTC", "tBTC"]:
                price_usd = 43000.0  # Example BTC price
            elif vault_name in ["WETH", "pufETH", "wstETH"]:
                price_usd = 2400.0  # Example ETH price
            elif vault_name == "UwU":
                price_usd = 0.01  # Example UwU price
            
            # Calculate USD value
            usd_value = float(eth_balance) * price_usd
            
            print(f"Your Balance: {float(eth_balance):.6f} {vault_name}")
            print(f"USD Value: {format_usd(usd_value)}")
            
            return usd_value
            
        except Exception as e:
            print(f"Error getting balance: {str(e)}")
            return 0
            
    except Exception as e:
        print(f"Error querying vault: {str(e)}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Query vault balances at a specific block or date')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--block', type=int, help='Block number to query')
    group.add_argument('--date', type=str, help='Date to query (YYYY-MM-DD format)')
    args = parser.parse_args()

    # Check Web3 connection
    if not w3.is_connected():
        print("Error: Could not connect to Ethereum node")
        return

    print(f"Connected to Ethereum node: {ARCHIVE_RPC_URL}")
    print(f"Current block number: {w3.eth.block_number}")

    block_number = None
    if args.block:
        block_number = args.block
        print(f"\nQuerying balances at block {block_number}")
    elif args.date:
        block_number = get_block_by_date(args.date)
        print(f"\nQuerying balances at date {args.date} (Block {block_number})")
    
    print(f"Address: {USER_ADDRESS}")
    vaults = load_vault_contracts()
    
    total_usd_value = 0
    
    for vault_name, vault_data in vaults.items():
        try:
            usd_value = query_vault_info(vault_name, vault_data, block_number)
            total_usd_value += usd_value
            time.sleep(0.2)  # Add delay between vault queries
        except Exception as e:
            print(f"Error processing {vault_name}: {str(e)}")
            continue
    
    print("\n=== Summary ===")
    print(f"Total Value Across All Vaults: {format_usd(total_usd_value)}")

if __name__ == "__main__":
    main()