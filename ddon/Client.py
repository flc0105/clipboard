import DdonSocketTcpClient


def ByteHandler(bytes):
    text = str(bytes, "utf-8")
    print(text)


client = DdonSocketTcpClient.TcpClient(
    "192.168.0.102", 9664, ByteHandler).Start()

while True:
    clientId = input("接收方Id:")
    text = input("消息:")
    client.Send(text.encode("utf8"), clientId, clientId)
