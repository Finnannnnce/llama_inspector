"""Utility functions for formatting token amounts"""
from decimal import Decimal
from typing import Union

def format_token_amount(amount: Union[int, str], decimals: int) -> Decimal:
    """Convert raw token amount to human readable decimal considering token decimals
    
    Args:
        amount: Raw token amount (integer or string)
        decimals: Number of decimals for the token
        
    Returns:
        Decimal: Human readable token amount
    """
    if not amount:
        return Decimal('0')
        
    # Convert to string first to handle scientific notation
    amount_str = str(amount)
    
    # Convert to Decimal
    amount_dec = Decimal(amount_str)
    
    # Divide by 10^decimals
    divisor = Decimal(10) ** decimals
    
    return amount_dec / divisor