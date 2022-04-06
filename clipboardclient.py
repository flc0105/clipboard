# coding=utf-8
import hashlib
import json
import os
import socket
import struct
import sys
import threading
import time
import uuid
from io import BytesIO

import pyperclip
import win32clipboard
from PIL import ImageGrab, Image, ImageFile

import client

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ClipboardClient(object):
    def __init__(self):
        self.host = None
        self.port = None
        self.client_name = socket.gethostname()
        self.group_id = None
        self.interval = 1
        self.auto_sync = None
        self.save_image = None
        self.socket = None
        self.recent_text = None
        self.image_hash = None
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
            self.group_id = config['group_id']
            if config['interval']:
                self.interval = config['interval']
            self.auto_sync = config['auto_sync']
            self.save_image = config['save_image']
        except Exception as e:
            print('[-] Failed to load configuration: ' + str(e))
            sys.exit(0)

    def connect(self):
        try:
            self.socket = client.Client(self.host, self.port)
        except Exception as e:
            print('[-] Connection failed: ' + str(e))
            sys.exit(0)

    def send_info(self):
        try:
            client_info = {
                'client_id': self.client_id,
                'client_name': self.client_name,
                'group_id': self.group_id
            }
            self.socket.send_dict(client_info)
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
                data = self.socket.recv_dict()
                if data['msg_type'] == 'text':
                    sender = data['msg']['sender']
                    text = data['msg']['text']
                    self.recent_text = text
                    pyperclip.copy(text)
                    print('[+] {0} Clipboard synced from {1}: {2}'.format(self.get_time(), sender, text))
                elif data['msg_type'] == 'image':
                    image_bytes = self.socket.recv_bytes()
                    print('[+] {0} You received an image from {1}'.format(self.get_time(), data['sender']))
                    image = Image.open(image_bytes)
                    image.show()
                    self.image_hash = hashlib.sha256(image.tobytes()).hexdigest()
                    b = BytesIO()
                    image.save(b, 'BMP')
                    if self.save_image:
                        image.save(str(time.strftime('%Y%m%d%H%M%S', time.localtime())) + '.png', 'PNG')
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, b.getvalue()[14:])
                    win32clipboard.CloseClipboard()
                elif data['msg_type'] == 'client_dict':
                    self.clients = data['msg']
                    del self.clients[self.client_id]
            except (ConnectionResetError, struct.error) as e:
                print('[-] Disconnected: ' + str(e))
                sys.exit(0)
            except Exception as exception:
                print('[-] Error while receiving data: ' + str(exception))
                time.sleep(2)

    def monitor_clipboard(self, send_type, target_id=None):
        while True:
            try:
                im = ImageGrab.grabclipboard()
                if im is None:
                    clipboard_text = pyperclip.paste()
                    if clipboard_text != '' and clipboard_text != self.recent_text:
                        self.recent_text = clipboard_text
                        print('[+] {0} Clipboard change detected: {1}'.format(self.get_time(), self.recent_text))
                        if send_type == 'public':
                            self.send_public()
                        elif send_type == 'private':
                            self.send_private(target_id)
                elif isinstance(im, Image.Image):
                    image_hash = hashlib.sha256(im.tobytes()).hexdigest()
                    if image_hash != self.image_hash:
                        self.image_hash = image_hash
                        print('[+] {0} You copied an image'.format(self.get_time()))
                        self.socket.send_dict({'msg_type': 'image', 'sender': self.client_name})
                        b = BytesIO()
                        im.save(b, 'BMP')
                        self.socket.send_bytes(b)
                else:
                    filename = im[0]
                    if os.path.isfile(filename):
                        try:
                            image = Image.open(filename)
                            b = BytesIO()
                            image.save(b, 'BMP')
                            win32clipboard.OpenClipboard()
                            win32clipboard.EmptyClipboard()
                            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, b.getvalue()[14:])
                            win32clipboard.CloseClipboard()
                        except IOError:
                            pass
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print('[-] Error while monitoring clipboard: ' + str(e))
                time.sleep(2)

    def send_public(self):
        try:
            data = {
                'msg_type': 'public',
                'sender': self.client_name,
                'text': self.recent_text
            }
            self.socket.send_dict(data)
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
            self.socket.send_dict(data)
        except Exception as e:
            print('[-] Error while sending data: ' + str(e))


clipboard_client = ClipboardClient()
clipboard_client.load_config()
clipboard_client.connect()
clipboard_client.send_info()
threading.Thread(target=clipboard_client.recv, daemon=True).start()
if clipboard_client.auto_sync:
    clipboard_client.monitor_clipboard('public')
else:
    clipboard_client.input_command()
