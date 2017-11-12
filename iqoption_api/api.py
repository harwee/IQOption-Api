import requests
import websocket
import time
from threading import Thread
from  datetime import datetime
import json
from .position import Position

class IQOption():
    
    practice_balance = 0
    real_balance = 0
    server_time = 0
    positions = {}
    
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
        self.__ssid = self.__login_response.cookies["ssid"]
        self.parse_account_info(json_login_response)
        return json_login_response["isSuccessful"]
    
    def parse_account_info(self,jsondata):
        """Parse Account Info"""
        
        self.real_balance = jsondata["result"]["balances"][0]["amount"]/1000000
        self.practice_balance = jsondata["result"]["balances"][1]["amount"]/1000000
        self.currency = jsondata["result"]["currency"]
        self.account_to_id = {"real":jsondata["result"]["balances"][0]["id"],"practice":jsondata["result"]["balances"][1]["id"]}
        self.id_to_account = {jsondata["result"]["balances"][0]["id"]:"real",jsondata["result"]["balances"][1]["id"]:"practice"}
        self.active_account = ["real" if jsondata["result"]["balance_type"] == 1 else "practice"][0]
        self.balance = jsondata["result"]["balance"]
        
    def on_socket_message(self,socket,message):
        message = json.loads(message)
        
        
        if message["name"] == "timeSync":
            self.__server_timestamp = message["msg"]
            self.server_time = datetime.fromtimestamp(self.__server_timestamp/1000)
            self.tick = self.server_time.second
        
        elif message["name"] == "heartbeat":
            pass
        
        elif message["name"] == "profile":
            self.parse_profile_message(message["msg"])
              
        elif message["name"] == "position-changed":
            self.parse_position_message(message["msg"])
        
        else:
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
        
        else:
            pass
    
    def parse_position_message(self,message):
        id = message["id"]
        if id in self.positions:
            self.positions[id].update(message)
        else:
            self.positions[id] = Position(message)
            
    
    def change_account(self,account_type):
        """Change active account `real` or `practice`"""
        
        data = {"balance_id":self.account_to_id[account_type.lower()]}
        response = self.session.request(url=self.change_account_url,data=data,method="POST")
        self.update_info()
        return self.active_account
    
    def update_info(self):
        """Update Account Info"""
        
        self.parse_account_info(self.session.request(url=self.getprofile_url,method="GET").json())
            