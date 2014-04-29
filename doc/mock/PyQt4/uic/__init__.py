from __future__ import print_function

import sip

def _mockf(*args, **kwargs): pass


_display_code = '\nif __name__ == "__main__":\n\timport sys\n\tapp = QtGui.QApplication(sys.argv)\n\t%(widgetname)s = QtGui.%(baseclass)s()\n\tui = %(uiclass)s()\n\tui.setupUi(%(widgetname)s)\n\t%(widgetname)s.show()\n\tsys.exit(app.exec_())\n'

_header = "# -*- coding: utf-8 -*-\n\n# Form implementation generated from reading ui file '%s'\n#\n# Created: %s\n#      by: PyQt4 UI code generator %s\n#\n# WARNING! All changes made in this file will be lost!\n\n"

_pyqt3_wrapper_code = '\nclass %(widgetname)s(QtGui.%(baseclass)s, %(uiclass)s):\n\tdef __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):\n\t\tQtGui.%(baseclass)s.__init__(self, parent, f)\n\n\t\tself.setupUi(self)\n'

def compileUi(*a,**k): pass

def compileUiDir(*a,**k): pass

def loadUi(*a,**k): pass

def loadUiType(*a,**k): pass



