# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""A widget dedicated view/edit the properties of any QObject.

Example::

    from qarbon.external.qt import QtGui
    from qarbon.qt.gui.application import Application
    from qarbon.qt.gui.propertyeditor import PropertyEditor

    app = Application()
    inspector = PropertyEditor(qobject=None)

    # watch myself... weard
    inspector.setQObject(inspector)
    inspector.show()
    app.exec_()
"""

__all__ = ["PropertyEditor"]

import weakref

from qarbon import log
from qarbon.external.qt import QtCore, QtGui
from qarbon.qt.gui.ui import UILoadable


def getPropertyValueDisplay(qMetaProperty, value):
    if qMetaProperty.isEnumType():
        metaEnum = qMetaProperty.enumerator()
        return metaEnum.key(value)
    return str(value)


def getPropertyValueToolTip(qMetaProperty, value):
    if qMetaProperty.isEnumType():
        enu = qMetaProperty.enumerator()
        tooltip = "<html>A {0}<br/>".format(enu.name())
        for i in range(enu.keyCount()):
            k, v = enu.key(i), enu.value(i)
            text = "{0}: {1}<br/>".format(k, v)
            if v == value:
                text = "<b>" + text + "</b>"
            tooltip += text
        return tooltip
    return str(value)


@UILoadable(with_ui="_ui")
class PropertyEditor(QtGui.QWidget):
    """A widget dedicated view/edit the properties of any QObject."""

    def __init__(self, parent=None, qobject=None):
        super(PropertyEditor, self).__init__(parent)
        self.loadUi()

        self._ui.focusButton.clicked.connect(self.__onFocus)

        self.setQObject(qobject)

    @property
    def qobject(self):
        """returns the current QObject being edited or None if no QObject is
        associated with the editor.

        :return: the current QObject being edited or None if no QObject is
                 associated with the editor
        """
        if self.__qobject is None:
            return
        return self.__qobject()

    def setQObject(self, qobject):
        """Sets the current QObject whose properties are to been seen by the
        editor.

        :param qobject: the new QObject (can be None)
        """
        ui = self._ui
        superClassName = ""
        _class = ""
        className = ""
        isWidget = False
        propCount = 0
        if qobject is None:
            self.__qobject = None
        else:
            _class = qobject.__class__.__name__
            self.__qobject = weakref.ref(qobject)
            metaObject = qobject.metaObject()
            if metaObject is not None:
                className = metaObject.className()
                superClass = metaObject.superClass()
                if superClass is not None:
                    superClassName = superClass.className()
                isWidget = qobject.isWidgetType()
                propCount = metaObject.propertyCount()

        ui.classLineEdit.setText(_class)
        ui.classNameLineEdit.setText(className)
        ui.superClassNameLineEdit.setText(superClassName)
        ui.isWidgetLineEdit.setText(str(isWidget))
        ui.focusButton.setEnabled(isWidget)

        propTree = ui.propertiesTreeWidget

        QtCore.QObject.disconnect(propTree,
                        QtCore.SIGNAL("itemChanged (QTreeWidgetItem*, int)"),
                        self.__onPropertyTreeChanged)
        propTree.clear()
        if propCount == 0:
            return

        metaO, props = metaObject, []
        while True:
            first, last = metaO.propertyOffset(), metaO.propertyCount()
            if first < last:
                class_props = {}
                for p_index in range(first, last):
                    metaProp = metaObject.property(p_index)
                    class_props[metaProp.name()] = metaProp
                props.insert(0, (metaO, class_props))
            metaO = metaO.superClass()
            if metaO is None:
                break

        # build tree
        for metaO, props in props:
            topItem = QtGui.QTreeWidgetItem(propTree)
            topItem.setText(0, metaO.className())
            for prop_name in sorted(props.keys()):
                metaProp = props[prop_name]
                prop_type = metaProp.typeName()
                value = qobject.property(prop_name)
                prop_value = getPropertyValueDisplay(metaProp, value)
                columns = [prop_name, prop_type, prop_value]
                propItem = QtGui.QTreeWidgetItem(topItem, columns)
                propItem.setFlags(propItem.flags() | QtCore.Qt.ItemIsEditable)
                propItem.setData(2, QtCore.Qt.UserRole, prop_name)
                propItem.setData(2, QtCore.Qt.DisplayRole, value)
                propItem.setToolTip(2, getPropertyValueToolTip(metaProp,
                                                               value))

        propTree.expandToDepth(1)
        propTree.headerItem()
        QtCore.QObject.connect(propTree,
                    QtCore.SIGNAL("itemChanged (QTreeWidgetItem*, int)"),
                    self.__onPropertyTreeChanged)

    def __onPropertyTreeChanged(self, item, column):
        if column != 2:
            return
        qobject = self.qobject
        if qobject is None:
            log.warning("qobject disappeared while trying to set a property " \
                        "on it")
            return
        prop_name = item.data(column, QtCore.Qt.UserRole)
        prop_value = item.data(column, QtCore.Qt.DisplayRole)
        qobject.setProperty(prop_name, prop_value)

    def __onFocus(self):
        qwidget = self.qobject
        if qwidget is None:
            log.warning("widget disappeared while trying to set a property " \
                        "on it")
            return
        #TODO: animate somehow


def main():
    from qarbon.qt.gui.application import Application
    app = Application()
    inspector = PropertyEditor(qobject=None)
    # watch myself... weard
    inspector.setQObject(inspector)
    inspector.show()
    app.exec_()

if __name__ == "__main__":
    main()
