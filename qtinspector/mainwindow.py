import os
import sys
import signal
from PyQt4 import QtGui, QtCore, uic
from kazoo.exceptions import KazooException
from kazoo.handlers.threading import TimeoutError

from state import ZkState
from config import ZkConfig, ZkConfigException
from historywindow import HistoryWindow


class MainWindow(QtGui.QMainWindow):

  def __init__(self):
    super(MainWindow, self).__init__()
    self.config = ZkConfig()
    self.state = ZkState()
    self.tree_model = QtGui.QStandardItemModel()
    self.tree_model.setHorizontalHeaderLabels(['Items'])
    self.ui = uic.loadUi(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/main.ui'), self)
    self.setWindowTitle('PyZK Inspector')
    self.ui.actionQuit.triggered.connect(self.quit)
    self.ui.connectButton.clicked.connect(self.connect)
    self.ui.saveButton.clicked.connect(self.save)
    self.ui.historyButton.clicked.connect(self.history)
    self.ui.znodesTree.setModel(self.tree_model)
    self.ui.znodesTree.clicked.connect(self.tree_clicked)
    self.ui.znodesTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.ui.znodesTree.customContextMenuRequested.connect(self.tree_menu)
    self.update_widgets()
    self.current_path = None
    self.history_window = HistoryWindow(self.config, self)

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
      except (TimeoutError, KazooException) as e:  
        QtGui.QMessageBox.critical(None, 'Failed connecting to ZK', str(e))

      try:
        self.config.add_connection(':'.join(map(str, [host, port])))
      except ZkConfigException as e:
        QtGui.QMessageBox.warning(None, 'Failed adding connection to history', str(e))

    self.update_widgets()
    if self.state.connected:
      self.populate_tree()

  def populate_connection_history(self):
    connections = self.config.get_connection_history()
    if not connections:
      return
    self.ui.hostBox.clear()
    self.ui.hostBox.addItems(connections)

  def update_widgets(self):
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
    item = QtGui.QStandardItem(os.path.basename(path) or '/')
    item.setEditable(False)
    item._path = path
    
    kids = self.state.get_kids(path)
    
    for kid in kids:
      self.recurse_tree(os.path.join(path, kid), item)

    root_icon_path = '/usr/share/icons/gnome/16x16/mimetypes'

    if len(kids):
      icon_name = 'package-x-generic'
    else:
      icon_name = 'text-x-generic'

    icon_file = os.path.join(root_icon_path, icon_name + '.png')
    item.setIcon(QtGui.QIcon.fromTheme(icon_name, QtGui.QIcon(icon_file)))

    parent.appendRow(item)

  def populate_tree(self):
    self.tree_model.clear()
    if self.state.connected:
      self.recurse_tree('/', self.tree_model)

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_clicked(self, index):
    item = self.tree_model.itemFromIndex(index)
    self.current_path = item._path
    contents = self.state.get_contents(self.current_path)
    self.ui.textBox.setText(contents)

    if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:
      print 'would spawn context for ' + path

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_menu(self, position):
    indexes = self.znodesTree.selectedIndexes()
    if not len(indexes):
      return
    item = self.tree_model.itemFromIndex(indexes[0])
    path = item._path

    menu = QtGui.QMenu()
    menu.addAction('Create child of ' + path, lambda: self.create_child(path))

    if path != '/':
      menu.addAction('Delete ' + path, lambda: self.delete_path(path))

    menu.exec_(self.znodesTree.viewport().mapToGlobal(position))

  @QtCore.pyqtSlot()
  def save(self):
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
    if path == '/':
      QtGui.QMessageBox.critical(None, 'No', 'I refuse to delete /')
      return
    if not self.confirm_prompt('Are you sure?', 'Do you REALLY want to delete {0}?'.format(path)):
      return
    print 'would delete ' + path
    self.state.delete(path)
    self.populate_tree()

  def create_child(self, parent):
    result = QtGui.QInputDialog.getText(self, 'Child name', 'What child name under "{0}"?'.format(parent))
    if not result[1]:
      return
    child = str(result[0]).strip()
    if child.startswith('/'):
      child = path[1:]
    if child == '':
      QtGui.QMessageBox.critical(None, 'No', 'Empty path. Give me something that doesn\'t start with /')
      return
    self.state.set_contents(os.path.join(parent, child), '')
    self.populate_tree()

  def confirm_prompt(self, title, message):
    result = QtGui.QMessageBox.question(self, title, message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
    return result == QtGui.QMessageBox.Yes

def main():
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.show()
  if len(sys.argv) > 1:
    window._load_map(sys.argv[1])
  sys.exit(app.exec_())