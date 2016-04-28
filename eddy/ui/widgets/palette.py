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


from PyQt5.QtCore import Qt, QSize, QMimeData
from PyQt5.QtGui import QIcon, QPainter, QDrag
from PyQt5.QtWidgets import QWidget, QGridLayout, QButtonGroup, QToolButton
from PyQt5.QtWidgets import QApplication, QStyleOption, QStyle

from eddy.core.datatypes.graphol import Item
from eddy.core.items.nodes.attribute import AttributeNode
from eddy.core.items.nodes.complement import ComplementNode
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.datatype_restriction import DatatypeRestrictionNode
from eddy.core.items.nodes.disjoint_union import DisjointUnionNode
from eddy.core.items.nodes.domain_restriction import DomainRestrictionNode
from eddy.core.items.nodes.enumeration import EnumerationNode
from eddy.core.items.nodes.individual import IndividualNode
from eddy.core.items.nodes.intersection import IntersectionNode
from eddy.core.items.nodes.property_assertion import PropertyAssertionNode
from eddy.core.items.nodes.range_restriction import RangeRestrictionNode
from eddy.core.items.nodes.role import RoleNode
from eddy.core.items.nodes.role_chain import RoleChainNode
from eddy.core.items.nodes.role_inverse import RoleInverseNode
from eddy.core.items.nodes.union import UnionNode
from eddy.core.items.nodes.value_domain import ValueDomainNode
from eddy.core.items.nodes.value_restriction import ValueRestrictionNode
from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.edges.input import InputEdge
from eddy.core.items.edges.membership import MembershipEdge


class Palette(QWidget):
    """
    This class implements the graphol palette.
    """
    Padding = 6
    Spacing = 4

    def __init__(self, *args):
        """
        Initialize the Palette.
        """
        super().__init__(*args)
        self.buttonById = {}
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(False)
        self.buttonClicked = self.buttonGroup.buttonClicked
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, Palette.Padding, 0, Palette.Padding)
        self.mainLayout.setSpacing(Palette.Spacing)
        self.add(ConceptNode, 0, 0)
        self.add(RoleNode, 0, 1)
        self.add(AttributeNode, 0, 2)
        self.add(IndividualNode, 1, 0)
        self.add(ValueDomainNode, 1, 1)
        self.add(ValueRestrictionNode, 1, 2)
        self.add(DomainRestrictionNode, 2, 0)
        self.add(RangeRestrictionNode, 2, 1)
        self.add(IntersectionNode, 2, 2)
        self.add(RoleChainNode, 3, 0)
        self.add(DatatypeRestrictionNode, 3, 1)
        self.add(RoleInverseNode, 3, 2)
        self.add(ComplementNode, 4, 0)
        self.add(EnumerationNode, 4, 1)
        self.add(UnionNode, 4, 2)
        self.add(DisjointUnionNode, 5, 0)
        self.add(PropertyAssertionNode, 5, 1)
        self.add(InclusionEdge, 5, 2)
        self.add(InputEdge, 6, 0)
        self.add(MembershipEdge, 6, 1)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)
        #self.setMaximumHeight(372)

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    #############################################
    #   INTERFACE
    #################################

    def add(self, clazz, row, column):
        """
        Add a button to the palette.
        :type clazz: class
        :type row: int
        :type column: int
        """
        button = PaletteButton(clazz)
        self.buttonById[clazz.Type] = button
        self.buttonGroup.addButton(button, clazz.Type)
        self.mainLayout.addWidget(button, row, column)

    def button(self, item):
        """
        Returns the button matching the given item type.
        :type item: Item
        :rtype: PaletteButton
        """
        return self.buttonById[item]

    def clear(self, *args):
        """
        Clear the palette selection.
        :type args: Item
        """
        for button in self.buttonById.values():
            if button not in args:
                button.setChecked(False)

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QSize
        """
        return QSize(216, 372)


class PaletteButton(QToolButton):
    """
    This class implements a single palette button.
    """
    def __init__(self, clazz, parent=None):
        """
        Initialize the palette button.
        :type clazz: class
        :type parent: QWidget
        """
        super().__init__(parent)
        self.item = clazz.Type
        self.pixmap = clazz.image(w=60, h=44)
        self.startPos = None
        self.setCheckable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIcon(QIcon(self.pixmap))
        self.setIconSize(QSize(60, 44))

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the button..
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            self.startPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    # noinspection PyArgumentList
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            # Exclude edges from drag & drop.
            if Item.ConceptNode <= self.item <= Item.PropertyAssertionNode:

                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QApplication.startDragDistance():

                    mimeData = QMimeData()
                    mimeData.setText(str(self.item.value))

                    drag = QDrag(self)
                    drag.setMimeData(mimeData)
                    drag.setPixmap(self.pixmap)
                    drag.setHotSpot(self.startPos - self.rect().topLeft())
                    drag.exec_(Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released.
        :type mouseEvent: QMouseEvent
        """
        super().mouseReleaseEvent(mouseEvent)