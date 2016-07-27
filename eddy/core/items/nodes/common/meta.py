# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import isEmpty


class MetaFactory(QObject):
    """
    This class can be used to produce predicate meta data containers.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: QObject
        """
        super().__init__(parent)

    @staticmethod
    def create(item, predicate):
        """
        Build and return a predicate meta data container using to the given parameters.
        :type item: Item
        :type predicate: str
        :rtype: AbstractItem
        """
        if item is Item.RoleNode:
            return RoleMetaData(item, predicate)
        if item is Item.AttributeNode:
            return AttributeMetaData(item, predicate)
        return PredicateMetaData(item, predicate)


class PredicateMetaData(object):
    """
    This class implements the basic predicate node metadata container.
    """
    def __init__(self, item, predicate):
        """
        Initialize the metadata container.
        :type item: Item
        :type predicate: str
        """
        super().__init__()
        self.item = item
        self.predicate = predicate
        self.description = ''
        self.url = ''

    #############################################
    #   INTERFACE
    #################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = PredicateMetaData(self.item, self.predicate)
        meta.description = self.description
        meta.url = self.url
        return meta

    def __bool__(self):
        """
        Boolean operator implementation.
        :rtype: bool
        """
        return not isEmpty(self.description) or not isEmpty(self.url)

    def __eq__(self, other):
        """
        Equality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, PredicateMetaData):
            return self.url == other.url and \
                   self.description == other.description and \
                   self.predicate == other.predicate
        return False

    def __ne__(self, other):
        """
        Inequality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, PredicateMetaData):
            return self.url != other.url or \
                   self.description != other.description or \
                   self.predicate != other.predicate
        return True


class AttributeMetaData(PredicateMetaData):
    """
    This class implements the attribute predicate node metadata container.
    """
    def __init__(self, item, predicate):
        """
        Initialize the attribute metadata container.
        :type item: Item
        :type predicate: str
        """
        super().__init__(item, predicate)
        self.functional = False

    #############################################
    #   INTERFACE
    #################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = AttributeMetaData(self.item, self.predicate)
        meta.description = self.description
        meta.functional = self.functional
        meta.url = self.url
        return meta

    def __bool__(self):
        """
        Boolean operator implementation.
        :rtype: bool
        """
        return True

    def __eq__(self, other):
        """
        Equality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, AttributeMetaData):
            return self.url == other.url and \
                   self.description == other.description and \
                   self.functional == other.functional and \
                   self.predicate == other.predicate
        return False

    def __ne__(self, other):
        """
        Inequality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, AttributeMetaData):
            return self.url != other.url or \
                   self.description != other.description or \
                   self.functional != other.functional or \
                   self.predicate != other.predicate
        return True


class RoleMetaData(PredicateMetaData):
    """
    This class implements the role predicate node metadata container.
    """
    def __init__(self, item, predicate):
        """
        Initialize the role metadata container.
        :type item: Item
        :type predicate: str
        """
        super().__init__(item, predicate)
        self.asymmetric = False
        self.functional = False
        self.inverseFunctional = False
        self.irreflexive = False
        self.reflexive = False
        self.symmetric = False
        self.transitive = False

    #############################################
    #   INTERFACE
    #################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = RoleMetaData(self.item, self.predicate)
        meta.asymmetric = self.asymmetric
        meta.description = self.description
        meta.functional = self.functional
        meta.inverseFunctional = self.inverseFunctional
        meta.irreflexive = self.irreflexive
        meta.reflexive = self.reflexive
        meta.symmetric = self.symmetric
        meta.transitive = self.transitive
        meta.url = self.url
        return meta

    def __bool__(self):
        """
        Boolean operator implementation.
        :rtype: bool
        """
        return True

    def __eq__(self, other):
        """
        Equality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, RoleMetaData):
            return self.url == other.url and \
                   self.description == other.description and \
                   self.predicate == other.predicate and \
                   self.asymmetric == other.asymmetric and \
                   self.functional == other.functional and \
                   self.inverseFunctional == other.inverseFunctional and \
                   self.irreflexive == other.irreflexive and \
                   self.reflexive == other.reflexive and \
                   self.symmetric == other.symmetric and \
                   self.transitive == other.transitive
        return False

    def __ne__(self, other):
        """
        Inequality operator implementation.
        :type other: PredicateMetaData
        :rtype: bool
        """
        if isinstance(other, RoleMetaData):
            return self.url != other.url or \
                   self.description != other.description or \
                   self.predicate != other.predicate or \
                   self.asymmetric != other.asymmetric or \
                   self.functional != other.functional or \
                   self.inverseFunctional != other.inverseFunctional or \
                   self.irreflexive != other.irreflexive or \
                   self.reflexive != other.reflexive or \
                   self.symmetric != other.symmetric or \
                   self.transitive != other.transitive
        return True