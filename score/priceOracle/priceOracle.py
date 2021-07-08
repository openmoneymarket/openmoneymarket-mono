from .utils.Math import convertToExa, exaMul
from .utils.checks import *


STABLE_TOKENS = ["USDS", "USDB"]

OMM_TOKENS = [
    {
        "name": "USDS",
        "priceOracleKey": "USDS",
        "convert": lambda _source, _amount, _decimals: convertToExa(_amount, _decimals)
    },
    {
        "name": "sICX",
        "priceOracleKey": "ICX",
        "convert": lambda _source, _amount, _decimals: exaMul(convertToExa(_amount, _decimals),
                                                              _source.getPriceByName("sICX/ICX"))
    },
    {
        "name": "IUSDC",
        "priceOracleKey": "USDC",
        "convert": lambda _source, _amount, _decimals: convertToExa(_amount, _decimals)
    }
]


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class AddressProviderInterface(InterfaceScore):
    @interface
    def getReserveAddresses(self) -> dict:
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def getPriceByName(self, _name: str) -> int:
        pass


class TokenInterface(InterfaceScore):
    @interface
    def decimals(self) -> int:
        pass


class PriceOracle(IconScoreBase):
    _PRICE = 'price'
    _BAND_ORACLE = 'bandOracle'
    _ORACLE_PRICE_BOOL = 'oraclePriceFeed'
    _DATA_SOURCE = 'data_source'
    _ADDRESS_PROVIDER = 'address_provider'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self._PRICE, db, value_type=int, depth=2)
        self._bandOracle = VarDB(self._BAND_ORACLE, db, value_type=Address)
        self._oraclePriceBool = VarDB(self._ORACLE_PRICE_BOOL, db, value_type=bool)
        self._dataSource = VarDB(self._DATA_SOURCE, db, value_type=Address)
        self._addressProvider = VarDB(self._ADDRESS_PROVIDER, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmPriceOracleProxy"

    @external
    @only_owner
    def setOraclePriceBool(self, _value: bool):
        self._oraclePriceBool.set(_value)

    @external(readonly=True)
    def getOraclePriceBool(self) -> bool:
        return self._oraclePriceBool.get()

    @external
    @only_owner
    def setBandOracle(self, _address: Address):
        self._bandOracle.set(_address)

    @external(readonly=True)
    def getBandOracle(self) -> Address:
        return self._bandOracle.get()

    @external
    @only_owner
    def setDataSource(self, _address: Address):
        self._dataSource.set(_address)

    @external(readonly=True)
    def getDataSource(self) -> Address:
        return self._dataSource.get()

    @external
    @only_owner
    def setAddressProvider(self, _address: Address):
        self._addressProvider.set(_address)

    @external(readonly=True)
    def getAddressProvider(self) -> Address:
        return self._addressProvider.get()

    @only_owner
    @external
    def set_reference_data(self, _base: str, _quote: str, _rate: int) -> None:
        self._price[_base][_quote] = _rate

    def _get_price(self, _base: str, _quote) -> int:
        if self._oraclePriceBool.get():
            if _base in STABLE_TOKENS:
                return 1 * 10 ** 18
            else:
                oracle = self.create_interface_score(self._bandOracle.get(), OracleInterface)
                price = oracle.get_reference_data(_base, _quote)
                return price['rate']        
        else:
            return self._price[_base][_quote]

    def _get_omm_price(self, _base: str, _quote: str) -> int:
        lp_token = self.create_interface_score(self.getDataSource(), DataSourceInterface)
        address_provider = self.create_interface_score(self.getAddressProvider(), AddressProviderInterface)
        reserve_addresses = address_provider.getReserveAddresses()

        _total_price = 0
        for token in OMM_TOKENS:
            name = token["name"]
            price_oracle_key = token["priceOracleKey"]

            _price = lp_token.getPriceByName(f"{_base}/{name}")

            _interface = self.create_interface_score(reserve_addresses[name], TokenInterface)
            _decimals = _interface.decimals()

            _adjusted_price = token["convert"](lp_token, _price, _decimals)
            _total_price += exaMul(_adjusted_price, self._get_price(price_oracle_key, _quote))

        return _total_price // len(OMM_TOKENS)

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote) -> int:
        if 'OMM' in _base:
            return self._get_omm_price(_base, _quote)
        else:
            return self._get_price(_base, _quote)
