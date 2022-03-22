# coding=utf-8
import json
import pickle
import socket
import struct
import threading
import uuid


class Connection:

    def __init__(self, client_id, hostname, conn):
        self.client_id = client_id
        self.hostname = hostname
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

    def send_list(self):
        clients_dict = {}
        for conn in self.connections.items():
            clients_dict[conn[1].client_id] = conn[1].hostname
        clients = pickle.dumps(clients_dict)
        for conn in self.connections.items():
            conn[1].conn.send(struct.pack('i', 0))
            conn[1].conn.send(struct.pack('i', len(clients)))
            conn[1].conn.send(clients)

    def handle_clients(self, conn):
        client_id = str(uuid.uuid4())
        hostname = ''
        try:
            hostname_len = struct.unpack('i', conn.recv(4))[0]
            hostname = conn.recv(hostname_len).decode()
            print('[+] Connection has been established: {} ({})'.format(hostname, client_id))
            self.connections[client_id] = (Connection(client_id, hostname, conn))
            self.send_list()
            while True:
                conn = self.connections[client_id].conn
                data_len = struct.unpack('i', conn.recv(4))[0]
                data = conn.recv(data_len)
                data_dict = json.loads(data.decode())
                target = data_dict['target']
                del data_dict['target']
                conn = self.connections[target].conn
                conn.send(struct.pack('i', 1))
                data_json = json.dumps(data_dict)
                conn.send(struct.pack('i', len(data_json)))
                conn.send(data_json.encode())
        except:
            del self.connections[client_id]
            print('[-] Connection closed: {} ({})'.format(hostname, client_id))
            self.send_list()


server = Server()
threading.Thread(target=server.accept).start()
