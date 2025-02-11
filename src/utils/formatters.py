from decimal import Decimal, ROUND_DOWN
from typing import Union, Optional

Number = Union[int, float, str, Decimal]

def format_token_amount(amount: Number, decimals: int) -> str:
    """Format token amount with proper decimal places"""
    if not amount:
        return "0.00"
        
    try:
        # Convert to Decimal for precise decimal arithmetic
        amount_decimal = Decimal(str(amount))
        
        # Adjust for token decimals
        adjusted_amount = amount_decimal / Decimal(10 ** decimals)
        
        # For stablecoins (decimals=18), round to 2 decimal places
        if decimals == 18 and "USD" in str(amount).upper():
            return f"{adjusted_amount:.2f}"
            
        # For other tokens, show up to 8 decimal places if needed
        formatted = f"{adjusted_amount:.8f}".rstrip('0').rstrip('.')
        return formatted if formatted else "0"
        
    except Exception:
        return str(amount)

def format_usd_amount(amount: Number) -> str:
    """Format USD amount with proper decimal places and currency symbol"""
    if not amount:
        return "$0.00"
        
    try:
        # Convert to Decimal for precise decimal arithmetic
        amount_decimal = Decimal(str(amount))
        
        # Format with 2 decimal places for USD
        return f"${amount_decimal:.2f}"
        
    except Exception:
        return f"${amount}"

def format_percentage(value: Number, decimals: int = 2) -> str:
    """Format percentage with specified decimal places"""
    if not value:
        return "0%"
        
    try:
        # Convert to Decimal for precise decimal arithmetic
        value_decimal = Decimal(str(value))
        
        # Format with specified decimal places
        formatted = f"{value_decimal:.{decimals}f}%"
        return formatted
        
    except Exception:
        return f"{value}%"

def format_eth_address(address: str) -> str:
    """Format Ethereum address with ellipsis in the middle"""
    if not address or len(address) < 42:
        return address
    return f"{address[:6]}...{address[-4:]}"

def format_token_pair(token1: str, token2: str) -> str:
    """Format token pair with separator"""
    return f"{token1}/{token2}"

def get_token_decimals(token_contract) -> int:
    """Get decimals from ERC20 token contract"""
    try:
        return token_contract.functions.decimals().call()
    except Exception:
        # Default to 18 decimals if not specified
        return 18