# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from datetime import datetime

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QDialogButtonBox, QTabWidget, QFormLayout
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView

from eddy.commands import CommandNodeMove, CommandNodeSetURL, CommandNodeSetDescription
from eddy.commands import CommandSceneResize, CommandNodeLabelEdit, CommandNodeChangeInputOrder
from eddy.datatypes import DistinctList
from eddy.fields import StringEditField, TextEditField, SpinBox, IntEditField
from eddy.functions import clamp, connect, isEmpty


########################################################################################################################
#                                                                                                                      #
#   DIAGRAM SCENE                                                                                                      #
#                                                                                                                      #
########################################################################################################################


class ScenePropertiesDialog(QDialog):
    """
    This class implements the 'Scene properties' dialog.
    """
    def __init__(self, scene, parent=None):
        """
        Initialize the scene properties dialog.
        :param scene: the scene whose properties we want to display.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.scene = scene
        self.mainWidget = QTabWidget(self)

        ################################################################################################################
        #                                                                                                              #
        #   GENERAL TAB                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)

        # amount of nodes in the scene
        self.nodesF = IntEditField(self.generalWidget)
        self.nodesF.setEnabled(False)
        self.nodesF.setFixedWidth(300)
        self.nodesF.setValue(len(self.scene.nodes()))

        # amount of edges in the scene
        self.edgesF = IntEditField(self.generalWidget)
        self.edgesF.setEnabled(False)
        self.edgesF.setFixedWidth(300)
        self.edgesF.setValue(len(self.scene.edges()))

        self.generalLayout.addRow('N° nodes', self.nodesF)
        self.generalLayout.addRow('N° edges', self.edgesF)

        self.mainWidget.addTab(self.generalWidget, 'General')

        ################################################################################################################
        #                                                                                                              #
        #   GEOMETRY TAB                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        R = self.scene.sceneRect()

        self.sceneSizeF = SpinBox(self)
        self.sceneSizeF.setRange(self.scene.MinSize, self.scene.MaxSize)
        self.sceneSizeF.setSingleStep(100)
        self.sceneSizeF.setValue(R.width())

        self.geometryLayout.addRow('Size', self.sceneSizeF)

        self.mainWidget.addTab(self.geometryWidget, 'Geometry')

        ################################################################################################################
        #                                                                                                              #
        #   DOCUMENT WIDGET                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        if self.scene.document.filepath:

            self.documentWidget = QWidget()
            self.documentLayout = QFormLayout(self.documentWidget)

            # filepath of the saved document
            self.filepathF = StringEditField(self.documentWidget)
            self.filepathF.setEnabled(False)
            self.filepathF.setFixedWidth(300)
            self.filepathF.setValue(self.scene.document.filepath)

            # timestamp when the document has been last modified
            self.editedF = StringEditField(self.documentWidget)
            self.editedF.setEnabled(False)
            self.editedF.setFixedWidth(300)
            self.editedF.setValue(datetime.fromtimestamp(int(self.scene.document.edited)).strftime('%Y/%m/%d %H:%M:%S'))

            self.documentLayout.addRow('File', self.filepathF)
            self.documentLayout.addRow('Last edit', self.editedF)

            self.mainWidget.addTab(self.documentWidget, 'Document')

        ################################################################################################################
        #                                                                                                              #
        #   BUTTON BOX                                                                                                 #
        #                                                                                                              #
        ################################################################################################################

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)

        ################################################################################################################
        #                                                                                                              #
        #   MAIN LAYOUT                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Scene properties')
        self.setWindowIcon(QIcon(':/images/eddy'))

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE SIGNALS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        connect(self.finished, self.handleFinished)
        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def handleFinished(self, code):
        """
        Executed when the dialog is terminated.
        :param code: the result code.
        """
        if code == QDialog.Accepted:
            self.handleSceneSizeChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def handleSceneSizeChanged(self):
        """
        Change the sice of the scene rect.
        """
        size1 = self.scene.sceneRect().width()
        size2 = self.sceneSizeF.value()

        if size1 != size2:

            # see if the new size is sufficient to contain all the elements in the scene
            items = self.scene.items()

            if len(items) > 0:

                X = set()
                Y = set()

                for item in items:
                    B = item.mapRectToScene(item.boundingRect())
                    X |= {B.left(), B.right()}
                    Y |= {B.top(), B.bottom()}

                # clamp size2 so that all the elements in the scene stays visible
                size2 = max(size2, abs(min(X) * 2), abs(max(X) * 2), abs(min(Y) * 2), abs(max(Y) * 2))

            self.scene.undostack.push(CommandSceneResize(self.scene, QRectF(-size2 / 2, -size2 / 2, size2, size2)))


########################################################################################################################
#                                                                                                                      #
#   NODE GENERIC                                                                                                       #
#                                                                                                                      #
########################################################################################################################


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

        ################################################################################################################
        #                                                                                                              #
        #   GENERAL TAB                                                                                                #
        #                                                                                                              #
        ################################################################################################################
        
        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)

        self.idF = StringEditField(self.generalWidget)
        self.idF.setEnabled(False)
        self.idF.setFixedWidth(300)
        self.idF.setValue(self.node.id)

        self.typeF = StringEditField(self.generalWidget)
        self.typeF.setEnabled(False)
        self.typeF.setFixedWidth(300)
        self.typeF.setValue(self.node.name)

        self.identityF = StringEditField(self.generalWidget)
        self.identityF.setEnabled(False)
        self.identityF.setFixedWidth(300)
        self.identityF.setValue(self.node.identity.label)

        self.urlF = StringEditField(self.generalWidget)
        self.urlF.setFixedWidth(300)
        self.urlF.setValue(self.node.url)

        self.descriptionF = TextEditField(self.generalWidget)
        self.descriptionF.setFixedSize(300, 160)
        self.descriptionF.setValue(self.node.description)

        self.generalLayout.addRow('ID', self.idF)
        self.generalLayout.addRow('Type', self.typeF)
        self.generalLayout.addRow('Identity', self.identityF)
        self.generalLayout.addRow('URL', self.urlF)
        self.generalLayout.addRow('Description', self.descriptionF)
        
        ################################################################################################################
        #                                                                                                              #
        #   GEOMETRY TAB                                                                                               #
        #                                                                                                              #
        ################################################################################################################
        
        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        P = self.node.pos()
        R = self.scene.sceneRect()

        self.xField = SpinBox(self.geometryWidget)
        self.xField.setFixedWidth(60)
        self.xField.setRange(R.left(), R.right())
        self.xField.setValue(int(P.x()))

        self.yField = SpinBox(self.geometryWidget)
        self.yField.setFixedWidth(60)
        self.yField.setRange(R.top(), R.bottom())
        self.yField.setValue(int(P.y()))

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

        ################################################################################################################
        #                                                                                                              #
        #   MAIN WIDGET                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, 'General')
        self.mainWidget.addTab(self.geometryWidget, 'Geometry')

        ################################################################################################################
        #                                                                                                              #
        #   BUTTON BOX                                                                                                 #
        #                                                                                                              #
        ################################################################################################################

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)

        ################################################################################################################
        #                                                                                                              #
        #   MAIN LAYOUT                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Properties')
        self.setWindowIcon(QIcon(':/images/eddy'))

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE SIGNALS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        connect(self.finished, self.handleFinished)
        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def handleFinished(self, code):
        """
        Executed when the dialog is terminated.
        :param code: the result code.
        """
        if code == QDialog.Accepted:
            self.handlePositionChanged()
            self.handleURLChanged()
            self.handleDescriptionChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def handleURLChanged(self):
        """
        Change the url property of the node.
        """
        url = self.urlF.value()
        if self.node.url != url:
            self.scene.undostack.push(CommandNodeSetURL(self.node, url))

    def handleDescriptionChanged(self):
        """
        Change the url property of the node.
        """
        description = self.descriptionF.value()
        if self.node.description != description:
            self.scene.undostack.push(CommandNodeSetDescription(self.node, description))

    def handlePositionChanged(self):
        """
        Move the node properly if the position has been changed.
        """
        R = self.scene.sceneRect()
        x = clamp(self.xField.value(), R.left(), R.right())
        y = clamp(self.yField.value(), R.top(), R.bottom())
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

            self.scene.undostack.push(CommandNodeMove(scene=self.scene, pos1=data1, pos2=data2))


########################################################################################################################
#                                                                                                                      #
#   EDITABLE NODES                                                                                                     #
#                                                                                                                      #
########################################################################################################################


class EditableNodePropertiesDialog(NodePropertiesDialog):
    """
    This class implements the properties dialog for label editable nodes.
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the editable node properties dialog.
        :param scene: the scene the node is placed into.
        :param node: the node whose properties we want to inspect.
        :param parent: the parent widget.
        """
        super().__init__(scene, node, parent)

        ################################################################################################################
        #                                                                                                              #
        #   LABEL TAB                                                                                                  #
        #                                                                                                              #
        ################################################################################################################

        self.labelWidget = QWidget()
        self.labelLayout = QFormLayout(self.labelWidget)

        self.labelF = StringEditField(self.labelWidget)
        self.labelF.setFixedWidth(300)
        self.labelF.setValue(self.node.labelText())
        self.labelF.setEnabled(self.node.label.editable)

        self.labelLayout.addRow('Text', self.labelF)

        self.mainWidget.addTab(self.labelWidget, 'Label')

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def handleFinished(self, code):
        """
        Executed when the dialog is terminated.
        :param code: the result code.
        """
        if code == QDialog.Accepted:
            super().handleFinished(code)
            self.handleLabelChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def handleLabelChanged(self):
        """
        Change the label of the node.
        """
        value = self.labelF.value().strip()
        if self.node.labelText().strip() != value:
            value = value if not isEmpty(value) else self.node.label.defaultText
            command = CommandNodeLabelEdit(self.scene, self.node)
            command.end(value)
            self.scene.undostack.push(command)


########################################################################################################################
#                                                                                                                      #
#   ORDERED INPUT NODES                                                                                                #
#                                                                                                                      #
########################################################################################################################


class OrderedInputNodePropertiesDialog(NodePropertiesDialog):
    """
    This class implements the properties dialog for constructor nodes having incoming input edges
    numbered according to source nodes partecipations to the axiom (Role chain and Property assertion).
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the editable node properties dialog.
        :param scene: the scene the node is placed into.
        :param node: the node whose properties we want to inspect.
        :param parent: the parent widget.
        """
        super().__init__(scene, node, parent)

        ################################################################################################################
        #                                                                                                              #
        #   ORDERING TAB                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        if self.node.inputs:

            self.orderingWidget = QWidget()
            self.orderingLayout = QFormLayout(self.orderingWidget)

            self.listWidget = QListWidget(self.orderingWidget)
            self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
            for i in self.node.inputs:
                edge = self.scene.edge(i)
                item = QListWidgetItem('{} ({})'.format(edge.source.labelText(), edge.source.id))
                item.setData(Qt.UserRole, edge.id)
                self.listWidget.addItem(item)

            self.orderingLayout.addRow('Sort', self.listWidget)
            self.mainWidget.addTab(self.orderingWidget, 'Ordering')

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def handleFinished(self, code):
        """
        Executed when the dialog is terminated.
        :param code: the result code.
        """
        if code == QDialog.Accepted:
            super().handleFinished(code)
            self.handleInputsOrderChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def handleInputsOrderChanged(self):
        """
        Change the order of inputs edges.
        """
        if self.node.inputs:

            inputs = DistinctList()
            for i in range(0, self.listWidget.count()):
                item = self.listWidget.item(i)
                inputs.append(item.data(Qt.UserRole))

            if self.node.inputs != inputs:
                self.scene.undostack.push(CommandNodeChangeInputOrder(self.scene, self.node, inputs))