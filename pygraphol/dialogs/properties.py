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
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QDialogButtonBox, QTabWidget, QFormLayout, QSizePolicy
from pygraphol.fields import StringEditField, TextEditField, IntEditField


class NodePropertiesDialog(QDialog):
    """
    This class implements the 'Node properties' dialog.
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the node properties dialog.
        :param scene: the scene the node is placed into.
        :param node: the node whose properties we want to inspect.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.node = node
        self.scene = scene

        self.finished.connect(self.handleFinished)

        ################################################ GENERAL TAB ###################################################
        
        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)

        self.idF = StringEditField(self.generalWidget)
        self.idF.setEnabled(False)
        self.idF.setFixedWidth(300)
        self.idF.setText(self.node.id)

        self.nameF = StringEditField(self.generalWidget)
        self.nameF.setEnabled(False)
        self.nameF.setFixedWidth(300)
        self.nameF.setText(self.node.name)

        self.urlF = StringEditField(self.generalWidget)
        self.urlF.setFixedWidth(300)
        self.urlF.setText(self.node.url)

        self.descriptionF = TextEditField(self.generalWidget)
        self.descriptionF.setFixedSize(300, 160)
        self.descriptionF.setText(self.node.description)

        self.generalLayout.addRow('ID', self.idF)
        self.generalLayout.addRow('Node', self.nameF)
        self.generalLayout.addRow('URL', self.urlF)
        self.generalLayout.addRow('Description', self.descriptionF)
        
        ############################################### GEOMETRY TAB ###################################################
        
        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        pos = self.node.shape.mapToScene(self.node.shape.center())

        self.xField = IntEditField(self.geometryWidget)
        self.xField.setFixedWidth(60)
        self.xField.setText(str(int(pos.x())))

        self.yField = IntEditField(self.geometryWidget)
        self.yField.setFixedWidth(60)
        self.yField.setText(str(int(pos.y())))

        self.wField = IntEditField(self.geometryWidget)
        self.wField.setEnabled(self.node.shape.resizable)
        self.wField.setFixedWidth(60)
        self.wField.setText(str(int(self.node.shape.width())))

        self.hField = IntEditField(self.geometryWidget)
        self.hField.setEnabled(self.node.shape.resizable)
        self.hField.setFixedWidth(60)
        self.hField.setText(str(int(self.node.shape.height())))

        self.geometryLayout.addRow('X', self.xField)
        self.geometryLayout.addRow('Y', self.yField)
        self.geometryLayout.addRow('Width', self.wField)
        self.geometryLayout.addRow('Height', self.hField)

        ################################################ MAIN WIDGET ###################################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, 'General')
        self.mainWidget.addTab(self.geometryWidget, 'Geometry')

        ################################################# BUTTON BOX ###################################################

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        ################################################ MAIN LAYOUT ###################################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Properties')

    ################################################# SIGNAL HANDLERS ##################################################

    def handleFinished(self, code):
        """
        Executed when the dialog is terminated.
        :param code: the result code.
        """
        pass