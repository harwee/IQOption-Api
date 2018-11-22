
# Harwee is damn busy and will not be responding to anyone hereafter. If you have any issues then please try to solve it yourself or try some another library.


# IQOption Api


A Simple websocket API for IQ Option.



* Version: 0.3a
* Python: 2, 3
* Website: https://github.com/harwee/IQOption-Api
* Author: Sri Harsha Gangisetty

## IMPORTANT
There are currently issues with this package functioning normally. The whole code will be overhauled and Python2 support will be removed, The whole code  will be converted to run  asynchronously using Python3 `asyncio` library. Date of release of new package is not yet decided but it will be released soon.

### Next Addition
* Ability to place Put, Sell Digital Options

## Basic Usage

### Initialisation
        from iqoption_api import IQOption
        api = IQOption("mail@email.com","password")
        api.login() # Returns True if successful else False
        api.start_socket_connection()

### Check Account Type

        print(api.active_account) # prints `real` or `practice`

### Check Active Account Balance
        print(api.balance) # prints active account balance

### Check Balances
        print(api.real_balance) # prints real account balance
        print(api.practice_balance) # prints practice account balance

### Change Account
        api.change_account("real") # `real` or `practice` Returns Account Type (`real` or `practice`)


### Check Positions Modified/Opened After API Started
        print(api.positions)  

### Get Server Tick
        print(api.tick) ## range 0, 59

### Get Instruments
        print(api.instruments_to_id) ## All Instruments Websocket Returned
        print(api.forex_instruments)
        print(api.cfd_instruments)
        print(api.crypto_instruments)

### Subscribe to Realtime Market Data
        api.subscribe_market("EURUSD")

### Access Market Data
        api.market_data
### Update Expiration list
        api.update_expiration_list("EURUSD")
    
### Get Expiration List
        print(api.binary_expiration_list["EURUSD"])
        
        ### Sample Response
            [{u'expiration_length': 60, u'type': u'PT1M', u'dead_time_length': 10, u'time': 1512475620},             {u'expiration_length': 300, u'type': u'PT5M', u'dead_time_length': 10, u'time': 1512475800}]


### Place a Binary Position
        api.open_position(direction="put",
                        expiration_time=api.binary_expiration_list["EURUSD"][-1]["time"],
                        market_name="EURUSD",
                        price=5,
                        type="turbo"
                        )
        

### Update Candle Data

        # api.update_candle_data(market_name,interval,start_time,end_time)
        api.update_candle_data("EURUSD",1,0,int(time.time())) ## get latest 1000 candles with 1 second interval

### Access CandleData
        # api.candle_data[market_name][interval] # list of lists  [time,open,close,high,low]
        print(api.candle_data["EURUSD][1]) # prints candles 
