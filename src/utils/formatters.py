def format_token_amount(amount: float, symbol: str) -> str:
    """Format token amount with 4 decimal places and symbol"""
    return f"{amount:.4f} {symbol}"

def format_usd_amount(amount: float) -> str:
    """Format USD amount with $ prefix and 2 decimal places"""
    return f"${amount:.2f}"