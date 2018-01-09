# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


class ComboBox(QtWidgets.QComboBox):
    """
    This class implements a multi selection box.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the spin box.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self._scrollEnabled = True

    def value(self):
        """
        Returns the currently selected value.
        :rtype: QVariant
        """
        return self.itemData(self.currentIndex())

    def setScrollEnabled(self, enabled=True):
        """
        Enable the selection of the option by scrolling the mouse wheel.
        :type enabled: bool
        """
        self._scrollEnabled = enabled

    def scrollEnabled(self):
        """
        Tells whether the selection of the option by scrolling the mouse wheel is enabled.
        :rtype: bool
        """
        return self._scrollEnabled

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is rotated on the item.
        :type wheelEvent: QWheelEvent
        """
        if self.scrollEnabled():
            super().wheelEvent(wheelEvent)


class CheckBox(QtWidgets.QCheckBox):
    """
    This class implements a check box.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the check box.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)


class DoubleField(QtWidgets.QLineEdit):
    """
    This class implements an input field where the user can enter float values.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the float input field.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.setValidator(QtGui.QDoubleValidator(self))

    def setValue(self, value):
        """
        Set the value of the field.
        :type value: float.
        """
        self.setText(str(value).strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: float
        """
        return float(self.text())


class IntegerField(QtWidgets.QLineEdit):
    """
    This class implements an input field where the user can enter only integer values.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the integer input field.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.setValidator(QtGui.QIntValidator(self))

    def setValue(self, value):
        """
        Set the value of the field.
        :type value: int.
        """
        self.setText(str(value).strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: int
        """
        return int(self.text())


class StringField(QtWidgets.QLineEdit):
    """
    This class implements an input field where the user can enter strings.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the string input field.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

    def setValue(self, value):
        """
        Set the value of the field.
        :type value: str.
        """
        if value is None:
            self.setText(None)
        else:
            self.setText(value.strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: str
        """
        return self.text().strip()


class TextField(QtWidgets.QPlainTextEdit):
    """
    This class implements a textarea field where the user can enter strings.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the string input field.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

    def setValue(self, value):
        """
        Set the value of the field.
        :type value: str.
        """
        self.setPlainText(value.strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: str
        """
        return self.toPlainText().strip()


class SpinBox(QtWidgets.QSpinBox):
    """
    This class implements a SpinBox.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the spin box.
        """
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)