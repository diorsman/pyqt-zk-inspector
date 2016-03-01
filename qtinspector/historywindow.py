import os
from PyQt4 import QtGui, QtCore, uic
from datetime import datetime


class HistoryWindow(QtGui.QDialog):
  '''Qt Window for viewing a local list of histories for a znode'''

  def __init__(self, config, mainwindow):
    super(HistoryWindow, self).__init__()
    self.setWindowTitle('History')

    # Dependency inject our config manager and mainwindow objects
    self.config = config
    self.mainwindow = mainwindow

    # This gets reset as we change znodes and respawn this window
    self.path = None

    # Get our XML widgets config
    self.ui = uic.loadUi(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui/history.ui'), self)

    # Configure the data model for our list of revisions on left side of window
    self.list_model = QtGui.QStandardItemModel()
    self.list_model.setHorizontalHeaderLabels(['Revisions'])
    self.ui.revisionsList.setModel(self.list_model)

    # Bind our button clicks
    self.ui.loadButton.clicked.connect(self.load)
    self.ui.closeButton.clicked.connect(self.close)
    self.ui.revisionsList.clicked.connect(self.list_clicked)

  def set_path(self, path):
    '''Localize path. We use the same HistoryWindow object throughout the entire program so we change this often'''
    self.path = path
    self.setWindowTitle('History of ' + path)

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def list_clicked(self, index):
    '''When list on left is clicked, show relevant revision on right'''
    if not self.path:
      return

    item = self.list_model.itemFromIndex(index)

    # This property was tacked on below; it is not present in this QstandardItem by default
    date = item._date

    contents = self.config.get_file_revision(self.path, date)
    self.ui.revisionText.setText(contents)

  def populate_list(self, path):
    '''Empty the list on the left and repopulate it from our glob'''

    self.list_model.clear()

    if not self.path:
      return

    revisions = self.config.list_file_revisions(self.path)

    # Sorting keys because I don't want to rely on OrderedDict existing as this is meant to run outside
    # of a venv on old versions of python
    for date in sorted(revisions.keys()):
      size = revisions[date]
      item = QtGui.QStandardItem('{0} ({1} bytes)'.format(datetime.fromtimestamp(date), size))
      item.setEditable(False)

      # Sneakily add a propety to our item object to store our date within, so we can refer to it
      # when we click on it
      item._date = date

      self.list_model.appendRow(item)

  def load(self):
    '''Populate the text box in the mainwindow with the currently selected revision, then close window'''
    if not self.path:
      return

    # Casting from QString to str() so it acts like a normal string
    contents = str(self.revisionText.toPlainText())

    if len(contents):
      self.mainwindow.ui.textBox.setText(contents)

    self.close()
