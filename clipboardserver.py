# coding=utf-8
import socket
import threading
import time

import server


class ClipboardServer(object):
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
            connection = server.Server(conn)
            client_info = connection.recv_dict()
            print('[+] Connection established: ' + str(client_info))
            connection.client_id = client_info['client_id']
            connection.client_name = client_info['client_name']
            connection.group_id = client_info['group_id']
            self.connections[connection.client_id] = connection
            self.send_list(connection.group_id)
            threading.Thread(target=self.recv, args=(connection,)).start()

    def recv(self, connection):
        while True:
            try:
                data = connection.recv_dict()
                print(data)
                if data['msg_type'] == 'public':
                    self.send_public(connection.client_id, connection.group_id, data)
                    continue
                if data['msg_type'] == 'private':
                    self.send_private(data)
                    continue
                if data['msg_type'] == 'image':
                    image = connection.recv_bytes()
                    self.send_image(connection.client_id, connection.group_id, data['sender'], image)
                    continue
            except ConnectionResetError:
                del self.connections[connection.client_id]
                self.send_list(connection.group_id)
                print('[+] Connection closed: ' + str(connection.client_id))
                break
            except Exception as e:
                print('[-] Error: ' + str(e))
                time.sleep(2)

    def send_list(self, group_id):
        client_dict = {}
        for connection in self.connections.values():
            if connection.group_id == group_id:
                client_dict[connection.client_id] = connection.client_name
        for connection in self.connections.values():
            connection.send_dict({'msg_type': 'client_dict', 'msg': client_dict})

    def send_public(self, client_id, group_id, data):
        for connection in self.connections.values():
            if connection.group_id == group_id and connection.client_id != client_id:
                connection.send_dict({'msg_type': 'text', 'msg': {'sender': data['sender'], 'text': data['text']}})

    def send_private(self, data):
        target_id = data['target']
        connection = self.connections[target_id]
        connection.send_dict({'msg_type': 'text', 'msg': data})

    def send_image(self, client_id, group_id, sender, data):
        for connection in self.connections.values():
            if connection.group_id == group_id and connection.client_id != client_id:
                connection.send_dict({'msg_type': 'image', 'sender': sender})
                connection.send_bytes(data)


clipboard_server = ClipboardServer()
threading.Thread(target=clipboard_server.accept).start()
