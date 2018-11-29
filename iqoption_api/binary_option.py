import asyncio
import time
import datetime
from .option import Option

class BinaryOption(Option):

    _type = "binary"


    async def get_expiration_list(self):
        server_time = int(self._parent._server_time/1000)

        if server_time%60 < 30:
            closest_minute_expiration = server_time-server_time%60+60
        else:
            closest_minute_expiration = server_time-server_time%60+120
        
        expirations_1M = [closest_minute_expiration+i*60 for i in range(5)]
        expirations_15M = [int(key) for key, value in self._option["bet_close_time"].items() if self._parent._server_time/1000 < int(key)-self._deadtime and value["enabled"] and self._option["exp_time"] == 900]
        expiration_EOD = 0
        expiration_EOW = 0
        expiration_EOM = 0
        for key, value in self._option["special"].items():
            if value["title"].endswith("End of day"):
                expiration_EOD = int(key)
            elif value["title"].endswith("End of week"):
                expiration_EOW = int(key)
            elif value["title"].endswith("End of month"):
                expiration_EOM = int(key)
        return {"1M":expirations_1M,"15M":expirations_15M,"EOD":expiration_EOD,"EOW":expiration_EOW,"EOM":expiration_EOM}

    async def buy_v2(self,price,direction,value,expiration,expiration_type,timeout=10):
        """ 
            expiration_type=1M,15M,EOD,EOW,EOM 
            direction=put or call
        """

        if expiration_type == "1M":
            sell_type = "turbo"
        else:
            sell_type ="binary"
        request_id = await self._parent.get_request_id(track_request=True)
        
        await self._parent.send_socket_message(
            "buyV2",
            {
                "price":price,
                "act":self._id,
                "exp":expiration,
                "type":sell_type,
                "direction":direction.lower(),
                "user_balance_id":self._parent._active_balance_id,
                "value":value,
                "time":int(self._parent._server_time/1000),
            },
            request_id,
        )
        return await self._parent.return_response_if_response_for_request_id_processed(request_id,timeout)
    
    def get_expiration_list_sync(self):
        return asyncio.run_coroutine_threadsafe(self.get_expiration_list(),self._parent._async_loop).result()
    
    def buy_v2_sync(self,price,direction,value,expiration,expiration_type,timeout=10):
        return asyncio.run_coroutine_threadsafe(self.buy_v2(price,direction,value,expiration,expiration_type,timeout=timeout),self._parent._async_loop).result()
    