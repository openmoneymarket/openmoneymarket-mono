from .interfaces import *
from .utils.checks import *

LENDING_POOL_CORE = 'lendingPoolCore'
OMM_TOKEN = 'ommToken'
SICX = 'sICX'
STAKING = 'staking'
BOOSTED_OMM = 'bOMM'


class Addresses(IconScoreBase):
    _ADDRESSES = 'addresses'
    _CONTRACTS = 'contracts'
    _ADDRESS_PROVIDER = 'addressProvider'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._addressProvider = VarDB(self._ADDRESS_PROVIDER, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)

    def on_install(self, _address: Address) -> None:
        super().on_install()
        self._addressProvider.set(_address)

    @only_address_provider
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @external(readonly=True)
    def getAddress(self, _name: str) -> Address:
        return self._addresses[_name]

    @external(readonly=True)
    def getAddressProvider(self) -> Address:
        return self._addressProvider.get()
