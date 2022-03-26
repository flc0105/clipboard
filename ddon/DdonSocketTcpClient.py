# coding=utf-8
import json
import socket
import string
import sys
import threading
import uuid
import DdonSocketHead

headLenght = 500


class TcpClient:
    def __init__(self, host: string, port: int, byteHandler) -> None:
        self.client = socket.socket()
        self.client.connect((host, port))
        guidBytes = self.client.recv(16)
        self.clientId = uuid.UUID(bytes_le=guidBytes)
        print("客户端Id:" + str(self.clientId))
        self.byteHandler = byteHandler

    def Start(self):
        threading.Thread(target=self.__ConsecutiveReadStream,
                         daemon=True).start()
        return self

    def Send(self, data: bytes, sendClientId, sendGroupId):
        headBytes = self.__GetHeadBytes(
            data.__len__(), sendClientId, sendGroupId)
        self.client.send(self.__MergeBytes(headBytes, data))

    def __ConsecutiveReadStream(self) -> uuid:
        try:
            while True:
                head = self.__ReadHeadAsync()
                self.byteHandler(self.client.recv(head.Length))
        except socket.error as e:
            print(e)
            sys.exit(0)

    def __ReadHeadAsync(self) -> DdonSocketHead.Head:
        by = self.client.recv(headLenght)
        text = str(by, "utf-8").strip(b'\x00'.decode())
        return json.loads(text, object_hook=DdonSocketHead.Head)

    def __GetHeadBytes(self, length, sendClientId, sendGroupId) -> bytes:
        head = DdonSocketHead.Head(None)
        head.ClientId = str(self.clientId) # 无所谓
        # head.GroupId = str(self.clientId) # 无所谓
        head.Length = length # 消息长度
        # head.Mode = 1
        head.OpCode = 10002 # 用于消息转发
        head.SendClient = sendClientId
        # head.SendGroup = '00000000-0000-0000-0000-000000000000'
        head.Type = 1 # 传输文本
        return json.dumps(head.__dict__).encode('utf-8')

    def __MergeBytes(left, byte1: bytes, byte2: bytes):
        b1 = bytearray(byte1)
        b3 = bytes(headLenght-byte1.__len__())
        b1.extend(b3)
        b1.extend(byte2)
        return b1
