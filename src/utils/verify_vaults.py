import asyncio
import json
from web3 import Web3
from web3.exceptions import ContractLogicError

async def verify_vaults():
    """Verify vault addresses and their deployed code"""
    
    # Connect to Ethereum node
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    
    # Known vault addresses
    vaults = {
        'Curve DAO Token (CRV)': '0xCeA18a8752bb7e7817F9AE7565328FE415C0f2cA',
        'Wrapped Ether (WETH)': '0x5AE28c9197a4a6570216fC7e53E7e0221D7A0FEF',
        'Wrapped liquid staked Ether 2.0 (wstETH)': '0x8cf1DE26729cfB7137AF1A6B2a665e099EC319b5',
        'tBTC v2 (tBTC)': '0xb2b23C87a4B6d1b03Ba603F7C3EB9A81fDC0AAC9'
    }
    
    # Load Vault ABI
    with open('contracts/interfaces/vault.json', 'r') as f:
        vault_abi = json.load(f)['abi']
    
    print("Verifying vault addresses...")
    
    for name, address in vaults.items():
        print(f"\nChecking {name} at {address}")
        
        # Check if address has code
        code = w3.eth.get_code(address)
        if code == b'':
            print("No contract code found at this address")
            continue
        
        print("Contract code found")
        
        # Create contract instance
        vault = w3.eth.contract(address=address, abi=vault_abi)
        
        # Try different function calls to verify interface
        try:
            # Try view functions that should always work
            print("Testing view functions:")
            
            try:
                collateral = vault.functions.collateral_token().call()
                print(f"- collateral_token(): {collateral}")
            except ContractLogicError as e:
                print(f"- collateral_token() failed: {str(e)}")
            
            try:
                borrowed = vault.functions.borrowed_token().call()
                print(f"- borrowed_token(): {borrowed}")
            except ContractLogicError as e:
                print(f"- borrowed_token() failed: {str(e)}")
            
            # Try different variations of total loans function
            try:
                total = vault.functions.total_loans().call()
                print(f"- total_loans(): {total}")
            except:
                try:
                    total = vault.functions.totalLoans().call()
                    print(f"- totalLoans(): {total}")
                except:
                    try:
                        total = vault.functions.n_loans().call()
                        print(f"- n_loans(): {total}")
                    except:
                        try:
                            total = vault.functions.numLoans().call()
                            print(f"- numLoans(): {total}")
                        except:
                            print("- Failed to get total loans with any function name")
                            total = None
            
            # Try different variations of loan functions if we got total
            if total and total > 0:
                print(f"\nFound {total} loans, checking first loan:")
                
                # Try different variations of loan_at function
                loan = None
                try:
                    loan = vault.functions.loan_at(0).call()
                    print(f"- loan_at(0): {loan}")
                except:
                    try:
                        loan = vault.functions.getLoanAt(0).call()
                        print(f"- getLoanAt(0): {loan}")
                    except:
                        try:
                            loan = vault.functions.loans(0).call()
                            print(f"- loans(0): {loan}")
                        except:
                            print("- Failed to get loan with any function name")
                
                if loan:
                    # Try different variations of loan_exists function
                    try:
                        exists = vault.functions.loan_exists(loan).call()
                        print(f"- loan_exists(): {exists}")
                    except:
                        try:
                            exists = vault.functions.loanExists(loan).call()
                            print(f"- loanExists(): {exists}")
                        except:
                            print("- Failed to check loan existence")
                            exists = False
                    
                    if exists:
                        # Try different variations of loan_debt function
                        try:
                            debt = vault.functions.loan_debt(loan).call()
                            print(f"- loan_debt(): {debt}")
                        except:
                            try:
                                debt = vault.functions.getLoanDebt(loan).call()
                                print(f"- getLoanDebt(): {debt}")
                            except:
                                try:
                                    debt = vault.functions.debt(loan).call()
                                    print(f"- debt(): {debt}")
                                except:
                                    print("- Failed to get loan debt")
            
        except Exception as e:
            print(f"Error verifying contract: {str(e)}")

if __name__ == '__main__':
    asyncio.run(verify_vaults())