
import string


class Head:
    OpCode: int = 0
    Mode: int = 0
    Type: int = 0
    Length: int = 0
    ClientId: string = None
    GroupId: string = None
    SendClient: string = None
    SendGroup: string = None

    def __init__(self, dict):
        if(dict != None):
            self.__dict__ = dict
