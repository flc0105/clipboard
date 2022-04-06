# coding=utf-8
import json
import socket
import struct
from io import BytesIO


class TcpSocket:

    def __init__(self, s: socket.socket):
        self.socket = s

    def send(self, data):
        self.socket.send(struct.pack('i', len(data)))
        self.socket.send(data.encode())

    def recv(self):
        size = struct.unpack('i', self.socket.recv(4))[0]
        data = b''
        while size:
            buf = self.socket.recv(size)
            size -= len(buf)
            data += buf
        return data.decode()

    def send_dict(self, data_dict):
        self.send(json.dumps(data_dict))

    def recv_dict(self):
        return json.loads(self.recv())

    def send_bytes(self, b):
        self.socket.send(struct.pack('i', b.getbuffer().nbytes))
        f = BytesIO(b.getvalue())
        while True:
            data = f.read(1024)
            if not data:
                break
            self.socket.send(data)

    def recv_bytes(self):
        size = struct.unpack('i', self.socket.recv(4))[0]
        b = BytesIO()
        while size:
            packet = self.socket.recv(size)
            size -= len(packet)
            b.write(packet)
        return b
