import os
import sys
from PyQt4 import QtGui, QtCore, uic
from kazoo.exceptions import KazooException

from state import ZkState
from config import ZkConfig, ZkConfigException
from historywindow import HistoryWindow


class MainWindow(QtGui.QMainWindow):
  '''Our main window. This class effectively runs the entire app and delegates to other classes as needed'''

  def __init__(self):
    super(MainWindow, self).__init__()

    self.current_path = None

    # Localize our interfaces to our dotfiles and kazoo respectively
    self.config = ZkConfig()
    self.state = ZkState()

    # Load our XML UI widget config
    self.ui = uic.loadUi(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/main.ui'), self)

    # Our tree model controls the list of znodes on the left
    self.tree_model = QtGui.QStandardItemModel()
    self.tree_model.setHorizontalHeaderLabels(['Items'])
    self.ui.znodesTree.setModel(self.tree_model)

    # When we click it, change the znode contents shown
    self.ui.znodesTree.clicked.connect(self.tree_clicked)

    # When we right click it, show options to create child or delete znode
    self.ui.znodesTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.ui.znodesTree.customContextMenuRequested.connect(self.tree_menu)

    # Bind callbacks for clicks/etc
    self.ui.actionQuit.triggered.connect(self.quit)
    self.ui.connectButton.clicked.connect(self.connect)
    self.ui.saveButton.clicked.connect(self.save)
    self.ui.historyButton.clicked.connect(self.history)

    # Keep a single object to refer to our history modal. It continues to get reconfigured,
    # closed, and shown.
    self.history_window = HistoryWindow(self.config, self)

    self.update_widgets()
    self.setWindowTitle('PyZK Inspector')

  @QtCore.pyqtSlot()
  def quit(self):
    sys.exit(0)

  @QtCore.pyqtSlot()
  def connect(self):
    if self.state.connected:
      self.state.disconnect()
    else:
      try:
        host, port = self.ui.hostBox.currentText().trimmed().split(':')
        port = int(port)
      except (ValueError, TypeError):
        QtGui.QMessageBox.critical(None, 'Failed connecting to ZK', 'Format is host:port')
        self.update_widgets()
        return

      try:
        self.state.connect(host, port)

      # Catching all exceptions as different versions of zk have different exception names
      except Exception as e:
        QtGui.QMessageBox.critical(None, 'Failed connecting to ZK', str(e))

      try:
        self.config.add_connection(':'.join(map(str, [host, port])))
      except ZkConfigException as e:
        QtGui.QMessageBox.warning(None, 'Failed adding connection to history', str(e))

    self.update_widgets()
    if self.state.connected:
      self.populate_tree()

  def populate_connection_history(self):
    '''Use our dotfile manager class to populate the editable dropdown with recent ZK connections'''
    connections = self.config.get_connection_history()
    if not connections:
      return
    self.ui.hostBox.clear()
    self.ui.hostBox.addItems(connections)

  def update_widgets(self):
    '''Change the state of our widgets (disabled/enabled/etc) depending on whether we\'re connected'''
    if self.state.connected:
      self.ui.saveButton.setEnabled(True)
      self.ui.historyButton.setEnabled(True)
      self.ui.connectButton.setText('Disconnect')
      self.ui.statusbar.showMessage('Connected to {0}:{1}'.format(self.state.host, self.state.port))
      self.ui.textBox.setReadOnly(False)
    else:
      self.ui.saveButton.setEnabled(False)
      self.ui.historyButton.setEnabled(False)
      self.ui.textBox.setReadOnly(True)
      self.ui.connectButton.setText('Connect')
      self.ui.statusbar.showMessage('Disconnected')
    self.populate_connection_history()

  def recurse_tree(self, path, parent):
    '''Recurse through the entire zookeeper tree to populate list on left'''
    # XXX: this is extremely inefficient if you have at on of znodes. This needs to be
    # rewritten to only parse when the znodes are expanded and not recurse forever

    # Create a standard item which has the path name
    item = QtGui.QStandardItem(os.path.basename(path) or '/')
    item.setEditable(False)

    # Sneakily add the path to this item, so we can refer to it later by the item object
    # alone
    item._path = path

    kids = self.state.get_kids(path)

    for kid in kids:
      self.recurse_tree(os.path.join(path, kid), item)

    # Stupid hacks to get some simple icons on linux
    root_icon_path = '/usr/share/icons/gnome/16x16/mimetypes'

    # These names are standard and Qt might have them for us built in
    if len(kids):
      icon_name = 'package-x-generic'
    else:
      icon_name = 'text-x-generic'

    icon_file = os.path.join(root_icon_path, icon_name + '.png')
    item.setIcon(QtGui.QIcon.fromTheme(icon_name, QtGui.QIcon(icon_file)))

    parent.appendRow(item)

  def populate_tree(self):
    '''Empty list on left, then recursively parse zookeeper to built the tree anew'''
    self.tree_model.clear()
    if self.state.connected:
      self.recurse_tree('/', self.tree_model)

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_clicked(self, index):
    '''When we click the tree, find where we clicked and update textbox with the current znode'''
    item = self.tree_model.itemFromIndex(index)
    self.current_path = item._path
    contents = self.state.get_contents(self.current_path)

    if contents:
      self.ui.textBox.setText(contents)

    if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:
      # print 'would spawn context for ' + self.current_path
      pass

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_menu(self, position):
    '''Create our context menu, which currenty lets you delete and create children of znodes'''
    indexes = self.znodesTree.selectedIndexes()
    if not len(indexes):
      return
    item = self.tree_model.itemFromIndex(indexes[0])
    path = item._path

    menu = QtGui.QMenu()
    menu.addAction('Create child of ' + path, lambda: self.create_child(path))

    if path != '/':
      menu.addAction('Delete ' + path, lambda: self.delete_path(path))

    # Spawn the context menu inside the treeview object where you clicked
    menu.exec_(self.znodesTree.viewport().mapToGlobal(position))

  @QtCore.pyqtSlot()
  def save(self):
    '''When you click "Save", write contents in textbox to highlighted znode. Also save a backup.'''
    path = self.current_path

    if not path:
      QtGui.QMessageBox.warning(None, 'No file selected', 'Cannot save as no path is selected')
      return

    if not self.confirm_prompt('Are you sure?', 'Do you REALLY want to write to {0}?'.format(path)):
      return

    old_contents = self.state.get_contents(path).strip()
    new_contents = str(self.ui.textBox.toPlainText())

    if old_contents != '':
      self.config.add_file_revision(path, old_contents)

    self.state.set_contents(path, new_contents)

  @QtCore.pyqtSlot()
  def history(self):
    '''Bring up history window for current znode, to view and revert to past saved revisions'''
    path = self.current_path

    if not path:
      QtGui.QMessageBox.warning(None, 'No file selected', 'Cannot show history as no path is selected')
      return

    self.history_window.set_path(path)
    self.history_window.populate_list(path)
    self.history_window.show()

  # XXX:
  # - Refuse to work on /
  # - Check for children; if there are, refuse or ask to confirm recursive
  # - If individual file, copy the file locally and preserve "history"
  # - Intelligently repopulate tree. Expand the parent of the leaf you killed,
  #   but keep / highlighted
  def delete_path(self, path):
    '''When you right click a znode and do delete'''
    if path == '/':
      QtGui.QMessageBox.critical(None, 'No', 'I refuse to delete /')
      return
    if not self.confirm_prompt('Are you sure?', 'Do you REALLY want to delete {0}?'.format(path)):
      return
    print 'would delete ' + path
    self.state.delete(path)
    self.populate_tree()

  def create_child(self, parent):
    '''When you right click a znode and do create child, prompt for the child path to create and initialize it'''
    result = QtGui.QInputDialog.getText(self, 'Child name', 'What child name under "{0}"?'.format(parent))
    if not result[1]:
      return
    child = str(result[0]).strip()
    if child.startswith('/'):
      child = child[1:]
    if child == '':
      QtGui.QMessageBox.critical(None, 'No', 'Empty path. Give me something that doesn\'t start with /')
      return
    self.state.set_contents(os.path.join(parent, child), '')
    self.populate_tree()

  def confirm_prompt(self, title, message):
    '''Simple wrapper function that spawns a yes/no prompt and returns bool if they click yes'''
    result = QtGui.QMessageBox.question(self, title, message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
    return result == QtGui.QMessageBox.Yes
