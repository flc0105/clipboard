# coding=utf-8
import json
import pickle
import re
import socket
import struct
import sys
import threading
import webbrowser
from tkinter import *
from tkinter import ttk, messagebox, Menu

import pyperclip
from wcwidth import wcwidth

root = Tk()


class Client(object):

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 8888
        self.socket = socket.socket()
        self.clients = {}
        self.tree_device = None
        self.tree_text = None
        self.menu = None

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            messagebox.showerror('clipboard', str(e))
            sys.exit(0)
        hostname = socket.gethostname().encode()
        self.socket.send(struct.pack('i', len(hostname)))
        self.socket.send(hostname)
        threading.Thread(target=self.recv_data, daemon=True).start()

    def recv_data(self):
        while True:
            code = struct.unpack('i', self.socket.recv(4))[0]
            size = struct.unpack('i', self.socket.recv(4))[0]
            data = b''
            while size:
                buf = self.socket.recv(size)
                size -= len(buf)
                data += buf
            if code:
                text = str(data.decode())
                pyperclip.copy(text)
                item = self.tree_text.insert('', END, value=[text], text=truncate(text))
                self.tree_text.move(item, '', 0)
                self.tree_text.selection_set(item)
                if re.match('^https?://\\w.+$', text):
                    if messagebox.askyesno(message='Open this link in web browser?'):
                        webbrowser.open(text)
            else:
                self.clients = pickle.loads(data)
                self.tree_device.delete(*self.tree_device.get_children())
                for i, (k, v) in enumerate(self.clients.items()):
                    self.tree_device.insert('', END, value=k, text=v)

    def send(self):
        uuid = self.tree_device.item(self.tree_device.focus())['values']
        if not uuid:
            messagebox.showinfo('clipboard', 'No device selected')
            return
        uuid = uuid[0]
        clipboard = pyperclip.paste()
        data = {
            'target': uuid,
            'text': clipboard
        }
        data_json = json.dumps(data)
        data_len = struct.pack('i', len(data_json))
        self.socket.send(data_len)
        self.socket.send(data_json.encode())

    def main(self):
        frame1 = Frame()
        frame1.pack(side='left', fill=Y)
        lbl = Label(frame1, text='Devices')
        lbl.pack()
        self.tree_device = ttk.Treeview(frame1, show='tree')
        self.tree_device.pack(fill=Y, expand=TRUE)
        button = ttk.Button(frame1, text='Send', command=self.send)
        button.pack(fill=X)
        frame2 = Frame()
        frame2.pack(side='right', fill=BOTH, expand=TRUE)
        ttk.Style().configure('myStyle1.Treeview', rowheight=40, font=('宋体', 9))
        self.tree_text = ttk.Treeview(frame2, show='tree', style='myStyle1.Treeview')
        self.tree_text.bind('<Double-1>', self.show_detail)
        self.tree_text.bind('<Button-3>', self.popup)
        self.tree_text.pack(fill=BOTH, expand=TRUE)
        self.menu = Menu(root, tearoff=0)
        self.menu.add_command(label='Copy', command=self.copy)
        self.menu.add_command(label='Delete', command=self.delete)
        root.title('clipboard')
        root.geometry('600x300')
        root.eval('tk::PlaceWindow . center')
        root.after_idle(self.connect)
        root.mainloop()

    def popup(self, event):
        iid = self.tree_text.identify_row(event.y)
        if iid:
            self.tree_text.selection_set(iid)
            self.menu.post(event.x_root, event.y_root)
        else:
            pass

    def copy(self):
        item = self.tree_text.selection()
        value = self.tree_text.item(item, 'values')[0]
        pyperclip.copy(value)

    def delete(self):
        item = self.tree_text.selection()
        self.tree_text.delete(item)

    def show_detail(self, event):
        if not self.tree_text.identify_row(event.y):
            return
        item = self.tree_text.selection()[0]
        value = self.tree_text.item(item, 'value')[0]
        top = Toplevel(root)
        top.geometry('%dx%d+%d+%d' % (400, 200, root.winfo_x() + 100, root.winfo_y() + 50))
        top.focus()
        text = Text(top)
        text.pack(fill=BOTH, expand=TRUE)
        text.insert(1.0, value)


def truncate(string):
    string = string.strip().replace('\n', '').replace('\r', '')
    size = 0
    for i, char in enumerate(str(string)):
        width = wcwidth(char)
        if size + width > 55:
            return string[0:i] + '..'
        size += width
    return string


client = Client()
client.main()
