# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2014 Tiago Coutinho
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper to load ui files for widgets.

The folowing example assumes the existence of the ui file 
:file:`<my_widget_dir>/ui/MyWidget.ui` which is a QWidget panel with *at
least* a QPushButton with objectName *my_button* ::

    from qarbon.external.qt import Qt
    from qarbon.qt.gui.ui import UILoadable
        
    @UILoadable
    class MyWidget(Qt.QWidget):
    
        def __init__(self, parent=None):
            Qt.QWidget.__init__(self, parent)
            self.loadUi()
            self.my_button.setText("This is MY button")
"""

import os
import sys
import functools

from qarbon.external.qt import Qt
from qarbon.external.qt import uic


def loadUi(obj, filename=None, path=None):
    """
    Loads a QtDesigner .ui file into the given widget.
    If no filename is given, it tries to load from a file name which is the
    widget class name plus the extension ".ui" (example: if your
    widget class is called MyWidget it tries to find a MyWidget.ui).
    If path is not given it uses the directory where the python file which
    defines the widget is located plus a *ui* directory (example: if your widget
    is defined in a file /home/homer/workspace/qarbongui/my_widget.py then it uses
    the path /home/homer/workspace/qarbongui/ui)

    :param filename: the QtDesigner .ui file name [default: None, meaning
                      calculate file name with the algorithm explained before]
    :type filename: str
    :param path: directory where the QtDesigner .ui file is located
                 [default: None, meaning calculate path with algorithm explained
                 before]
    :type path: str
    """
    if path is None:
        obj_file = sys.modules[obj.__module__].__file__
        path = os.path.join(os.path.dirname(obj_file), 'ui')
    if filename is None:
        filename = obj.__class__.__name__ + os.path.extsep + 'ui'
    full_name = os.path.join(path, filename)
    uic.loadUi(full_name, baseinstance=obj)


def UILoadable(klass=None, with_ui=None):
    """
    A class decorator intended to be used in a Qt.QWidget to make its UI
    loadable from a predefined QtDesigner UI file.
    This decorator will add a :func:`loadUi` method to the decorated class and
    optionaly a property with a name given by *with_ui* parameter.

    The folowing example assumes the existence of the ui file 
    :file:`<my_widget_dir>/ui/MyWidget.ui` which is a QWidget panel with *at
    least* a QPushButton with objectName *my_button* ::

        from qarbon.external.qt import Qt
        from qarbon.qt.gui.ui import UILoadable
        
        @UILoadable
        class MyWidget(Qt.QWidget):

            def __init__(self, parent=None):
                Qt.QWidget.__init__(self, parent)
                self.loadUi()
                self.my_button.setText("This is MY button")

    Another example using a :file:`superUI.ui` file in the same directory as
    the widget. The widget UI components can be accessed through the widget
    member *_ui* ::

        import os.path
        
        from qarbon.external.qt import Qt
        from qarbon.qt.gui.ui import UILoadable
        
        @UILoadable(with_ui="_ui")
        class MyWidget(Qt.QWidget):

            def __init__(self, parent=None):
                Qt.QWidget.__init__(self, parent)
                self.loadUi(filename="superUI.ui", path=os.path.dirname(__file__))
                self._ui.my_button.setText("This is MY button")

    :param with_ui: assigns a member to the decorated class from which you
                    can access all UI components [default: None, meaning no
                    member is created]
    :type with_ui: str
    """
    if klass is None:
        return functools.partial(UILoadable, with_ui=with_ui)
    klass.loadUi = loadUi
    if with_ui is not None:
        ui_prop = property(lambda x: x)
        setattr(klass, with_ui, ui_prop)
    return klass


def main():
    from qarbon.qt.gui.application import Application
    
    app = Application()
    
    @UILoadable(with_ui="ui")
    class A(Qt.QWidget):

        def __init__(self, parent=None):
            Qt.QWidget.__init__(self, parent)
            import qarbon.qt.gui.panel.ui
            path = os.path.dirname(qarbon.qt.gui.panel.ui.__file__)
            self.loadUi(filename='QarbonMessagePanel.ui', path=path)
    
    gui = A()
    gui.show()
    app.exec_()
    
if __name__ == "__main__":
    main()
