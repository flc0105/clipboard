# coding=utf-8
import json
import os
import socket
import sys
import threading
import time

import pyperclip

from tcpsocket import TcpSocket


class Client(object):

    def __init__(self):
        self.host = None
        self.port = None
        self.client_name = None
        self.group_id = None
        self.socket = socket.socket()
        self.recent_text = pyperclip.paste()

    def load_config(self):
        try:
            config = None
            config_file = 'config.json'
            if os.path.isfile(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            self.host = config['server_ip']
            self.port = int(config['server_port'])
            if config['client_name']:
                self.client_name = config['client_name']
            else:
                self.client_name = socket.gethostname()
            self.group_id = config['group_id']
        except Exception as e:
            print('[-] Failed to load configuration: ' + str(e))
            sys.exit(0)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            print('[-] Failed to connect to server: ' + str(e))
            sys.exit(0)

    def send_info(self):
        try:
            client_info = {
                'client_name': self.client_name,
                'group_id': self.group_id
            }
            TcpSocket.send_dict(self.socket, client_info)
        except Exception as e:
            print('[-] Failed to send client information: ' + str(e))
            sys.exit(0)

    @staticmethod
    def get_time():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def recv_data(self):
        while True:
            try:
                data = TcpSocket.recv_dict(self.socket)
                sender = data['sender']
                text = data['text']
                self.recent_text = text
                pyperclip.copy(text)
                print('[+] {0} Clipboard synced from {1}: {2}'.format(self.get_time(), sender, text))
            except ConnectionResetError:
                print('[-] Server closed')
                sys.exit(0)
            except Exception as e:
                print('[-] Error while receiving data: ' + str(e))

    def monitor_clipboard(self):
        while True:
            try:
                clipboard_text = pyperclip.paste()
                if clipboard_text != '' and clipboard_text != self.recent_text:
                    self.recent_text = clipboard_text
                    print('[+] {0} Clipboard change detected: {1}'.format(self.get_time(), self.recent_text))
                    data = {
                        'sender': self.client_name,
                        'text': self.recent_text
                    }
                    TcpSocket.send_dict(self.socket, data)
                time.sleep(1)
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print('[-] Error while monitoring clipboard: ' + str(e))


client = Client()
client.load_config()
client.connect()
client.send_info()
threading.Thread(target=client.recv_data, daemon=True).start()
client.monitor_clipboard()
