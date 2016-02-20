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


from PyQt5.QtCore import QObject, pyqtSignal

from eddy.core.datatypes import Item
from eddy.core.functions import isEmpty


class PredicateMetaIndex(QObject):
    """
    This class is used to index predicate metadata.
    """
    added = pyqtSignal(Item, str)
    removed = pyqtSignal(Item, str)
    cleared = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize the metadata index.
        :type parent: QObject
        """
        super().__init__(parent)
        self.index = {}
        self.metaFactory = MetaFactory(self)

    def add(self, item, predicate, metadata):
        """
        Insert predicate metadata in the index.
        :type item: Item
        :type predicate: str
        :type metadata: PredicateMetaData
        """
        if item not in self.index:
            self.index[item] = {}
        self.index[item][predicate] = metadata
        self.added.emit(item, predicate)

    def clear(self):
        """
        Clear the metadata index.
        """
        self.index.clear()
        self.cleared.emit()

    def entries(self):
        """
        Returns a list of pairs 'item', 'predicate' for all the elements in the index.
        :rtype: generator
        """
        return ((k1, k2) for k1 in self.index.keys() for k2 in self.index[k1].keys())

    def metaFor(self, item, predicate):
        """
        Returns predicate metadata.
        :type item: Item
        :type predicate: str
        :rtype: PredicateMetaData
        """
        try:
            return self.index[item][predicate]
        except KeyError:
            return self.metaFactory.create(item, predicate)

    def remove(self, item, predicate):
        """
        Remove predicate metadata from the index.
        :type item: Item
        :type predicate: str
        """
        if item in self.index:
            self.index[item].pop(predicate, None)
            if not self.index[item]:
                del self.index[item]
        self.removed.emit(item, predicate)


########################################################################################################################
#                                                                                                                      #
#   FACTORY IMPLEMENTATION                                                                                             #
#                                                                                                                      #
########################################################################################################################


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


########################################################################################################################
#                                                                                                                      #
#   PREDICATE METADATA CONTAINERS                                                                                      #
#                                                                                                                      #
########################################################################################################################


class PredicateMetaData(QObject):
    """
    This class implements the basic predicate node metadata container.
    """
    def __init__(self, item, predicate, parent=None):
        """
        Initialize the metadata container.
        :type item: Item
        :type predicate: str
        :type parent: QObject
        """
        super().__init__(parent)
        self._item = item
        self._predicate = predicate
        self._description = ''
        self._url = ''

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = PredicateMetaData(self.item, self.predicate)
        meta.description = self.description
        meta.url = self.url
        return meta

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################
    
    @property
    def item(self):
        """
        Returns the item type of the predicate.
        :rtype: Item
        """
        return self._item
    
    @property
    def description(self):
        """
        Returns the description of the predicate.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """
        Set the description of the predicate.
        :type description: str
        """
        self._description = description.strip()

    @property
    def predicate(self):
        """
        Returns the predicate identifier.
        :rtype: str
        """
        return self._predicate

    @predicate.setter
    def predicate(self, predicate):
        """
        Set the identifier of the predicate.
        :type predicate: str
        """
        self._predicate = predicate.strip()

    @property
    def url(self):
        """
        Returns the URL of the predicate.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        """
        Set the URL of the predicate.
        :type url: str
        """
        self._url = url.strip()

    ####################################################################################################################
    #                                                                                                                  #
    #   MAGIC METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

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
    def __init__(self, item, predicate, parent=None):
        """
        Initialize the attribute metadata container.
        :type item: Item
        :type predicate: str
        :type parent: QObject
        """
        super().__init__(item, predicate, parent)
        self.functionality = False

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = AttributeMetaData(self.item, self.predicate)
        meta.description = self.description
        meta.url = self.url
        meta.functionality = self.functionality
        return meta

    ####################################################################################################################
    #                                                                                                                  #
    #   MAGIC METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

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
                   self.functionality == other.functionality
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
                   self.functionality != other.functionality
        return True


class RoleMetaData(PredicateMetaData):
    """
    This class implements the role predicate node metadata container.
    """
    def __init__(self, item, predicate, parent=None):
        """
        Initialize the role metadata container.
        :type item: Item
        :type predicate: str
        :type parent: QObject
        """
        super().__init__(item, predicate, parent)
        self.asymmetry = False
        self.functionality = False
        self.inverseFunctionality = False
        self.irreflexivity = False
        self.reflexivity = False
        self.symmetry = False
        self.transitivity = False

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self):
        """
        Returns a copy of this predicate metadata.
        """
        meta = RoleMetaData(self.item, self.predicate)
        meta.description = self.description
        meta.url = self.url
        meta.asymmetry = self.asymmetry
        meta.functionality = self.functionality
        meta.inverseFunctionality = self.inverseFunctionality
        meta.irreflexivity = self.irreflexivity
        meta.reflexivity = self.reflexivity
        meta.symmetry = self.symmetry
        meta.transitivity = self.transitivity
        return meta

    ####################################################################################################################
    #                                                                                                                  #
    #   MAGIC METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

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
                   self.asymmetry == other.asymmetry and \
                   self.functionality == other.functionality and \
                   self.inverseFunctionality == other.inverseFunctionality and \
                   self.irreflexivity == other.irreflexivity and \
                   self.reflexivity == other.reflexivity and \
                   self.symmetry == other.symmetry and \
                   self.transitivity == other.transitivity
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
                   self.asymmetry != other.asymmetry or \
                   self.functionality != other.functionality or \
                   self.inverseFunctionality != other.inverseFunctionality or \
                   self.irreflexivity != other.irreflexivity or \
                   self.reflexivity != other.reflexivity or \
                   self.symmetry != other.symmetry or \
                   self.transitivity != other.transitivity
        return True