import asyncio
import json
import os
import aiohttp
import ssl
import yaml
from web3 import Web3

async def fetch_abi():
    """Fetch contract ABIs from Etherscan"""
    
    # Load configuration from config.yaml
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            api_key = config.get('api_keys', {}).get('etherscan')
            if not api_key:
                raise ValueError("Etherscan API key not found in config.yaml")
    except Exception as e:
        raise ValueError(f"Failed to load config.yaml: {str(e)}")
    
    # Etherscan API endpoint
    api_url = "https://api.etherscan.io/api"
    
    # Curve factory address
    factory_address = Web3.to_checksum_address('0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0')
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    
    # Create SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"\nFetching ABI for Curve Factory at {factory_address}")
        
        # Get contract bytecode first
        code = w3.eth.get_code(factory_address)
        if code == b'':
            print("No contract code found at this address")
            return
        
        print("Contract code found")
        
        # Get contract ABI from Etherscan
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': factory_address,
            'apikey': api_key
        }
        
        try:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['message'] == 'OK':
                        abi = data['result']
                        
                        # Save ABI to file
                        filename = f"contracts/interfaces/factory.json"
                        with open(filename, 'w') as f:
                            json.dump({'abi': json.loads(abi)}, f, indent=2)
                        print(f"Saved ABI to {filename}")
                        
                        # Print first few functions
                        abi_json = json.loads(abi)
                        functions = [item for item in abi_json if item.get('type') == 'function']
                        print("\nFirst 5 functions:")
                        for func in functions[:5]:
                            print(f"- {func.get('name', 'unnamed')}")
                    else:
                        print(f"Error: {data.get('message', 'Unknown error')}")
                else:
                    print(f"Error: HTTP {response.status}")
        
        except Exception as e:
            print(f"Error fetching ABI: {str(e)}")

if __name__ == '__main__':
    asyncio.run(fetch_abi())