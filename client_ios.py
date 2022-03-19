# coding=utf-8
import clipboard
import dialogs
import json
import pickle
import re
import socket
import struct
import sys
import threading
import ui
import webbrowser


class TableView(object):
  def __init__(self, data_dict=None):
    self.data = data_dict

  def key(self, section):
    return list(self.data.keys())[section]

  def tableview_number_of_sections(self, tableview):
    return len(self.data)

  def tableview_number_of_rows(self, tableview, section):
    return 1

  def tableview_cell_for_row(self, tableview, section, row):
    cell = ui.TableViewCell()
    cell.text_label.text = self.data[self.key(section)]
    return cell

  def tableview_did_select(self, tableview, section, row):
    global selected_uuid
    selected_uuid = self.key(section)


class Client(object):

  def __init__(self):
    self.host = '127.0.0.1'
    self.port = 8888
    self.socket = socket.socket()
    self.clients = {}
    self.v = None
    global s
    s = self.socket
    global selected_uuid
    selected_uuid = ''

  def connect(self):
    try:
      self.socket.connect((self.host, self.port))
    except Exception as e:
      dialogs.alert(str(e))
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
        clipboard.set(text)
        self.v['textview1'].text = text
        if re.match('^https?://\\w.+$', text):
          if dialogs.alert(title='Open this link in web browser?', button1='Open', button2='Cancel',
          hide_cancel_button=True) == 1:
            webbrowser.open('safari-' + text)
      else:
        self.clients = pickle.loads(data)
        self.v['tableview1'].data_source = TableView(self.clients)
        self.v['tableview1'].delegate = TableView(self.clients)
        self.v['tableview1'].reload_data()

  def main(self):
    self.v = ui.load_view()
    self.v['button1'].action = self.send
    self.connect()
    self.v.present('sheet')

  def send(self, sender):
    global selected_uuid
    if not selected_uuid:
      dialogs.alert('clipboard', 'No device selected')
      return
    clip = clipboard.get()
    data = {
    'target': selected_uuid,
    'text': clip
    }
    data_json = json.dumps(data)
    data_len = struct.pack('i', len(data_json))
    self.socket.send(data_len)
    self.socket.send(data_json.encode())
    dialogs.hud_alert('Success')


class MyView(ui.View):
  def will_close(self):
    global s
    s.close()


if __name__ == '__main__':
  client = Client()
  client.main()
