import os
from kazoo.client import KazooClient


class ZkState:
  '''Maintain and abstract away our zookeeper kazoo connection'''

  def __init__(self):
    self.zk = None
    self.host = None
    self.port = None

  def connect(self, host, port):
    self.host = host
    self.port = port
    self.zk = KazooClient(hosts='{0}:{1}'.format(host, port), timeout=2)
    self.zk.start()

  @property
  def connected(self):
    if not self.zk:
      return False
    return self.zk.connected

  def disconnect(self):
    if self.connected:
      self.zk.stop()
      self.zk.close()

  def get_contents(self, path):
    if not self.connected:
      return ''
    return self.zk.get(path)[0]

  def get_kids(self, path):
    if not self.connected:
      return []
    return [os.path.join(path, item) for item in self.zk.get_children(path)]

  def set_contents(self, path, value):
    if not self.connected:
      return False
    if not self.zk.exists(path):
      return self.zk.create(path, value)
    else:
      return self.zk.set(path, value)

  def delete(self, path):
    if not self.connected:
      return False
    return self.zk.delete(path, -1, False)
