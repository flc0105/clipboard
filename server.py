# coding=utf-8
import socket
import threading
import uuid

from tcpsocket import TcpSocket


class Connection:

    def __init__(self, client_id, client_name, group_id, conn):
        self.client_id = client_id
        self.client_name = client_name
        self.group_id = group_id
        self.conn = conn


class Server(object):
    def __init__(self):
        self.host = ''
        self.port = 8888
        self.connections = {}
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

    def accept(self):
        while True:
            conn, address = self.socket.accept()
            threading.Thread(target=self.handle_clients, args=(conn,)).start()

    def handle_clients(self, conn):
        client_id = str(uuid.uuid4())
        try:
            client_info = TcpSocket.recv_dict(conn)
            print('[+] Connection established: {0} {1}'.format(client_id, client_info))
            client_name = client_info['client_name']
            group_id = client_info['group_id']
            self.connections[client_id] = (Connection(client_id, client_name, group_id, conn))
            while True:
                data = TcpSocket.recv_dict(conn)
                for connection in self.connections.values():
                    if connection.group_id == group_id and connection.client_id != client_id:
                        TcpSocket.send_dict(connection.conn, data)
        except ConnectionResetError:
            del self.connections[client_id]
            print('[-] Connection closed: ' + client_id)
        except Exception as e:
            print('[-] Error: ' + str(e))


server = Server()
threading.Thread(target=server.accept).start()
