import asyncio
import json
import aiohttp
from web3 import Web3

async def fetch_abi():
    """Fetch contract ABIs from Etherscan"""
    
    # Etherscan API endpoint
    api_url = "https://api.etherscan.io/api"
    
    # Contracts to verify
    contracts = {
        'Controller': '0x413FD2511BAD510947a91f5c6c79EBD8138C29Fc',
        'CRV Vault': '0xCeA18a8752bb7e7817F9AE7565328FE415C0f2cA',
        'WETH Vault': '0x5AE28c9197a4a6570216fC7e53E7e0221D7A0FEF',
        'wstETH Vault': '0x8cf1DE26729cfB7137AF1A6B2a665e099EC319b5',
        'tBTC Vault': '0xb2b23C87a4B6d1b03Ba603F7C3EB9A81fDC0AAC9'
    }
    
    async with aiohttp.ClientSession() as session:
        for name, address in contracts.items():
            print(f"\nFetching ABI for {name} at {address}")
            
            # Get contract bytecode first
            w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
            code = w3.eth.get_code(address)
            if code == b'':
                print("No contract code found at this address")
                continue
            
            print("Contract code found")
            
            # Get contract ABI from Etherscan
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': address,
                'format': 'raw'
            }
            
            try:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == '1' and data['message'] == 'OK':
                            abi = data['result']
                            
                            # Save ABI to file
                            filename = f"contracts/interfaces/{name.lower().replace(' ', '_')}.json"
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
            
            # Add delay between requests
            await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(fetch_abi())