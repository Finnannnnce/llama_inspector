# Lending Protocol Analysis

## Overview
- Factory Contract: `0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0`
- Total Controllers: 28
- Main Borrowed Token: Curve.Fi USD Stablecoin (crvUSD)

## Contract Architecture
- Factory contract manages controller deployment
- Each controller has an associated AMM and admin contract
- Controllers handle specific token pairs
- Most controllers use crvUSD as the borrowed token
- Some controllers are "reverse" pairs (e.g., borrow WETH against crvUSD)

## Controllers and Collateral Types

1. wstETH Controller
   - Address: `0x1E0165DbD2019441aB7927C018701f3138114D71`
   - Collateral: Wrapped liquid staked Ether 2.0 (wstETH)
   - Price: $3,161.70

2. WETH Controller
   - Address: `0xaade9230AA9161880E13a38C83400d3D1995267b`
   - Collateral: Wrapped Ether (WETH)
   - Price: $2,653.34

3. tBTC Controller
   - Address: `0x413FD2511BAD510947a91f5c6c79EBD8138C29Fc`
   - Collateral: tBTC v2
   - Price: $96,732.00

4. CRV Controller
   - Address: `0xEdA215b7666936DEd834f76f3fBC6F323295110A`
   - Collateral: Curve DAO Token (CRV)
   - Price: $0.51

5. Reverse CRV Controller
   - Address: `0xC510d73Ad34BeDECa8978B6914461aA7b50CF3Fc`
   - Borrowed: CRV
   - Collateral: crvUSD

6. Reverse WETH Controller
   - Address: `0xa5D9137d2A1Ee912469d911A8E74B6c77503bac8`
   - Borrowed: WETH
   - Collateral: crvUSD

7. Reverse tBTC Controller
   - Address: `0xe438658874b0acf4D81c24172E137F0eE00621b8`
   - Borrowed: tBTC
   - Collateral: crvUSD

8. sUSDe Controller
   - Address: `0x98Fc283d6636f6DCFf5a817A00Ac69A3ADd96907`
   - Collateral: Staked USDe (sUSDe)
   - Price: $1.15

9. UwU Controller
   - Address: `0x09dBDEB3b301A4753589Ac6dF8A178C7716ce16B`
   - Collateral: UwU Lend (UwU)
   - Price: $0.01

10. WBTC Controller
    - Address: `0xcaD85b7fe52B1939DCEebEe9bCf0b2a5Aa0cE617`
    - Collateral: Wrapped BTC (WBTC)
    - Price: $96,720.00

11. pufETH Controller
    - Address: `0x4f87158350c296955966059C50263F711cE0817C`
    - Collateral: pufETH
    - Price: $2,751.09

12. Second sUSDe Controller
    - Address: `0xB536FEa3a01c95Dd09932440eC802A75410139D6`
    - Collateral: Staked USDe (sUSDe)
    - Price: $1.15

13. Second WETH Controller
    - Address: `0x23F5a668A9590130940eF55964ead9787976f2CC`
    - Collateral: Wrapped Ether (WETH)
    - Price: $2,653.34

14. Second wstETH Controller
    - Address: `0x5756A035F276a8095A922931F224F4ed06149608`
    - Collateral: Wrapped liquid staked Ether 2.0 (wstETH)
    - Price: $3,161.70

15. USDe Controller
    - Address: `0x74f88Baa966407b50c10B393bBD789639EFfE78B`
    - Collateral: USDe
    - Price: $1.00

16. sFRAX Controller
    - Address: `0x8C2537F1a5b1b167A960A14B89f7860dd5F7cD68`
    - Collateral: Staked FRAX (sFRAX)

17. ezETH Controller
    - Address: `0x3c1350aa6FaFF17c87Bde2015BBb45100D37dAD3`
    - Collateral: Renzo Restaked ETH (ezETH)

18. sDOLA Controller
    - Address: `0xCf3DF6C1B4A6b38496661B31170de9508b867C8E`
    - Collateral: Staked Dola (sDOLA)

19. ETHFI Controller
    - Address: `0xAC9AdD93364Aea685be238dB6c40BF53753f2cF1`
    - Collateral: ether.fi governance token (ETHFI)

20. USD0/USD0++ Controller
    - Address: `0x1F9D988cDeBfA1FD5563C122a987186e516173c2`
    - Collateral: USD0/USD0++

21. Second USD0/USD0++ Controller
    - Address: `0xDC8b1Caf2e10dE76fb67E82C2485E7d4fA098C53`
    - Collateral: USD0/USD0++

22. swBTC Controller
    - Address: `0x276B8C8873079eEACCF4Dd241De14be92D733b45`
    - Collateral: swBTC

23. ynETH Controller
    - Address: `0xdC5D5EE1223D4C8b7eAc8e876793f2171e7e8dEb`
    - Collateral: ynETH

24. Second ynETH Controller
    - Address: `0x143985860EFaeAcB92Db23E4b0c4d66Be51b08D2`
    - Collateral: ynETH

25. Reverse ynETH Controller
    - Address: `0x757C61d89bD0406BfcBB68178BBfaE79ECa46c0f`
    - Borrowed: ynETH
    - Collateral: crvUSD

26. LBTC Controller
    - Address: `0xC28C2FD809FC1795f90de1C9dA2131434A77721d`
    - Collateral: Lombard Staked Bitcoin (LBTC)

27. RCH Controller
    - Address: `0xf8C27436B277734AAA726A8fD5e6D7daDe0296c5`
    - Collateral: RCH Token (RCH)

28. XAUM Controller
    - Address: `0xB4544e705665e0856961a51F7E86Ccf633404b86`
    - Collateral: Matrixdock Gold (XAUM)

## Contract Functions

### Factory Contract
- `controllers(uint256)`: Returns controller address by index
- `borrowed_tokens(uint256)`: Returns borrowed token address by index
- `collateral_tokens(uint256)`: Returns collateral token address by index
- `market_count()`: Returns total number of markets

### Controller Contract
- `amm()`: Returns AMM contract address
- `borrowed_token()` / `borrowedToken()`: Returns borrowed token address
- `collateral_token()` / `collateralToken()`: Returns collateral token address
- `loans(uint256)`: Returns user address by loan index
- `loan_exists(address)` / `loanExists(address)`: Checks if user has an active loan
- `debt(address)` / `debtOf(address)`: Returns user's debt amount
- `collateral(address)` / `collateralOf(address)`: Returns user's collateral amount

### AMM Contract
- `admin()`: Returns admin contract address

## Implementation Details
- Each controller manages a specific token pair
- Loans are tracked by user address in the controller
- Active loans can be found by:
  1. Iterating through `loans(uint256)` to get user addresses
  2. Checking `loan_exists(address)` for each user
  3. Getting debt/collateral amounts for active loans

## Current State
- All 28 controllers are deployed and functional
- Token prices are being successfully queried
- Loan querying implemented through controller->AMM->admin path
- Rate limiting implemented for both Infura and Etherscan APIs

## Next Steps
1. Implement historical loan analysis
2. Add support for proxy contract patterns
3. Include liquidation event monitoring
4. Add more detailed token analytics
5. Implement WebSocket support for real-time updates