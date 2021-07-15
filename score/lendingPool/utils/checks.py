from iconservice import *

TAG = 'LendingPool'


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper

def only_address_provider(func):
    if not isfunction(func):
        revert(f"{TAG}: NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['addressProvider']:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper

