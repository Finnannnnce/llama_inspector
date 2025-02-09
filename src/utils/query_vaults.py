import asyncio
import json
import yaml
from web3 import Web3
from web3.exceptions import ContractLogicError

async def query_vaults():
    """Query vaults using active_loans functions"""
    
    # Connect to Ethereum node
    w3 = Web3(Web3.HTTPProvider('https://ethereum.publicnode.com'))
    
    if not w3.is_connected():
        print("Failed to connect")
        return
    
    print("Connected successfully")
    
    # Load Vault ABI
    with open('contracts/interfaces/vault.json', 'r') as f:
        vault_abi = json.load(f)['abi']
    
    # Known vault addresses and tokens
    vault_info = {
        'Curve DAO Token (CRV)': {
            'address': '0xCeA18a8752bb7e7817F9AE7565328FE415C0f2cA',
            'collateral': '0xD533a949740bb3306d119CC777fa900bA034cd52',
            'borrowed': '0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E'
        },
        'Wrapped Ether (WETH)': {
            'address': '0x5AE28c9197a4a6570216fC7e53E7e0221D7A0FEF',
            'collateral': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'borrowed': '0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E'
        },
        'Wrapped liquid staked Ether 2.0 (wstETH)': {
            'address': '0x8cf1DE26729cfB7137AF1A6B2a665e099EC319b5',
            'collateral': '0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0',
            'borrowed': '0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E'
        },
        'tBTC v2 (tBTC)': {
            'address': '0xb2b23C87a4B6d1b03Ba603F7C3EB9A81fDC0AAC9',
            'collateral': '0x18084fbA666a33d37592fA2633fD49a74DD93a88',
            'borrowed': '0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E'
        }
    }
    
    # Get active vaults
    active_vaults = {}
    
    # Query each vault
    for name, info in vault_info.items():
        print(f"\nQuerying vault: {name}")
        try:
            # Create vault contract instance
            vault = w3.eth.contract(address=info['address'], abi=vault_abi)
            
            # Verify vault tokens
            try:
                collateral = vault.functions.collateral_token().call()
                borrowed = vault.functions.borrowed_token().call()
                print(f"Collateral token: {collateral}")
                print(f"Borrowed token: {borrowed}")
                
                if collateral.lower() != info['collateral'].lower() or borrowed.lower() != info['borrowed'].lower():
                    print(f"Token mismatch for {name}")
                    continue
            except Exception as e:
                print(f"Error getting token info: {str(e)}")
                continue
            
            # Get number of active loans
            try:
                n_loans = vault.functions.active_loans().call()
                print(f"Number of active loans: {n_loans}")
                
                if n_loans > 0:
                    # Get active loan addresses
                    loans = []
                    for i in range(n_loans):
                        try:
                            loan_address = vault.functions.active_loans_list(i).call()
                            print(f"Found loan at index {i}: {loan_address}")
                            
                            # Verify loan exists and get details
                            if vault.functions.loan_exists(loan_address).call():
                                print(f"Loan {loan_address} exists, getting details...")
                                
                                try:
                                    debt = vault.functions.loan_debt(loan_address).call()
                                    collateral_amount = vault.functions.loan_collateral(loan_address).call()
                                    
                                    if debt > 0:
                                        loans.append({
                                            'address': loan_address,
                                            'debt': debt,
                                            'collateral': collateral_amount
                                        })
                                        print(f"Added active loan with debt: {debt}, collateral: {collateral_amount}")
                                except Exception as e:
                                    print(f"Error getting loan details: {str(e)}")
                        except Exception as e:
                            print(f"Error getting loan at index {i}: {str(e)}")
                    
                    if loans:
                        active_vaults[name] = {
                            'address': info['address'],
                            'collateral_token': collateral,
                            'borrowed_token': borrowed,
                            'active_loans': len(loans),
                            'loans': loans
                        }
                        print(f"Found {len(loans)} active loans")
                    else:
                        print("No active loans found")
                else:
                    print("No active loans")
            except Exception as e:
                print(f"Error getting active loans: {str(e)}")
        
        except Exception as e:
            print(f"Error querying vault: {str(e)}")
    
    if active_vaults:
        # Load existing config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Update vaults section
        config['vaults'] = active_vaults
        
        # Save updated config
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, sort_keys=False)
        
        print(f"\nUpdated config with {len(active_vaults)} active vaults")
    else:
        print("\nNo active vaults found")

if __name__ == '__main__':
    asyncio.run(query_vaults())