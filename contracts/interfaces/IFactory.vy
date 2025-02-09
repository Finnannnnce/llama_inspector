# @version 0.3.7

interface IFactory:
    def market_count() -> uint256: view
    def vaults(i: uint256) -> address: view
    def controllers(i: uint256) -> address: view
    def borrowed_tokens(i: uint256) -> address: view
    def collateral_tokens(i: uint256) -> address: view