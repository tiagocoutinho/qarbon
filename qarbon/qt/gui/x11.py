# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""A X11 widget that may run any command and an XTermWidget runs a xterm.

.. note:: this widget only works on X11 systems.

Example::

    from qarbon.external.qt import QtGui
    from qarbon.qt.gui.application import Application
    from qarbon.qt.gui.x11terminal import XTermWindow

    app = Application()
    term = XTermWindow()
    term.start()
    term.show()
    app.exec_()"""

__all__ = ["XEmbedCommandWidget", "XTermWidget",
           "XEmbedCommandWindow", "XTermWindow"]

import weakref

from qarbon import log
from qarbon.external.qt import QtCore, QtGui
from qarbon.qt.gui.application import Application
from qarbon.qt.gui.action import Action
from qarbon.qt.gui.icon import Icon


class XEmbedCommandWidget(QtGui.QWidget):
    """A widget displaying an X11 window inside from a command.

    Example::

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import Application
        from qarbon.qt.gui.x11 import XEmbedCommandWidget

        app = Application()
        w = QtGui.QMainWindow()
        cmdWidget = XEmbedCommandWidget(parent=w)
        cmdWidget.command = 'xterm'
        cmdWidget.winIdParam = '-into'
        cmdWidget.start()
        w.setCentralWidget(cmdWidget)
        w.show()
        app.exec_()"""

    DefaultAutoRestart = False
    DefaultWinIdParam = '-into'

    def __init__(self, parent=None):
        super(XEmbedCommandWidget, self).__init__(parent)
        self.__process = QtCore.QProcess(self)
        self.__x11_widget = x11_widget = QtGui.QX11EmbedContainer(self)
        layout = QtGui.QVBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(x11_widget)
        x11_widget.error.connect(self.__onError)
        self.resetCommand()
        self.resetAutoRestart()
        self.resetWinIdParam()
        self.resetExtraParams()

    def __onError(self, error):
        log.error("XEmbedContainer: Error")

    def __convert_wait(self, wait):
        if wait:
            if wait < 0:
                wait = -1
            else:
                wait = int(wait * 1000)
        return wait

    def __finish(self, finish_func, wait=0):
        process = self.__process
        wait = self.__convert_wait(wait)
        finish_func()
        if wait:
            return process.waitForFinished(msecs=wait)

    def getX11WinId(self):
        return self.getX11Widget().winId()

    def getX11Widget(self):
        return self.__x11_widget

    def getProcess(self):
        return self.__process

    def getCommand(self):
        return self.__command

    def setCommand(self, command):
        self.__command = command
        if command is None:
            self.setWindowTitle("<None>")
        else:
            self.setWindowTitle(command)

    def resetCommand(self):
        self.setCommand(None)

    def getWinIdParam(self):
        return self.__winIdParam

    def setWinIdParam(self, winIdParam):
        self.__winIdParam = winIdParam

    def resetWinIdParam(self):
        self.setWinIdParam(self.DefaultWinIdParam)

    def setExtraParams(self, params):
        if params is None:
            params = []
        self.__extraParams = params

    def getExtraParams(self):
        return self.__extraParams

    def resetExtraParams(self):
        self.setExtraParams(None)

    def setAutoRestart(self, yesno):
        self.__autoRestart = yesno

    def getAutoRestart(self):
        return self.__autoRestart

    def resetAutoRestart(self):
        return self.setAutoRestart(self.DefaultAutoRestart)

    def setWorkingDirectory(self, wd):
        if wd is not None:
            self.getProcess().setWorkingDirectory(wd)

    def getWorkingDirectory(self):
        return self.getProcess().workingDirectory()

    def start(self, wait=0):
        """wait < 0 -> wait forever,
           wait == 0 -> not wait,
           wait > 0 -> wait amount in seconds"""
        if self.__command is None:
            raise Exception("Cannot start: no command")
        if self.__winIdParam is None:
            raise Exception("Cannot start: no winIdParam")
        process = self.__process
        params = [self.__winIdParam, str(self.getX11WinId())] + \
                 self.__extraParams
        process.start(self.__command, params)
        wait = self.__convert_wait(wait)
        if wait:
            return process.waitForStarted(msecs=wait)

    def restart(self, wait=0):
        self.terminate(wait=-1)
        return self.start(wait=wait)

    def kill(self, wait=0):
        return self.__finish(self.__process.kill, wait=wait)

    def terminate(self, wait=0):
        return self.__finish(self.__process.terminate, wait=wait)

    def __del__(self):
        import sip
        if not sip.isdeleted(self.__process):
            log.debug("X11CommandWidget: __del__...")
            self.terminate(wait=-1)

    def deleteLater(self):
        self.terminate(wait=-1)
        return super(XEmbedCommandWidget, self).deleteLater()

#    def closeEvent(self, event):
#        log.info("X11CommandWidget: closeEvent...")
#        self.terminate()
#        return super(XEmbedCommandWidget, self).closeEvent(event)

    command = QtCore.Property(str, getCommand, setCommand, resetCommand)

    winIdParam = QtCore.Property(str, getWinIdParam, setWinIdParam,
                                 resetWinIdParam)

    extraParams = QtCore.Property("QStringList", getExtraParams,
                                  setExtraParams, resetExtraParams)

    autoRestart = QtCore.Property(bool, getAutoRestart, setAutoRestart,
                                  resetAutoRestart)

    workingDirectory = QtCore.Property(str, getWorkingDirectory,
                                       setWorkingDirectory)


class XEmbedCommandWindow(QtGui.QMainWindow):
    """The QMainWindow version of :class:`XEmbedCommandWidget`.

    Example::

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import Application
        from qarbon.qt.gui.x11 import XEmbedCommandWindow

        app = Application()
        w = XEmbedCommandWindow()
        w.command = 'xterm'
        w.winIdParam = '-into'
        w.start()
        w.show()
        app.exec_()"""

    Widget = XEmbedCommandWidget

    def __init__(self, **kwargs):
        parent = kwargs.pop('parent', None)
        flags = kwargs.pop('flags', QtCore.Qt.WindowFlags())
        super(XEmbedCommandWindow, self).__init__(parent=parent, flags=flags)
        x11 = self.Widget(parent=self, **kwargs)
        self.setCentralWidget(x11)
        toolBar = self.addToolBar("Actions")
        self.__actionsToolBar = weakref.ref(toolBar)
        self.__restartAction = Action("Restart", parent=self,
                                      icon=Icon("view-refresh"),
                                      tooltip="restart the current command",
                                      triggered=self.restart)
        toolBar.addAction(self.__restartAction)

    def XWidget(self):
        return self.centralWidget()

    def start(self, wait=0):
        self.XWidget().start(wait=wait)

    def restart(self, wait=0):
        self.XWidget().restart(wait=wait)

    def terminate(self, wait=0):
        self.XWidget().terminate(wait=wait)

    def getCommand(self):
        return self.XWidget().command

    def setCommand(self, command):
        self.XWidget().command = command

    def resetCommand(self):
        self.XWidget().resetCommand()

    def getWinIdParam(self):
        return self.XWidget().winIdParam

    def setWinIdParam(self, winIdParam):
        self.XWidget().winIdParam = winIdParam

    def resetWinIdParam(self):
        self.XWidget().resetWinIdParam()

    def setExtraParams(self, params):
        self.XWidget().extraParams = params

    def getExtraParams(self):
        return self.XWidget().extraParams

    def resetExtraParams(self):
        self.XWidget().resetExtraParams()

    def setAutoRestart(self, yesno):
        self.XWidget().autoRestart = yesno

    def getAutoRestart(self):
        return self.XWidget().autoRestart

    def resetAutoRestart(self):
        self.XWidget().resetAutoRestart()

    def setWorkingDirectory(self, wd):
        self.XWidget().workingDirectory = wd

    def getWorkingDirectory(self):
        return self.XWidget().workingDirectory

    command = QtCore.Property(str, getCommand, setCommand, resetCommand)

    winIdParam = QtCore.Property(str, getWinIdParam, setWinIdParam,
                                 resetWinIdParam)

    extraParams = QtCore.Property("QStringList", getExtraParams,
                                  setExtraParams, resetExtraParams)

    autoRestart = QtCore.Property(bool, getAutoRestart, setAutoRestart,
                                        resetAutoRestart)

    workingDirectory = QtCore.Property(str, getWorkingDirectory,
                                       setWorkingDirectory)


class XTermWidget(XEmbedCommandWidget):
    """A widget with an xterm console inside.

    Example::

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import Application
        from qarbon.qt.gui.x11 import XTermWidget

        app = Application()
        w = QtGui.QMainWindow()
        term = XTermWidget(parent=w)
        term.extraParams = ["-e", "python"]
        w.setCentralWidget(term)
        w.start()
        w.show()
        app.exec_()"""

    def __init__(self, auto_start=False, parent=None):
        super(XTermWidget, self).__init__(parent=parent)
        self.command = 'xterm'
        if auto_start:
            self.start()

    def sizeHint(self):
        return QtCore.QSize(800, 600)


class XTermWindow(XEmbedCommandWindow):
    """The QMainWindow version of :class:`XTermWidget`

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import Application
        from qarbon.qt.gui.x11 import XTermWidget

        app = Application()
        term = XTermWindow()
        term.start()
        term.show()
        app.exec_()"""

    Widget = XTermWidget


def main():
    log.initialize(log_level='debug')
    app = Application()
    log.info("starting main...")
    w = XTermWindow()
    w.extraParams = ["-e", "python"]
    w.start()
    w.show()
    app.exec_()


if __name__ == "__main__":
    main()
