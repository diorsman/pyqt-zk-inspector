import os
import time
import json
import glob


class ZkConfig:
  '''
    Interface with our dotfiles, mainly to store our list of last used connections
    and backups of revisions as we delete and edit files
  '''

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
    '''Parse our connections,json file and return our results'''

    if not self.config_dir:
      return []

    if not os.path.exists(self.connection_file):
      return []

    try:
      with open(self.connection_file, 'r') as h:
        data = json.load(h)
        return data['connections']
    except IOError:
      return []
    except (ValueError, KeyError):
      return []

  def add_connection(self, host):
    '''Prepend a connection to our connections.json file. Make sure it\'s at front of list if we already have it '''

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

  def revision_path(self, path, rev=None):
    '''Given a zookeeper path, formulate our local path for the backup revisions'''

    # Note, this keeps everything in the same folder. It is really bad. It is done this way,
    # instead of using a verbatim local tree, because zookeeper folders have text as well as
    # children.
    path = path.strip().replace('/', '_')
    if rev:
      path += '-' + str(rev)
    return os.path.join(self.revisions_dir, path)

  def add_file_revision(self, path, contents):
    if not self.config_dir:
      return

    if contents == '':
      return

    path = self.revision_path(path, int(time.time()))

    parent = os.path.dirname(path)

    if not os.path.exists(parent):
      os.makedirs(parent)

    with open(path, 'w') as h:
      h.write(contents)

  def list_file_revisions(self, path):
    '''Glob over where our revisions for a path should be and return their dates and bytes'''
    if not self.config_dir:
      return {}
    if path.startswith('/'):
      path[1:]
    if path == '':
      return {}

    paths = glob.glob(self.revision_path(path, '*'))

    revisions = {}

    for path in paths:
      try:
        date = int(path.split('-')[-1])
      except ValueError:
        continue
      try:
        revisions[date] = os.path.getsize(path)
      except IOError:
        continue

    return revisions

  def get_file_revision(self, path, revision):
    '''Get text of a revision'''
    if not self.config_dir:
      return False
    path = self.revision_path(path, revision)
    if not os.path.exists(path):
      return ''
    try:
      with open(path, 'r') as h:
        return h.read()
    except IOError:
      return ''


class ZkConfigException(Exception):
  pass
