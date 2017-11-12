class Position():
    
    def __init__(self,data):
        self.__parse_data(data)
    
    def __parse_data(self,data):
        self.__dict__ = data
    
    def update(self,data):
        self.__parse_data(data)