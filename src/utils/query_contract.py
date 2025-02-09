from ape import Contract, networks
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# USDT Contract address on Ethereum mainnet
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USER_ADDRESS = os.getenv("USER_ADDRESS")

def main():
    # Connect to Ethereum mainnet using node provider
    with networks.ethereum.mainnet.use_provider("node") as provider:
        # Get the USDT contract instance
        usdt_contract = Contract(USDT_ADDRESS)
        
        try:
            # Query basic information about the token
            name = usdt_contract.name()
            symbol = usdt_contract.symbol()
            decimals = usdt_contract.decimals()
            total_supply = usdt_contract.totalSupply() / (10 ** decimals)
            
            print(f"Contract Information:")
            print(f"Name: {name}")
            print(f"Symbol: {symbol}")
            print(f"Decimals: {decimals}")
            print(f"Total Supply: {total_supply:,.2f} {symbol}")
            
            # Query user's address balance
            balance = usdt_contract.balanceOf(USER_ADDRESS) / (10 ** decimals)
            print(f"\nBalance of {USER_ADDRESS}:")
            print(f"{balance:,.2f} {symbol}")
            
        except Exception as e:
            print(f"Error querying contract: {e}")

if __name__ == "__main__":
    main()