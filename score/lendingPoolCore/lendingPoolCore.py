from iconservice import *
from .ReserveData import *
from .UserData import *
from .Math import *

TAG = 'LendingPoolCore'

RESERVE_DB_PREFIX = b'reserve'
USER_DB_PREFIX = b'userReserve'
SECONDS_PER_YEAR = 31536000


class ReserveAttributes(TypedDict):
    reserveAddress: Address
    oTokenAddress: Address
    totalBorrows: int
    lastUpdateTimestamp: int
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex:int
    baseLTVasCollateral: int
    liquidationThreshold: int
    liquidationBonus: int
    decimals: int
    borrowingEnabled: bool
    usageAsCollateralEnabled: bool
    isFreezed: bool
    isActive: bool

class UserDataAttributes(TypedDict):
    reserveAddress: Address
    userAddress: Address
    principalBorrowBalance: int
    userBorrowCumulativeIndex:int
    lastUpdateTimestamp: int
    originationFee: int
    useAsCollateral: bool

class Constant(TypedDict):
    reserve: Address
    optimalUtilizationRate: int
    baseBorrowRate: int
    slopeRate1: int
    slopeRate2:int

# An interface to oToken
class oTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _user: Address) -> int:
        pass

class LendingPoolCore(IconScoreBase):
 
    ID = 'id'
    RESERVE_LIST = 'reserveList'
    CONSTANTS = 'constants'
     
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.id = VarDB(self.ID, db, str)
        self.reserveList = ArrayDB(self.RESERVE_LIST, db, value_type = Address)
        self._constants = DictDB(self.CONSTANTS, db, value_type = int , depth = 2)
        self.reserve = ReserveDataDB(db)
        self.userReserve = UserReserveDataDB(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed = 3)
    def ReserveUpdated(self, _reserve: Address, _liquidityRate: int, _borrowRate: int, _liquidityCumulativeIndex: int, _borrowCumulativeIndex: int ):
        pass

    @external
    def set_id(self, _val: str):
        self.id.set(_val)

    @external(readonly=True)
    def get_id(self) -> str:
        return self.id.get()

    def reservePrefix(self, _reserveAddress: Address) -> bytes:
        return b'|'.join([RESERVE_DB_PREFIX, self.id.get().encode(), str(_reserveAddress).encode()])

    def userReservePrefix(self, _reserveAddress: Address, _userAddress: Address) -> bytes:
        return b'|'.join(
            [USER_DB_PREFIX, self.id.get().encode(), str(_reserveAddress).encode(), str(_userAddress).encode()])

    # Methods to update the states of a reserve
    @external
    def updateTotalBorrows(self, _reserveAddress: Address, _totalBorrows: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].totalBorrows.set(_totalBorrows)

    @external
    def updateLastUpdateTimestamp(self, _reserveAddress: Address, _lastUpdateTimestamp: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].lastUpdateTimestamp.set(_lastUpdateTimestamp)

    @external
    def updateLiquidityRate(self, _reserveAddress: Address, _liquidityRate: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].liquidityRate.set(_liquidityRate)

    @external
    def updateBorrowRate(self, _reserveAddress: Address, _borrowRate: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].borrowRate.set(_borrowRate)

    @external
    def updateBorrowCumulativeIndex(self, _reserveAddress: Address, _borrowCumulativeIndex: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].borrowCumulativeIndex.set(_borrowCumulativeIndex)

    @external
    def updateLiquidityCumulativeIndex(self, _reserveAddress: Address, _liquidityCumulativeIndex: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].liquidityCumulativeIndex.set(_liquidityCumulativeIndex)

    @external
    def updateBaseLTVasCollateral(self, _reserveAddress: Address, _baseLTVasCollateral: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].baseLTVasCollateral.set(_baseLTVasCollateral)

    @external
    def updateLiquidationThreshold(self, _reserveAddress: Address, _liquidationThreshold: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].liquidationThreshold.set(_liquidationThreshold)

    @external
    def updateLiquidationBonus(self, _reserveAddress: Address, _liquidationBonus: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].liquidationBonus.set(_liquidationBonus)

    @external
    def updateDecimals(self, _reserveAddress: Address, _decimals: int):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].decimals.set(_decimals)

    def updateBorrowingEnabled(self, _reserveAddress: Address, _borrowingEnabled: bool):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].borrowingEnabled.set(_borrowingEnabled)

    @external
    def updateUsageAsCollateralEnabled(self, _reserveAddress: Address, _usageAsCollateralEnabled: bool):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].usageAsCollateralEnabled.set(_usageAsCollateralEnabled)

    @external
    def updateIsFreezed(self, _reserveAddress: Address, _isFreezed: bool):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].isFreezed.set(_isFreezed)

    @external
    def updateIsActive(self, _reserveAddress: Address, _isActive: bool):
        prefix = self.reservePrefix(_reserveAddress)
        self.reserve[prefix].isActive.set(_isActive)

    # Update methods for user attributes for a specific reserve
    @external
    def updateUserPrincipalBorrowBalance(self, _reserveAddress: Address, _userAddress: Address,
                                          _principalBorrowBalance: int):
        prefix = self.userReservePrefix(_reserveAddress, _userAddress)
        self.userReservePrefix[prefix].principalBorrowBalance.set(_principalBorrowBalance)
    
    @external
    def updateUserBorrowCumulativeIndex(self, _reserveAddress: Address, _userAddress: Address,
                                          _userBorrowCumulativeIndex: int):
        prefix = self.userReservePrefix(_reserveAddress, _userAddress)
        self.userReservePrefix[prefix].userBorrowCumulativeIndex.set(_userBorrowCumulativeIndex)

    @external
    def updateUserLastUpdateTimestamp(self, _reserveAddress: Address, _userAddress: Address,
                                       _lastUpdateTimestamp: int):
        prefix = self.userReservePrefix(_reserveAddress, _userAddress)
        self.userReservePrefix[prefix].lastUpdateTimestamp.set(_lastUpdateTimestamp)

    @external
    def updateUserOriginationFee(self, _reserveAddress: Address, _userAddress: Address, _originationFee: int):
        prefix = self.userReservePrefix(_reserveAddress, _userAddress)
        self.userReservePrefix[prefix].originationFee.set(_originationFee)

    @external
    def updateUserReserveUseAsCollateral(self, _reserveAddress: Address, _userAddress: Address, _useAsCollateral: int):
        prefix = self.userReservePrefix(_reserveAddress, _userAddress)
        self.userReservePrefix[prefix].useAsCollateral.set(_useAsCollateral)

    def _check_reserve(self, _reserve: Address):
        if _reserve not in self.getReserves():
            return False
        else:
            return True

    @external(readonly=True)
    def getReserves(self) -> list:
        reserves = []
        for item in self.reserveList:
            reserves.append(item)
        return reserves

    def _addNewReserve(self, _res: Address):
        self.reserveList.put(_res)

    @external
    def addReserveData(self, _reserve: ReserveAttributes):
        reserve_data_obj = createReserveDataObject(_reserve)
        if not self._check_reserve(reserve_data_obj.reserveAddress):
            self._addNewReserve(reserve_data_obj.reserveAddress)
        prefix = self.reservePrefix(reserve_data_obj.reserveAddress)
        addDataToReserve(prefix, self.reserve, reserve_data_obj)

    @external(readonly=True)
    def getReserveData(self, _reserveAddress: Address) -> dict:
        if self._check_reserve(_reserveAddress):
            prefix = self.reservePrefix(_reserveAddress)
            response = getDataFromReserve(prefix, self.reserve)
            return response

    @external
    def addUserReserveData(self, _userReserveData: UserDataAttributes):
        user_reserve_data_object = createUserReserveDataObject(_userReserveData)
        if self._check_reserve(user_reserve_data_object.reserveAddress):
            prefix = self.userReservePrefix(user_reserve_data_object.reserveAddress,
                                            user_reserve_data_object.userAddress)
            addDataToUserReserve(prefix, self.userReserve, user_reserve_data_object)
        else:
            revert("Reserve error:The reserve is not added to pool")

    @external(readonly=True)
    def getUserReserveData(self, _reserveAddress: Address, _userAddress: Address) -> dict:
        if self._check_reserve(_reserveAddress):
            prefix = self.userReservePrefix(_reserveAddress, _userAddress)
            response = getDataFromUserReserve(prefix, self.userReserve)
            return response

    @external
    def enableAsCollateral(self, _reserve: Address, _baseLTVasCollateral: int, _liquidationThreshold: int, _liquidationBonus: int  ) -> None:
        self.updateUsageAsCollateralEnabled(_reserve, True)
        self.updateBaseLTVasCollateral(_reserve, _base_reserveLTVasCollateral)
        self.updateLiquidationThreshold(_reserve, _liquidationThreshold) 
        self.updateLiquidationBonus(_reserve, _liquidationBonus)

        reserveData = self.getReserveData(_reserve)
        if reserveData['liquidityCumulativeIndex'] == 0:
            self.updateLiquidityCumulativeIndex(_reserve, 10 ** 18)

    @external
    def disableAsCollateral(self, _reserve: Address) -> None:
        self.updateUsageAsCollateralEnabled(_reserve, False)

    @external
    def enableBorrowing(self, _reserve: Address) -> None:
        self.updateBorrowingEnabled(_reserve, True)

    @external
    def disableBorrowing(self, _reserve: Address) -> None:
        self.updateBorrowingEnabled(_reserve, False)


    # Internal calculations
    @external(readonly = True)
    def calculateLinearInterest(self, _rate: int, _lastUpdateTimestamp: int) ->int:
        timeDifference = (self.now() - _lastUpdateTimestamp) // 10**6
        timeDelta =  exaDiv(timeDifference, SECONDS_PER_YEAR)
        return exaMul(_rate, timeDelta) + EXA
    
    @external(readonly = True)
    def getPresentTimestamp(self) -> int:
        return self.now()

    @external(readonly = True)
    def calculateCompoundedInterest(self, _rate: int, _lastUpdateTimestamp: int) ->int:
        timeDifference = (self.now() - _lastUpdateTimestamp) // 10**6
        ratePerSecond =  _rate // SECONDS_PER_YEAR
        return exaPow((ratePerSecond + EXA), timeDifference)

    @external(readonly = True)
    def getNormalizedIncome(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        interest = self.calculateLinearInterest(reserveData['liquidityRate'],reserveData['lastUpdateTimestamp'])
        cumulated = exaMul( interest, reserveData['liquidityCumulativeIndex'])
        return cumulated

    @external
    def updateCumulativeIndexes(self, _reserve: Address) -> None:
        reserveData = self.getReserveData(_reserve)
        totalBorrows =  reserveData['totalBorrows']

        if totalBorrows > 0:
            cummulatedLiquidityInterest = self.calculateLinearInterest(reserveData['liquidityRate'],reserveData['lastUpdateTimestamp'])
            self.updateLiquidityCumulativeIndex(_reserve, exaMul(cummulatedLiquidityInterest, reserveData['liquidityCumulativeIndex']))
            cummulatedBorrowInterest = self.calculateCompoundedInterest(reserveData['borrowRate'],reserveData['lastUpdateTimestamp'])
            self.updateBorrowCumulativeIndex(_reserve, exaMul(cummulatedBorrowInterest, reserveData['borrowCumulativeIndex']) )

    def _increaseTotalBorrows(self, _reserve: Address, _amount: int) -> None:
        reserveData = self.getReserveData(_reserve)
        self.updateTotalBorrows(_reserve, reserveData['totalBorrows'] + _amount )

    def _decreaseTotalBorrows(self, _reserve: Address, _amount: int) -> None:
        reserveData = self.getReserveData(_reserve)
        self.updateTotalBorrows(_reserve, reserveData['totalBorrows'] - _amount )

    @external(readonly = True)
    def getCompoundedBorrowBalance(self, _reserve: Address, _user: Address) -> int:
        userReserveData = self.getUserReserveData(_reserve , _user)
        reserveData = self.getReserveData(_reserve)
        if userReserveData['principalBorrowBalance'] == 0:
            return 0
        
        cumulatedInterest = exaDiv( exaMul(self.calculateCompoundedInterest(reserveData['borrowRate'], reserveData['lastUpdateTimestamp']), reserveData['borrowCumulativeIndex']) , userReserveData['userBorrowCumulativeIndex'])
        compoundedBalance = exaMul(userReserveData['principalBorrowBalance'], cumulatedInterest)
        
        if compoundedBalance == userReserveData['principalBorrowBalance']:
            if userReserveData['lastUpdateTimestamp'] != self.block.timestamp:
                return userReserveData['principalBorrowBalance'] + 1

        return compoundedBalance

    @external(readonly = True)
    def getReserveAvailableLiquidity(self, _reserve: Address) -> int:
        reserveScore = self.create_interface_score(_reserve, ReserveInterface)
        balance= reserveScore.balanceOf(self.address)
        return balance

    @external(readonly = True)
    def getReserveTotalLiquidity(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        return self.getReserveAvailableLiquidity(_reserve) + reserveData['totalBorrows']

    @external(readonly = True)
    def getReserveNormalizedIncome(self, _reserve: Address) -> int:
        return self.getNormalizedIncome(_reserve)

    @external(readonly = True)
    def getReserveUtilizationRate(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        totalBorrows = reserveData['totalBorrows']
        
        if totalBorrows == 0:
            return 0
        
        totalLiquidity = self.getReserveTotalLiquidity(_reserve)

        return exaDiv(totalBorrows, perTotalLiquidity)
    
    @external(readonly = True)
    def getReserveConfiguration(self, _reserve) -> dict:
        reserveData = self.getReserveData(_reserve)
        response ={
            'decimals': reserveData['decimals'],
            'baseLTVasCollateral': reserveData['baseLTVasCollateral'],
            'liquidationThreshold': reserveData['liquidationThreshold'],
            'usageAsCollateralEnabled': reserveData['usageAsCollateralEnabled']

        }
        return response

    @external
    def updateReserveInterestRatesAndTimestampInternal(self, _reserve: Address, _liquidityAdded: int, _liquidityTaken: int) -> None:
        reserveData = self.getReserveData(_reserve)
        rate = self.calculateInterestRates(_reserve, self.getReserveAvailableLiquidity + _liquidityAdded - _liquidityTaken, reserveData['totalBorrows'] )
        self.updateLiquidityRate(_reserve, rate['liquidityRate'])
        self.updateBorrowRate(_reserve, rate['borrowRate'])
        self.updateLastUpdateTimestamp(_reserve, self.block.timestamp)

        self.ReserveUpdated(_reserve, rate['liquidityRate'], rate['borrowRate'], reserveData['liquidityCumulativeIndex'], reserveData['borrowCumulativeIndex'] )
    
    @external
    def setReserveConstants(self, _constants: List[Constant]) -> None:
        for constants in _constants:
            self._constants[(constants['reserve'])]['optimalUtilizationRate'] = constants['optimalUtilizationRate']
            self._constants[(constants['reserve'])]['baseBorrowRate'] = constants['baseBorrowRate']
            self._constants[(constants['reserve'])]['slopeRate1'] = constants['slopeRate1']
            self._constants[(constants['reserve'])]['slopeRate2'] = constants['slopeRate2']
    
   

    @external(readonly = True)
    def getReserveConstants(self, _reserve: Address) -> dict:
        data = {
            'optimalUtilizationRate' : self._constants[_reserve]['optimalUtilizationRate'],
            'baseBorrowRate' : self._constants[_reserve]['baseBorrowRate'],
            'slopeRate1' : self._constants[_reserve]['slopeRate1'],
            'slopeRate2' : self._constants[_reserve]['slopeRate2'] 
        }

        return data

    @external
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int, _isFirstDeposit: bool) -> None:
        self.updateCumulativeIndexes(_reserve)
        self.updateReserveInterestRatesAndTimestampInternal(_reserve,_amount,0)

        if _isFirstDeposit:
            self.setUserUseReserveAsCollateral(_reserve, _user, True)

    @external
    def setUserUseReserveAsCollateral(self, _reserve: Address, _user: Address, _useAsCollateral: bool) -> None:
        self.updateUserReserveUseAsCollateral(_reserve, _user, _useAsCollateral)

    @external
    def getUserUnderlyingAssetBalance(self, _reserve: Address, _user: Address) -> None:
        reserveData = self.getReserveData(_reserve)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], oTokenInterface)
        balance = oToken.balanceOf(_user)
        return balance

    @external(readonly = True)
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        userReserveData = self.getUserReserveData(_reserve, _user)
        underlyingBalance = self.getUserUnderlyingAssetBalance(_reserve, _user)
        if userReserveData['principalBorrowBalance'] == 0:
            response ={
                'underlyingBalance': underlyingBalance,
                'compoundedBorrowBalance': 0,
                'originationFee': 0,
                'useAsCollateral': userReserveData['useAsCollateral']
            }
            return response

        compoundedBorrowBalance = self.getCompoundedBorrowBalance(_reserve, _user)
        response ={
                'underlyingBalance': underlyingBalance,
                'compoundedBorrowBalance': compoundedBorrowBalance,
                'originationFee': userReserveData['priginationFee'],
                'useAsCollateral': userReserveData['useAsCollateral']
            }
        return response

    
    @external(readonly = True)
    def calculateInterestRates(self, _reserve: Address, _availableLiquidity: int, _totalBorrows: int  )-> dict:
        constants = self.getReserveConstants(_reserve)
        rate = {}
           
        if(_totalBorrows == 0 and _availableLiquidity == 0 ):
            utilizationRate = 0
        else:
            utilizationRate = exaDiv(_totalBorrows , (_totalBorrows + _availableLiquidity))

        if utilizationRate < constants['optimalUtilizationRate']:
            rate['borrowRate'] = constants['baseBorrowRate'] + exaMul( exaDiv(utilizationRate , constants['optimalUtilizationRate']), constants['slopeRate1'])
        else:
            rate['borrowRate'] =  constants['baseBorrowRate'] + constants['slopeRate1']+ exaMul(exaDiv((utilizationRate - constants['optimalUtilizationRate'] ), (EXA - constants['optimalUtilizationRate'])), constants['slopeRate2'])
        
        rate['lendingRate'] = exaMul( exaMul(rate['borrowRate'], utilizationRate), 9 * EXA // 10 )

        return rate

        

        
  


    



