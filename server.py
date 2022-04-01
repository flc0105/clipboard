# coding=utf-8
from tcpsocket import TcpSocket


class Server(TcpSocket):
    def __init__(self, socket):
        super().__init__(socket)
        self.client_id = None
        self.client_name = None
        self.group_id = None
