# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""A set of widgets to get input from the user."""

__all__ = ["InputPanel"]

import sys
import collections

from qarbon.external.qt import QtCore, QtGui
from qarbon.qt.gui.application import Application
from qarbon.qt.gui.icon import Pixmap
from qarbon.qt.gui.ui import UILoadable


@UILoadable(with_ui="_ui")
class InputPanel(QtGui.QWidget):
    """A panel design to get an input from the user.

    The input_data is a dictionary which contains information on how to build
    the input dialog. It **must** contains the following keys:

        - *prompt* <str>: message to be displayed

    The following are optional keys (and their corresponding default values):

        - *title* <str> (doesn't have default value)
        - *key* <str> (doesn't have default value):
          a label to be presented left to the input box represeting the label
        - *unit* <str> (doesn't have default value):
          a label to be presented right to the input box representing the units
        - *data_type* <str or sequence> ('String'):
          type of data to be requested. Standard
          accepted data types are 'String', 'Integer', 'Float', 'Boolean',
          'Text'. A list of elements will be interpreted as a selection.
          Default TaurusInputPanel class will interpret any custom data types
          as 'String' and will display input widget accordingly. Custom
          data types can be handled differently by supplying a different
          input_panel_klass.
        - *minimum* <int/float> (-sys.maxint):
          minimum value (makes sence when data_type is 'Integer' or 'Float')
        - *maximum* <int/float> (sys.maxint):
          maximum value (makes sence when data_type is 'Integer' or 'Float')
        - *step* <int/float> (1):
          step size value (makes sence when data_type is 'Integer' or 'Float')
        - *decimals* <int> (1):
          number of decimal places to show (makes sence when data_type is
          'Float')
        - *default_value* <obj> (doesn't have default value):
          default value
        - *allow_multiple* <bool> (False):
          allow more than one value to be selected (makes sence when data_type
          is a sequence of possibilities)


    Example::

        app = Application()

        d = dict(prompt="What's your favourite car brand?",
                 data_type=["Mazda", "Skoda", "Citroen", "Mercedes", "Audi",
                            "Ferrari"],
                 default_value="Mercedes")
        w = InputPanel(d)

        class Listener(object):
            def onAccept(self):
                print "user selected", w.value()

        l = Listener()
        w.buttonBox().accepted.connect(l.onAccept)
        w.show()
        app.exec_()
    """
    def __init__(self, input_data, parent=None):
        super(InputPanel, self).__init__(parent=parent)
        self.loadUi()
        self._input_data = input_data
        self.fill_main_panel(self.inputPanel(), input_data)

    def fill_main_panel(self, panel, input_data):
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        panel.setLayout(layout)
        if isinstance(input_data, collections.Mapping):
            single_panel, getter = self.create_single_input_panel(input_data)
            layout.addWidget(single_panel)
            self.value = getter
            if 'title' in input_data:
                self.setWindowTitle(input_data['title'])

    def create_single_input_panel(self, input_data):
#        style = Application().style()
        pixmap = Pixmap(QtGui.QStyle.SP_MessageBoxQuestion, 64)
        self.setIconPixmap(pixmap)

        self.setText(input_data['prompt'])

        data_type = input_data.get('data_type', 'String')
        is_seq = not isinstance(data_type, (str, unicode)) and \
                 isinstance(data_type, collections.Sequence)
        if is_seq:
            panel, getter = self.create_selection_panel(input_data)
        else:
            data_type_l = data_type.lower()
            creator = getattr(self, "create_" + data_type_l + "_panel",
                              self.create_custom_panel)
            if creator:
                panel, getter = creator(input_data)

        if panel is None:
            panel = QtGui.QLabel("Cannot create widget for data type '%s'"
                              % data_type)
            getter = lambda: None
        return panel, getter

    def create_custom_panel(self, input_data):
        return self.create_string_panel(input_data)

    def create_selection_panel(self, input_data):
        allow_multiple = input_data.get('allow_multiple', False)

        if allow_multiple:
            return self._create_multi_selection_panel(input_data)
        else:
            return self._create_single_selection_panel(input_data)

    def _create_single_selection_panel(self, input_data):
        items = list(map(str, input_data['data_type']))
        if len(items) > 5:
            return self._create_combobox_panel(input_data)
        return self._create_radiobutton_panel(input_data)

    def _create_combobox_panel(self, input_data):
        panel = self._create_simple_panel(input_data)
        layout = panel.layout()
        self._ui.inputWidget = combobox = QtGui.QComboBox()
        items = input_data['data_type']
        for item in items:
            is_seq = not isinstance(item, (str, unicode)) and \
                     isinstance(item, collections.Sequence)
            if is_seq:
                text, userData = item
            else:
                text, userData = str(item), item
            combobox.addItem(text, userData)
        layout.addWidget(combobox, 0, 1)
        return panel, self._get_combobox_value

    def _get_combobox_value(self):
        combo = self._ui.inputWidget
        return combo.itemData(combo.currentIndex())

    def _create_radiobutton_panel(self, input_data):
        panel = self._create_group_panel(input_data)
        layout = panel.layout()
        items = input_data['data_type']
        default_value = input_data.get('default_value')
        self._ui.inputWidget = buttongroup = QtGui.QButtonGroup()
        buttongroup.setExclusive(True)
        for item in items:
            is_seq = not isinstance(item, (str, unicode)) and \
                     isinstance(item, collections.Sequence)
            if is_seq:
                text, userData = item
            else:
                text, userData = str(item), item
            button = QtGui.QRadioButton(text)
            button._value = userData
            if default_value == userData:
                button.setChecked(True)
            buttongroup.addButton(button)
            layout.addWidget(button)
        return panel, self._get_radiobutton_value

    def _get_radiobutton_value(self):
        buttongroup = self._ui.inputWidget
        button = buttongroup.checkedButton()
        if button is not None:
            return button._value

    def _create_multi_selection_panel(self, input_data):
        panel = self._create_group_panel(input_data)
        layout = panel.layout()
        items = input_data['data_type']
        default_value = input_data.get('default_value')
        if default_value is None:
            default_value = ()
        dft_is_seq = not isinstance(default_value, (str, unicode)) and \
                     isinstance(default_value, collections.Sequence)
        if not dft_is_seq:
            default_value = default_value,

        self._ui.inputWidget = listwidget = QtGui.QListWidget()
        listwidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        for item in items:
            is_seq = not isinstance(item, (str, unicode)) and \
                     isinstance(item, collections.Sequence)
            if is_seq:
                text, userData = item
            else:
                text, userData = str(item), item
            item_widget = QtGui.QListWidgetItem(text, listwidget)
            item_widget.setData(QtCore.Qt.UserRole, userData)
            if userData in default_value:
                item_widget.setSelected(True)
        layout.addWidget(listwidget)
        return panel, self._get_multi_selection_value

    def _get_multi_selection_value(self):
        listwidget = self._ui.inputWidget
        return [item.data(QtCore.Qt.UserRole)
                    for item in listwidget.selectedItems()]

    def _create_group_panel(self, input_data):
        title = input_data.get('key', '')
        unit = input_data.get('unit', '')
        if unit:
            title += "(" + unit + ")"
        panel = QtGui.QGroupBox(title)
        layout = QtGui.QVBoxLayout()
        panel.setLayout(layout)
        self._ui.inputLabel = QtGui.QLabel()
        self._ui.unitLabel = QtGui.QLabel()
        return panel

    def _create_simple_panel(self, input_data):
        panel = QtGui.QWidget()
        key = input_data.get('key', '')
        if key:
            key += ":"
        unit = input_data.get('unit', '')
        layout = QtGui.QGridLayout()
        panel.setLayout(layout)
        self._ui.inputLabel = label = QtGui.QLabel(key)
        layout.addWidget(label, 0, 0)
        self._ui.unitLabel = unit = QtGui.QLabel(unit)
        layout.addWidget(unit, 0, 2)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        return panel

    def create_integer_panel(self, input_data):
        panel = self._create_simple_panel(input_data)
        minimum = input_data.get('minimum', -sys.maxint)
        maximum = input_data.get('maximum', sys.maxint)
        step = input_data.get('step', 1)
        layout = panel.layout()
        self._ui.inputWidget = spinbox = QtGui.QSpinBox()
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setSingleStep(step)
        if 'default_value' in input_data:
            spinbox.setValue(input_data['default_value'])
        layout.addWidget(spinbox, 0, 1)
        return panel, self._get_integer_value

    def _get_integer_value(self):
        return int(self._ui.inputWidget.value())

    def create_float_panel(self, input_data):
        panel = self._create_simple_panel(input_data)
        minimum = input_data.get('minimum', -sys.maxint)
        maximum = input_data.get('maximum', sys.maxint)
        step = input_data.get('step', 1)
        decimals = input_data.get('decimals', 1)
        layout = panel.layout()
        self._ui.inputWidget = spinbox = QtGui.QDoubleSpinBox()
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(decimals)
        if 'default_value' in input_data:
            spinbox.setValue(input_data['default_value'])
        layout.addWidget(spinbox, 0, 1)
        return panel, self._get_float_value

    def _get_float_value(self):
        return float(self._ui.inputWidget.value())

    def create_string_panel(self, input_data):
        panel = self._create_simple_panel(input_data)
        layout = panel.layout()
        self._ui.inputWidget = lineedit = QtGui.QLineEdit()
        if 'default_value' in input_data:
            lineedit.setText(str(input_data['default_value']))
        lineedit.selectAll()
        layout.addWidget(lineedit, 0, 1)
        return panel, self._get_string_value

    def _get_string_value(self):
        return str(self._ui.inputWidget.text())

    def create_text_panel(self, input_data):
        panel = self._create_group_panel(input_data)
        layout = panel.layout()
        self._ui.inputWidget = textedit = QtGui.QTextEdit()
        textedit.setAcceptRichText(False)
        if 'default_value' in input_data:
            textedit.setPlainText(str(input_data['default_value']))
        textedit.selectAll()
        layout.addWidget(textedit)
        return panel, self._get_text_value

    def _get_text_value(self):
        return str(self._ui.inputWidget.toPlainText())

    def create_boolean_panel(self, input_data):
        panel = self._create_simple_panel(input_data)
        layout = panel.layout()
        self._ui.inputWidget = checkbox = QtGui.QCheckBox()
        value = input_data.get('default_value', False)
        checkbox.setChecked(value)
        layout.addWidget(checkbox, 0, 1)
        return panel, self._get_boolean_value

    def _get_boolean_value(self):
        return self._ui.inputWidget.checkState() == QtCore.Qt.Checked

    def inputPanel(self):
        return self._ui._inputPanel

    def buttonBox(self):
        """Returns the button box from this panel

        :return: the button box from this panel
        :rtype: PyQt4.Qt.QDialogButtonBox"""
        return self._ui._buttonBox

    def addButton(self, button, role=QtGui.QDialogButtonBox.ActionRole):
        """Adds the given button with the given to the button box

        :param button: the button to be added
        :type button: PyQt4.QtGui.QPushButton
        :param role: button role
        :type role: PyQt4.Qt.QDialogButtonBox.ButtonRole"""
        self.buttonBox().addButton(button, role)

    def setIconPixmap(self, pixmap):
        """Sets the icon to the dialog

        :param pixmap: the icon pixmap
        :type pixmap: PyQt4.Qt.QPixmap"""
        self._ui.iconLabel.setPixmap(pixmap)

    def setText(self, text):
        """Sets the text of this panel

        :param text: the new text
        :type text: str"""
        self._ui.textLabel.setText(text)

    def getText(self):
        """Returns the current text of this panel

        :return: the text for this panel
        :rtype: str"""
        return self._ui.textLabel.text()

    def setInputFocus(self):
        inputWidget = self._ui.inputWidget
        if not inputWidget:
            return
        if isinstance(inputWidget, QtGui.QWidget):
            inputWidget.setFocus()
        elif isinstance(inputWidget, QtGui.QButtonGroup):
            bid = inputWidget.checkedId()
            if bid < 0:
                button = inputWidget.buttons()[0]
            else:
                button = inputWidget.button(bid)
            button.setFocus()


def main():
    app = Application()

    d = dict(prompt="What's your favourite car brand?",
             data_type=["Mazda", "Skoda", "Citroen", "Mercedes", "Audi",
                        "Ferrari"],
             default_value="Mercedes")
    w = InputPanel(d)

    class Listener(object):
        def onAccept(self):
            print "user selected", w.value()

    l = Listener()
    w.buttonBox().accepted.connect(l.onAccept)
    w.show()
    app.exec_()

if __name__ == "__main__":
    main()
