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


from collections import OrderedDict
from functools import partial
from pygraphol.commands import CommandNodeHexagonSwitchTo
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeMixin
from PyQt5.QtCore import QPointF, Qt, QLineF
from PyQt5.QtGui import QColor, QPen, QPolygonF, QPainter, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QGraphicsPolygonItem, QAction


class Hexagon(QGraphicsPolygonItem, ShapeMixin):
    """
    This class implements an irregolar hexagon which is used to render some 'Construct' nodes.
    """
    HSpan = 70.0
    VSpan = 40.0
    DSize = 10.0

    shapePen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)

    def __init__(self, **kwargs):
        """
        Initialize the diamond shape.
        :param item: the node attached to this shape.
        :param r: the red component of the shape background.
        :param g: the green component of the shape background.
        :param b: the blue component of the shape background.
        :param text: the text to be rendered inside the shape.
        :param parent: the parent element.
        """
        # remove some data from kwargs so the super() constructor doesn't complain
        label = kwargs.pop('text', '')
        brush = QColor(*kwargs.pop('rgb', (252, 252, 252)))

        super().__init__(**kwargs)

        # store shape default brush locally
        self.shapeBrush = brush

        # initialize the polygon
        self.setPolygon(Hexagon.getPolygon(Hexagon.HSpan, Hexagon.VSpan, Hexagon.DSize))

        # initialize shape label with default text
        self.label = Label(label, movable=False, editable=False, parent=self)
        self.label.updatePos()

    ################################################## EVENT HANDLERS ##################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()
        contextMenu.addSeparator()

        data = OrderedDict()

        # keep those imports defered to avoid cyclic import troubles
        from pygraphol.items.nodes import UnionNode, DisjointUnionNode
        from pygraphol.items.nodes import EnumerationNode, RoleChainNode, RoleInverseNode
        from pygraphol.items.nodes import ComplementNode, IntersectionNode, DatatypeRestrictionNode

        data[ComplementNode] = 'Complement'
        data[DisjointUnionNode] = 'Disjoint union'
        data[DatatypeRestrictionNode] = 'Datatype restriction'
        data[EnumerationNode] = 'Enumeration'
        data[IntersectionNode] = 'Intersection'
        data[RoleChainNode] = 'Role chain'
        data[RoleInverseNode] = 'Role inverse'
        data[UnionNode] = 'Union'

        subMenu = contextMenu.addMenu('Switch to')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        for k, v in data.items():
            if not isinstance(self.node, k):
                action = QAction(v, scene)
                action.triggered.connect(partial(self.handleSwitchTo, clazz=k))
                subMenu.addAction(action)

        contextMenu.exec_(menuEvent.screenPos())

    ################################################## ACTION HANDLERS #################################################

    def handleSwitchTo(self, clazz):
        """
        Switch the current node to a different type.
        :param clazz: the class implementing the new node type.
        """
        scene = self.scene()
        xnode = clazz(scene)
        xnode.shape.setPos(self.pos())
        scene.undoStack.push(CommandNodeHexagonSwitchTo(scene, self.node, xnode))

    ################################################ AUXILIARY METHODS #################################################

    @staticmethod
    def getPolygon(shape_w, shape_h, oblique):
        """
        Returns the initialized polygon according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
        :param oblique: the width of the oblique side.
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-shape_w / 2, 0),
            QPointF(-shape_w / 2 + oblique, +shape_h / 2),
            QPointF(+shape_w / 2 - oblique, +shape_h / 2),
            QPointF(+shape_w / 2, 0),
            QPointF(+shape_w / 2 - oblique, -shape_h / 2),
            QPointF(-shape_w / 2 + oblique, -shape_h / 2),
            QPointF(-shape_w / 2, 0)
        ])

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.boundingRect().height()

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        intersection = QPointF()
        polygon = self.mapToScene(self.polygon())

        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection

        return None

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.boundingRect().width()

    ################################################### ITEM DRAWING ###################################################
    
    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 48
        shape_h = 30
        oblique = 6

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = Hexagon.getPolygon(shape_w, shape_h, oblique)

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(*kwargs['rgb']))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the polygon
        if 'text' in kwargs:
            painter.setFont(QFont('Arial', 11, QFont.Light))
            painter.drawText(polygon.boundingRect(), Qt.AlignCenter, kwargs['text'])

        return pixmap
    
    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.shapeSelectedBrush if self.isSelected() else self.shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawPolygon(self.polygon())