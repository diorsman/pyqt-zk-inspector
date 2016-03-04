import sys
import os

try:
  from PyQt4 import QtGui
except ImportError:
  # Tweak for mac/pip
  extra_path = '/usr/local/lib/python2.7/site-packages'
  if os.path.exists(extra_path):
    sys.path.append(extra_path)
  try:
    from PyQt4 import QtGui
  except ImportError:
    raise

import signal
from mainwindow import MainWindow


def main():
  '''Spawn main window, start qt, and exit app with proper status when time comes'''
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.show()
  if len(sys.argv) > 1:
    window._load_map(sys.argv[1])
  sys.exit(app.exec_())
