# coding=utf-8
import json
import struct


class TcpSocket:
    @staticmethod
    def send(s, data):
        s.send(struct.pack('i', len(data)))
        s.send(data.encode())

    @staticmethod
    def recv(s):
        size = struct.unpack('i', s.recv(4))[0]
        data = b''
        while size:
            buf = s.recv(size)
            size -= len(buf)
            data += buf
        return data.decode()

    @staticmethod
    def send_dict(s, data_dict):
        TcpSocket.send(s, json.dumps(data_dict))

    @staticmethod
    def recv_dict(s):
        return json.loads(TcpSocket.recv(s))
