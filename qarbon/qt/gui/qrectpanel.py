#!/usr/bin/env python

#############################################################################
##
## This file is part of Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
###########################################################################


"""A panel that displays a rectangle coordinates.
"""

__all__ = ["QRectPanel"]

__docformat__ = 'restructuredtext'

#from taurus.qt import Qt
from PyQt4 import Qt

Signal = Qt.pyqtSignal


def _buildEditorWidget(dtype, slot=None, **kwargs):
    if dtype == int:
        editor = Qt.QSpinBox()
        if slot:
            editor.valueChanged.connect(slot)
    elif dtype == float:
        editor = Qt.QDoubleSpinBox()
        if slot:
            editor.valueChanged.connect(slot)
    elif dtype == str:
        editor = Qt.QLineEdit()
        if slot:
            editor.textEdited.connect(slot)
    else:
        raise TypeError(str(dtype))
    return editor


class _Panel(Qt.QWidget):

    valueChanged = Signal(str, object)
    
    def __init__(self, parent=None, dtype=int, unit='', fields=None):
        Qt.QWidget.__init__(self, parent)
        self.dtype = dtype
        self.unit = unit
        layout = Qt.QGridLayout(self)
        if fields is None:
            fields = []
        self.setFields(fields)

    def setFields(self, fields):
        layout = self.layout()
        while not layout.isEmpty():
            layout.takeAt(0)
        self.__widgets = widgets = {}
        row = 0
        for field in fields:
            label = field.pop('label')
            name = field.pop('name', label)
            dtype = field.pop('dtype', self.dtype)
            unit = field.pop('unit', self.unit)
            label_w = Qt.QLabel(label + ":")
            def valueChanged(value):
                self.valueChanged.emit(name, value)
            editor_w = _buildEditorWidget(dtype, slot=valueChanged, **field)
            unit_w = Qt.QLabel(unit)
            layout.addWidget(label_w, row, 0)
            layout.addWidget(editor_w, row, 1)
            layout.addWidget(unit_w, row, 2)
            widgets[name] = label_w, editor_w, unit_w
            row += 1
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)

    def getFieldsWidgets(self):
        return self.__widgets

    def getFieldWidgets(self, field_name):
        return self.__widgets[field_name]

    def getFieldEditorWidget(self, field_name):
        return self.getFieldWidgets(field_name)[1]

    def getFieldValue(self, field_name):
        return self.getFieldEditorWidget(field_name).value()

    def setFieldValue(self, field_name, value):
        self.getFieldEditorWidget(field_name).setValue(value)


def Rect(dtype=int, args=None):
    if args is None:
        args = []
    klass = Qt.QRectF
    if dtype == int:
        klass = Qt.QRect
    return klass(*args)


class XYWHPanel(_Panel):

    rectChanged = Signal(object)
    
    def __init__(self, parent=None, dtype=int, unit=''):
        fields = [{'label':'x'}, {'label':'y'}, {'label':'w'}, {'label':'h'}]
        _Panel.__init__(self, parent=parent, dtype=dtype, unit=unit, fields=fields)
        
    def getRect(self):
        result = Rect(dtype=self.dtype)
        result.setRect(self.getFieldValue('x'), self.getFieldValue('y'),
                       self.getFieldValue('w'), self.getFieldValue('h'))
        return result

    def setRect(self, rect, emit=True):
        if not emit:
            b = self.blockSignals(True)
        self.setFieldValue('x', rect.x())
        self.setFieldValue('y', rect.y())
        self.setFieldValue('w', rect.width())
        self.setFieldValue('h', rect.height())
        if not emit:
            self.blockSignals(b)
    
class X1Y1X2Y2Panel(_Panel):

    def __init__(self, parent=None, dtype=int, unit=''):
        fields = [{'label':'x1'}, {'label':'y1'}, {'label':'x2'}, {'label':'y2'}]
        _Panel.__init__(self, parent=parent, dtype=dtype, unit=unit, fields=fields)

    def getRect(self):
        result = Rect(dtype=self.dtype)
        result.setCoords(self.getFieldValue('x1'), self.getFieldValue('y1'),
                         self.getFieldValue('x2'), self.getFieldValue('y2'))
        return result

    def setRect(self, rect, emit=True):
        if not emit:
            b = self.blockSignals(True)        
        x1, y1, x2, y2 = rect.getCoords()
        self.setFieldValue('x1', x1)
        self.setFieldValue('y1', y1)
        self.setFieldValue('x2', x2)
        self.setFieldValue('y2', y2)
        if not emit:
            self.blockSignals(b)


class QRectPanel(Qt.QWidget):

    rectChanged = Signal(object)
    
    def __init__(self, parent=None, dtype=int, unit=''):
        self.__dtype = dtype
        self.__unit = unit
        if dtype == int:
            self.Rect = Qt.QRect
        else:
            self.Rect = Qt.QRectF
        self.__rect = self.Rect()
        Qt.QWidget.__init__(self, parent)
        layout = Qt.QStackedLayout(self)
        self.__xywh = XYWHPanel(dtype=dtype, unit=unit)
        layout.addWidget(self.__xywh)
        self.__x1y1x2y2 = X1Y1X2Y2Panel(dtype=dtype, unit=unit)
        layout.addWidget(self.__x1y1x2y2)

        self.__xywh.valueChanged.connect(self.__valueChanged)
        self.__x1y1x2y2.valueChanged.connect(self.__valueChanged)

    def __valueChanged(self, name, value):
        layout = self.layout()
        curr_panel = layout.currentWidget()
        rect = curr_panel.getRect()
        print rect
        for panel_index in range(layout.count()):
            panel = layout.widget(panel_index)
            if panel != curr_panel:
                panel.setRect(rect, emit=False)
            

def main():
    app = Qt.QApplication([])
    w = QRectPanel(dtype=float, unit='px')
    w.show()
    app.exec_()
        
if __name__ == "__main__":
    main()
