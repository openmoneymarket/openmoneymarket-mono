from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class PrepICXDelegations(TypedDict):
    _address: Address
    _votes_in_per: int
    _votes_in_icx: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int


class SystemInterface(InterfaceScore):
    @interface
    def getPRep(self, address: Address) -> dict:
        pass


class BoostedOmmInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def getLocked(self, _user: Address) -> dict:
        pass

    @interface
    def getTotalLocked(self) -> int:
        pass


class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: int) -> int:
        pass


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def updatePrepDelegations(self, _delegations: List[PrepDelegations]):
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass


class GovernanceContractInterface(InterfaceScore):
    @interface
    def getPRep(self, address: Address) -> dict:
        pass
