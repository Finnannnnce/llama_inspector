from typing import List, Optional
from pydantic import BaseModel, Field

class TokenInfo(BaseModel):
    """Token information model"""
    address: str = Field(..., description="Token contract address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    decimals: int = Field(..., description="Token decimals")

class VaultInfo(BaseModel):
    """Vault information model"""
    address: str = Field(..., description="Vault contract address")
    borrowed_token: TokenInfo = Field(..., description="Borrowed token information")
    collateral_token: TokenInfo = Field(..., description="Collateral token information")

class VaultStats(BaseModel):
    """Vault statistics"""
    address: str = Field(..., description="Vault contract address")
    total_debt: str = Field(..., description="Total debt amount (human readable)")
    total_collateral: str = Field(..., description="Total collateral amount (human readable)")
    total_debt_usd: str = Field(..., description="Total debt in USD")
    total_collateral_usd: str = Field(..., description="Total collateral in USD")
    active_loans: int = Field(..., description="Number of active loans")

class UserPosition(BaseModel):
    """User position in a vault"""
    user_address: str = Field(..., description="User's Ethereum address")
    vault_address: str = Field(..., description="Vault contract address")
    debt: str = Field(..., description="User's debt amount (human readable)")
    collateral: str = Field(..., description="User's collateral amount (human readable)")
    debt_usd: str = Field(..., description="User's debt in USD")
    collateral_usd: str = Field(..., description="User's collateral in USD")

class UserVaultSummary(BaseModel):
    """Summary of user's positions across all vaults"""
    user_address: str = Field(..., description="User's Ethereum address")
    positions: List[UserPosition] = Field(default_factory=list, description="List of user's positions")
    total_debt_usd: str = Field(..., description="Total debt across all vaults in USD")
    total_collateral_usd: str = Field(..., description="Total collateral across all vaults in USD")

class RpcEndpoint(BaseModel):
    """RPC endpoint information"""
    name: str = Field(..., description="Name of the RPC provider")
    url: str = Field(..., description="RPC endpoint URL")
    chain_id: int = Field(..., description="Chain ID")
    is_active: bool = Field(..., description="Whether the endpoint is currently active")
    priority: int = Field(..., description="Priority order for fallback (lower is higher priority)")

class ErrorResponse(BaseModel):
    """API error response"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")