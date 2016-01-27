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


from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPixmap, QPainter, QPen, QColor

from eddy.core.datatypes import Font, Item, Restriction, Special, DiagramMode, Identity
from eddy.core.functions import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import Label

from eddy.ui.properties import EditableNodeProperties


class RoleNode(AbstractResizableNode):
    """
    This class implements the 'Role' node.
    """
    indexL = 0
    indexB = 1
    indexT = 3
    indexR = 2
    indexE = 4

    identities = {Identity.Role}
    item = Item.RoleNode
    minheight = 50
    minwidth = 70
    xmlname = 'role'

    def __init__(self, width=minwidth, height=minheight, brush='#fcfcfc',special=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        :type special: Special
        """
        super().__init__(**kwargs)

        self._special = special

        self.brush = brush
        self.pen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)
        self.polygon = self.createPolygon(max(width, self.minwidth), max(height, self.minheight))
        self.label = Label('role', movable=special is None, editable=special is None, parent=self)
        self.updateHandlesPos()
        self.updateLabelPos()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Role

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return self._special

    @special.setter
    def special(self, special):
        """
        Set the special type of this node.
        :type special: Special
        """
        self._special = special
        self.label.editable = self._special is None
        self.label.movable = self._special is None
        self.label.setText(self._special.value if self._special else self.label.defaultText)

    @property
    def asymmetric(self):
        """
        Tells whether the Role is defined as asymmetric.
        :rtype: bool
        """
        for e1 in self.edges:
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleInverseNode):
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.source is e1.target and \
                            e2.target.isItem(Item.ComplementNode):
                        for e3 in e2.target.edges:
                            if e3.isItem(Item.InclusionEdge) and \
                                e3.target is e2.target and \
                                    e3.source is self:
                                return True
        return False

    @property
    def asymmetryPath(self):
        """
        Returns a collection of items that are defining the asymmetry for this role node.
        :rtype: set
        """
        paths = set()
        for e1 in self.edges:
            path = set()
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleInverseNode) and \
                        all(x not in paths for x in {e1, e1.target}):
                path |= {e1, e1.target}
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.source is e1.target and \
                            e2.target.isItem(Item.ComplementNode) and \
                                all(x not in paths for x in {e2, e2.target}):
                        path |= {e2, e2.target}
                        for e3 in e2.target.edges:
                            if e3.isItem(Item.InclusionEdge) and \
                                e3.target is e2.target and \
                                    e3.source is self and \
                                        e3 not in paths:
                                paths |= path | {e3}
        return paths

    @property
    def irreflexive(self):
        """
        Tells whether the Role is defined as irreflexive.
        :rtype: bool
        """
        for e1 in self.edges:
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.DomainRestrictionNode) and \
                        e1.target.restriction is Restriction.Self:
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.source is e1.target and \
                            e2.target.isItem(Item.ComplementNode):
                        for e3 in e2.target.edges:
                            if e3.source.isItem(Item.ConceptNode) and \
                                e3.source.special is Special.Top and \
                                    e3.target is e2.target:
                                return True
        return False

    @property
    def irreflexivityPath(self):
        """
        Returns a collection of items that are defining the irreflexivity for this role node.
        :rtype: set
        """
        paths = set()
        for e1 in self.edges:
            path = set()
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.DomainRestrictionNode) and \
                        e1.target.restriction is Restriction.Self and \
                            all(x not in paths for x in {e1, e1.target}):
                path |= {e1, e1.target}
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.source is e1.target and \
                            e2.target.isItem(Item.ComplementNode) and \
                                all(x not in paths for x in {e2, e2.target}):
                        path |= {e2, e2.target}
                        for e3 in e2.target.edges:
                            if e3.source.isItem(Item.ConceptNode) and \
                                e3.source.special is Special.Top and \
                                    e3.target is e2.target and \
                                        all(x not in paths for x in {e3, e3.source}):
                                paths |= path | {e3, e3.source}
        return paths

    @property
    def reflexive(self):
        """
        Tells whether the Role is defined as reflexive.
        :rtype: bool
        """
        for e1 in self.edges:
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.DomainRestrictionNode) and \
                        e1.target.restriction is Restriction.Self:
                for e2 in e1.target.edges:
                    if e2.source.isItem(Item.ConceptNode) and \
                        e2.source.special is Special.Top and \
                            e2.target is e1.target:
                        return True
        return False

    @property
    def reflexivityPath(self):
        """
        Returns a collection of items that are defining the reflexivity for this role node.
        :rtype: set
        """
        paths = set()
        for e1 in self.edges:
            path = set()
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.DomainRestrictionNode) and \
                        e1.target.restriction is Restriction.Self and \
                            all(x not in paths for x in {e1, e1.target}):
                path |= {e1, e1.target}
                for e2 in e1.target.edges:
                    if e2.source.isItem(Item.ConceptNode) and \
                        e2.source.special is Special.Top and \
                            e2.target is e1.target and \
                                all(x not in paths for x in {e2, e2.source}):
                        paths |= path | {e2, e2.source}
        return paths

    @property
    def symmetric(self):
        """
        Tells whether the Role is defined as asymmetric.
        :rtype: bool
        """
        for e1 in self.edges:
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleInverseNode):
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InclusionEdge) and \
                        e2.target is e1.target and \
                            e2.source is self:
                        return True
        return False

    @property
    def symmetryPath(self):
        """
        Returns a collection of items that are defining the simmetry for this role node.
        :rtype: set
        """
        paths = set()
        for e1 in self.edges:
            path = set()
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleInverseNode) and \
                        all(x not in paths for x in {e1, e1.target}):
                path |= {e1, e1.target}
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InclusionEdge) and \
                        e2.target is e1.target and \
                            e2.source is self and \
                                e2 not in paths:
                        paths |= path | {e2}
        return paths

    @property
    def transitive(self):
        """
        Tells whether the Role is defined as transitive.
        :rtype: bool
        """
        for e1 in self.edges:
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleChainNode):
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.target is e1.target and \
                            e2 is not e1 and e2.source is self:
                        for e3 in e2.source.edges:
                            if e3.isItem(Item.InclusionEdge) and \
                                e3.source is e1.target and \
                                    e3.target is e1.source:
                                        return True
        return False

    @property
    def transitivityPath(self):
        """
        Returns a collection of items that are defining the transitivity for this role node.
        :rtype: set
        """
        paths = set()
        for e1 in self.edges:
            path = set()
            if e1.isItem(Item.InputEdge) and \
                e1.source is self and \
                    e1.target.isItem(Item.RoleChainNode) and \
                        all(x not in paths for x in {e1, e1.target}):
                path |= {e1, e1.target}
                for e2 in e1.target.edges:
                    if e2.isItem(Item.InputEdge) and \
                        e2.target is e1.target and \
                            e2 is not e1 and \
                                e2.source is self and \
                                    e2 not in paths:
                        path |= {e2}
                        for e3 in e2.source.edges:
                            if e3.isItem(Item.InclusionEdge) and \
                                e3.source is e1.target and \
                                    e3.target is e1.source and \
                                        e3 not in paths:
                                paths |= path | {e3}
        return paths

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()
        mainwindow = scene.mainwindow

        menu = super().contextMenu()
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeRefactor)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuChangeNodeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuRoleNodeCompose)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeSpecial)

        # Check currently composed axioms
        mainwindow.actionComposeAsymmetricRole.setChecked(self.asymmetric)
        mainwindow.actionComposeIrreflexiveRole.setChecked(self.irreflexive)
        mainwindow.actionComposeReflexiveRole.setChecked(self.reflexive)
        mainwindow.actionComposeSymmetricRole.setChecked(self.symmetric)
        mainwindow.actionComposeTransitiveRole.setChecked(self.transitive)

        # Switch the check on the currently active special
        for action in mainwindow.actionsNodeSetSpecial:
            action.setChecked(self.special is action.data())

        # Disable refactor name if special type is set
        mainwindow.actionRefactorName.setEnabled(self.special is None)

        if not self.special:
            collection = self.label.contextMenuAdd()
            if collection:
                menu.insertSeparator(mainwindow.actionOpenNodeProperties)
                for action in collection:
                    menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        kwargs = {
            'brush': self.brush,
            'description': self.description,
            'height': self.height(),
            'id': self.id,
            'scene': scene,
            'special': self.special,
            'url': self.url,
            'width': self.width(),
        }

        node = self.__class__(**kwargs)
        node.setPos(self.pos())
        node.setLabelText(self.labelText())
        node.setLabelPos(node.mapFromScene(self.mapToScene(self.labelPos())))
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.boundingRect().height() - 2 * (self.handleSize + self.handleSpace)

    def propertiesDialog(self):
        """
        Build and returns the node properties dialog.
        """
        return EditableNodeProperties(scene=self.scene(), node=self)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.boundingRect().width() - 2 * (self.handleSize + self.handleSpace)

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def createPolygon(shape_w, shape_h):
        """
        Returns the initialized polygon according to the given width/height.
        :type shape_w: int
        :type shape_h: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-shape_w / 2, 0),
            QPointF(0, +shape_h / 2),
            QPointF(+shape_w / 2, 0),
            QPointF(0, -shape_h / 2),
            QPointF(-shape_w / 2, 0)
        ])

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :type scene: DiagramScene
        :type E: QDomElement
        :rtype: Node
        """
        U = E.elementsByTagName('data:url').at(0).toElement()
        D = E.elementsByTagName('data:description').at(0).toElement()
        G = E.elementsByTagName('shape:geometry').at(0).toElement()
        L = E.elementsByTagName('shape:label').at(0).toElement()

        kwargs = {
            'brush': E.attribute('color', '#fcfcfc'),
            'description': D.text(),
            'height': int(G.attribute('height')),
            'id': E.attribute('id'),
            'scene': scene,
            'special': Special.forValue(L.text()),
            'url': U.text(),
            'width': int(G.attribute('width')),
        }

        node = cls(**kwargs)
        node.setPos(QPointF(int(G.attribute('x')), int(G.attribute('y'))))
        node.setLabelText(L.text())
        node.setLabelPos(node.mapFromScene(QPointF(int(L.attribute('x')), int(L.attribute('y')))))
        return node

    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :type document: QDomDocument
        :rtype: QDomElement
        """
        pos1 = self.pos()
        pos2 = self.mapToScene(self.labelPos())

        # create the root element for this node
        node = document.createElement('node')
        node.setAttribute('id', self.id)
        node.setAttribute('type', self.xmlname)
        node.setAttribute('color', self.brush.color().name())

        # add node attributes
        url = document.createElement('data:url')
        url.appendChild(document.createTextNode(self.url))
        description = document.createElement('data:description')
        description.appendChild(document.createTextNode(self.description))

        # add the shape geometry
        geometry = document.createElement('shape:geometry')
        geometry.setAttribute('height', self.height())
        geometry.setAttribute('width', self.width())
        geometry.setAttribute('x', pos1.x())
        geometry.setAttribute('y', pos1.y())

        # add the shape label
        label = document.createElement('shape:label')
        label.setAttribute('height', self.label.height())
        label.setAttribute('width', self.label.width())
        label.setAttribute('x', pos2.x())
        label.setAttribute('y', pos2.y())
        label.appendChild(document.createTextNode(self.label.text()))

        node.appendChild(url)
        node.appendChild(description)
        node.appendChild(geometry)
        node.appendChild(label)

        return node

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        o = self.handleSize + self.handleSpace
        x = self.polygon[self.indexL].x()
        y = self.polygon[self.indexT].y()
        w = self.polygon[self.indexR].x() - x
        h = self.polygon[self.indexB].y() - y
        return QRectF(x - o, y - o, w + o * 2, h + o * 2)

    # noinspection PyTypeChecker
    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        offset = self.handleSize + self.handleSpace
        moved = self.label.moved
        scene = self.scene()
        snap = scene.settings.value('scene/snap_to_grid', False, bool)
        rect = self.boundingRect()
        diff = QPointF(0, 0)

        minBoundingRectW = self.minwidth + offset * 2
        minBoundingRectH = self.minheight + offset * 2

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            self.polygon[self.indexT] = QPointF(rect.left() + rect.width() / 2, rect.top() + offset)
            self.polygon[self.indexB] = QPointF(rect.left() + rect.width() / 2, self.polygon[self.indexB].y())
            self.polygon[self.indexL] = QPointF(rect.left() + offset, rect.top() + rect.height() / 2)
            self.polygon[self.indexE] = QPointF(rect.left() + offset, rect.top() + rect.height() / 2)
            self.polygon[self.indexR] = QPointF(self.polygon[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.handleSelected == self.handleTM:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setY(toY - fromY)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            self.polygon[self.indexT] = QPointF(self.polygon[self.indexT].x(), rect.top() + offset)
            self.polygon[self.indexL] = QPointF(self.polygon[self.indexL].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexE] = QPointF(self.polygon[self.indexE].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexR] = QPointF(self.polygon[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.handleSelected == self.handleTR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            self.polygon[self.indexT] = QPointF(rect.right() - rect.width() / 2, rect.top() + offset)
            self.polygon[self.indexB] = QPointF(rect.right() - rect.width() / 2, self.polygon[self.indexB].y())
            self.polygon[self.indexL] = QPointF(self.polygon[self.indexL].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexE] = QPointF(self.polygon[self.indexE].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexR] = QPointF(rect.right() - offset, rect.top() + rect.height() / 2)

        elif self.handleSelected == self.handleML:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            rect.setLeft(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())

            self.polygon[self.indexL] = QPointF(rect.left() + offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            self.polygon[self.indexE] = QPointF(rect.left() + offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            self.polygon[self.indexT] = QPointF(rect.left() + rect.width() / 2, self.polygon[self.indexT].y())
            self.polygon[self.indexB] = QPointF(rect.left() + rect.width() / 2, self.polygon[self.indexB].y())

        elif self.handleSelected == self.handleMR:

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            rect.setRight(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())

            self.polygon[self.indexR] = QPointF(rect.right() - offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            self.polygon[self.indexT] = QPointF(rect.right() - rect.width() / 2, self.polygon[self.indexT].y())
            self.polygon[self.indexB] = QPointF(rect.right() - rect.width() / 2, self.polygon[self.indexB].y())

        elif self.handleSelected == self.handleBL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            self.polygon[self.indexT] = QPointF(rect.left() + rect.width() / 2, self.polygon[self.indexT].y())
            self.polygon[self.indexB] = QPointF(rect.left() + rect.width() / 2, rect.bottom() - offset)
            self.polygon[self.indexL] = QPointF(rect.left() + offset, rect.bottom() - rect.height() / 2)
            self.polygon[self.indexE] = QPointF(rect.left() + offset, rect.bottom() - rect.height() / 2)
            self.polygon[self.indexR] = QPointF(self.polygon[self.indexR].x(), rect.bottom() - rect.height() / 2)

        elif self.handleSelected == self.handleBM:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setY(toY - fromY)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            self.polygon[self.indexB] = QPointF(self.polygon[self.indexB].x(), rect.bottom() - offset)
            self.polygon[self.indexL] = QPointF(self.polygon[self.indexL].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexE] = QPointF(self.polygon[self.indexE].x(), rect.top() + rect.height() / 2)
            self.polygon[self.indexR] = QPointF(self.polygon[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.handleSelected == self.handleBR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            self.polygon[self.indexT] = QPointF(rect.right() - rect.width() / 2, self.polygon[self.indexT].y())
            self.polygon[self.indexB] = QPointF(rect.right() - rect.width() / 2, rect.bottom() - offset)
            self.polygon[self.indexL] = QPointF(self.polygon[self.indexL].x(), rect.bottom() - rect.height() / 2)
            self.polygon[self.indexE] = QPointF(self.polygon[self.indexE].x(), rect.bottom() - rect.height() / 2)
            self.polygon[self.indexR] = QPointF(rect.right() - offset, rect.bottom() - rect.height() / 2)

        self.updateHandlesPos()
        self.updateLabelPos(moved=moved)

        # update edge anchors
        for edge, pos in self.mousePressData.items():
            self.setAnchor(edge, pos + diff * 0.5)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)

        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)

        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def labelPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def setLabelPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def setLabelText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)

    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :type painter: QPainter
        :type option: int
        :type widget: QWidget
        """
        scene = self.scene()

        if scene.mode is not DiagramMode.NodeResize and self.isSelected():
            painter.setPen(self.selectionPen)
            painter.drawRect(self.boundingRect())

        if scene.mode is DiagramMode.EdgeInsert and scene.mouseOverNode is self:

            edge = scene.command.edge
            brush = self.brushConnectionOk
            if not scene.validator.valid(edge.source, edge, scene.mouseOverNode):
                brush = self.brushConnectionBad

            boundingRect = self.boundingRect()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawPolygon(self.createPolygon(boundingRect.width(), boundingRect.height()))

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawPolygon(self.polygon)
        self.paintHandles(painter)

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = cls.createPolygon(46, 34)

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the rectangle
        painter.setFont(Font('Arial', 11, Font.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'role')

        return pixmap