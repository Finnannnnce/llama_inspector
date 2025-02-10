from typing import List, Optional, Dict, Any, cast
from fastapi import APIRouter, HTTPException, Depends
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from decimal import Decimal
import os

from .models import (
    VaultInfo,
    VaultStats,
    UserPosition,
    UserVaultSummary,
    ErrorResponse,
    TokenInfo,
    RpcEndpoint
)
from ..utils.contract_queries import ContractQueries
from ..utils.formatters import format_token_amount, format_usd_amount

router = APIRouter(prefix="/api/v1")

@router.get("/rpc-nodes", response_model=List[RpcEndpoint], responses={503: {"model": ErrorResponse}})
async def list_rpc_nodes():
    """Get list of available Ethereum RPC nodes"""
    try:
        # Define available RPC nodes
        rpc_nodes = [
            RpcEndpoint(
                name="Local Ethereum Node",
                url="http://192.168.40.201:8545",
                chain_id=1,
                is_active=True,
                priority=1
            ),
            RpcEndpoint(
                name="Alchemy",
                url="https://eth-mainnet.alchemyapi.io/v2/",
                chain_id=1,
                is_active=bool(os.getenv("ALCHEMY_API_KEY")),
                priority=2
            ),
            RpcEndpoint(
                name="Infura",
                url="https://mainnet.infura.io/v3/",
                chain_id=1,
                is_active=bool(os.getenv("INFURA_PROJECT_ID")),
                priority=3
            ),
            RpcEndpoint(
                name="Ankr",
                url="https://rpc.ankr.com/eth/",
                chain_id=1,
                is_active=bool(os.getenv("ANKR_API_KEY")),
                priority=4
            )
        ]
        return rpc_nodes
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test Web3 connection
        w3 = await get_web3()
        if not await w3.is_connected():
            raise HTTPException(status_code=503, detail="Failed to connect to Ethereum node")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

def contract_token_to_api_token(token_dict: Dict[str, Any]) -> TokenInfo:
    """Convert contract token info dictionary to API TokenInfo model"""
    return TokenInfo(
        address=str(token_dict['address']),
        name=str(token_dict['name']),
        symbol=str(token_dict['symbol']),
        decimals=int(token_dict['decimals'])
    )

async def get_web3() -> AsyncWeb3:
    """Get Web3 instance with caching"""
    w3 = AsyncWeb3(AsyncHTTPProvider("http://192.168.40.201:8545"))
    if not await w3.is_connected():
        raise HTTPException(status_code=503, detail="Failed to connect to Ethereum node")
    return w3

async def get_queries(w3: AsyncWeb3 = Depends(get_web3)) -> ContractQueries:
    """Get ContractQueries instance"""
    return ContractQueries(w3, ".cache")

@router.get("/vaults", response_model=List[VaultInfo], responses={503: {"model": ErrorResponse}})
async def list_vaults(queries: ContractQueries = Depends(get_queries)):
    """Get list of all vaults with their token information"""
    try:
        factory_address = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
        factory = await queries.get_factory_async(factory_address)
        if not factory:
            raise HTTPException(status_code=503, detail="Failed to get factory contract")

        vaults = []
        market_count = await factory.functions.market_count().call()
        
        for i in range(market_count):
            vault_address = await factory.functions.controllers(i).call()
            if vault_address == "0x" + "0" * 40:
                continue
                
            vault = await queries.get_vault_async(factory, vault_address)
            if not vault:
                continue
                
            token_info = await queries.get_vault_tokens_async(vault, vault_address)
            if token_info:
                token_info_dict = cast(Dict[str, Dict[str, Any]], token_info)
                vaults.append(VaultInfo(
                    address=vault_address,
                    borrowed_token=contract_token_to_api_token(token_info_dict['borrowed_token']),
                    collateral_token=contract_token_to_api_token(token_info_dict['collateral_token'])
                ))
                
        return vaults
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/vaults/{vault_address}/stats", response_model=VaultStats, responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def get_vault_stats(vault_address: str, queries: ContractQueries = Depends(get_queries)):
    """Get statistics for a specific vault"""
    try:
        factory_address = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
        factory = await queries.get_factory_async(factory_address)
        if not factory:
            raise HTTPException(status_code=503, detail="Failed to get factory contract")
            
        vault = await queries.get_vault_async(factory, vault_address)
        if not vault:
            raise HTTPException(status_code=404, detail=f"Vault {vault_address} not found")
            
        total_debt = Decimal(0)
        total_collateral = Decimal(0)
        active_loans = 0
        
        # Get token info first for decimals
        token_info = await queries.get_vault_tokens_async(vault, vault_address)
        if not token_info:
            raise HTTPException(status_code=503, detail="Failed to get token information")
            
        borrowed_decimals = token_info['borrowed_token']['decimals']
        collateral_decimals = token_info['collateral_token']['decimals']
        
        index = 0
        while True:
            try:
                user_address = await vault.functions.loans(index).call()
                if not user_address or user_address == "0x" + "0" * 40:
                    break
                    
                loan_info = await queries.get_loan_info_async(vault, user_address)
                if loan_info:
                    # Convert amounts considering token decimals
                    debt = Decimal(loan_info['debt']) / (Decimal(10) ** borrowed_decimals)
                    collateral = Decimal(loan_info['collateral']) / (Decimal(10) ** collateral_decimals)
                    
                    total_debt += debt
                    total_collateral += collateral
                    active_loans += 1
                    
                index += 1
                
            except Exception:
                break
            
        borrowed_price = Decimal(1.0)  # Default to 1.0 for stablecoins
        collateral_price = Decimal(0.0)  # Default to 0.0 for unknown tokens
            
        total_debt_usd = total_debt * borrowed_price
        total_collateral_usd = total_collateral * collateral_price
        
        return VaultStats(
            address=vault_address,
            total_debt=format_token_amount(total_debt, 0),  # Already in human readable form
            total_collateral=format_token_amount(total_collateral, 0),  # Already in human readable form
            total_debt_usd=format_usd_amount(total_debt_usd),
            total_collateral_usd=format_usd_amount(total_collateral_usd),
            active_loans=active_loans
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/vaults/{vault_address}/users/{user_address}", response_model=UserPosition, responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def get_user_position(vault_address: str, user_address: str, queries: ContractQueries = Depends(get_queries)):
    """Get user's position in a specific vault"""
    try:
        factory_address = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
        factory = await queries.get_factory_async(factory_address)
        if not factory:
            raise HTTPException(status_code=503, detail="Failed to get factory contract")
            
        vault = await queries.get_vault_async(factory, vault_address)
        if not vault:
            raise HTTPException(status_code=404, detail=f"Vault {vault_address} not found")
            
        loan_info = await queries.get_loan_info_async(vault, user_address)
        if not loan_info:
            raise HTTPException(status_code=404, detail=f"No position found for user {user_address}")
            
        # Get token info for decimals
        token_info = await queries.get_vault_tokens_async(vault, vault_address)
        if not token_info:
            raise HTTPException(status_code=503, detail="Failed to get token information")
            
        borrowed_decimals = token_info['borrowed_token']['decimals']
        collateral_decimals = token_info['collateral_token']['decimals']
        
        # Convert amounts considering token decimals
        debt = Decimal(loan_info['debt']) / (Decimal(10) ** borrowed_decimals)
        collateral = Decimal(loan_info['collateral']) / (Decimal(10) ** collateral_decimals)
        
        borrowed_price = Decimal(1.0)  # Default to 1.0 for stablecoins
        collateral_price = Decimal(0.0)  # Default to 0.0 for unknown tokens
        
        debt_usd = debt * borrowed_price
        collateral_usd = collateral * collateral_price
        
        return UserPosition(
            user_address=user_address,
            vault_address=vault_address,
            debt=format_token_amount(debt, 0),  # Already in human readable form
            collateral=format_token_amount(collateral, 0),  # Already in human readable form
            debt_usd=format_usd_amount(debt_usd),
            collateral_usd=format_usd_amount(collateral_usd)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/vaults/{vault_address}/users", response_model=List[str], responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def list_vault_users(vault_address: str, queries: ContractQueries = Depends(get_queries)):
    """Get list of users with positions in a specific vault"""
    try:
        factory_address = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
        factory = await queries.get_factory_async(factory_address)
        if not factory:
            raise HTTPException(status_code=503, detail="Failed to get factory contract")
            
        vault = await queries.get_vault_async(factory, vault_address)
        if not vault:
            raise HTTPException(status_code=404, detail=f"Vault {vault_address} not found")
            
        users = []
        index = 0
        while True:
            try:
                user_address = await vault.functions.loans(index).call()
                if not user_address or user_address == "0x" + "0" * 40:
                    break
                    
                users.append(user_address)
                index += 1
                
            except Exception:
                break
            
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/users/{user_address}/positions", response_model=UserVaultSummary, responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def get_user_positions(user_address: str, queries: ContractQueries = Depends(get_queries)):
    """Get all positions for a specific user across all vaults"""
    try:
        factory_address = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
        factory = await queries.get_factory_async(factory_address)
        if not factory:
            raise HTTPException(status_code=503, detail="Failed to get factory contract")
            
        positions = []
        total_debt_usd = Decimal(0)
        total_collateral_usd = Decimal(0)
        
        market_count = await factory.functions.market_count().call()
        for i in range(market_count):
            vault_address = await factory.functions.controllers(i).call()
            if vault_address == "0x" + "0" * 40:
                continue
                
            vault = await queries.get_vault_async(factory, vault_address)
            if not vault:
                continue
                
            loan_info = await queries.get_loan_info_async(vault, user_address)
            if not loan_info:
                continue
                
            # Get token info for decimals
            token_info = await queries.get_vault_tokens_async(vault, vault_address)
            if not token_info:
                continue
                
            borrowed_decimals = token_info['borrowed_token']['decimals']
            collateral_decimals = token_info['collateral_token']['decimals']
            
            # Convert amounts considering token decimals
            debt = Decimal(loan_info['debt']) / (Decimal(10) ** borrowed_decimals)
            collateral = Decimal(loan_info['collateral']) / (Decimal(10) ** collateral_decimals)
            
            borrowed_price = Decimal(1.0)  # Default to 1.0 for stablecoins
            collateral_price = Decimal(0.0)  # Default to 0.0 for unknown tokens
            
            debt_usd = debt * borrowed_price
            collateral_usd = collateral * collateral_price
            
            position = UserPosition(
                user_address=user_address,
                vault_address=vault_address,
                debt=format_token_amount(debt, 0),  # Already in human readable form
                collateral=format_token_amount(collateral, 0),  # Already in human readable form
                debt_usd=format_usd_amount(debt_usd),
                collateral_usd=format_usd_amount(collateral_usd)
            )
            
            positions.append(position)
            total_debt_usd += debt_usd
            total_collateral_usd += collateral_usd
            
        if not positions:
            raise HTTPException(status_code=404, detail=f"No positions found for user {user_address}")
            
        return UserVaultSummary(
            user_address=user_address,
            positions=positions,
            total_debt_usd=format_usd_amount(total_debt_usd),
            total_collateral_usd=format_usd_amount(total_collateral_usd)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))