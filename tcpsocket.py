# coding=utf-8
import json
import struct


class TcpSocket:
    @staticmethod
    def send_dict(s, data_dict):
        data_json = json.dumps(data_dict)
        s.send(struct.pack('i', len(data_json)))
        s.send(data_json.encode())

    @staticmethod
    def recv_dict(s):
        size = struct.unpack('i', s.recv(4))[0]
        data = b''
        while size:
            buf = s.recv(size)
            size -= len(buf)
            data += buf
        return json.loads(data.decode())
