import os
import json
import glob

class ZkConfig:
  
  def __init__(self):
    self.config_dir = os.path.expanduser('~/.qtinspector')
    self.connection_file = os.path.join(self.config_dir, 'connections.json')
    self.revisions_dir = os.path.join(self.config_dir, 'revisions')
    if not os.path.exists(self.config_dir):
      try:
        os.makedirs(self.config_dir)
      except IOError:
        self.config_dir = False
        raise UserWarning('Cannot create {0}'.format(self.config_dir))

  def get_connection_history(self):
    if not self.config_dir:
      return []

    if not os.path.exists(self.connection_file):
      return []

    try:
      with open(self.connection_file, 'r') as h:
        data = json.load(h)
        return data['connections']
    except IOError as e:
      return []
    except (ValueError, KeyError) as e:
      return []

  def add_connection(self, host):
    if not self.config_dir:
      return
    connections = self.get_connection_history()
    try:
      index = connections.index(host)
      del connections[index]
    except (ValueError, IndexError):
      pass
    connections.insert(0, host)
    try:
      with open(self.connection_file, 'w') as h:
        json.dump({'connections': connections}, h, indent=4)
        h.write('\n')
    except IOError as e:
      raise ZkConfigException('Failed writing "{0}": {1}'.format(self.connection_file, e))

  def add_file_revision(self, path, contents):
    if not self.config_dir:
      return

  def list_file_revisions(self, path):
    if not self.config_dir:
      return {}

  def get_file_revision(self, path, revision):
    if not self.config_dir:
      return False


class ZkConfigException(Exception):
  pass
