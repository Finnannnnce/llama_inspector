# @version 0.3.7

from vyper.interfaces import ERC20

interface ILoan:
    def debt() -> uint256: view
    def collateral() -> uint256: view
    def borrower() -> address: view
    def liquidator() -> address: view
    def is_liquidated() -> bool: view

interface IController:
    def owner() -> address: view
    def is_approved_borrower(_borrower: address) -> bool: view
    def is_approved_liquidator(_liquidator: address) -> bool: view
    def is_approved_loan(_loan: address) -> bool: view

event LoanCreated:
    loan: indexed(address)
    borrower: indexed(address)
    collateral_amount: uint256
    debt_amount: uint256

event LoanClosed:
    loan: indexed(address)
    collateral_amount: uint256
    debt_amount: uint256

event LoanLiquidated:
    loan: indexed(address)
    liquidator: indexed(address)
    collateral_amount: uint256
    debt_amount: uint256

@external
@view
def collateral_token() -> address:
    """
    @notice Get the collateral token address
    @return The collateral token address
    """
    raise "Not implemented"

@external
@view
def borrowed_token() -> address:
    """
    @notice Get the borrowed token address
    @return The borrowed token address
    """
    raise "Not implemented"

@external
@view
def active_loans() -> uint256:
    """
    @notice Get the number of active loans
    @return The number of active loans
    """
    raise "Not implemented"

@external
@view
def active_loans_list(arg0: uint256) -> address:
    """
    @notice Get the loan address at the given index
    @param arg0 The index
    @return The loan address
    """
    raise "Not implemented"

@external
@view
def loan_exists(_loan: address) -> bool:
    """
    @notice Check if a loan exists and is active
    @param _loan The loan address to check
    @return True if the loan exists and is active
    """
    raise "Not implemented"

@external
@view
def loan_debt(_loan: address) -> uint256:
    """
    @notice Get the current debt of a loan
    @param _loan The loan address
    @return The current debt amount
    """
    raise "Not implemented"

@external
@view
def loan_collateral(_loan: address) -> uint256:
    """
    @notice Get the current collateral of a loan
    @param _loan The loan address
    @return The current collateral amount
    """
    raise "Not implemented"