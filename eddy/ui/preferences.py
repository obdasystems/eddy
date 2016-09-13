# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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

from eddy import ORGANIZATION, APPNAME
from eddy.core.datatypes.qt import Font
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect

from eddy.ui.fields import SpinBox


class PreferencesDialog(QtWidgets.QDialog):
    """
    This class implements the 'Preferences' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the Preferences dialog.
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        arial12r = Font('Arial', 12)
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # EDITOR TAB
        #################################

        self.diagramSizeLabel = QtWidgets.QLabel(self)
        self.diagramSizeLabel.setFont(arial12r)
        self.diagramSizeLabel.setText('Diagram size')
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setFont(arial12r)
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setToolTip('This setting changes the default size of all the new created diagrams.')
        self.diagramSizeField.setValue(settings.value('diagram/size', 5000, int))

        self.editorWidget = QtWidgets.QWidget()
        self.editorLayout = QtWidgets.QFormLayout(self.editorWidget)
        self.editorLayout.addRow(self.diagramSizeLabel, self.diagramSizeField)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # MAIN WIDGET
        #################################

        self.mainWidget = QtWidgets.QTabWidget(self)
        self.mainWidget.addTab(self.editorWidget, 'Editor')
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Preferences')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/size', self.diagramSizeField.value())
        settings.sync()
        super().accept()