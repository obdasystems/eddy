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


import math

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasThreadingSystem, HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.functions.misc import natsorted
from eddy.ui.fields import CheckBox


class DiagramSelectionDialog(HasThreadingSystem, HasWidgetSystem, QtWidgets.QDialog):
    """
    Extends QtWidgets.QDialog providing the form used to select the diagrams for a specific task like export/import
    """
    def __init__(self, session, project=None, **kwargs):
        """
        Initialize the form dialog.
        :type session: Session
        :type project: Project
        """
        super().__init__(parent=session, **kwargs)
        self._project = project
        diagrams = natsorted(self.project.diagrams(), key=lambda diagram: diagram.name)
        for diagram in diagrams:
            self.addWidget(CheckBox(diagram.name, self, objectName=diagram.name,
                                    checked=True, clicked=self.onDiagramChecked))

        diagramLayout = QtWidgets.QGridLayout(self)
        diagramLayout.setContentsMargins(8, 8, 8, 8)
        nrows = math.floor(math.sqrt(max(len(diagrams), 1)))
        for i, d in enumerate(diagrams):
            col = i % nrows
            row = math.floor(i / nrows)
            diagramLayout.addWidget(self.widget(d.name), row, col)

        diagramGroup = QtWidgets.QGroupBox('Diagrams', self)
        diagramGroup.setLayout(diagramLayout)

        diagramGroupLayout = QtWidgets.QHBoxLayout(self)
        diagramGroupLayout.addWidget(diagramGroup)

        diagramWidget = QtWidgets.QWidget(self)
        diagramWidget.setLayout(diagramGroupLayout)

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Ok)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setObjectName('confirmation')
        self.addWidget(confirmation)
        # noinspection PyArgumentList
        self.addWidget(QtWidgets.QPushButton('All', self, objectName='btn_check_all', clicked=self.doCheckDiagram))
        # noinspection PyArgumentList
        self.addWidget(QtWidgets.QPushButton('Clear', self, objectName='btn_clear_all', clicked=self.doCheckDiagram))

        buttonLayout = QtWidgets.QHBoxLayout(self)
        buttonLayout.setAlignment(QtCore.Qt.AlignRight)
        buttonLayout.addWidget(self.widget('btn_clear_all'), 0, QtCore.Qt.AlignRight)
        buttonLayout.addWidget(self.widget('btn_check_all'), 0, QtCore.Qt.AlignRight)
        buttonLayout.addWidget(self.widget('confirmation'), 0, QtCore.Qt.AlignRight)

        buttonWidget = QtWidgets.QWidget(self)
        buttonWidget.setLayout(buttonLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.addWidget(diagramWidget)
        mainLayout.addWidget(buttonWidget)

        self.setLayout(mainLayout)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Diagram Selection')

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for self.parent()).
        :rtype: Session
        """
        return self.parent()

    @property
    def project(self):
        """
        Returns the active project.
        :rtype: Project
        """
        return self._project or self.session.project

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onDiagramChecked(self):
        """
        Executed when an diagram checkbox is clicked.
        """
        self.widget('confirmation').setEnabled(
            any(x.isChecked() for x in (self.widget(d.name) for d in self.project.diagrams())))

    @QtCore.pyqtSlot()
    def doCheckDiagram(self):
        """
        Check diagrams marks according to the action that triggered the slot.
        """
        checked = self.sender() is self.widget('btn_check_all')
        for diagram in self.project.diagrams():
            checkbox = self.widget(diagram.name)
            checkbox.setChecked(checked)

    #############################################
    #   INTERFACE
    #################################

    def selectedDiagrams(self):
        """
        Returns the list of diagrams selected in the dialog.
        :rtype: list
        """
        return [diagram for diagram in self.project.diagrams() if self.widget(diagram.name).isChecked()]
