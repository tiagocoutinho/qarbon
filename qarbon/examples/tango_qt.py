# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

from __future__ import print_function

import sys
import time

from qarbon import log
from qarbon.tango import Factory
from qarbon.external.qt import Qt

def main():
    import sys

    log.initialize(log_level='debug')

    attr_name = 'sys/tg_test/1/double_scalar'
    if len(sys.argv) > 1:
        attr_name = sys.argv[1]

    class QAttribute(Qt.QObject):

        valueChanged = Qt.Signal(object, name="valueChanged")

        def __init__(self, attr_name, parent=None):
            Qt.QObject.__init__(self, parent)
            attr = Factory().get_attribute(attr_name)
            self.__attr = attr
            self.__attr.valueChanged.connect(self.__on_value_changed)

        def __on_value_changed(self, value):
            self.valueChanged.emit(value)


    class Label(Qt.QLabel):
        
        def __init__(self, parent=None):
            Qt.QLabel.__init__(self, parent)
            self.__model = None
            self.__model_name = None

        def __on_value_changed(self, value):
            print("Value changed")
            if value.error:
                text = "-----"
                tooltip = "Error:\n" + str(value.exc_info[1])
            else:
                text = "{0.label}: {0.r_value}".format(value)
                tooltip = value.description
            self.setText(text)
            self.setToolTip(tooltip)

        @Qt.Slot(str)
        def setModel(self, name):
            if self.__model_name == name:
                return
            if self.__model:
                self.__model.valueChanged.disconnect(self.__on_value_changed)
            
            if not name:
                name = ''
                model = None
            else:
                model = QAttribute(name, parent=self)
                model.valueChanged.connect(self.__on_value_changed)

            self.__model_name = name
            self.__model = model
            
        def getModel(self):
            return self.__model_name

        model = Qt.Property(str, getModel, setModel)

    app = Qt.QApplication([])
    w = Qt.QMainWindow()
    l = Label()
    l.model = attr_name
    w.setCentralWidget(l)
    w.show()
    app.exec_()

if __name__ == "__main__":
    main()
