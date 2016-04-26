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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem

from eddy.core.datatypes.graphol import Item


class AbstractItem(QGraphicsItem):
    """
    Base class for all the diagram items.
    """
    __metaclass__ = ABCMeta

    Prefix = 'i'
    Type = Item.Undefined

    def __init__(self, project, id=None, **kwargs):
        """
        Initialize the item.
        :type project: Project
        :type id: str
        """
        super().__init__(**kwargs)
        self.id = id or project.guid.next(self.Prefix)
        self.selectionBrush = QBrush(Qt.NoBrush)
        self.selectionPen = QPen(Qt.NoPen)
        self.brush = QBrush(Qt.NoBrush)
        self.pen = QPen(Qt.NoPen)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram holding this item (alias for AbstractItem.scene()).
        :rtype: Diagram
        """
        return self.scene()

    @property
    def name(self):
        """
        Returns the item readable name.
        :rtype: str
        """
        item = self.type()
        return item.realname

    @property
    def shortname(self):
        """
        Returns the item readable short name, i.e:
        * .name = datatype restriction node | .shortname = datatype restriction
        * .name = inclusion edge | .shortname = inclusion
        :rtype: str
        """
        item = self.type()
        return item.shortname

    @property
    def project(self):
        """
        Returns the project this item belongs to.
        :rtype: Project
        """
        return self.diagram.parent()

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def copy(self, project):
        """
        Create a copy of the current item.
        :type project: Project
        """
        pass

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns a snapshot of this item suitable for the palette.
        :rtype: QPixmap
        """
        pass

    def isEdge(self):
        """
        Returns True if this element is an edge, False otherwise.
        :rtype: bool
        """
        return Item.InclusionEdge <= self.type() <= Item.MembershipEdge

    def isNode(self):
        """
        Returns True if this element is a node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type() <= Item.PropertyAssertionNode

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    @abstractmethod
    def redraw(self, **kwargs):
        """
        Schedule this item for redrawing.
        """
        pass

    def type(self):
        """
        Returns the type of this item.
        :rtype: Item
        """
        return self.Type

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{}:{}'.format(self.__class__.__name__, self.id)


class AbstractLabel(QGraphicsTextItem):
    """
    Base class for the diagram labels.
    """
    __metaclass__ = ABCMeta

    Type = Item.Label

    def __init__(self, parent=None):
        """
        Initialize the label.
        :type parent: QObject
        """
        super().__init__(parent)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram holding this label (alias for AbstractLabel.scene()).
        :rtype: Diagram
        """
        return self.scene()

    @property
    def project(self):
        """
        Returns the project this label belongs to.
        :rtype: Project
        """
        return self.diagram.parent()

    #############################################
    #   INTERFACE
    #################################

    @staticmethod
    def isEdge():
        """
        Returns True if this element is an edge, False otherwise.
        :rtype: bool
        """
        return False

    @staticmethod
    def isNode():
        """
        Returns True if this element is a node, False otherwise.
        :rtype: bool
        """
        return False

    def __repr__(self):
        """
        Returns repr(self).
        """
        return 'Label<{}:{}>'.format(self.parentItem().__class__.__name__, self.parentItem().id)