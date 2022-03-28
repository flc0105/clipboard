# coding=utf-8
import json
import os
import socket
import sys
import threading
import time
import uuid

import pyperclip

from tcpsocket import TcpSocket


class Client(object):
    def __init__(self):
        self.host = None
        self.port = None
        self.client_name = None
        self.group_id = None
        self.socket = socket.socket()
        self.recent_text = None
        self.clients = {}
        self.client_id = str(uuid.uuid4())

    def load_config(self):
        try:
            config_file = 'config.json'
            if os.path.isfile(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                print('[-] No configuration file found')
                sys.exit(0)
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
            while self.socket.connect_ex((self.host, self.port)) != 0:
                time.sleep(5)
            print('[+] Connected to {0}:{1}'.format(self.host, self.port))
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print('[-] Error: ' + str(e))

    def send_info(self):
        try:
            client_info = {
                'client_id': self.client_id,
                'client_name': self.client_name,
                'group_id': self.group_id
            }
            TcpSocket.send_dict(self.socket, client_info)
        except Exception as e:
            print('[-] Failed to send client information: ' + str(e))
            sys.exit(0)

    def input_command(self):
        while True:
            try:
                cmd = input(self.client_name + ' > ')
                if not cmd:
                    pass
                elif cmd in ['exit', 'quit']:
                    sys.exit(0)
                elif cmd == 'ls':
                    print('----- Devices -----')
                    for i, (k, v) in enumerate(self.clients.items()):
                        if k == self.client_id:
                            v += ' (this device)'
                        print('{0}   {1}'.format(i, v))
                    print()
                elif cmd.split(' ')[0] == 'all':
                    self.monitor_clipboard('public')
                elif cmd.split(' ')[0] == 'to':
                    try:
                        target = int(cmd.split(' ')[1])
                        target_id = list(self.clients.keys())[target]
                        self.monitor_clipboard('private', target_id)
                    except (IndexError, ValueError):
                        print('[-] Not a valid selection')
                else:
                    print('[-] Command not recognized')
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print('[-] Error: ' + str(e))

    @staticmethod
    def get_time():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def recv(self):
        while True:
            try:
                data = TcpSocket.recv_dict(self.socket)
                if data['msg_type'] == 'text':
                    sender = data['msg']['sender']
                    text = data['msg']['text']
                    self.recent_text = text
                    pyperclip.copy(text)
                    print('[+] {0} Clipboard synced from {1}: {2}'.format(self.get_time(), sender, text))
                elif data['msg_type'] == 'client_dict':
                    self.clients = data['msg']
            except ConnectionResetError:
                print('[-] Server closed')
                self.clients.clear()
                self.socket.close()
                self.socket = socket.socket()
                self.connect()
                self.send_info()
                continue
            except Exception as e:
                print('[-] Error while receiving data: ' + str(e))

    def monitor_clipboard(self, send_type, target_id=None):
        while True:
            try:
                clipboard_text = pyperclip.paste()
                if clipboard_text != '' and clipboard_text != self.recent_text:
                    self.recent_text = clipboard_text
                    print('[+] {0} Clipboard change detected: {1}'.format(self.get_time(), self.recent_text))
                    if send_type == 'public':
                        self.send_public()
                    elif send_type == 'private':
                        self.send_private(target_id)
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print('[-] Error while monitoring clipboard: ' + str(e))

    def send_public(self):
        try:
            data = {
                'msg_type': 'public',
                'sender': self.client_name,
                'text': self.recent_text
            }
            TcpSocket.send_dict(self.socket, data)
        except Exception as e:
            print('[-] Error while sending data: ' + str(e))

    def send_private(self, target_id):
        try:
            data = {
                'msg_type': 'private',
                'target': target_id,
                'sender': self.client_name,
                'text': self.recent_text
            }
            TcpSocket.send_dict(self.socket, data)
        except Exception as e:
            print('[-] Error while sending data: ' + str(e))


client = Client()
client.load_config()
client.connect()
client.send_info()
threading.Thread(target=client.recv, daemon=True).start()
client.input_command()
