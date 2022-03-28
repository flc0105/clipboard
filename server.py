# coding=utf-8
import socket
import threading

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
        client_id = None
        group_id = None
        client_info = None
        try:
            client_info = TcpSocket.recv_dict(conn)
            print('[+] Connection established: ' + str(client_info))
            client_id = client_info['client_id']
            client_name = client_info['client_name']
            group_id = client_info['group_id']
            self.connections[client_id] = (Connection(client_id, client_name, group_id, conn))
            self.send_list(group_id)
            while True:
                data = TcpSocket.recv_dict(conn)
                if data['msg_type'] == 'public':
                    self.send_public(client_id, group_id, data)
                    continue
                if data['msg_type'] == 'private':
                    self.send_private(data)
                    continue
        except ConnectionResetError:
            del self.connections[client_id]
            self.send_list(group_id)
            print('[-] Connection closed: ' + str(client_info))
        except Exception as e:
            print('[-] Error: ' + str(e))

    def send_list(self, group_id):
        client_dict = {}
        for connection in self.connections.values():
            if connection.group_id == group_id:
                client_dict[connection.client_id] = connection.client_name
        for connection in self.connections.values():
            TcpSocket.send_dict(connection.conn, {'msg_type': 'client_dict', 'msg': client_dict})

    def send_public(self, client_id, group_id, data):
        for connection in self.connections.values():
            if connection.group_id == group_id and connection.client_id != client_id:
                TcpSocket.send_dict(connection.conn,
                                    {'msg_type': 'text', 'msg': {'sender': data['sender'], 'text': data['text']}})

    def send_private(self, data):
        target_id = data['target']
        target_connection = self.connections[target_id].conn
        TcpSocket.send_dict(target_connection, {'msg_type': 'text', 'msg': data})


server = Server()
threading.Thread(target=server.accept).start()
