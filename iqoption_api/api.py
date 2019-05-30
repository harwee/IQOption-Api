import asyncio
import requests
import websockets
import time
import json
import threading
import logging
import random
from concurrent import futures
LOGIN_URL = "https://auth.iqoption.com/api/v1.0/login"
WSS_URL = "wss://iqoption.com/echo/websocket"

from .binary_option import BinaryOption
from .portfolio_item import PortfolioItem

logger = logging.getLogger("iqoption-api")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class TimedRequestStore(object):

    def __init__(self,ttl=10):
        self.ttl = ttl
        self._store = {}
    
    def clear_expired(self):
        for key, value in dict(self._store).items():
            if time.time()-value["created_at"] > self.ttl:
                del(self._store[key])
    
    def get(self,key):
        return self._store[key]["value"]
    
    def pop(self,key):
        return self._store.pop(key)["value"]
    
    def __contains__(self, key):
        return self._store.__contains__(key)
    
    def put(self, key, value):
        self._store[key] = {"created_at":time.time(),"value":value}

class TimedOutException(Exception):
    pass

class IQOption(object):

    def __init__(self,username,password):
        self._session = requests.Session()
        self._username = username
        self._password = password
        self._end_session = False
        self._async_loop = asyncio.new_event_loop()
        self._logger = logger
        self.set_default_params()
        self._requests_count = 0
        self._request_responses = TimedRequestStore()
    
    def set_default_params(self):        
        self._server_time = 0
        self._pre_init_complete = False
        self._init_complete = False
        self._options = dict(binary={})
        self._active_balance_id = 0
        self._id_to_option_name = dict(binary={})
        self._message_name_to_method = {
            "heartbeat": self.send_heartbeat,
            "timeSync": self.set_server_time,
            "profile": self.process_profile_message,
            "balances": self.process_balances_message,
            "api_option_init_all_result": self.process_options_message,
            "newChartData":self.process_new_chart_data_message,
            "candle-generated": self.process_candle_generated_message,
            "listInfoData":self.process_list_info_data_message,
        }
        self._balances = {}
        self._portfolio = {}
    
    def start(self):
        self._logger.debug("Starting Async thread")
        self._async_thread = threading.Thread(target=self.start_async_loop_thread)
        self._async_thread.start()
        while True:
            if self._init_complete:
                self._logger.info("Init Complete")
                break
            time.sleep(1)
            
    def stop(self):
        self._end_session = True
        while True:
            pending = asyncio.Task.all_tasks(loop=self._async_loop)
            if all([x.done() for x in pending]):
                return 
            time.sleep(1)
    
    def start_async_loop_thread(self):
        self._logger.debug("Async thread Started")
        asyncio.set_event_loop(self._async_loop)
        self._logger.debug("Thread event loop set")
        self._logger.debug("Creating Task async_run")
        self._async_loop.create_task(self.async_run())
        self._logger.debug("async_run task created")
        self._async_loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks(loop=self._async_loop)))
    
    async def get_request_id(self,track_request=False):
        self._requests_count += 1
        if track_request:
            return "r_"+str(self._requests_count)
        return str(self._requests_count)
    
    async def clear_request_response_store_task(self,interval=10):
        while not self._end_session:
            await asyncio.sleep(interval)
            self._request_responses.clear_expired()
            
    async def async_run(self):
        self._logger.debug("Started async_run")

        self._logger.debug("Creating Task to monitor and clear request response")
        self._async_loop.create_task(self.clear_request_response_store_task())
        self._logger.debug("Created Task to monitor and clear request response")
        self._logger.debug("Initiating Login")
        login_response = await self.login()
        self._logger.debug("Login Complete")
        self._logger.debug("Establishing Socket Connection")
        await self.establish_socket_connection_and_run()
        self._logger.info("Socket Connection Established")
        self._logger.debug("Creating task torun on preinit")
        self._async_loop.create_task(self.on_preinit_complete())
        self._logger.debug("Task created to run on preinit")
        self._logger.info("Started monitoring Incoming socket messages")
        while True:
            if self._end_session:
                await self._socket.close()
            try:
                self._async_loop.create_task(self.process_incoming_message(await self._socket.recv()))
            except websockets.exceptions.ConnectionClosed as e:
                if self._end_session:
                    break
                else:
                    self._logger.error(e)
                    raise(e)
        self._logger.debug("Stopped Monitoring Incoming socket Messages")
    
    async def on_preinit_complete(self):
        while True:
            if self._pre_init_complete:
                break
            await asyncio.sleep(1)
        
        await self.update_balances()

        self._init_complete = True

    async def establish_socket_connection_and_run(self):
        
        self._socket = await websockets.connect(WSS_URL,ping_interval=None)
        await self._async_loop.create_task(self.on_socket_connect())

    async def login(self):
        """Login and set Session Cookies"""
        
        data = {"email":self._username,"password":self._password}
        login_response = self._session.request(url=LOGIN_URL,data=data,method="POST")
        requests.utils.add_dict_to_cookiejar(self._session.cookies, dict(platform="9"))
        self.__ssid = login_response.cookies["ssid"]
        json_login_response = login_response.json()
        return json_login_response
    
    async def send_socket_message(self,name,msg,request_id=None):
        data = {"name":name,"msg":msg}
        if (request_id != None):
            data["request_id"] = str(request_id)
        else:
            data["request_id"] = await self.get_request_id()
        payload = json.dumps(data)
        self._logger.debug("> : {}".format(payload))
        await self._socket.send(payload)

    async def on_socket_connect(self,*args):
        await self.send_socket_message("setOptions",{"sendResults":True,"getNewChartData":False},-1)
        await self.send_socket_message("ssid",self.__ssid,)    
        await self.update_balances()
        await self.get_all_options()

    async def process_incoming_message(self,raw_message):
        self._logger.debug("< : {}".format(raw_message))
        message = json.loads(raw_message)
        if "request_id" in message:
            if message["request_id"].startswith("r_"):
                self._request_responses.put(message["request_id"],message)
        async_method = self._message_name_to_method.get(message["name"])
        if async_method:
            self._async_loop.create_task(async_method(message))
        else:
            # print(message)
            pass
    
    async def send_heartbeat(self, message):
        await self.send_socket_message("heartbeat",{"userTime":int(time.time()*1000),"heartbeat":message["msg"]})

    async def set_server_time(self, message):
        if self._server_time < message["msg"]:
            self._server_time = message["msg"]
    
    async def process_options_message(self,message):
        binaries = message["msg"]["result"]["binary"]
        for boption in binaries["actives"].values():
            x  = BinaryOption(boption, self)
            self._options["binary"][x.name] = x
            self._id_to_option_name["binary"][x.id] = x.name

    async def process_profile_message(self,message):
        msg = message["msg"]
        self._active_balance_id = msg["balance_id"]
        if not self._pre_init_complete:
            self._logger.info("User Balance Id: {}".format(self._active_balance_id))
            self._pre_init_complete = True
    
    async def process_balances_message(self,message):
        msg = message["msg"]
        for x in msg:
            self._balances[x["id"]] = x
    
    async def process_candle_generated_message(self,message):
        msg = message["msg"]
        active_id = msg["active_id"]
        if active_id in self._id_to_option_name["binary"]:
            binary_name = self._id_to_option_name["binary"][active_id]
            if binary_name in self._options["binary"]:
                self._async_loop.create_task(self._options["binary"][binary_name].process_generated_candle(msg))
    
    async def process_new_chart_data_message(self,message):
        msg = message["msg"]
        active_id = msg["active_id"]
        if active_id in self._id_to_option_name["binary"]:
            binary_name = self._id_to_option_name["binary"][active_id]
            if binary_name in self._options["binary"]:
                self._async_loop.create_task(self._options["binary"][binary_name].process_chart_data(msg))
    
    async def process_list_info_data_message(self, message):
        msg = message["msg"]
        for portfolio_item in msg:
            if portfolio_item["type_name"] in ["turbo","binary"]:
                _option = self._options["binary"][portfolio_item["active"]]
            temp = PortfolioItem(portfolio_item, _option)
            self._portfolio[temp.id] = temp
    
    async def return_response_if_response_for_request_id_processed(self, request_id,timeout):
        monitoring_started_at = time.time()
        while True:
            if request_id in self._request_responses:
                return self._request_responses.pop(request_id)
            if time.time()-monitoring_started_at > timeout:
                break
            await asyncio.sleep(.1)

    async def subscribe(self,message,request_id=None):
        await self.send_socket_message("subscribe",message,request_id)
    
    async def unsubscribe(self,message,request_id=None):
        await self.send_socket_message("unSubscribe",message,request_id)
    
    async def send_message(self,message,timeout=5):
        request_id = await self.get_request_id(track_request=True)
        await self.send_socket_message("sendMessage",message,request_id)
        return await self.return_response_if_response_for_request_id_processed(request_id,timeout)
    
    async def send_subscribe_message(self,message,timeout=5):
        request_id = await self.get_request_id(track_request=True)
        await self.send_socket_message("subscribeMessage",message,request_id)
        return await self.return_response_if_response_for_request_id_processed(request_id,timeout)
    
    async def send_unsubscribe_message(self,message,timeout=5):
        request_id = await self.get_request_id(track_request=True)
        await self.send_socket_message("unsubscribeMessage",message,request_id)
        return await self.return_response_if_response_for_request_id_processed(request_id,timeout)
    
    async def change_balance(self, balance_id, timeout=5):
        request_id = await self.get_request_id(track_request=True)
        await self.send_socket_message("api_profile_changebalance",{"balance_id":balance_id},request_id)
        response = await self.return_response_if_response_for_request_id_processed(request_id,timeout)
        if response["msg"]["isSuccessful"]:
            self._active_balance_id = balance_id
        self._logger.info("User Balance Id: {}".format(self._active_balance_id))
        return response

    async def update_balances(self):
        await self.send_message({"name": "get-balances", "version": "1.0", "body": {"tournaments_statuses_ids": [2, 3]}})
    
    async def get_all_options(self,timeout=5):
        request_id = await self.get_request_id(track_request=True)
        await self.send_socket_message("api_option_init_all","",request_id)
        return await self.return_response_if_response_for_request_id_processed(request_id,timeout)
  
    def send_socket_message_sync(self,name, msg, request_id=None):
        asyncio.run_coroutine_threadsafe(self.send_socket_message(name,msg,request_id),self._async_loop)
    
    def subscribe_sync(self, msg, request_id=None):
        asyncio.run_coroutine_threadsafe(self.subscribe(msg,request_id),self._async_loop)
    
    def unsubscribe_sync(self, msg, request_id=None):
        asyncio.run_coroutine_threadsafe(self.unsubscribe(msg,request_id),self._async_loop)

    def send_message_sync(self, msg, timeout=5):
        return asyncio.run_coroutine_threadsafe(self.send_message(msg,timeout=timeout),self._async_loop).result(timeout=timeout)
    
    def send_subscribe_message_sync(self, msg, timeout=5):
        return asyncio.run_coroutine_threadsafe(self.send_subscribe_message(msg,timeout=timeout),self._async_loop).result(timeout=timeout)
    
    def send_unsubscribe_message_sync(self, msg, timeout=5):
        return asyncio.run_coroutine_threadsafe(self.send_unsubscribe_message(msg,timeout=timeout),self._async_loop).result(timeout=timeout)
    
    def update_balances_sync(self):
        asyncio.run_coroutine_threadsafe(self.update_balances(),self._async_loop)
    
    def change_balance_sync(self,balance_id,timeout=5):
        return asyncio.run_coroutine_threadsafe(self.change_balance(balance_id,timeout=timeout),self._async_loop).result(timeout=timeout)
    
    def get_option(self, option_type, name):
        return self._options[option_type][name]
    
    def __getattr__(self, attr):
        internal_atttribute = "_"+attr
        if internal_atttribute in self.__dict__:
            return self.__dict__[internal_atttribute]
        raise(AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__,attr)))
    
    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            return super().__setattr__(attr,value)
        raise(AttributeError(" Cannot set attribute '{1}' to '{0}' ".format(self.__class__.__name__,attr)))
