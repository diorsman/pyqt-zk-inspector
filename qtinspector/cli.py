from mainwindow import MainWindow
from PyQt4 import QtGui
import signal
import sys


def main():
  '''Spawn main window, start qt, and exit app with proper status when time comes'''
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.show()
  if len(sys.argv) > 1:
    window._load_map(sys.argv[1])
  sys.exit(app.exec_())
