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


from abc import ABCMeta, abstractmethod

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem

from eddy.core.datatypes import Item


class AbstractItem(QGraphicsItem):
    """
    Base class for all the diagram items.
    """
    __metaclass__ = ABCMeta

    item = Item.Undefined  # an integer identifying this node as unique item type
    prefix = 'i' # a prefix character to be prepended to the unique id
    xmlname = 'item' # a lowercase word used to identify this node in XML related documents

    def __init__(self, scene, id=None, description='', url='', **kwargs):
        """
        Initialize the item.
        :type scene: DiagramScene
        :type id: str
        :type description: str
        :type url: str
        """
        self._id = id or scene.guid.next(self.prefix)
        self._description = description
        self._url = url

        super().__init__(**kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def description(self):
        """
        Returns the description of the node.
        :rtype: str
        """
        return self._description.strip()

    @description.setter
    def description(self, value):
        """
        Set the description of the node.
        :type value: str
        """
        self._description = value.strip()

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
    def node(self):
        """
        Tells whether the current element is a node.
        :rtype: bool
        """
        return Item.ConceptNode <= self.item <= Item.PropertyAssertionNode

    @property
    def url(self):
        """
        Returns the url attached to the node.
        :rtype: str
        """
        return self._url.strip()

    @url.setter
    def url(self, value):
        """
        Set the url attached to the node.
        :type value: str
        """
        self._url = value.strip()

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def contextMenu(self, *args, **kwargs):
        """
        Returns the basic node context menu.
        :rtype: QMenu
        """
        pass

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

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :type document: QDomDocument
        :rtype: QDomElement
        """
        pass

    @classmethod
    @abstractmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :type scene: DiagramScene
        :type E: QDomElement
        :rtype: AbstractItem
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


from eddy.core.items.nodes import AttributeNode, ConceptNode, ComplementNode, DatatypeRestrictionNode, DisjointUnionNode
from eddy.core.items.nodes import DomainRestrictionNode, EnumerationNode, IndividualNode, IntersectionNode
from eddy.core.items.nodes import PropertyAssertionNode, RangeRestrictionNode, RoleNode, RoleChainNode
from eddy.core.items.nodes import RoleInverseNode, UnionNode, ValueDomainNode, ValueRestrictionNode
from eddy.core.items.edges import InputEdge, InclusionEdge, InstanceOfEdge


__mapping__ = {
    ConceptNode.xmlname: ConceptNode,
    ValueDomainNode.xmlname: ValueDomainNode,
    RoleNode.xmlname: RoleNode,
    IndividualNode.xmlname: IndividualNode,
    AttributeNode.xmlname: AttributeNode,
    ValueRestrictionNode.xmlname: ValueRestrictionNode,
    DomainRestrictionNode.xmlname: DomainRestrictionNode,
    RangeRestrictionNode.xmlname: RangeRestrictionNode,
    UnionNode.xmlname: UnionNode,
    EnumerationNode.xmlname: EnumerationNode,
    ComplementNode.xmlname: ComplementNode,
    RoleChainNode.xmlname: RoleChainNode,
    IntersectionNode.xmlname: IntersectionNode,
    RoleInverseNode.xmlname: RoleInverseNode,
    DatatypeRestrictionNode.xmlname: DatatypeRestrictionNode,
    DisjointUnionNode.xmlname: DisjointUnionNode,
    PropertyAssertionNode.xmlname: PropertyAssertionNode,
    InclusionEdge.xmlname: InclusionEdge,
    InputEdge.xmlname: InputEdge,
    InstanceOfEdge.xmlname: InstanceOfEdge,
}