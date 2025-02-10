"""Utility functions for formatting amounts"""
from decimal import Decimal
from typing import Union

def to_decimal(amount: Union[int, float, str, Decimal]) -> Decimal:
    """Convert amount to Decimal type
    
    Args:
        amount: Amount to convert
        
    Returns:
        Decimal: Converted amount
    """
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))

def format_token_amount(amount: Union[int, float, str, Decimal], decimals: int) -> str:
    """Convert raw token amount to human readable decimal considering token decimals
    
    Args:
        amount: Raw token amount
        decimals: Number of decimals for the token
        
    Returns:
        str: Human readable token amount
    """
    if not amount:
        return '0.00'
        
    # Convert to Decimal for precise arithmetic
    amount_dec = to_decimal(amount)
    
    # Divide by 10^decimals
    divisor = Decimal(10) ** decimals
    
    result = amount_dec / divisor
    return f"{result:,.2f}"

def format_usd_amount(amount: Union[int, float, str, Decimal]) -> str:
    """Format USD amount with 2 decimal places and dollar sign
    
    Args:
        amount: Amount in USD
        
    Returns:
        str: Formatted USD amount with $ prefix
    """
    if not amount:
        return '$0.00'
        
    # Convert to Decimal for precise arithmetic
    amount_dec = to_decimal(amount)
    
    # Format with 2 decimal places and thousands separator
    return f"${amount_dec:,.2f}"