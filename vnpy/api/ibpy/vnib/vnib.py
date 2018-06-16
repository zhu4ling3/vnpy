
from ..ibapi.client import EClient
from ..ibapi.wrapper import EWrapper



class IbApi(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

