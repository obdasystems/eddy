# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QDialogButtonBox, QTabWidget, QFormLayout
from grapholed.commands import CommandNodeMove, CommandNodeSetURL, CommandNodeSetDescription
from grapholed.fields import StringEditField, TextEditField, SpinBox
from grapholed.functions import clamp


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
        self.idF.setValue(self.node.id)

        self.nameF = StringEditField(self.generalWidget)
        self.nameF.setEnabled(False)
        self.nameF.setFixedWidth(300)
        self.nameF.setValue(self.node.name)

        self.urlF = StringEditField(self.generalWidget)
        self.urlF.setFixedWidth(300)
        self.urlF.setValue(self.node.url)

        self.descriptionF = TextEditField(self.generalWidget)
        self.descriptionF.setFixedSize(300, 160)
        self.descriptionF.setValue(self.node.description)

        self.generalLayout.addRow('ID', self.idF)
        self.generalLayout.addRow('Node', self.nameF)
        self.generalLayout.addRow('URL', self.urlF)
        self.generalLayout.addRow('Description', self.descriptionF)
        
        ############################################### GEOMETRY TAB ###################################################
        
        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        p = self.node.pos()
        r = self.scene.sceneRect()

        self.xField = SpinBox(self.geometryWidget)
        self.xField.setFixedWidth(60)
        self.xField.setRange(0, r.width())
        self.xField.setValue(int(p.x()))

        self.yField = SpinBox(self.geometryWidget)
        self.yField.setFixedWidth(60)
        self.yField.setRange(0, r.height())
        self.yField.setValue(int(p.y()))

        # TODO: allow to modify shape width from properties dialog
        self.wField = SpinBox(self.geometryWidget)
        self.wField.setEnabled(False)
        self.wField.setFixedWidth(60)
        self.wField.setValue(int(self.node.width()))

        # TODO: allow to modify shape height from properties dialog
        self.hField = SpinBox(self.geometryWidget)
        self.hField.setEnabled(False)
        self.hField.setFixedWidth(60)
        self.hField.setValue(int(self.node.height()))

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
        if code == QDialog.Accepted:
            self.handlePositionChanged()
            self.handleURLChanged()
            self.handleDescriptionChanged()

    ################################################ AUXILIARY METHODS #################################################

    def handleURLChanged(self):
        """
        Change the url property of the node.
        """
        url = self.urlF.value()
        if self.node.url != url:
            self.scene.undoStack.push(CommandNodeSetURL(self.node, url))

    def handleDescriptionChanged(self):
        """
        Change the url property of the node.
        """
        description = self.descriptionF.value()
        if self.node.description != description:
            self.scene.undoStack.push(CommandNodeSetDescription(self.node, description))

    def handlePositionChanged(self):
        """
        Move the node properly if the position has been changed.
        """
        x = clamp(self.xField.value(), 0, self.scene.sceneRect().width())
        y = clamp(self.yField.value(), 0, self.scene.sceneRect().height())
        pos1 = self.node.pos()
        pos2 = QPointF(x, y)

        if pos1 != pos2:

            diff = pos2 - pos1

            data1 = {
                'nodes': {
                    self.node: {
                        'anchors': {k: v for k, v in self.node.anchors.items()},
                        'pos': pos1,
                    }
                },
                'edges': {}
            }

            data2 = {
                'nodes': {
                    self.node: {
                        'anchors': {k: v + diff for k, v in self.node.anchors.items()},
                        'pos': pos2,
                    }
                },
                'edges': {}
            }

            self.scene.undoStack.push(CommandNodeMove(data1, data2))