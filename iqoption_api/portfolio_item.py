import time

class PortfolioItem(object):

    def __init__(self,portfolio_item,option):
        portfolio_item["amount"] = portfolio_item["amount"]/10**option._precision
        self.__dict__ = portfolio_item
        self._option = option
    
    async def sell(self):
        await self._option._parent.sendMessage({"name":"sell-options","version":"2.0","body":{"options_ids":[self.id]}})
