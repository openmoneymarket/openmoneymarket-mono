import json

from checkscore.repeater import retry
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

from .configurations import *
from .test_integrate_utils import TestUtils

RE_DEPLOY_CONTRACT = []
SCORE_ADDRESS = "scoreAddress"

class OMMTestBase(TestUtils):
    DIR = ROOT

    CONTRACTS = ['addressProvider', 'daoFund', 'delegation', 'lendingPool', 'feeProvider',
                 'lendingPoolCore', 'lendingPoolDataProvider', 'liquidationManager', 'stakedLp',
                 'ommToken', 'priceOracle', 'rewardDistribution', 'governance', 'workerToken']
    OTOKENS = ['oUSDS', 'oICX']
    DTOKENS = ['dUSDS', 'dICX']

    def setUp(self):
        self._wallet_setup()
        self.icon_service = IconService(HTTPProvider(SERVER_URL, 3))
        super().setUp(
            network_only=True,
            icon_service=self.icon_service,  # aws tbears
            nid=NID,
            tx_result_wait=5
        )
        print(f"balanace------setup------${self.icon_service.get_balance(self.deployer_wallet.get_address())}")
        self.contracts = {}
        # self._deploy_contracts()
        with open(CONTRACT_ADDRESSES, "r") as file:
            self.contracts = json.load(file)
            self.contracts['bandOracle'] = BAND_ORACLE # dummy oracle for liquidation test 
        for contract in RE_DEPLOY_CONTRACT:
            self._update_contract(contract)

    def tearDown(self):
        print(f"balanace-----teardown-------${self.icon_service.get_balance(self.deployer_wallet.get_address())}")

    def _deploy_contracts(self):
        if os.path.exists(CONTRACT_ADDRESSES) is False:
            print(f'{CONTRACT_ADDRESSES} does not exists')
            self._deploy_all()
            self._config_omm()
            self._supply_liquidity()

    def _wallet_setup(self):
        # self.deployer_wallet: 'KeyWallet' = self._test1
        self.deployer_wallet: 'KeyWallet' = KeyWallet.load(bytes.fromhex(keystore_private_key))

    def _deploy_all(self):
        txns = []

        for item in self.CONTRACTS:
            params = {}
            if item == "sample_token":
                params = {'_name': "BridgeDollars",
                          '_symbol': 'USDs', '_decimals': 18}
            elif item == "omm_token":
                params = {'_initialSupply': 0, '_decimals': 18}
            elif item == "workerToken":
                params = {'_initialSupply': 100, '_decimals': 18}
            elif item == "sicx":
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif item == "oToken":
                params = {"_name": "BridgeUSDInterestToken",
                          "_symbol": "oUSDs"}

            deploy_tx = self.build_deploy_tx(
                from_=self.deployer_wallet,
                to=self.contracts.get(item, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(self.DIR, item)),
                params=params
            )
            txns.append(deploy_tx)

        otxns = []
        param1 = {"_name": "OmmUSDsInterestToken", "_symbol": "oUSDs"}
        param2 = {"_name": "ICXinterestToken", "_symbol": "oICX"}
        # param3 = {"_name":"IconUSDInterest","_symbol":"oIUSDC","_decimals":6}
        deploy_oUSDs = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("oUSDS", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "oToken")),
            params=param1
        )
        deploy_oICX = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("oICX", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "oToken")),
            params=param2
        )
        # deploy_oIUSDc = self.build_deploy_tx(
        #   from_ = self.deployer_wallet,
        #   to = self.contracts.get("oIUSDC", SCORE_INSTALL_ADDRESS),
        #   content = os.path.abspath(os.path.join(self.DIR, "oToken")),
        #   params = param3
        #   )
        otxns.append(deploy_oUSDs)
        otxns.append(deploy_oICX)
        # otxns.append(deploy_oIUSDc)

        dtxns = []
        param1 = {"_name": "Omm USDS Debt Token", "_symbol": "dUSDS"}
        param2 = {"_name": "Omm ICX Debt Token", "_symbol": "dICX"}
        deploy_dUSDS = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("dUSDS", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "dToken")),
            params=param1
        )
        deploy_dICX = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("dICX", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "dToken")),
            params=param2
        )
        dtxns.append(deploy_dUSDS)
        dtxns.append(deploy_dICX)

        results = self.process_transaction_bulk(
            requests=txns,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        oresults = self.process_transaction_bulk(
            requests=otxns,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        dresults = self.process_transaction_bulk(
            requests=dtxns,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        for idx, tx_result in enumerate(results):
            # print(tx_result)
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.CONTRACTS[idx]] = tx_result[SCORE_ADDRESS]

        for idx, tx_result in enumerate(oresults):
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.OTOKENS[idx]] = tx_result[SCORE_ADDRESS]

        for idx, tx_result in enumerate(dresults):
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.DTOKENS[idx]] = tx_result[SCORE_ADDRESS]

        with open(CONTRACT_ADDRESSES, "w") as file:
            json.dump(self.contracts, file, indent=4)

    def _update_token_contract(self, contract, token):
        content = os.path.abspath(os.path.join(self.DIR, contract))
        update_contract = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(token),
            content=content,
            params={}
        )

        tx_hash = self.process_transaction(update_contract, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)

    def _update_contract(self, contract):

        content = os.path.abspath(os.path.join(self.DIR, contract))
        deploy_contract = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
            content=content,
            params={}
        )
        print(contract)

        tx_hash = self.process_transaction(deploy_contract, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)

    def _config_omm(self):
        print("-------------------------------Configuring OMM----------------------------------------------------")
        with open(CONTRACT_ADDRESSES, "r") as file:
            self.contracts = json.load(file)
        self._deposit_for_fee_sharing()
        self._mint_bridge()
        self._config_address_provider()
        self._config_general()
        self._config_staking()
        self._config_rewards()
        self._add_reserves_to_lendingPoolCore()
        self._add_reserves_constants()

    def _config_address_provider(self):
        contracts = self.contracts
        contracts['bandOracle'] = "cx399dea56cf199b1c9e43bead0f6a284bdecfbf62"
        contract_details = [
            {'name': 'addressProvider', 'address': contracts['addressProvider']},
            {'name': 'daoFund', 'address': contracts['daoFund']},
            {'name': 'delegation', 'address': contracts['delegation']},
            {'name': 'feeProvider', 'address': contracts['feeProvider']},
            {'name': 'governance', 'address': contracts['governance']},
            {'name': 'lendingPool', 'address': contracts['lendingPool']},
            {'name': 'lendingPoolCore', 'address': contracts['lendingPoolCore']},
            {'name': 'lendingPoolDataProvider', 'address': contracts['lendingPoolDataProvider']},
            {'name': 'liquidationManager', 'address': contracts['liquidationManager']},
            {'name': 'ommToken', 'address': contracts['ommToken']},
            {'name': 'priceOracle', 'address': contracts['priceOracle']},
            {'name': 'bandOracle', 'address': contracts['bandOracle']},
            {'name': 'bridgeOToken', 'address': contracts['oUSDS']},
            {'name': 'rewards', 'address': contracts['rewardDistribution']},
            {'name': 'workerToken', 'address': contracts['workerToken']},
            {'name': 'sICX', 'address': contracts['sicx']},
            {'name': 'usds', 'address': contracts['usds']},
            {'name': 'staking', 'address': contracts['staking']},
            {'name': 'ousds', 'address': contracts['oUSDS']},
            {'name': 'dusds', 'address': contracts['dUSDS']},
            {'name': 'oICX', 'address': contracts['oICX']},
            {'name': 'dICX', 'address': contracts['dICX']},
            {'name': 'stakedLp', 'address': contracts['stakedLp']},
            {'name': 'dex', 'address': contracts['lpToken']}
            # {'name': 'diusdc', 'address': contracts['dIUSDC']},
            # {'name': 'oiusdc', 'address': contracts['oIUSDC']},
            # {'name': 'iusdc', 'address': contracts['iusdc']},
        ]

        setting_address_provider = [
            {'contract': 'addressProvider', 'method': 'setAddresses', 'params': {'_addressDetails': contract_details}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolCoreAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolDataProviderAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setLiquidationManagerAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setOmmTokenAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setoICXAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setoUSDsAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setdICXAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setdUSDsAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setDelegationAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setRewardAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setGovernanceAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setGovernanceAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setStakedLpAddresses', 'params': {}},
            {'contract': 'addressProvider', 'method': 'setPriceOracleAddress', 'params': {}},
        ]

        self._get_transaction(setting_address_provider)

    def _config_general(self):
        contracts = self.contracts
        settings = [
            {'contract': 'lendingPool', 'method': 'setFeeSharingTxnLimit', 'params': {'_limit': 3}},
            {'contract': 'feeProvider', 'method': 'setLoanOriginationFeePercentage',
             'params': {'_percentage': f"{LOAN_ORIGINATION_PERCENT}"}},
            {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol',
             'params': {'_reserve': contracts['usds'], '_sym': "USDS"}},
            {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol',
             'params': {'_reserve': contracts['sicx'], '_sym': "ICX"}},
            {'contract': 'priceOracle', 'method': 'setOraclePriceBool', 'params': {'_value': '0x0'}},
            {'contract': 'priceOracle', 'method': 'set_reference_data',
             'params': {'_base': 'USDS', '_quote': 'USD', '_rate': 1 * 10 ** 18}},
            {'contract': 'priceOracle', 'method': 'set_reference_data',
             'params': {'_base': 'ICX', '_quote': 'USD', '_rate': 10 * 10 ** 17}},
            {'contract': 'delegation', 'method': 'addAllContributors', 'params': {'_preps': PREP_LIST}},
            {'contract': 'governance', 'method': 'setStartTimestamp', 'params': {'_timestamp': TIMESTAMP}},
            {'contract': 'ommToken', 'method': 'setMinimumStake', 'params': {'_min': 10 * 10 ** 18}},
            {'contract': 'stakedLp', 'method': 'addPool',
             'params': {'_pool': contracts['sicx'], '_id': f"{OMM_SICX_ID}"}},
            {'contract': 'stakedLp', 'method': 'addPool',
             'params': {'_pool': contracts['usds'], '_id': f"{OMM_USDS_ID}"}},
            # {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['iusdc'],'_sym':"USDC"}},
            # {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'IUSDC','_quote':'USD','_rate':10*10**17}},  
            # {'contract':  'stakedLp', 'method': 'addPool','params': {'_pool': contracts['iusdc'] , '_id': OMM_USDC_ID}}
        ]

        self._get_transaction(settings)

    def _deposit_for_fee_sharing(self):
        contracts = ['usds', 'lendingPool']
        for contract in contracts:
            print(
                f"-------------------------------Deposit fee sharing amount to {contract}----------------------------------")
            deposit_fee = self.deposit_tx(self.deployer_wallet, self.contracts[contract])
            tx_hash = self.process_transaction(deposit_fee, self.icon_service)
            tx_result = self.get_tx_result(tx_hash['txHash'])
            self.assertEqual(True, tx_hash['status'])

    def _mint_bridge(self):
        param = {
            '_to': self.deployer_wallet.get_address(),
            '_value': 1000000 * 10 ** 18
        }
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts['usds'],
            method="mint",
            params=param
        )
        self.assertEqual(True, tx_result['status'])

    def _add_reserves_constants(self):
        print(
            "-------------------------------Configuring LENDING POOL CORE RESERVE SETTINGS VIA GOVERNANCE ----------------------------------------------------")

        contracts = self.contracts
        settings_reserves = [{'contract': 'governance',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['usds'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"2{'0' * 16}",
                                                         "slopeRate1": f"6{'0' * 16}",
                                                         "slopeRate2": f"1{'0' * 18}"}]}},
                             {'contract': 'governance',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['sicx'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"0{'0' * 17}",
                                                         "slopeRate1": f"8{'0' * 16}",
                                                         "slopeRate2": f"2{'0' * 18}"}]}}
                             # {'contract': 'lendingPoolCore',
                             #  'method': 'setReserveConstants',
                             #  'params' :{"_constants": [{"reserve":contracts['iusdc'],
                             #                              "optimalUtilizationRate":f"8{'0'*17}",
                             #                             "baseBorrowRate":f"2{'0'*16}",
                             #                             "slopeRate1":f"6{'0'*16}",
                             #                             "slopeRate2":f"1{'0'*18}"} ]}}
                             ]

        self._get_transaction(settings_reserves)

    def _config_rewards(self):
        print("-------------------------------Configuring REWARDS ----------------------------------------------------")

        contracts = self.contracts
        settings_rewards = [
            {'contract': 'rewardDistribution', 'method': 'configureAssetEmission',
             'params': {
                 "_assetConfig":
                     [
                         {"asset": contracts["oUSDS"], "distPercentage": f"{OUSDS_EMISSION}"},
                         {"asset": contracts["dUSDS"], "distPercentage": f"{DUSDS_EMISSION}"},
                         {"asset": contracts["dICX"], "distPercentage": f"{DICX_EMISSION}"},
                         {"asset": contracts["oICX"], "distPercentage": f"{OICX_EMISSION}"},
                         # {"asset": contracts["oIUSDC"], "distPercentage":f"{OIUSDC_EMISSION}"},
                         # {"asset": contracts["dIUSDC"], "distPercentage":f"{DIUSDC_EMISSION}"}
                     ]
             }
             },
            {'contract': 'rewardDistribution', 'method': 'configureLPEmission',
             'params': {
                 "_lpConfig":
                     [
                         {"_id": f"{OMM_SICX_ID}", "distPercentage": f"{OMM_SICX_DIST_PERCENTAGE}"},
                         {"_id": f"{OMM_USDS_ID}", "distPercentage": f"{OMM_USDS_DIST_PERCENTAGE}"},
                         # {"_id": f"{OMM_USDC_ID}", "distPercentage": f"{OMM_USDC_DIST_PERCENTAGE}"}
                     ]
             }
             },
            {'contract': 'rewardDistribution', 'method': 'configureOmmEmission',
             'params': {"_distPercentage": f"{OMM_DIST_PERCENTAGE}"}
             },
            {'contract': 'rewardDistribution', 'method': 'setDailyDistributionPercentage',
             'params': {"_recipient": "worker", "_percentage": f"{WORKER_DIST_PERCENTAGE}"}
             },
            {'contract': 'rewardDistribution', 'method': 'setDailyDistributionPercentage',
             'params': {"_recipient": "daoFund", "_percentage": f"{DAO_DIST_PERCENTAGE}"}
             },
            {'contract': 'lendingPoolDataProvider', 'method': 'setDistPercentages',
             'params': {
                 "_percentages": [
                     {'recipient': 'worker', 'distPercentage': f"{WORKER_DIST_PERCENTAGE}"},
                     {'recipient': 'daoFund', 'distPercentage': f"{DAO_DIST_PERCENTAGE}"}
                 ]
             }
             }
        ]

        self._get_transaction(settings_rewards)

    def _config_staking(self):
        print("-------------------------------Configuring STAKING----------------------------------------------------")

        contracts = self.contracts
        settings_staking = [
            {'contract': 'staking', 'method': 'setSicxAddress',
             'params': {'_address': contracts['sicx']}},
            {'contract': 'staking', 'method': 'toggleStakingOn',
             'params': {}}
        ]

        self._get_transaction(settings_staking)

    def _add_reserves_to_lendingPoolCore(self):
        print(
            "------------------------------- ADDING RESERVES TO LENDING POOL CORE VIA GOVERNANCE ----------------------------------------------------")

        contracts = self.contracts
        # params_iusdc ={
        #     "_reserve": {
        #         "reserveAddress":contracts['iusdc'],
        #         "oTokenAddress":contracts['oIUSDC'],
        #         "dTokenAddress": contracts['dIUSDC'],
        #         "lastUpdateTimestamp": "0",
        #         "liquidityRate":"0",
        #         "borrowRate":"0",
        #         "liquidityCumulativeIndex":f"1{'0'*18}",
        #         "borrowCumulativeIndex":f"1{'0'*18}",
        #         "baseLTVasCollateral":"500000000000000000",
        #         "liquidationThreshold":"650000000000000000",
        #         "liquidationBonus":"100000000000000000",
        #         "decimals":"6",
        #         "borrowingEnabled": "1",
        #         "usageAsCollateralEnabled":"1",
        #         "isFreezed":"0",
        #         "isActive":"1"
        #     } 
        # }

        params_usds = {
            "_reserve": {
                "reserveAddress": contracts['usds'],
                "oTokenAddress": contracts['oUSDS'],
                "dTokenAddress": contracts['dUSDS'],
                "lastUpdateTimestamp": "0",
                "liquidityRate": "0",
                "borrowRate": "0",
                "liquidityCumulativeIndex": f"1{'0' * 18}",
                "borrowCumulativeIndex": f"1{'0' * 18}",
                "baseLTVasCollateral": "500000000000000000",
                "liquidationThreshold": "650000000000000000",
                "liquidationBonus": "100000000000000000",
                "decimals": "18",
                "borrowingEnabled": "1",
                "usageAsCollateralEnabled": "1",
                "isFreezed": "0",
                "isActive": "1"
            }
        }

        params_icx = {
            "_reserve": {
                "reserveAddress": contracts['sicx'],
                "oTokenAddress": contracts['oICX'],
                "dTokenAddress": contracts['dICX'],
                "lastUpdateTimestamp": "0",
                "liquidityRate": "0",
                "borrowRate": "0",
                "liquidityCumulativeIndex": f"1{'0' * 18}",
                "borrowCumulativeIndex": f"1{'0' * 18}",
                "baseLTVasCollateral": "500000000000000000",
                "liquidationThreshold": "650000000000000000",
                "liquidationBonus": "100000000000000000",
                "decimals": "18",
                "borrowingEnabled": "1",
                "usageAsCollateralEnabled": "1",
                "isFreezed": "0",
                "isActive": "1"
            }
        }

        settings = [
            # {'contract': 'governance',
            #  'method': 'addReserveData', 'params': params_iusdc},
            {'contract': 'governance',
             'method': 'initializeReserve', 'params': params_usds},
            {'contract': 'governance',
             'method': 'initializeReserve', 'params': params_icx}
        ]
        self._get_transaction(settings)

    def _supply_liquidity(self):

        # deposit USDS
        depositData = {'method': 'deposit', 'params': {'amount': 50 * 10 ** 18}}

        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": 50 * EXA,
                  "_data": data}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["usds"],  # USDS contract
            method="transfer",
            params=params
        )
        self.assertEqual(tx_result['status'], 1)

        # deposit ICX
        params = {"_amount": 10 * 10 ** 18}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["lendingPool"],
            value=100 * 10 ** 18,
            method="deposit",
            params=params
        )
        self.assertEqual(tx_result['status'], 1)


    def _get_transaction(self, settings):
        txs = []
        contracts = self.contracts
        for sett in settings:
            print(
                f'Calling {sett["method"]}, with parameters {sett["params"]} on the {sett["contract"]} contract.')
            res = self.build_tx(self.deployer_wallet, to=contracts[sett['contract']], method=sett['method'],
                                params=sett['params'])
            txs.append(res)

        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        for tx_result in results:
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
