import asyncio
import time

class Option(object):

    _type = "option"

    def __init__(self, option, parent):
        self._id = option["id"]
        self._name = option["name"].split(".")[-1]
        self._group_id = option.get("group_id")
        self._min_bet = option.get("minimal_bet")
        self._max_bet = option.get("maximal_bet")
        self._precision = option.get("precision")
        self._is_enabled = option.get("enabled")
        self._schedule = option.get("schedule")
        self._image = option.get("image")
        self._parent = parent
        self._candle_update_rate = 1
        self._first_candles = {}
        self._candles = {}
        self._option = option.get("option")
        self._deadtime = option.get("deadtime")


        self._bid = 0
        self._ask = 0
        self._value = 0
        self._volume = 0
        self._show_value = 0
        self._buy = 0
        self._sell = 0
    
    async def is_valid_interval(self, interval):
        valid_intervals = list(self._first_candles.keys())
        if str(interval) in valid_intervals:
            return True

    async def get_candles(self, from_second, to_second, interval):
        if await self.is_valid_interval(interval):
            return (await self._parent.send_message({"name":"get-candles","version":"2.0","body":{"active_id":self._id,"size":interval,"from":from_second,"to":to_second}}))["msg"]
    
    async def get_previous_candles(self,interval,count):        
        end_id = int(self._parent._server_time/1000)
        start_id = end_id-(interval*count)
        return await self.get_candles(start_id,end_id,interval)

    async def subscribe(self):
        await self._parent.send_subscribe_message({"name":"quote-generated","params":{"routingFilters":{"active_id":self._id}}})
        await self._parent.send_subscribe_message({"name":"expiration-top-computed","version":"1.0","params":{"routingFilters":{"instrument_type":self._type,"asset_id":str(self._id)}}})
        self._first_candles = (await self._parent.send_message({"name":"get-first-candles","version":"1.0","body":{"active_id":self._id}}))["msg"]["candles_by_size"]
        return True
    
    async def process_generated_candle(self, message):
        size = message["size"]
        if size in self._candles:
            self._candles[size].append(message)
        else:
            self._candles[size] = [message]
    
    async def process_chart_data(self, message):
        self._bid = message["bid"]
        self._ask = message["ask"]
        self._value = message["value"]
        self._volume = message["volume"]
        self._show_value = message["show_value"]
        self._buy = message["buy"]
        self._sell = message["sell"]
        
    async def subscribe_to_candle_interval(self, interval):
        if await self.is_valid_interval(interval):
            await self._parent.send_subscribe_message({"name":"candle-generated","params":{"routingFilters":{"size":self._id,"size":interval}}})
            
    def subscribe_sync(self):
        return asyncio.run_coroutine_threadsafe(self.subscribe(),self._parent._async_loop).result()

    def get_candles_sync(self, from_second, to_second, interval):
        return asyncio.run_coroutine_threadsafe(self.get_candles(from_second, to_second, interval),self._parent._async_loop).result()

    def get_previous_candles_sync(self, interval, count):
        return asyncio.run_coroutine_threadsafe(self.get_previous_candles(interval, count),self._parent._async_loop).result()

    def subscribe_to_candle_interval_sync(self, interval):
        return asyncio.run_coroutine_threadsafe(self.subscribe_to_candle_interval(interval),self._parent._async_loop).result()
    
    def __getattr__(self, attr):
        internal_atttribute = "_"+attr
        if internal_atttribute in self.__dict__:
            return self.__dict__[internal_atttribute]
        raise(AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__,attr)))
    
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            return super().__setattr__(attr,value)
        raise(AttributeError(" Cannot set attribute '{1}' to '{0}' ".format(self.__class__.__name__,attr)))