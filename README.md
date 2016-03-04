# Qt ZK Inspector

Simple interface to browsing and editing ZooKeeper from Python, leveraging Kazoo and PyQt4. Effectively a lighter version of ZooInspector.

![screenshot](http://jrgp.us/screenshots/qtinspector/mac_mainwindow1.png)

### Features

- Cross platform. Tested on Linux + mac
- Keeps local history of your edits, so you can revert changes if they cause problems
- Makes use of threads so the UI doesn't freeze when you connect and perform other actions

### Run

    ./inspector.py

### Deps

You need PyQt4 and Kazoo. PyQt4 is not installable via pip, but instead via your distribution's package manager.

RHEL/Centos 6:

    sudo yum install PyQt4 python-kazoo

Debian/Ubuntu:

    sudo apt-get install python-qt4 python-kazoo
    
Mac:

    brew install pyqt qt
    sudo pip install Kazoo
    
### Meta

- License: GPL
- Contact: Joe Gillotti (<joe@u13.net>)
