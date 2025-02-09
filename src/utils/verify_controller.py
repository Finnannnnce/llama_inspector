import asyncio
import json
from web3 import Web3
from web3.exceptions import ContractLogicError

async def verify_controller():
    """Verify Controller contract and its functions"""
    
    # Connect to Ethereum node
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    
    # Controller address
    controller_address = '0x413FD2511BAD510947a91f5c6c79EBD8138C29Fc'
    
    # Known vault addresses
    vaults = {
        'Curve DAO Token (CRV)': '0xCeA18a8752bb7e7817F9AE7565328FE415C0f2cA',
        'Wrapped Ether (WETH)': '0x5AE28c9197a4a6570216fC7e53E7e0221D7A0FEF',
        'Wrapped liquid staked Ether 2.0 (wstETH)': '0x8cf1DE26729cfB7137AF1A6B2a665e099EC319b5',
        'tBTC v2 (tBTC)': '0xb2b23C87a4B6d1b03Ba603F7C3EB9A81fDC0AAC9'
    }
    
    # Load Controller ABI
    with open('contracts/interfaces/controller.json', 'r') as f:
        controller_abi = json.load(f)['abi']
    
    print(f"\nChecking Controller at {controller_address}")
    
    # Check if address has code
    code = w3.eth.get_code(controller_address)
    if code == b'':
        print("No contract code found at this address")
        return
    
    print("Contract code found")
    
    # Create contract instance
    controller = w3.eth.contract(address=controller_address, abi=controller_abi)
    
    # Try different function calls to verify interface
    for name, vault_address in vaults.items():
        print(f"\nChecking loans for {name}:")
        
        try:
            # Try different variations of loan count function
            try:
                n_loans = controller.functions.numLoans(vault_address).call()
                print(f"- numLoans(): {n_loans}")
            except:
                try:
                    n_loans = controller.functions.n_loans(vault_address).call()
                    print(f"- n_loans(): {n_loans}")
                except:
                    print("- Failed to get loan count")
                    continue
            
            if n_loans > 0:
                print(f"\nFound {n_loans} loans, checking first loan:")
                
                # Try to get first loan
                try:
                    loan = controller.functions.getLoanAt(vault_address, 0).call()
                    print(f"- getLoanAt(0): {loan}")
                except:
                    try:
                        loan = controller.functions.loans(vault_address, 0).call()
                        print(f"- loans(0): {loan}")
                    except:
                        print("- Failed to get loan address")
                        continue
                
                if loan:
                    # Check if loan exists
                    try:
                        exists = controller.functions.loanExists(loan).call()
                        print(f"- loanExists(): {exists}")
                    except:
                        try:
                            exists = controller.functions.loan_exists(loan).call()
                            print(f"- loan_exists(): {exists}")
                        except:
                            print("- Failed to check loan existence")
                            continue
                    
                    if exists:
                        # Get loan debt
                        try:
                            debt = controller.functions.getDebt(loan).call()
                            print(f"- getDebt(): {debt}")
                        except:
                            try:
                                debt = controller.functions.debt(loan).call()
                                print(f"- debt(): {debt}")
                            except:
                                print("- Failed to get loan debt")
        
        except Exception as e:
            print(f"Error checking vault: {str(e)}")

if __name__ == '__main__':
    asyncio.run(verify_controller())