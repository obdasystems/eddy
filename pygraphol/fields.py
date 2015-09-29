# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QSpinBox


class DoubleEditField(QLineEdit):
    """
    This class implements an input field where the user can enter float values.
    """
    def __init__(self, parent=None):
        """
        Initialize the float input field.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setValidator(QDoubleValidator(self))

    def setValue(self, value):
        """
        Set the value of the field.
        :param value: the value to set.
        """
        self.setText(str(value).strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: float
        """
        return float(self.text())


class IntEditField(QLineEdit):
        """
        This class implements an input field where the user can enter only integer values.
        """
        def __init__(self, parent=None):
            """
            Initialize the integer input field.
            """
            super().__init__(parent)
            self.setAttribute(Qt.WA_MacShowFocusRect, 0)
            self.setValidator(QIntValidator(self))

        def setValue(self, value):
            """
            Set the value of the field.
            :param value: the value to set.
            """
            self.setText(str(value).strip())

        def value(self):
            """
            Returns the value of the field.
            :rtype: int
            """
            return int(self.text())


class StringEditField(QLineEdit):
    """
    This class implements an input field where the user can enter strings.
    """
    def __init__(self, parent=None):
        """
        Initialize the string input field.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)

    def setValue(self, value):
        """
        Set the value of the field.
        :param value: the value to set.
        """
        self.setText(value.strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: str
        """
        return self.text().strip()


class TextEditField(QPlainTextEdit):
    """
    This class implements a textarea field where the user can enter strings.
    """
    def __init__(self, parent=None):
        """
        Initialize the string input field.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)

    def setValue(self, value):
        """
        Set the value of the field.
        :param value: the value to set.
        """
        self.setPlainText(value.strip())

    def value(self):
        """
        Returns the value of the field.
        :rtype: str
        """
        return self.toPlainText().strip()


class SpinBox(QSpinBox):
    """
    This class implements a SpinBox.
    """
    def __init__(self, parent=None):
        """
        Initialize the spin box.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)