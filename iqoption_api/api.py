import requests
import websocket
import time
from threading import Thread
from  datetime import datetime
import json
from .position import Position
from .constants import ACTIVES
             
class IQOption():
    
    practice_balance = 0
    real_balance = 0
    server_time = 0
    positions = {}
    instruments_categories = ["cfd","forex","crypto"]
    top_assets_categories = ["forex","crypto","binary"]
    instruments_to_id = ACTIVES
    id_to_instruments = {y:x for x,y in ACTIVES.items()}
    market_data = {}
    binary_expiration_list = {}
    digital_strike_list = {}
    candle_data = {}
    
    
    def __init__(self,username,password,host="iqoption.com"):
        
        self.username = username
        self.password = password
        self.host = host
        self.session = requests.Session()
        self.generate_urls()
        self.socket = websocket.WebSocketApp(self.socket_url,on_open=self.on_socket_connect,on_message=self.on_socket_message,on_close=self.on_socket_close,on_error=self.on_socket_error)
        
    def generate_urls(self):
        """Generates Required Urls to operate the API"""
        
        self.api_url = "https://{}/api/".format(self.host)
        self.socket_url = "wss://{}/echo/websocket".format(self.host)
        self.login_url = self.api_url+"login"
        self.profile_url = self.api_url+"profile"
        self.change_account_url = self.profile_url+"/"+"changebalance"
        self.getprofile_url = self.api_url+"getprofile"
    
    def login(self):
        """Login and set Session Cookies"""
        
        data = {"email":self.username,"password":self.password}
        self.__login_response = self.session.request(url=self.login_url,data=data,method="POST")
        requests.utils.add_dict_to_cookiejar(self.session.cookies, dict(platform="9"))
        json_login_response = self.__login_response.json()
        if json_login_response["isSuccessful"]:
            self.__ssid = self.__login_response.cookies["ssid"]
            self.parse_account_info(json_login_response)
            self.start_socket_connection()
            time.sleep(1) ## artificial delay to complete socket connection
            self.get_instruments()
            self.get_top_assets()
            time.sleep(1) ## artificial delay to populate symbols
        return json_login_response["isSuccessful"]
    
    def parse_account_info(self,jsondata):
        """Parse Account Info"""
        
        self.real_balance = jsondata["result"]["balances"][0]["amount"]/1000000
        self.practice_balance = jsondata["result"]["balances"][1]["amount"]/1000000
        self.currency = jsondata["result"]["currency"]
        self.account_to_id = {"real":jsondata["result"]["balances"][0]["id"],"practice":jsondata["result"]["balances"][1]["id"]}
        self.id_to_account = {jsondata["result"]["balances"][0]["id"]:"real",jsondata["result"]["balances"][1]["id"]:"practice"}
        self.active_account = ["real" if jsondata["result"]["balance_type"] == 1 else "practice"][0]
        self.group_id = jsondata["result"]["balance_type"]
        self.balance = jsondata["result"]["balance"]
        
    def on_socket_message(self,socket,message):
        message = json.loads(message)
        
        
        if message["name"] == "timeSync":
            self.server_timestamp = int(message["msg"]/1000)
            self.server_time = datetime.fromtimestamp(self.server_timestamp)
            self.tick = self.server_time.second
        
        elif message["name"] in  ["heartbeat","tradersPulse"]:
            pass
        
        elif message["name"] == "profile":
            self.parse_profile_message(message["msg"])
              
        elif message["name"] == "position-changed":
            self.parse_position_message(message["msg"])
        
        elif message["name"] == "newChartData":
            self.parse_new_chart_data_message(message["msg"])
        
        elif message["name"] == "top-assets":
            self.parse_top_assets_message(message["msg"])
        
        elif message["name"] == "instruments":
            self.parse_instruments_message(message["msg"]) 
        
        elif message["name"] == "listInfoData":
            self.parse_update_position_message(message["msg"])
        
        elif message["name"] == "expiration-list":
            self.parse_expiration_list_message(message["msg"])
        
        elif message["name"] == "candles":
            self.parse_candles_message(message["msg"])
            
        else:
#             print(message)
            pass
    
    def on_socket_connect(self,socket):
        """Called on Socket Connection"""
        
        self.initial_subscriptions()
        print("On connect")
    
    def on_socket_error(self,socket,error):
        """Called on Socket Error"""
        
        print(message)
    
    def on_socket_close(self,socket):
        """Called on Socket Close"""
           
    def start_socket_connection(self):
        """Start Socket Connection"""
        self.socket_thread = Thread(target=self.socket.run_forever).start()
    
    def send_socket_message(self,name,msg):
        data = {"name":name,"msg":msg}
        self.socket.send(json.dumps(data))
    
    def initial_subscriptions(self):
        self.send_socket_message("ssid",self.__ssid)
        self.send_socket_message("subscribe","tradersPulse")

    def parse_profile_message(self,message):

        if "balance" in message and "balance_id" in message and "currency" in message:
            account = self.id_to_account[message["balance_id"]]
            self.__dict__["{}_balance".format(account)]=message["balance"]
        
        elif "balance" in message and "balance_id" in message:
            self.balance = message["balance"]
            self.active_account = self.id_to_account[message["balance_id"]]
            self.group_id = [1 if self.active_account == "real" else 4][0]

    def parse_position_message(self,message):
        id = message["id"]
        if id in self.positions:
            self.positions[id].update(message)
        else:
            self.positions[id] = Position(message)
    
    def parse_new_chart_data_message(self,message):
        symbol = message["symbol"]
        if symbol in self.market_data:
            self.market_data[symbol][message["time"]]= message
        else:
            self.market_data[symbol] = {message["time"]: message}
    
    
    def parse_top_assets_message(self,message):
        instrument_type = message["instrument_type"]
        temp = {}
        for ele in message["data"]:
            temp[ele["active_id"]] = ele["active_id"]
        self.__dict__["{}_top_assets".format(instrument_type)] = temp
    
    def parse_instruments_message(self,message):
        instrument_type = message["type"]
        temp = {}
        for ele in message["instruments"]:
            temp[ele["id"]] = ele["active_id"]
        self.__dict__["{}_instruments".format(instrument_type)] = temp
    
    def parse_expiration_list_message(self,message):
        for idx, ele in enumerate(message["expiration"]):
            message["expiration"][idx]["time"] = ele["time"]/1000
        
        self.binary_expiration_list[message["underlying"]] = [x for x in message["expiration"] if x["time"] > self.server_timestamp]
    
    def parse_update_position_message(self,message):
        for ele in message:
            self.positions[ele["id"]] = ele
    
    def parse_candles_message(self,message):
        self.__latest_candles_data = message["data"]
        market_name = self.id_to_instruments[message["active_id"]]
        if market_name in self.candle_data:
            self.candle_data[market_name][message["duration"]] = message["data"]
        else:
            self.candle_data[market_name] = {message["duration"]:message["data"]}
            
    def change_account(self,account_type):
        """Change active account `real` or `practice`"""
        
        data = {"balance_id":self.account_to_id[account_type.lower()]}
        response = self.session.request(url=self.change_account_url,data=data,method="POST")
        self.update_info()
        return self.active_account
    
    def update_info(self):
        """Update Account Info"""
        
        self.parse_account_info(self.session.request(url=self.getprofile_url,method="GET").json())
    
    def get_top_assets(self):
        for ele in self.top_assets_categories:
            self.send_socket_message("sendMessage",{"name":"get-top-assets","version":"1.1","body":{"instrument_type":ele}})
    
    def get_instruments(self):
        for ele in self.instruments_categories:
            self.send_socket_message("sendMessage",{"name":"get-instruments","version":"1.0","body":{"type":ele}})
    
    def subscribe_market(self,market_name=None,market_id=None):
        if market_name:
            market_id = self.instruments_to_id.get(market_name)
        
        self.send_socket_message("subscribeMessage",{"name":"quote-generated","version":"1.0","params":{"routingFilters":{"active_id":market_id}}})
        self.update_expiration_list(market_name)
    
    def update_expiration_list(self,market_name):      
        self.send_socket_message("sendMessage",
                                 {"name":"get-expiration-list","version":"3.0",
                                  "body":{"type":"digital-option","underlying":market_name}
                                 })

    def open_position(self,market_name,price,direction,type,expiration_time):
        msg = dict(user_balance_id = self.account_to_id[self.active_account],
        price = price,
        direction = direction,
        platform = "9",
        time = self.server_timestamp,
        exp = expiration_time,
        act = self.instruments_to_id[market_name],
        type = type,
        )
        self.send_socket_message("buyV2",msg) 
    
    def update_candle_data(self,market_name,interval,start_time,end_time):
        """
            interval (seconds)
            start_time (integer timestamp) 
            end_time (integer tiestamp)
        """
        chunk_size = int((end_time-start_time)/interval)+5
        self.send_socket_message("candles",{"active_id":self.instruments_to_id[market_name],
                                            "duration":interval,
                                            "chunk_size":chunk_size,
                                            "from":start_time,
                                            "till":end_time,
                                           })
