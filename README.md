

# IQOption Api

A simple asynchronous API for IQOption

* Version: 0.3a0
* Python: 3.6+
* Repository: https://github.com/harwee/IQOption-Api
* Author: SriHarsha Gangisetty

## Contributors Required

* Bug Fixes and new feature implementations are welcome
* The current code is limited to Python 3.6+ To make this compatible with Python > 2 and Python < 3.6 I am thiking of Tornado Implementation (https://www.tornadoweb.org/en/stable/releases/v5.0.0.html) but no guarantees
* Any one willing to contribute create a pull request to `async`  branch

## Basic Usage

### Initialisation
        from iqoption_api import IQOption
        iqoption = IQOption("mail@email.com","password")
        iqoption.start()

### Check Account Balance 

        print(api.active_balance_id) # Prints the active balance id

### Check Active Account Balance
        balance_id = api.active_balance_id
        balance_object = api.balances[balance_id]
        print(balance_object["amount"]) # prints active account balance

### Change Account

        await iqoption.change_balance(balance_id) ## For Asynchronous
        iqoption.change_balance_sync(balance_id) ## For Synchronous


### Check Positions Modified/Opened After API Started
        print(iqoption.portfolio)  


### Get Instruments
        print(api.options) ## All Instruments Websocket Returned
        print(api.options["binary"]) ## All binary Options Websocket Returned

### Subscribe to Realtime Market Data

>   Subscribe method must be called to get first candle data and auto update real time price of option 
> 
        EURUSD = iqoption.options["binary"]["EURUSD"]

        await EURUSD.subscribe() ## For Asynchronous
        EURUSD.subscribe_sync() ## For Synchronous

### Subscribe to Candle Data
> interval (`int`) in Seconds


        await EURUSD.subscribe_to_candle_interval(interval) ## For Asynchronous
        EURUSD.subscribe_to_candle_interval_sync(interval) ## For Synchronous

### Get Expiration list

        await EURUSD.get_expiration_list() ## For Asynchronous
        EURUSD.get_expiration_list_sync() ## For Synchronous

### Access CandleData
       print(EURUSD.candles)

### Place a Binary Position



> expiration_type (`string`) =`1M`,`15M`,`EOD`,`EOW` or `EOM` 

> direction (`string`) = `put` or `call`

        await EURUSD.buy_v2(price,direction,value,expiration,expiration_type,timeout) ## For Asynchronous
        EURUSD.buy_v2_sync(price,direction,value,expiration,expiration_type,timeout) ## For Synchronous

### Send Socket Message Directly

        await EURUSD.send_socket_message(name, message, request_id(optional)) ## For Asynchronous
        EURUSD.send_socket_message_sync(name, message, request_id(optional)) ## For Synchronous

### Send Message Directly

        await EURUSD.send_message(message) ## For Asynchronous
        EURUSD.send_message_sync(message) ## For Synchronous

### Send Subscribe Message Directly

        await EURUSD.send_subscribe_message(message) ## For Asynchronous
        EURUSD.send_subscribe_message_sync(message) ## For Synchronous

### Send unSubscribe Message Directly

        await EURUSD.send_unsubscribe_message(message) ## For Asynchronous
        EURUSD.send_unsubscribe_message_sync(message) ## For Synchronous

### Send subscribe Directly

        await EURUSD.subscribe(message) ## For Asynchronous
        EURUSD.subscribe_sync(message) ## For Synchronous

### Send unsubscribe Directly

        await EURUSD.unsubscribe(message) ## For Asynchronous
        EURUSD.unsubscribe_sync(message) ## For Synchronous

### Update Balances Manually

        await EURUSD.update_balances(message) ## For Asynchronous
        EURUSD.update_balances_sync(message) ## For Synchronous

### Server Time

        print(iqoption.server_time) ## Prints Server time


### Attributes of BinaryOption 

        BinaryOption.id 
        BinaryOption.name
        BinaryOption.group_id
        BinaryOption.min_bet
        BinaryOption.max_be
        BinaryOption.precision
        BinaryOption.is_enabled
        BinaryOption.schedule
        BinaryOption.image
        BinaryOption.parent
        BinaryOption.candle_update_rate
        BinaryOption.first_candle
        BinaryOption.candles
        BinaryOption.option
        BinaryOption.deadtime

        BinaryOption.bid
        BinaryOption.ask
        BinaryOption.value
        BinaryOption.volume
        BinaryOption.show_value
        BinaryOption.buy
        BinaryOption.sell


* Example
        
        EURUSD.buy # get current buy price
        EURUSD.sell # get current sell price
        EURUSD.bid # get current bid price