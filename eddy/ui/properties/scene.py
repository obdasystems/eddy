# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from datetime import datetime

from PyQt5.QtCore import Qt, QRectF, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QDialogButtonBox, QTabWidget, QFormLayout

from eddy.core.commands import CommandSceneResize
from eddy.core.functions import connect

from eddy.ui.fields import StringField, SpinBox, IntField


class SceneProperty(QDialog):
    """
    This class implements the 'Scene properties' dialog.
    """
    def __init__(self, scene, parent=None):
        """
        Initialize the scene properties dialog.
        :type scene: DiagramScene
        :type parent: QWidget
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

        # Amount of nodes in the scene
        self.nodesField = IntField(self.generalWidget)
        self.nodesField.setReadOnly(True)
        self.nodesField.setFixedWidth(300)
        self.nodesField.setValue(len(self.scene.nodes()))

        # Amount of edges in the scene
        self.edgesField = IntField(self.generalWidget)
        self.nodesField.setReadOnly(True)
        self.edgesField.setFixedWidth(300)
        self.edgesField.setValue(len(self.scene.edges()))

        self.generalLayout.addRow('N° nodes', self.nodesField)
        self.generalLayout.addRow('N° edges', self.edgesField)

        self.mainWidget.addTab(self.generalWidget, 'General')

        ################################################################################################################
        #                                                                                                              #
        #   GEOMETRY TAB                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        R = self.scene.sceneRect()

        self.sceneSizeField = SpinBox(self)
        self.sceneSizeField.setRange(self.scene.MinSize, self.scene.MaxSize)
        self.sceneSizeField.setSingleStep(100)
        self.sceneSizeField.setValue(R.width())

        self.geometryLayout.addRow('Size', self.sceneSizeField)

        self.mainWidget.addTab(self.geometryWidget, 'Geometry')

        ################################################################################################################
        #                                                                                                              #
        #   DOCUMENT WIDGET                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        if self.scene.document.path:

            self.documentWidget = QWidget()
            self.documentLayout = QFormLayout(self.documentWidget)

            # Filepath of the saved document.
            self.pathField = StringField(self.documentWidget)
            self.pathField.setReadOnly(True)
            self.pathField.setFixedWidth(300)
            self.pathField.setValue(self.scene.document.path)

            # Timestamp when the document has been last modified.
            self.editedField = StringField(self.documentWidget)
            self.editedField.setReadOnly(True)
            self.editedField.setFixedWidth(300)
            self.editedField.setValue(datetime.fromtimestamp(int(self.scene.document.edited)).strftime('%Y/%m/%d %H:%M:%S'))

            self.documentLayout.addRow('File', self.pathField)
            self.documentLayout.addRow('Last edit', self.editedField)

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

        connect(self.finished, self.completed)
        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(int)
    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == QDialog.Accepted:
            self.sceneSizeChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def sceneSizeChanged(self):
        """
        Change the size of the DiagramScene rectangle.
        """
        size1 = self.scene.sceneRect().width()
        size2 = self.sceneSizeField.value()

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