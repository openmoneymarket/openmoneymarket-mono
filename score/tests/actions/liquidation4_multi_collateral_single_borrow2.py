from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
    "description": "4. Deposit 200 ICX, 800 USDs, Borrow 500 ICX, ICX price increases to $1.5, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "borrower",
            "amount": 2 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_USDS,
            "user": "borrower",
            "amount": 8 * EXA, # 100 deposit
            "expectedResult": 1
        },
        {
            "_step": Steps.DEPOSIT_ICX,
            "user": "liquidator",
            "amount": 12 * EXA,
            "expectedResult": 1
        },
        {
            "_step": Steps.BORROW_ICX,
            "user": "liquidator",
            "amount": 55 * EXA//10, #liquidator has enough funds get it back to 30
            "expectedResult": 1
        },
        {
           "_step": Steps.BORROW_ICX,
            "user": "borrower",
            "amount": 48 * EXA // 10,
            "expectedResult": 1
        },
        {
            "_step": Steps.UPDATE_PRICE,
            "action": "set_reference_data",
            "contract": "bandOracle",
            "user": "admin", 
            "rate": 15 * EXA // 10, 
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1.5 USD"
        },
        {
            "_step": Steps.LIQUIDATION,
            "user": "liquidator",
            "_reserve": "icx",
            "expectedResult": 1 # now, liquidator has enough sicx to call liquidation 
        }, 
    ]}