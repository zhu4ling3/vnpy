from ..ibapi.client import EClient
from ..ibapi.wrapper import EWrapper



class IbApi(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
    #     self.thread = Thread(target=self.run, name='ibgw-runner')
    #
    #
    #
    # def start(self):
    #     if self.isConnected()==True:
    #         self.thread.start()
    #     else:
    #         raise Exception('start() method must be called after connection')
