

# IQOption Api

IQ Option API for Python

* Version: 0.1a
* Python: 2, 3
* Website: https://github.com/harwee/IQOption-Api
* Author: Sri Harsha Gangisetty

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
        print(api.instruments_to_id) ## All Instruments Recieved
        print(api.forex_instruments)
        print(api.cfd_instruments)
        print(api.crypto_instruments)

### Subscribe to Realtime Market Data
        api.subscribe_market("EURUSD")
        
        
