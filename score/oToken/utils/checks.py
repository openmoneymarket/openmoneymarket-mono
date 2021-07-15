from iconservice import *

TAG = "oToken"


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['lendingPool']:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (lendingPool){self._addresses['lendingPool']}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_liquidation(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['liquidationManager']:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (liquidation){self._addresses['liquidationManager']}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper


def origin_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.tx.origin != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.txn.origin} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper
