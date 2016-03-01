from PyQt4 import QtGui, QtCore, uic
from datetime import datetime


class HistoryWindow(QtGui.QDialog):

  def __init__(self, config, mainwindow):
    super(HistoryWindow, self).__init__()
    self.current_rev = None
    self.path = None
    self.config = config
    self.mainwindow = mainwindow
    self.ui = uic.loadUi('history.ui', self)
    self.list_model = QtGui.QStandardItemModel()
    self.list_model.setHorizontalHeaderLabels(['Revisions'])
    self.ui.revisionsList.setModel(self.list_model)
    self.ui.loadButton.clicked.connect(self.load)
    self.ui.closeButton.clicked.connect(self.close_window)
    self.ui.revisionsList.clicked.connect(self.list_clicked)
    self.setWindowTitle('History')

  def set_path(self, path):
    self.path = path
    self.setWindowTitle('History of ' + path)

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def list_clicked(self, index):
    if not self.path:
      return
    item = self.list_model.itemFromIndex(index)
    date = item._date
    contents = self.config.get_file_revision(self.path, date)
    self.ui.revisionText.setText(contents)

  def populate_list(self, path):
    self.list_model.clear()
    if not self.path:
      return
    revisions = self.config.list_file_revisions(self.path)
    for date in sorted(revisions.keys()):
      size = revisions[date]
      item = QtGui.QStandardItem('{0} ({1} bytes)'.format(datetime.fromtimestamp(date), size))
      item.setEditable(False)
      item._date = date
      self.list_model.appendRow(item)

  def load(self):
    if not self.path:
      return
    contents = str(self.revisionText.toPlainText())
    if len(contents):
      self.mainwindow.ui.textBox.setText(contents)
    self.close_window()

  def close_window(self):
    self.close()
