import os
from PyQt4.QtCore import QObject, SIGNAL, pyqtSlot, pyqtSignal
from kazoo.client import KazooClient


class ZkConnection(QObject):
  '''Maintain and abstract away our zookeeper kazoo connection'''

  connect_signal = pyqtSignal(list)
  disconnect_signal = pyqtSignal()
  delete_signal = pyqtSignal(str)
  get_contents_signal = pyqtSignal(str)
  set_contents_signal = pyqtSignal(str, str)
  get_kids_signal = pyqtSignal(str)

  def __init__(self, main_window):
    super(ZkConnection, self).__init__()
    self.main_window = main_window
    self.zk = None
    self.host = None
    self.port = None

    self.connect_signal.connect(self.connect)
    self.disconnect_signal.connect(self.disconnect)
    self.get_contents_signal.connect(self.get_contents)
    self.set_contents_signal.connect(self.set_contents)
    self.delete_signal.connect(self.delete)
    self.get_kids_signal.connect(self.get_kids)

  @pyqtSlot(list)
  def connect(self, args):
    host, port = args
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
    self.main_window.get_connection_status_signal.emit(self.connected, first, str(msg))

  @pyqtSlot(str)
  def get_contents(self, path):
    path = str(path)
    if self.connected:
      contents = self.zk.get(path)[0]
    else:
      contents = ''
    self.main_window.get_contents_signal.emit(path, contents)

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
    self.main_window.get_kids_signal.emit(path, paths)

  @pyqtSlot(str, str)
  def set_contents(self, path, value):
    print 'worker: received set contents'
    if not self.connected:
      self.emit(SIGNAL('give_set_contents()'), [path, False])
      return

    if not self.zk.exists(path):
      self.zk.create(path, value)
      self.emit(SIGNAL('give_set_contents()'), [path, True])
    else:
      self.zk.set(path, value)
      self.emit(SIGNAL('give_set_contents()'), [path, True])

  @pyqtSlot(str)
  def delete(self, path):
    print 'worker: received delete'
    if self.connected:
      self.emit(SIGNAL('give_delete()'), [path, self.zk.delete(path, -1, False)])
    else:
      self.emit(SIGNAL('give_delete()'), [path, False])
