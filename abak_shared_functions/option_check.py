from .exceptions import Sorry
def option_not_none(param, value):
    if value is None:
        raise Sorry(param + ' cannot be empty')