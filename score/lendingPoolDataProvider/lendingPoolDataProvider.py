from .Math import *
from .utils.checks import *

HEALTH_FACTOR_LIQUIDATION_THRESHOLD = 10 ** 18
LENDING_POOL_CORE = 'lendingPoolCore'
LENDING_POOL = 'lendingPool'
LIQUIDATION_MANAGER = 'liquidationManager'
PRICE_ORACLE = 'priceOracle'
STAKING = 'staking'
FEE_PROVIDER = 'feeProvider'
REWARDS = 'rewards'


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int
    decimals: int


class RewardPercentage(TypedDict):
    reserve: Address
    rewardPercentage: int
    lendingPercentage: int
    borrowingPercentage: int


class DistPercentage(TypedDict):
    recipient: str
    distPercentage: int


class AddressDetails(TypedDict):
    name: str
    address: Address


# An interface to fee provider
class FeeProviderInterface(InterfaceScore):
    @interface
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        pass

    @interface
    def getLoanOriginationFeePercentage(self) -> int:
        pass


# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

    @interface
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getUserBorrowBalances(self, _reserve: Address, _user: Address) -> dict:
        pass


# An interface to PriceOracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


# An interface to oToken
class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        pass

    @interface
    def getUserBorrowCumulativeIndex(self, _user: Address) -> int:
        pass

    @interface
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        pass

    @interface
    def totalSupply(self) -> int:
        pass


# An interface to LendingPool
class LendingPoolInterface(InterfaceScore):
    @interface
    def getBorrowWallets(self, _index: int) -> list:
        pass

    @interface
    def getLoanOriginationFeePercentage(self) -> int:
        pass



# An interface to liquidation manager
class LiquidationInterface(InterfaceScore):
    @interface
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass

    @interface
    def getUserUnstakeInfo(self, _address: Address) -> list:
        pass


class RewardInterface(InterfaceScore):

    @interface
    def getRecipients(self) -> list:
        pass

    @interface
    def getAllDistributionPercentage(self) -> dict:
        pass

    @interface
    def assetDistPercentage(self, asset: Address) -> int:
        pass


class LendingPoolDataProvider(IconScoreBase):
    _SYMBOL = 'symbol'
    _REWARD_PERCENTAGE = 'rewardPercentage'
    _CONTRACTS = 'contracts'
    _ADDRESSES = 'addresses'
    _BORROW_PERCENTAGE_THRESHOLD = "borrowPercentageThreshold"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._symbol = DictDB(self._SYMBOL, db, value_type=str)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)
        self._borrowPercentageThreshold = VarDB(self._BORROW_PERCENTAGE_THRESHOLD, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmLendingPoolDataProvider"

    @only_owner
    @external
    def setSymbol(self, _reserve: Address, _sym: str):
        self._symbol[_reserve] = _sym

    @external(readonly=True)
    def getSymbol(self, _reserve: Address) -> str:
        return self._symbol[_reserve]

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @only_owner
    @external
    def setBorrowPercentage(self, _borrowPercentage: int) -> None:
        if not (0 < _borrowPercentage <= EXA):
            revert(f'{TAG}: BorrowPercentage cannot exceed 100% and be less or equal to zero')
        self._borrowPercentageThreshold.set(_borrowPercentage)

    @external(readonly=True)
    def getBorrowPercentage(self) -> int:
        return self._borrowPercentageThreshold.get()

    @external(readonly=True)
    def getRecipients(self) -> list:
        reward = self.create_interface_score(self._addresses["rewards"], RewardInterface)
        return reward.getRecipients()

    @external(readonly=True)
    def getDistPercentages(self) -> dict:
        reward = self.create_interface_score(self._addresses["rewards"], RewardInterface)
        return reward.getAllDistributionPercentage()

    @external(readonly=True)
    def getReserveAccountData(self) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        oracle = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
        todayRate = staking.getTodayRate()
        totalLiquidityBalanceUSD = 0
        totalCollateralBalanceUSD = 0
        totalBorrowBalanceUSD = 0
        availableLiquidityBalanceUSD = 0
        reserves = core.getReserves()

        for _reserve in reserves:
            symbol = self._symbol[_reserve]
            reserveData = core.getReserveData(_reserve)
            reserveDecimals = reserveData['decimals']
            reservePrice = oracle.get_reference_data(symbol, 'USD')
            if symbol == 'ICX':
                reservePrice = exaMul(reservePrice, todayRate)
            reserveTotalLiquidity = reserveData['totalLiquidity']
            reserveAvailableLiquidity = reserveData['availableLiquidity']
            reserveTotalBorrows = reserveData['totalBorrows']

            if reserveDecimals != 18:
                reserveTotalLiquidity = convertToExa(reserveTotalLiquidity, reserveDecimals)
                reserveAvailableLiquidity = convertToExa(reserveAvailableLiquidity, reserveDecimals)
                reserveTotalBorrows = convertToExa(reserveAvailableLiquidity, reserveDecimals)

            totalLiquidityBalanceUSD += exaMul(reserveTotalLiquidity, reservePrice)
            availableLiquidityBalanceUSD += exaMul(reserveAvailableLiquidity, reservePrice)
            totalBorrowBalanceUSD += exaMul(reserveTotalBorrows, reservePrice)
            if reserveData['usageAsCollateralEnabled']:
                totalCollateralBalanceUSD += exaMul(reserveTotalLiquidity, reservePrice)

        return {
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'availableLiquidityBalanceUSD': availableLiquidityBalanceUSD,
            'totalBorrowsBalanceUSD': totalBorrowBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,
        }

    @external(readonly=True)
    def getUserAccountData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        oracle = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
        todaySicxRate = staking.getTodayRate()
        totalLiquidityBalanceUSD = 0
        totalCollateralBalanceUSD = 0
        currentLtv = 0
        currentLiquidationThreshold = 0
        totalBorrowBalanceUSD = 0
        totalFeesUSD = 0

        reserves = core.getReserves()
        for _reserve in reserves:
            userBasicReserveData = core.getUserBasicReserveData(_reserve, _user)
            if userBasicReserveData['underlyingBalance'] == 0 and userBasicReserveData['compoundedBorrowBalance'] == 0:
                continue

            reserveConfiguration = core.getReserveConfiguration(_reserve)
            reserveDecimals = reserveConfiguration['decimals']

            # converting the user balances into 18 decimals
            if reserveDecimals != 18:
                userBasicReserveData['underlyingBalance'] = convertToExa(userBasicReserveData['underlyingBalance'],
                                                                         reserveDecimals)
                userBasicReserveData['compoundedBorrowBalance'] = convertToExa(
                    userBasicReserveData['compoundedBorrowBalance'], reserveDecimals)
                userBasicReserveData['originationFee'] = convertToExa(userBasicReserveData['originationFee'],
                                                                      reserveDecimals)

            symbol = self._symbol[_reserve]
            reserveConfiguration['reserveUnitPrice'] = oracle.get_reference_data(symbol, 'USD')
            if symbol == 'ICX':
                reserveConfiguration['reserveUnitPrice'] = exaMul(reserveConfiguration['reserveUnitPrice'],
                                                                  todaySicxRate)

            if userBasicReserveData['underlyingBalance'] > 0:
                liquidityBalanceUSD = exaMul(reserveConfiguration['reserveUnitPrice'],
                                             userBasicReserveData['underlyingBalance'])
                totalLiquidityBalanceUSD += liquidityBalanceUSD

                if reserveConfiguration['usageAsCollateralEnabled'] and userBasicReserveData['useAsCollateral']:
                    totalCollateralBalanceUSD += liquidityBalanceUSD
                    currentLtv += exaMul(liquidityBalanceUSD, reserveConfiguration['baseLTVasCollateral'])
                    currentLiquidationThreshold += exaMul(liquidityBalanceUSD,
                                                          reserveConfiguration['liquidationThreshold'])

            if userBasicReserveData['compoundedBorrowBalance'] > 0:
                totalBorrowBalanceUSD += exaMul(reserveConfiguration['reserveUnitPrice'],
                                                userBasicReserveData['compoundedBorrowBalance'])
                totalFeesUSD += exaMul(reserveConfiguration['reserveUnitPrice'], userBasicReserveData['originationFee'])

        if totalCollateralBalanceUSD > 0:
            currentLtv = exaDiv(currentLtv, totalCollateralBalanceUSD)
            currentLiquidationThreshold = exaDiv(currentLiquidationThreshold, totalCollateralBalanceUSD)
        else:
            currentLtv = 0
            currentLiquidationThreshold = 0

        healthFactor = self.calculateHealthFactorFromBalancesInternal(totalCollateralBalanceUSD, totalBorrowBalanceUSD,
                                                                      totalFeesUSD, currentLiquidationThreshold)
        healthFactorBelowThreshold = healthFactor < HEALTH_FACTOR_LIQUIDATION_THRESHOLD and healthFactor != - 1

        borrowingPower = self.calculateBorrowingPowerFromBalancesInternal(totalCollateralBalanceUSD,
                                                                          totalBorrowBalanceUSD,
                                                                          totalFeesUSD, currentLiquidationThreshold)
        borrowsAllowedUSD = exaMul(totalCollateralBalanceUSD - totalFeesUSD, currentLtv)
        availableBorrowsUSD = borrowsAllowedUSD - totalBorrowBalanceUSD
        if availableBorrowsUSD < 0:
            availableBorrowsUSD = 0

        return {
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,
            'totalBorrowBalanceUSD': totalBorrowBalanceUSD,
            'totalFeesUSD': totalFeesUSD,
            'availableBorrowsUSD': availableBorrowsUSD,
            'currentLtv': currentLtv,
            'currentLiquidationThreshold': currentLiquidationThreshold,
            'healthFactor': healthFactor,
            'borrowingPower': borrowingPower,
            'healthFactorBelowThreshold': healthFactorBelowThreshold
        }

    @external(readonly=True)
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserveData = core.getReserveData(_reserve)
        dToken = self.create_interface_score(reserveData['dTokenAddress'], TokenInterface)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], TokenInterface)
        userReserveData = core.getUserReserveData(_reserve, _user)
        currentOTokenBalance = oToken.balanceOf(_user)
        principalOTokenBalance = oToken.principalBalanceOf(_user)
        userLiquidityCumulativeIndex = oToken.getUserLiquidityCumulativeIndex(_user)
        # principalBorrowBalance = userReserveData['principalBorrowBalance']
        principalBorrowBalance = dToken.principalBalanceOf(_user)
        # currentBorrowBalance = core.getCompoundedBorrowBalance(_reserve, _user)
        currentBorrowBalance = dToken.balanceOf(_user)
        borrowRate = reserveData['borrowRate']
        reserveDecimals = reserveData['decimals']
        liquidityRate = reserveData['liquidityRate']
        originationFee = userReserveData['originationFee']
        # userBorrowCumulativeIndex = userReserveData['userBorrowCumulativeIndex']
        userBorrowCumulativeIndex = dToken.getUserBorrowCumulativeIndex(_user)
        lastUpdateTimestamp = userReserveData['lastUpdateTimestamp']
        useAsCollateral = userReserveData['useAsCollateral']
        price_provider = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        symbol = self._symbol[_reserve]
        price = price_provider.get_reference_data(symbol, "USD")
        if symbol == "ICX":
            staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
            todaySicxRate = staking.getTodayRate()
            price = exaMul(price, todaySicxRate)
        else:
            todaySicxRate = None

        currentOTokenBalanceUSD = exaMul(convertToExa(currentOTokenBalance, reserveDecimals), price)
        principalOTokenBalanceUSD = exaMul(convertToExa(principalOTokenBalance, reserveDecimals), price)
        currentBorrowBalanceUSD = exaMul(convertToExa(currentBorrowBalance, reserveDecimals), price)
        principalBorrowBalanceUSD = exaMul(convertToExa(principalBorrowBalance, reserveDecimals), price)

        response = {
            'currentOTokenBalance': currentOTokenBalance,
            'currentOTokenBalanceUSD': currentOTokenBalanceUSD,
            'principalOTokenBalance': principalOTokenBalance,
            'principalOTokenBalanceUSD': principalOTokenBalanceUSD,
            'currentBorrowBalance': currentBorrowBalance,
            'currentBorrowBalanceUSD': currentBorrowBalanceUSD,
            'principalBorrowBalance': principalBorrowBalance,
            'principalBorrowBalanceUSD': principalBorrowBalanceUSD,
            'userLiquidityCumulativeIndex': userLiquidityCumulativeIndex,
            'borrowRate': borrowRate,
            'liquidityRate': liquidityRate,
            'originationFee': originationFee,
            'userBorrowCumulativeIndex': userBorrowCumulativeIndex,
            'lastUpdateTimestamp': lastUpdateTimestamp,
            'useAsCollateral': useAsCollateral,
            'exchangeRate': price,
            'decimals': reserveDecimals
        }

        if isinstance(todaySicxRate, int):
            response['sICXRate'] = todaySicxRate

        return response

    @external(readonly=True)
    def balanceDecreaseAllowed(self, _reserve: Address, _user: Address, _amount: int) -> bool:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserveConfiguration = core.getReserveConfiguration(_reserve)
        userReserveData = core.getUserReserveData(_reserve, _user)
        reserveLiquidationThreshold = reserveConfiguration['liquidationThreshold']
        reserveUsageAsCollateralEnabled = reserveConfiguration['usageAsCollateralEnabled']

        if not reserveUsageAsCollateralEnabled or not userReserveData['useAsCollateral']:
            return True

        userAccountData = self.getUserAccountData(_user)
        collateralBalanceUSD = userAccountData['totalCollateralBalanceUSD']
        borrowBalanceUSD = userAccountData['totalBorrowBalanceUSD']
        totalFeesUSD = userAccountData['totalFeesUSD']
        currentLiquidationThreshold = userAccountData['currentLiquidationThreshold']

        if reserveConfiguration['decimals'] != 18:
            _amount = convertToExa(_amount, reserveConfiguration['decimals'])

        if borrowBalanceUSD == 0:
            return True

        oracle = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        symbol = self._symbol[_reserve]
        price = oracle.get_reference_data(symbol, 'USD')
        if symbol == "ICX":
            staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
            todaySicxRate = staking.getTodayRate()
            price = exaMul(price, todaySicxRate)
        amountToDecreaseUSD = exaMul(price, _amount)
        collateralBalanceAfterDecreaseUSD = collateralBalanceUSD - amountToDecreaseUSD

        if collateralBalanceAfterDecreaseUSD == 0:
            return False

        liquidationThresholdAfterDecrease = exaDiv((exaMul(collateralBalanceUSD, currentLiquidationThreshold) - exaMul(
            amountToDecreaseUSD, reserveLiquidationThreshold)), collateralBalanceAfterDecreaseUSD)

        healthFactorAfterDecrease = self.calculateHealthFactorFromBalancesInternal(collateralBalanceAfterDecreaseUSD,
                                                                                   borrowBalanceUSD, totalFeesUSD,
                                                                                   liquidationThresholdAfterDecrease)

        return healthFactorAfterDecrease > HEALTH_FACTOR_LIQUIDATION_THRESHOLD

    @external(readonly=True)
    def calculateCollateralNeededUSD(self, _reserve: Address, _amount: int, _fee: int,
                                     _userCurrentBorrowBalanceUSD: int,
                                     _userCurrentFeesUSD: int, _userCurrentLtv: int) -> int:

        symbol = self._symbol[_reserve]
        price_provider = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        price = price_provider.get_reference_data(symbol, "USD")
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserveConfiguration = core.getReserveConfiguration(_reserve)
        if reserveConfiguration['decimals'] != 18:
            _amount = _amount * EXA // (10 ** reserveConfiguration["decimals"])
        if symbol == "ICX":
            staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
            todaySicxRate = staking.getTodayRate()
            price = exaMul(price, todaySicxRate)
        requestedBorrowUSD = exaMul(price, _amount)
        collateralNeededInUSD = exaDiv(_userCurrentBorrowBalanceUSD + requestedBorrowUSD,
                                       _userCurrentLtv) + _userCurrentFeesUSD
        return collateralNeededInUSD

    @external(readonly=True)
    def getUserAllReserveData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserves = core.getReserves()
        return {
            self._symbol[reserve]: self.getUserReserveData(reserve, _user)
            for reserve in reserves
        }

    @external(readonly=True)
    def getUserLiquidationData(self, _user: Address) -> dict:
        liquidationManager = self.create_interface_score(self._addresses[LIQUIDATION_MANAGER], LiquidationInterface)
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        price_provider = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        reserves = core.getReserves()
        userAccountData = self.getUserAccountData(_user)
        badDebt = 0
        if userAccountData['healthFactorBelowThreshold']:
            badDebt = liquidationManager.calculateBadDebt(userAccountData['totalBorrowBalanceUSD'],
                                                          userAccountData['totalFeesUSD'],
                                                          userAccountData['totalCollateralBalanceUSD'],
                                                          userAccountData['currentLtv'])

        borrows = {}
        collaterals = {}
        for _reserve in reserves:
            userReserveData = core.getUserBasicReserveData(_reserve, _user)
            reserveConfiguration = core.getReserveConfiguration(_reserve)
            reserveDecimals = reserveConfiguration['decimals']

            userBorrowBalance = convertToExa(userReserveData['compoundedBorrowBalance'],
                                             reserveDecimals)
            userReserveUnderlyingBalance = convertToExa(userReserveData['underlyingBalance'],
                                                        reserveDecimals)

            symbol = self._symbol[_reserve]
            price = price_provider.get_reference_data(symbol, "USD")
            if symbol == "ICX":
                staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
                todaySicxRate = staking.getTodayRate()
                price = exaMul(price, todaySicxRate)

            if userBorrowBalance > 0:
                if badDebt > exaMul(price, userBorrowBalance):
                    maxAmountToLiquidateUSD = exaMul(price, userBorrowBalance)
                    maxAmountToLiquidate = userReserveData['compoundedBorrowBalance']
                else:
                    maxAmountToLiquidateUSD = badDebt
                    maxAmountToLiquidate = convertExaToOther(exaDiv(badDebt, price), reserveDecimals)

                borrows[symbol] = {
                    'compoundedBorrowBalance': userReserveData['compoundedBorrowBalance'],
                    'compoundedBorrowBalanceUSD': exaMul(price, userBorrowBalance),
                    'maxAmountToLiquidate': maxAmountToLiquidate,
                    'maxAmountToLiquidateUSD': maxAmountToLiquidateUSD
                }
            if userReserveUnderlyingBalance > 0:
                collaterals[symbol] = {
                    'underlyingBalance': userReserveData['underlyingBalance'],
                    'underlyingBalanceUSD': exaMul(price, userReserveUnderlyingBalance)
                }

        return {
            'badDebt': badDebt,
            'borrows': borrows,
            'collaterals': collaterals
        }

    @external(readonly=True)
    def liquidationList(self, _index: int) -> dict:
        pool = self.create_interface_score(self._addresses[LENDING_POOL], LendingPoolInterface)
        wallets = pool.getBorrowWallets(_index)
        return {
            wallet: self.getUserLiquidationData(wallet)
            for wallet in wallets
            if self.getUserAccountData(wallet)['healthFactor'] < 10 ** 18
        }

    @staticmethod
    def calculateHealthFactorFromBalancesInternal(_collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                  _totalFeesUSD: int, _liquidationThreshold: int) -> int:
        if _borrowBalanceUSD == 0:
            return -1
        healthFactor = exaDiv(exaMul(_collateralBalanceUSD - _totalFeesUSD, _liquidationThreshold), _borrowBalanceUSD)
        return healthFactor

    @staticmethod
    def calculateBorrowingPowerFromBalancesInternal(_collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                    _totalFeesUSD: int, _ltv: int) -> int:
        if _collateralBalanceUSD == 0:
            return 0
        borrowingPower = exaDiv(_borrowBalanceUSD, exaMul(_collateralBalanceUSD - _totalFeesUSD, _ltv))
        return borrowingPower

    @external(readonly=True)
    def getReserveData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        oracle = self.create_interface_score(self._addresses[PRICE_ORACLE], OracleInterface)
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        reserveData = core.getReserveData(_reserve)
        symbol = self._symbol[_reserve]

        dToken = self.create_interface_score(reserveData['dTokenAddress'], TokenInterface)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], TokenInterface)

        totalDeposited = oToken.totalSupply()
        totalBorrowed = dToken.totalSupply()
        borrowThreshold = self.getBorrowPercentage()
        totalAvailableBorrow = exaMul(borrowThreshold, totalDeposited)
        availableBorrow = totalAvailableBorrow - totalBorrowed
        reserveData["availableBorrows"] = availableBorrow if availableBorrow > 0 else 0
        price = oracle.get_reference_data(symbol, "USD")
        reserveData["exchangePrice"] = price
        if symbol == "ICX":
            staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
            reserveData['sICXRate'] = staking.getTodayRate()
            price = exaMul(staking.getTodayRate(), price)
        reserveDecimals = reserveData['decimals']

        reserveData["totalLiquidityUSD"] = exaMul(convertToExa(reserveData['totalLiquidity'], reserveDecimals), price)
        reserveData["availableLiquidityUSD"] = exaMul(convertToExa(reserveData['availableLiquidity'], reserveDecimals),
                                                      price)
        reserveData["totalBorrowsUSD"] = exaMul(convertToExa(reserveData['totalBorrows'], reserveDecimals), price)
        reserveData["lendingPercentage"] = rewards.assetDistPercentage(reserveData["oTokenAddress"])
        reserveData["borrowingPercentage"] = rewards.assetDistPercentage(reserveData["dTokenAddress"])
        reserveData["rewardPercentage"] = reserveData["lendingPercentage"] + reserveData["borrowingPercentage"]

        return reserveData

    @external(readonly=True)
    def getAllReserveData(self) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserves = core.getReserves()
        return {
            self._symbol[reserve]: self.getReserveData(reserve)
            for reserve in reserves
        }

    @external(readonly=True)
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        return core.getReserveConfiguration(_reserve)

    @external(readonly=True)
    def getAllReserveConfigurationData(self) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserves = core.getReserves()
        return {
            self._symbol[reserve]: core.getReserveConfiguration(reserve)
            for reserve in reserves
        }

    @external(readonly=True)
    def getUserUnstakeInfo(self, _address: Address) -> list:
        staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
        unstakeDetails = staking.getUserUnstakeInfo(_address)
        response = []
        for unstakedRecords in unstakeDetails:
            if unstakedRecords['from'] == self._addresses[LENDING_POOL_CORE]:
                unstake = {'amount': unstakedRecords["amount"], 'unstakingBlockHeight': unstakedRecords["blockHeight"]}
                response.append(unstake)
        return response

    @external(readonly=True)
    def getLoanOriginationFeePercentage(self) -> int:
        feeProvider = self.create_interface_score(self._addresses[FEE_PROVIDER], FeeProviderInterface)
        return feeProvider.getLoanOriginationFeePercentage()

    @external(readonly=True)
    def getRealTimeDebt(self, _reserve: Address, _user: Address) -> int:
        userReserveData = self.getUserReserveData(_reserve, _user)
        return userReserveData['currentBorrowBalance'] + userReserveData['originationFee']

    @external(readonly=True)
    def getAssetPrincipalSupply(self, _asset: Address, _user: Address) -> SupplyDetails:
        token = create_interface_score(_asset, TokenInterface)
        supply = token.getPrincipalSupply(_user)
        decimals = supply['decimals']
        supply['principalUserBalance'] = convertToExa(supply['principalUserBalance'], decimals)
        supply['principalTotalSupply'] = convertToExa(supply['principalTotalSupply'], decimals)
        return supply
