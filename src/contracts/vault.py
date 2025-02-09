import asyncio
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from web3.contract import Contract
from ..utils.rate_limiter import retry_forever
from ..utils.cache import ContractCache
from .helpers import ContractHelper
from ..price_feeds.aggregator import PriceFeedAggregator

class VaultInfo:
    """Data class for vault information"""
    def __init__(self, name: str, collateral_name: str, borrowed_name: str,
                 collateral_amount: Decimal = Decimal('0'),
                 collateral_value: Decimal = Decimal('0'),
                 debt_amount: Decimal = Decimal('0'),
                 debt_value: Decimal = Decimal('0'),
                 loans: List[Dict] = None,
                 liquidity_providers: List[str] = None,
                 has_position: bool = False):
        self.name = name
        self.collateral_name = collateral_name
        self.borrowed_name = borrowed_name
        self.collateral_amount = collateral_amount
        self.collateral_value = collateral_value
        self.debt_amount = debt_amount
        self.debt_value = debt_value
        self.loans = loans or []
        self.liquidity_providers = liquidity_providers or []
        self.has_position = has_position

class VaultManager:
    """Manager class for vault operations"""
    
    def __init__(self, contract_helper: ContractHelper, price_feed: PriceFeedAggregator,
                 loan_cache: ContractCache, verbose: bool = False):
        """Initialize vault manager
        
        Args:
            contract_helper: Helper for contract interactions
            price_feed: Price feed aggregator
            loan_cache: Cache for loan information
            verbose: Enable verbose logging
        """
        self.contract_helper = contract_helper
        self.price_feed = price_feed
        self.loan_cache = loan_cache
        self.verbose = verbose
    
    @retry_forever
    async def get_loan_addresses(self, controller_contract: Contract) -> List[str]:
        """Get all loan addresses from a controller
        
        Args:
            controller_contract: Controller contract instance
            
        Returns:
            List of loan addresses (excluding burn addresses)
        """
        addresses = []
        i = 0
        batch_size = 20  # Get 20 addresses at a time
        
        try:
            while True:
                # Create batch of loan index functions
                funcs = [
                    controller_contract.functions.loans(j)
                    for j in range(i, i + batch_size)
                ]
                
                # Get addresses in batch
                batch_addresses = await self.contract_helper.batch_call_contract_functions(
                    funcs,
                    [f"loan_address_{j}" for j in range(i, i + batch_size)]
                )
                
                # Process results
                valid_addresses = []
                for addr in batch_addresses:
                    if not addr or addr == "0x0000000000000000000000000000000000000000":
                        # End of loans reached
                        if self.verbose:
                            print(f"Found {len(addresses)} active loans")
                        return addresses
                    valid_addresses.append(addr)
                
                if not valid_addresses:  # No more valid addresses
                    break
                
                addresses.extend(valid_addresses)
                i += batch_size
                
                # Add delay between batches
                await asyncio.sleep(0.5)
            
            if self.verbose:
                print(f"Found {len(addresses)} active loans")
            return addresses
            
        except Exception as e:
            if self.verbose:
                print(f"Error getting loan addresses: {str(e)}")
            return addresses
    
    async def get_loan_info_batch(self, addresses: List[str], controller_contract: Contract, 
                                 amm_contract: Contract, collateral_decimals: int,
                                 borrowed_decimals: int, collateral_price: Optional[Decimal],
                                 borrowed_price: Optional[Decimal]) -> List[Optional[Dict]]:
        """Get detailed loan information for multiple addresses in batch
        
        Args:
            addresses: List of loan addresses
            controller_contract: Controller contract instance
            amm_contract: AMM contract instance
            collateral_decimals: Collateral token decimals
            borrowed_decimals: Borrowed token decimals
            collateral_price: Collateral token price in USD
            borrowed_price: Borrowed token price in USD
            
        Returns:
            List of loan information dictionaries or None for invalid loans
        """
        if not addresses:
            return []
        
        # Check cache first
        results = []
        uncached_indices = []
        uncached_addresses = []
        
        for i, addr in enumerate(addresses):
            cache_key = f"loan_info_{addr}"
            cached_info = self.loan_cache.get(cache_key)
            if cached_info is not None:
                results.append(cached_info)
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_addresses.append(addr)
        
        if uncached_addresses:
            # Create batch of exists checks
            exists_funcs = [
                controller_contract.functions.loan_exists(addr)
                for addr in uncached_addresses
            ]
            exists_results = await self.contract_helper.batch_call_contract_functions(
                exists_funcs,
                [f"loan_exists_{addr}" for addr in uncached_addresses]
            )
            
            # Get collateral amounts for valid loans
            valid_indices = []
            valid_addresses = []
            for i, exists in enumerate(exists_results):
                if exists:
                    valid_indices.append(uncached_indices[i])
                    valid_addresses.append(uncached_addresses[i])
            
            if valid_addresses:
                # Get collateral amounts
                sum_xy_funcs = [
                    amm_contract.functions.get_sum_xy(addr)
                    for addr in valid_addresses
                ]
                sum_xy_results = await self.contract_helper.batch_call_contract_functions(
                    sum_xy_funcs,
                    [f"sum_xy_{addr}" for addr in valid_addresses]
                )
                
                # Get debt amounts
                debt_funcs = [
                    controller_contract.functions.debt(addr)
                    for addr in valid_addresses
                ]
                debt_results = await self.contract_helper.batch_call_contract_functions(
                    debt_funcs,
                    [f"debt_{addr}" for addr in valid_addresses]
                )
                
                # Process results
                for i, (addr, sum_xy, debt) in enumerate(zip(valid_addresses, sum_xy_results, debt_results)):
                    if sum_xy and debt:
                        collateral_amount = self.contract_helper.format_token_amount(
                            sum_xy[1], collateral_decimals
                        )
                        collateral_value = collateral_amount * (collateral_price or Decimal('0'))
                        
                        debt_amount = self.contract_helper.format_token_amount(
                            debt, borrowed_decimals
                        )
                        debt_value = debt_amount * (borrowed_price or Decimal('0'))
                        
                        loan_info = {
                            'address': addr,
                            'collateral_amount': collateral_amount,
                            'collateral_value': collateral_value,
                            'debt_amount': debt_amount,
                            'debt_value': debt_value
                        }
                        
                        # Update results and cache
                        results[valid_indices[i]] = loan_info
                        self.loan_cache.set(f"loan_info_{addr}", loan_info)
        
        return results
    
    async def get_vault_info(self, name: str, address: str, collateral_token: str,
                           borrowed_token: str, vault_abi: list, controller_abi: list,
                           erc20_abi: list, user_address: Optional[str] = None) -> Optional[VaultInfo]:
        """Get comprehensive vault information
        
        Args:
            name: Vault name
            address: Vault contract address
            collateral_token: Collateral token address
            borrowed_token: Borrowed token address
            vault_abi: Vault contract ABI
            controller_abi: Controller contract ABI
            erc20_abi: ERC20 contract ABI
            user_address: Optional address to check positions for
            
        Returns:
            VaultInfo instance or None if error occurs
        """
        try:
            if self.verbose:
                print(f"Processing {name}...", flush=True)
            
            # Create contract instances
            vault_contract = self.contract_helper.get_contract(address, vault_abi)
            
            # Get token information
            if self.verbose:
                print("  - Getting token info...", flush=True)
            
            token_info = await self.contract_helper.get_token_info(
                [collateral_token, borrowed_token],
                erc20_abi
            )
            if not token_info or len(token_info) != 2:
                raise Exception("Failed to get token info")
            
            (collateral_name, collateral_decimals), (borrowed_name, borrowed_decimals) = token_info
            
            # Get token prices
            collateral_price = await self.price_feed.get_price(
                collateral_token, verbose=self.verbose
            )
            borrowed_price = await self.price_feed.get_price(
                borrowed_token, verbose=self.verbose
            )
            
            # Get AMM contract
            if self.verbose:
                print("  - Getting AMM contract...", flush=True)
            amm_address = await self.contract_helper.call_contract_function(
                vault_contract.functions.amm(),
                cache_key=f"amm_{address}"
            )
            amm_contract = self.contract_helper.get_contract(amm_address, vault_abi)
            
            # Get controller contract
            if self.verbose:
                print("  - Getting controller contract...", flush=True)
            controller_address = await self.contract_helper.call_contract_function(
                vault_contract.functions.controller(),
                cache_key=f"controller_{address}"
            )
            controller_contract = self.contract_helper.get_contract(
                controller_address, controller_abi
            )
            
            # Get loan addresses
            if self.verbose:
                print("  - Getting loan addresses...", flush=True)
            loan_addresses = await self.get_loan_addresses(controller_contract)
            
            # Get loan information in batches
            if self.verbose:
                print("  - Getting loan details...", flush=True)
            
            loans = []
            for i in range(0, len(loan_addresses), 10):  # Process 10 loans at a time
                batch_addresses = loan_addresses[i:i+10]
                batch_info = await self.get_loan_info_batch(
                    batch_addresses, controller_contract, amm_contract,
                    collateral_decimals, borrowed_decimals,
                    collateral_price, borrowed_price
                )
                loans.extend([info for info in batch_info if info])
                await asyncio.sleep(1)  # Add delay between batches
            
            # Check user position if address provided
            has_position = False
            collateral_amount = Decimal('0')
            collateral_value = Decimal('0')
            debt_amount = Decimal('0')
            debt_value = Decimal('0')
            
            if user_address:
                if self.verbose:
                    print("  - Checking user position...", flush=True)
                has_position = await self.contract_helper.call_contract_function(
                    amm_contract.functions.has_liquidity(user_address),
                    cache_key=f"has_liquidity_{user_address}_{amm_address}"
                )
                if has_position:
                    sum_xy = await self.contract_helper.call_contract_function(
                        amm_contract.functions.get_sum_xy(user_address),
                        cache_key=f"sum_xy_{user_address}_{amm_address}"
                    )
                    collateral_amount = self.contract_helper.format_token_amount(
                        sum_xy[1], collateral_decimals
                    )
                    collateral_value = collateral_amount * (collateral_price or Decimal('0'))
                    
                    debt = await self.contract_helper.call_contract_function(
                        controller_contract.functions.debt(user_address),
                        cache_key=f"debt_{user_address}_{controller_address}"
                    )
                    debt_amount = self.contract_helper.format_token_amount(
                        debt, borrowed_decimals
                    )
                    debt_value = debt_amount * (borrowed_price or Decimal('0'))
            
            if self.verbose:
                print("  - Vault processing complete", flush=True)
            
            return VaultInfo(
                name=name,
                collateral_name=collateral_name,
                borrowed_name=borrowed_name,
                collateral_amount=collateral_amount,
                collateral_value=collateral_value,
                debt_amount=debt_amount,
                debt_value=debt_value,
                loans=loans,
                liquidity_providers=[loan['address'] for loan in loans],
                has_position=has_position
            )
            
        except Exception as e:
            if self.verbose:
                print(f"Error processing vault {name}: {str(e)}", flush=True)
            return None