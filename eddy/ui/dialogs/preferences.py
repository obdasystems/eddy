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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout
from PyQt5.QtWidgets import QDialogButtonBox, QTabWidget, QFormLayout

from eddy.core.functions.signals import connect
from eddy.ui.fields import SpinBox


class PreferencesDialog(QDialog):
    """
    This class implements the 'Preferences' dialog.
    """
    def __init__(self, mainwindow):
        """
        Initialize the Preferences dialog.
        :type mainwindow: QMainWindow
        """
        super().__init__(mainwindow)

        self.mainwindow = mainwindow

        ################################################################################################################
        #                                                                                                              #
        #   EDITOR TAB                                                                                                 #
        #                                                                                                              #
        ################################################################################################################

        # TODO: GET FROM SETTINGS
        self.diagramSizeF = SpinBox(self)
        self.diagramSizeF.setRange(2000, 1000000)
        self.diagramSizeF.setSingleStep(100)
        self.diagramSizeF.setValue('')

        self.editorWidget = QWidget()
        self.editorLayout = QFormLayout(self.editorWidget)
        self.editorLayout.addRow('Diagram size', self.diagramSizeF)

        ################################################################################################################
        #                                                                                                              #
        #   MAIN WIDGET                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.editorWidget, 'Editor')

        ################################################################################################################
        #                                                                                                              #
        #   BUTTON BOX                                                                                                 #
        #                                                                                                              #
        ################################################################################################################

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close, Qt.Horizontal, self)

        ################################################################################################################
        #                                                                                                              #
        #   MAIN LAYOUT                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Preferences')

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE SIGNALS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)
        connect(self.finished, self.completed)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    # TODO: SAVE ON SETTINGS
    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == PreferencesDialog.Accepted:
            pass