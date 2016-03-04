import os
from PyQt4.QtCore import QObject, SIGNAL, pyqtSlot, pyqtSignal
from kazoo.client import KazooClient


class ZkConnection(QObject):
  '''Maintain and abstract away our zookeeper kazoo connection'''

  # Signals our main window thread hits us with
  signal_connect = pyqtSignal(str, int)
  signal_disconnect = pyqtSignal()
  signal_delete = pyqtSignal(str)
  signal_get_contents = pyqtSignal(str)
  signal_set_contents = pyqtSignal(str, str)
  signal_get_kids = pyqtSignal(str)

  def __init__(self, main_window):
    super(ZkConnection, self).__init__()
    self.main_window = main_window
    self.zk = None

    self.host = None
    self.port = None

    # Register callbacks for all those signals.
    self.signal_connect.connect(self.connect)
    self.signal_disconnect.connect(self.disconnect)
    self.signal_get_contents.connect(self.get_contents)
    self.signal_set_contents.connect(self.set_contents)
    self.signal_delete.connect(self.delete)
    self.signal_get_kids.connect(self.get_kids)

  @pyqtSlot(str, int)
  def connect(self, host, port):
    host = str(host)
    port = int(port)

    self.host = host
    self.port = port

    self.zk = KazooClient(hosts='{0}:{1}'.format(host, port), timeout=3)
    try:
      self.zk.start(1)
    except Exception as e:
      self.give_connection_status(True, e)
      return

    self.give_connection_status(True)

  @property
  def connected(self):
    if not self.zk:
      return False
    return self.zk.connected

  @pyqtSlot()
  def disconnect(self):
    if self.connected:
      self.zk.stop()
      self.zk.close()
    self.give_connection_status()

  def give_connection_status(self, first=False, msg=''):
    self.main_window.signal_get_connection_status.emit(self.connected, first, str(msg))

  @pyqtSlot(str)
  def get_contents(self, path):
    path = str(path)
    contents = ''
    if self.connected:
      contents = self.zk.get(path)[0]
    if not contents:
      contents = ''
    self.main_window.signal_get_contents.emit(path, contents)

  @pyqtSlot(str)
  def get_kids(self, path):
    if not self.connected:
      return
    path = str(path)
    items = [os.path.join(path, item) for item in self.zk.get_children(path)]
    paths = {}
    if items:
      for item in items:
        try:
          paths[item] = len(self.zk.get_children(item))
        except Exception as e:
          print e
          paths[item] = 0
    self.main_window.signal_get_kids.emit(path, paths)

  @pyqtSlot(str, str)
  def set_contents(self, path, value):
    if not self.connected:
      self.main_window.signal_show_error_prompt.emit('Cannot set because not connected')
      return

    path = str(path)
    value = str(value)

    try:
      if not self.zk.exists(path):
        self.zk.create(path, value)
        self.main_window.signal_reload_tree.emit()
      else:
        self.zk.set(path, value)
    except Exception as e:
      self.main_window.signal_show_error_prompt.emit('Failed setting: {0}'.format(e))

  @pyqtSlot(str)
  def delete(self, path):
    path = str(path)
    try:
      self.zk.delete(path, -1, False)
      self.main_window.signal_reload_tree.emit()
    except Exception as e:
      self.main_window.signal_show_error_prompt.emit(str(e))
