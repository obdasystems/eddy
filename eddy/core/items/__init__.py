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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
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

from eddy.core.datatypes import Item
from eddy.core.functions import cutR


class AbstractItem(QGraphicsItem):
    """
    Base class for all the diagram items.
    """
    __metaclass__ = ABCMeta

    item = Item.Undefined
    prefix = 'i'

    def __init__(self, scene, id=None, **kwargs):
        """
        Initialize the item.
        :type scene: DiagramScene
        :type id: str
        :type description: str
        :type url: str
        """
        self._id = id or scene.guid.next(self.prefix)
        self.selectionBrush = QBrush(Qt.NoBrush)
        self.selectionPen = QPen(Qt.NoPen)
        self.brush = QBrush(Qt.NoBrush)
        self.pen = QPen(Qt.NoPen)
        super().__init__(**kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def edge(self):
        """
        Tells whether the current element is an Edge.
        :rtype: bool
        """
        return Item.InclusionEdge <= self.item <= Item.InstanceOfEdge

    @property
    def id(self):
        """
        Returns the node id.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Set the node id.
        :type value: str
        """
        self._id = value

    @property
    def name(self):
        """
        Returns the item readable name.
        :rtype: str
        """
        return self.item.label

    @property
    def shortname(self):
        """
        Returns the item readable short name, i.e:
        * .name = datatype restriction node | .shortname = datatype restriction
        * .name = inclusion edge | .shortname = inclusion edge
        :rtype: str
        """
        return cutR(cutR(self.name, ' node'), ' edge')

    @property
    def node(self):
        """
        Tells whether the current element is a node.
        :rtype: bool
        """
        return Item.ConceptNode <= self.item <= Item.PropertyAssertionNode

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        pass

    def isItem(self, *args):
        """
        Tells whether the current item is one of the given types.
        :type args: Item
        :rtype: bool
        """
        return self.item in args

    @abstractmethod
    def updateBrush(self, **kwargs):
         """
         Perform updates on pens and brushes needed by the paint() method.
         """
         pass

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   REPRESENTATION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def __repr__(self):
        """
        Object representaton.
        """
        return '{}:{}'.format(self.__class__.__name__, self.id)


class LabelItem(QGraphicsTextItem):
    """
    Base class for all the diagram labels: this class is mostly needed to improve performances.
    By using the LabelItem interface we can check the item type using the isItem() method instead of using isinstance().
    """
    __metaclass__ = ABCMeta

    item = Item.Undefined

    def __init__(self, parent=None):
        """
        Initialize the Label item.
        :type parent: QObject
        """
        super().__init__(parent)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def edge(self):
        """
        Tells whether the current element is an Edge.
        :rtype: bool
        """
        return False

    @property
    def node(self):
        """
        Tells whether the current element is a Node.
        :rtype: bool
        """
        return False

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def isItem(self, *args):
        """
        Tells whether the current item is one of the given types.
        :type args: Item
        :rtype: bool
        """
        return self.item in args

    ####################################################################################################################
    #                                                                                                                  #
    #   REPRESENTATION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def __repr__(self):
        """
        Object representaton.
        """
        return '{}:{}'.format(self.__class__.__name__, self.id)


from eddy.core.items.nodes import AttributeNode
from eddy.core.items.nodes import ComplementNode
from eddy.core.items.nodes import ConceptNode
from eddy.core.items.nodes import DatatypeRestrictionNode
from eddy.core.items.nodes import DisjointUnionNode
from eddy.core.items.nodes import DomainRestrictionNode
from eddy.core.items.nodes import EnumerationNode
from eddy.core.items.nodes import IndividualNode
from eddy.core.items.nodes import IntersectionNode
from eddy.core.items.nodes import PropertyAssertionNode
from eddy.core.items.nodes import RangeRestrictionNode
from eddy.core.items.nodes import RoleNode
from eddy.core.items.nodes import RoleChainNode
from eddy.core.items.nodes import RoleInverseNode
from eddy.core.items.nodes import UnionNode
from eddy.core.items.nodes import ValueDomainNode
from eddy.core.items.nodes import ValueRestrictionNode
from eddy.core.items.edges import InclusionEdge
from eddy.core.items.edges import InputEdge
from eddy.core.items.edges import InstanceOfEdge