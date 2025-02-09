# @version 0.3.7

interface IERC20:
    def name() -> String[32]: view
    def symbol() -> String[32]: view
    def decimals() -> uint8: view
    def totalSupply() -> uint256: view
    def balanceOf(account: address) -> uint256: view
    def allowance(owner: address, spender: address) -> uint256: view
    def transfer(recipient: address, amount: uint256) -> bool: nonpayable
    def approve(spender: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable