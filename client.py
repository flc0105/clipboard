# coding=utf-8
import socket

from tcpsocket import TcpSocket


class Client(TcpSocket):
    def __init__(self, host, port):
        s = socket.socket()
        s.connect((host, port))
        super().__init__(s)
