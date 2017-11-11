

# IQOption Api

IQ Option API for Python

* Python: 2, 3
* Website: https://github.com/harwee/IQOption-Api
* Author: Sri Harsha Gangisetty

## Basic Usage

### Login
        from iqoption_api import IQOption
        api = IQOption("mail@email.com","password")
        api.login() # Returns True if successful else False

### Check Account Type

        print(api.active_account) # prints `real` or `practice`

### Check Active Account Balance
        print(api.balance) # prints active account balance

### Check Balances
        print(api.real_balance) # prints real account balance
        print(api.practice_balance) # prints practice account balance

### Change Account
        api.change_account("real") # `real` or `practice` Returns Account Type (`real` or `practice`)