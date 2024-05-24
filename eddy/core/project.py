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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

from __future__ import annotations

from typing import (
    cast,
    Any,
    Optional,
    Set,
    TYPE_CHECKING,
)

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from eddy.core.datatypes.graphol import Item
from eddy.core.diagram import Diagram
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.items.common import AbstractItem
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.nodes.attribute import AttributeNode
from eddy.core.items.nodes.common.base import (
    AbstractNode,
    PredicateNodeMixin,
)
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.individual import IndividualNode
from eddy.core.items.nodes.role import RoleNode
from eddy.core.items.nodes.value_domain import ValueDomainNode
from eddy.core.output import getLogger
# noinspection PyUnresolvedReferences
# FIXME: Many modules still expect K_ constants to be defined in project,
#        identify such modules and make them import from owl module.
from eddy.core.owl import (
    IRIManager,
    IRI,
    K_ASYMMETRIC,
    K_DEPRECATED,
    K_INVERSE_FUNCTIONAL,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
    K_FUNCTIONAL,
)
from eddy.core.profiles.owl2 import OWL2Profile

if TYPE_CHECKING:
    from eddy.ui.session import Session

#############################################
#   GLOBALS
#################################

LOGGER = getLogger()


# PROJECT INDEX
K_DESCRIPTION = 'description'
K_DIAGRAM = 'diagrams'
K_EDGE = 'edges'
K_ITEMS = 'items'
K_NODE = 'nodes'
K_TYPE = 'types'

#TODO ADDED
K_OCCURRENCES = 'occurrences'
K_CLASS_OCCURRENCES = 'class_occurrences'
K_DATATYPE_OCCURRENCES = 'datatype_occurrences'
K_OBJ_PROP_OCCURRENCES = 'obj_prop_occurrences'
K_DATA_PROP_OCCURRENCES = 'data_prop_occurrences'
K_INDIVIDUAL_OCCURRENCES = 'individual_occurrences'

K_IRI_CLASS = 'IRI_CLASS'
K_IRI_OBJ_PROP = 'IRI_OBJ_PROP'
K_IRI_DATA_PROP = 'IRI_DATA_PROP'
K_IRI_INDIVIDUAL = 'IRI_INDIVIDUAL'
K_IRI_DATATYPE = "IRI_DATATYPE"
#TODO END ADDED

# PROJECT MERGE
K_CURRENT = 'current'
K_FINAL = 'final'
K_IMPORTING = 'importing'
K_REDO = 'redo'
K_UNDO = 'undo'
K_ITEM = 'item'
K_NAME = 'name'
K_PROPERTY = 'property'


class Project(IRIManager):
    """
    Extension of QtCore.QObject which implements a Graphol project.
    Additionally to built-in signals, this class emits:

    * sgnDiagramAdded: whenever a Diagram is added to the Project.
    * sgnDiagramRemoved: whenever a Diagram is removed from the Project.
    * sgnItemAdded: whenever an item is added to the Project.
    * sgnItemRemoved: whenever an item is removed from the Project.
    * sgnMetaAdded: whenever predicate metadata are added to the Project.
    * sgnMetaRemoved: whenever predicate metadata are removed from the Project.
    * sgnUpdated: whenever the Project is updated in any of its parts.
    """
    sgnDiagramAdded = QtCore.pyqtSignal(QtWidgets.QGraphicsScene)
    sgnDiagramRemoved = QtCore.pyqtSignal(QtWidgets.QGraphicsScene)
    sgnItemAdded = QtCore.pyqtSignal(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    sgnItemRemoved = QtCore.pyqtSignal(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    sgnUpdated = QtCore.pyqtSignal()

    sgnIRIRemovedFromAllDiagrams = QtCore.pyqtSignal(IRI)
    sgnSingleNodeSwitchIRI = QtCore.pyqtSignal(QtWidgets.QGraphicsItem,IRI)
    sgnIRIChanged = QtCore.pyqtSignal(QtWidgets.QGraphicsItem, IRI)
    sgnIRIRefactor = QtCore.pyqtSignal(IRI, IRI)

    def __init__(
        self,
        name: str = None,
        path: str = None,
        profile: OWL2Profile = None,
        version: str = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the graphol project.
        """
        super().__init__(**kwargs)
        self.index = ProjectIRIIndex(self)
        self.name = name
        self.path = expandPath(path) if path else None
        self.profile = profile
        self.profile.setParent(self)
        self.version = version if version is not None else '1.0'

        # FIXME: delete once all references have been dropped
        self.IRI_prefixes_nodes_dict = kwargs.get('IRI_prefixes_nodes_dict')

        connect(self.sgnIRIRemovedFromAllDiagrams,self.onIRIRemovedFromAllDiagrams)
        connect(self.sgnIRIChanged, self.doSingleSwitchIRI)
        connect(self.sgnIRIRefactor, self.doSwitchIRI)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self) -> Session:
        """
        Returns the reference to the project session.
        """
        return cast('Session', self.parent())

    #############################################
    #   INTERFACE
    #################################

    def addDiagram(self, diagram: Diagram) -> None:
        """
        Add the given diagram to the Project, together with all its items.
        """
        if self.index.addDiagram(diagram):
            diagram.setParent(self)
            self.sgnDiagramAdded.emit(diagram)
            for item in diagram.items():
                if item.isNode() or item.isEdge():
                    diagram.sgnItemAdded.emit(diagram, item)
            self.sgnUpdated.emit()

    def diagram(self, did: str) -> Optional[Diagram]:
        """
        Returns the diagram matching the given id or None if no diagram is found.
        """
        return self.index.diagram(did)

    def diagrams(self) -> Set[Diagram]:
        """
        Returns a collection with all the diagrams in this Project.
        """
        return self.index.diagrams()

    def edge(self, diagram: Diagram, eid: str) -> Optional[AbstractEdge]:
        """
        Returns the edge matching the given id or None if no edge is found.
        """
        return self.index.edge(diagram, eid)

    def edges(self, diagram: Diagram = None) -> Set[AbstractEdge]:
        """
        Returns a collection with all the edges in the given diagram.
        If no diagram is supplied a collection with all the edges in the Project will be returned.
        """
        return self.index.edges(diagram)

    def isEmpty(self) -> bool:
        """
        Returns True if the Project contains no element, False otherwise.
        """
        return self.index.isEmpty()

    def item(self, diagram: Diagram, iid: str) -> Optional[AbstractItem]:
        """
        Returns the item matching the given id or None if no item is found.
        """
        return self.index.item(diagram, iid)

    def itemNum(self, item: Item, diagram: Diagram = None) -> int:
        """
        Returns the number of items of the given type which belongs to the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project.
        """
        return self.index.itemNum(item, diagram)

    def items(self, diagram: Diagram = None) -> Set[AbstractItem]:
        """
        Returns a collection with all the items in the given diagram.
        If no diagram is supplied a collection with all the items in the Project will be returned.
        """
        return self.index.items(diagram)

    def node(self, diagram: Diagram, nid: str) -> Optional[AbstractNode]:
        """
        Returns the node matching the given id or None if no node is found.
        """
        return self.index.node(diagram, nid)

    def nodes(self, diagram: Diagram = None) -> Set[AbstractNode]:
        """
        Returns a collection with all the nodes in the given diagram.
        If no diagram is supplied a collection with all the nodes in the Project will be returned.
        """
        return self.index.nodes(diagram)

    '''
    def predicateNum(self, item, diagram=None):
        """
        Returns the number of predicates of the given type which are defined in the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project.
        :type item: Item
        :type diagram: Diagram
        :rtype: int
        """
        return self.index.predicateNum(item, diagram)
    '''

    def iriOccurrences(
        self,
        item: Item = None,
        iri: IRI = None,
        diagram: Diagram = None,
    ) -> Set[AbstractNode]:
        """
        Returns a collection of nodes identified by the given IRI belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        """
        return self.index.iriOccurrences(item, iri, diagram)

    def existIriOccurrence(
        self,
        iri: IRI,
        item: Item = None,
        diagram: Diagram = None,
    ) -> bool:
        """
        Returns True if there exists a node of type k_metatype identified by the given IRI
        belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        If no type is supplied the lookup is performed across all the nodes.
        """
        return self.index.existIriOccurrence(iri, item, diagram)

    def removeDiagram(self, diagram: Diagram) -> None:
        """
        Remove the given diagram from the project index, together with all its items.
        """
        if self.index.removeDiagram(diagram):
            for item in self.items(diagram):
                diagram.sgnItemRemoved.emit(diagram, item)
            self.sgnDiagramRemoved.emit(diagram)
            self.sgnUpdated.emit()

    #############################################
    #   IRI
    #################################

    def isDLCompliant(self) -> bool:
        return self.index.isDLCompliant()

    def itemIRIs(self,item, diagram=None) -> Set[IRI]:
        return self.index.itemIRIs(item, diagram)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def doAddItem(self, diagram: Diagram, item: AbstractItem) -> None:
        """
        Executed whenever an item is added to a diagram belonging to this Project.
        """
        if self.index.addItem(diagram, item):
            if isinstance(item, PredicateNodeMixin):
                self.addIRI(item.iri)
                self.index.addIRIOccurenceToDiagram(diagram, item)
            self.sgnItemAdded.emit(diagram, item)
            self.sgnUpdated.emit()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def doRemoveItem(self, diagram: Diagram, item: AbstractItem) -> None:
        """
        Executed whenever an item is removed from a diagram belonging to this project.
        This slot will remove the given element from the project index.
        """
        if self.index.removeItem(diagram, item):
            if isinstance(item, PredicateNodeMixin):
                if self.index.removeIRIOccurenceFromDiagram(diagram, item):
                    self.sgnIRIRemovedFromAllDiagrams.emit(item.iri)
            self.sgnItemRemoved.emit(diagram, item)
            self.sgnUpdated.emit()

    @QtCore.pyqtSlot(IRI, IRI)
    def doSwitchIRI(self, sub: IRI, master: IRI) -> None:
        """
        Executed whenever the IRI sub must be replaced by the IRI master
        """
        self.index.switchIRI(sub,master)
        self.sgnIRIRemovedFromAllDiagrams.emit(sub)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem, IRI)
    def doSingleSwitchIRI(self, node: QtWidgets.QGraphicsItem, oldIri: IRI) -> None:
        """
        Executed whenever the iri associated to node change
        """
        if self.index.switchIRIForNode(node, oldIri):
            self.sgnIRIRemovedFromAllDiagrams.emit(oldIri)
        else:
            self.sgnSingleNodeSwitchIRI.emit(node, oldIri)


class ProjectIndex(dict):
    """
    Extends built-in dict and implements the Project index.
    """
    def __init__(self, project):
        """
        Initialize the Project Index.
        :type project: Project
        """
        super().__init__(self)
        self[K_DIAGRAM] = dict()
        self[K_EDGE] = dict()
        self[K_ITEMS] = dict()
        self[K_NODE] = dict()
        self[K_TYPE] = dict()
        self.project = project

    def addDiagram(self, diagram):
        """
        Add the given diagram to the Project index.
        :type diagram: Diagram
        :rtype: bool
        """
        if diagram.name not in self[K_DIAGRAM]:
            self[K_DIAGRAM][diagram.name] = diagram
            return True
        return False

    def removeDiagram(self, diagram):
        """
        Remove the given diagram from the Project index.
        :type diagram: Diagram
        :rtype: bool
        """
        if diagram.name in self[K_DIAGRAM]:
            del self[K_DIAGRAM][diagram.name]
            return True
        return False

    def diagram(self, did):
        """
        Retrieves a diagram given its id.
        :type did: str
        :rtype: Diagram
        """
        try:
            return self[K_DIAGRAM][did]
        except KeyError:
            return None

    def diagrams(self):
        """
        Returns a collection with all the diagrams in this Project Index.
        :rtype: set
        """
        return set(self[K_DIAGRAM].values())

    def addItem(self, diagram, item):
        """
        Add the given item to the Project index.
        :type diagram: Diagram
        :type item: AbstractItem
        :rtype: bool
        """
        i = item.type()
        if diagram.name not in self[K_ITEMS]:
            self[K_ITEMS][diagram.name] = dict()
        if item.id not in self[K_ITEMS][diagram.name]:
            self[K_ITEMS][diagram.name][item.id] = item
            if diagram.name not in self[K_TYPE]:
                self[K_TYPE][diagram.name] = dict()
            if i not in self[K_TYPE][diagram.name]:
                self[K_TYPE][diagram.name][i] = set()
            self[K_TYPE][diagram.name][i] |= {item}
            if item.isNode():
                if diagram.name not in self[K_NODE]:
                    self[K_NODE][diagram.name] = dict()
                self[K_NODE][diagram.name][item.id] = item
            if item.isEdge():
                if diagram.name not in self[K_EDGE]:
                    self[K_EDGE][diagram.name] = dict()
                self[K_EDGE][diagram.name][item.id] = item
            return True
        return False

    def edge(self, diagram, eid):
        """
        Retrieves an edge given it's id and the diagram the edge belongs to.
        :type diagram: Diagram
        :type eid: str
        :rtype: AbstractEdge
        """
        try:
            return self[K_EDGE][diagram.name][eid]
        except KeyError:
            return None

    def edges(self, diagram=None):
        """
        Returns a collection with all the edges in the given diagram.
        If no diagram is supplied a collection with all the edges in the Project Index will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self[K_EDGE][i].values()) for i in self[K_EDGE]))
            return set(self[K_EDGE][diagram.name].values())
        except (KeyError, TypeError):
            return set()

    def isEmpty(self):
        """
        Returns True if the Project Index contains no element, False otherwise.
        :rtype: bool
        """
        for i in self[K_ITEMS]:
            for _ in self[K_ITEMS][i]:
                return False
        return True

    def item(self, diagram, iid):
        """
        Retrieves an item given it's id and the diagram the edge belongs to.
        :type diagram: Diagram
        :type iid: str
        :rtype: AbstractItem
        """
        try:
            return self[K_ITEMS][diagram.name][iid]
        except KeyError:
            return None

    def itemNum(self, item, diagram=None):
        """
        Count the number of items of the given type which belongs to the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project.
        :type item: Item
        :type diagram: Diagram
        :rtype: int
        """
        try:
            subdict = self[K_TYPE]
            if not diagram:
                return len(set.union(*(subdict[i][item] for i in subdict if item in subdict[i])))
            return len(subdict[diagram.name][item])
        except (KeyError, TypeError):
            return 0

    def items(self, diagram=None):
        """
        Returns a collection with all the items in the given diagram.
        If no diagram is supplied a collection with all the items in the Project Index will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self[K_ITEMS][i].values()) for i in self[K_ITEMS]))
            return set(self[K_ITEMS][diagram.name].values())
        except (KeyError, TypeError):
            return set()

    def node(self, diagram, nid):
        """
        Retrieves the node matching the given id or None if no node is found.
        :type diagram: Diagram
        :type nid: str
        :rtype: AbstractNode
        """
        try:
            return self[K_EDGE][diagram.name][nid]
        except KeyError:
            return None

    def nodes(self, diagram=None):
        """
        Returns a collection with all the nodes in the given diagram.
        If no diagram is supplied a collection with all the nodes in the Project Index will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self[K_NODE][i].values()) for i in self[K_NODE]))
            return set(self[K_NODE][diagram.name].values())
        except (KeyError, TypeError):
            return set()

    def removeItem(self, diagram, item):
        """
        Remove the given item from the Project index.
        :type diagram: Diagram
        :type item: AbstractItem
        :rtype: bool
        """
        i = item.type()
        if diagram.name in self[K_ITEMS]:
            if item.id in self[K_ITEMS][diagram.name]:
                del self[K_ITEMS][diagram.name][item.id]
                if not self[K_ITEMS][diagram.name]:
                    del self[K_ITEMS][diagram.name]
            if diagram.name in self[K_TYPE]:
                if i in self[K_TYPE][diagram.name]:
                    self[K_TYPE][diagram.name][i] -= {item}
                    if not self[K_TYPE][diagram.name][i]:
                        del self[K_TYPE][diagram.name][i]
                        if not self[K_TYPE][diagram.name]:
                            del self[K_TYPE][diagram.name]
            if item.isNode():
                if diagram.name in self[K_NODE]:
                    if item.id in self[K_NODE][diagram.name]:
                        del self[K_NODE][diagram.name][item.id]
                        if not self[K_NODE][diagram.name]:
                            del self[K_NODE][diagram.name]
            if item.isEdge():
                if diagram.name in self[K_EDGE]:
                    if item.id in self[K_EDGE][diagram.name]:
                        del self[K_EDGE][diagram.name][item.id]
                        if not self[K_EDGE][diagram.name]:
                            del self[K_EDGE][diagram.name]
            return True
        return False


class ProjectIRIIndex(ProjectIndex):
    """
    Extends ProjectIndex to manage Project IRI index.
    """
    def __init__(self, project):
        """
        Initialize the Project Index.
        """
        super().__init__(project)
        self[K_OCCURRENCES] = dict()
        self[K_CLASS_OCCURRENCES] = dict()
        self[K_DATATYPE_OCCURRENCES] = dict()
        self[K_OBJ_PROP_OCCURRENCES] = dict()
        self[K_DATA_PROP_OCCURRENCES] = dict()
        self[K_INDIVIDUAL_OCCURRENCES] = dict()

        self[K_IRI_CLASS] = dict()
        self[K_IRI_OBJ_PROP] = dict()
        self[K_IRI_DATA_PROP] = dict()
        self[K_IRI_DATATYPE] = dict()
        self[K_IRI_INDIVIDUAL] = dict()

    def switchIRIForNode(self,node,oldIRI):
        """
        Make all occurrences of sub become occurrences of master
        :type oldIRI: IRI
        :type node: PredicateNodeMixin
        """

        if isinstance(node, ConceptNode):
            if node in self[K_CLASS_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_CLASS_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
                if not self[K_CLASS_OCCURRENCES][oldIRI][node.diagram.name]:
                    self[K_CLASS_OCCURRENCES][oldIRI].pop(node.diagram.name)
                    if oldIRI in self[K_IRI_CLASS][node.diagram.name]:
                        self[K_IRI_CLASS][node.diagram.name].remove(oldIRI)
                    if not self[K_CLASS_OCCURRENCES][oldIRI]:
                        self[K_CLASS_OCCURRENCES].pop(oldIRI)

        if isinstance(node, IndividualNode):
            if node in self[K_INDIVIDUAL_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_INDIVIDUAL_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
                if not self[K_INDIVIDUAL_OCCURRENCES][oldIRI][node.diagram.name]:
                    self[K_INDIVIDUAL_OCCURRENCES][oldIRI].pop(node.diagram.name)
                    if oldIRI in self[K_IRI_INDIVIDUAL][node.diagram.name]:
                        self[K_IRI_INDIVIDUAL][node.diagram.name].remove(oldIRI)
                    if not self[K_INDIVIDUAL_OCCURRENCES][oldIRI]:
                        self[K_INDIVIDUAL_OCCURRENCES].pop(oldIRI)

        if isinstance(node, AttributeNode):
            if node in self[K_DATA_PROP_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_DATA_PROP_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
                if not self[K_DATA_PROP_OCCURRENCES][oldIRI][node.diagram.name]:
                    self[K_DATA_PROP_OCCURRENCES][oldIRI].pop(node.diagram.name)
                    if oldIRI in self[K_IRI_DATA_PROP][node.diagram.name]:
                        self[K_IRI_DATA_PROP][node.diagram.name].remove(oldIRI)
                    if not self[K_DATA_PROP_OCCURRENCES][oldIRI]:
                        self[K_DATA_PROP_OCCURRENCES].pop(oldIRI)

        if isinstance(node, RoleNode):
            if node in self[K_OBJ_PROP_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_OBJ_PROP_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
                if not self[K_OBJ_PROP_OCCURRENCES][oldIRI][node.diagram.name]:
                    self[K_OBJ_PROP_OCCURRENCES][oldIRI].pop(node.diagram.name)
                    if oldIRI in self[K_IRI_OBJ_PROP][node.diagram.name]:
                        self[K_IRI_OBJ_PROP][node.diagram.name].remove(oldIRI)
                    if not self[K_OBJ_PROP_OCCURRENCES][oldIRI]:
                        self[K_OBJ_PROP_OCCURRENCES].pop(oldIRI)

        if isinstance(node, ValueDomainNode):
            if node in self[K_DATATYPE_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_DATATYPE_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
                if not self[K_DATATYPE_OCCURRENCES][oldIRI][node.diagram.name]:
                    self[K_DATATYPE_OCCURRENCES][oldIRI].pop(node.diagram.name)
                    if oldIRI in self[K_IRI_DATATYPE][node.diagram.name]:
                        self[K_IRI_DATATYPE][node.diagram.name].remove(oldIRI)
                    if not self[K_DATATYPE_OCCURRENCES][oldIRI]:
                        self[K_DATATYPE_OCCURRENCES].pop(oldIRI)

        self.addIRIOccurenceToDiagram(node.diagram, node)
        if node in self[K_OCCURRENCES][oldIRI][node.diagram.name]:
            self[K_OCCURRENCES][oldIRI][node.diagram.name].remove(node)
            if not self[K_OCCURRENCES][oldIRI][node.diagram.name]:
                self[K_OCCURRENCES][oldIRI].pop(node.diagram.name)
                if not self[K_OCCURRENCES][oldIRI]:
                    self[K_OCCURRENCES].pop(oldIRI)
                    return True
        return False

    def switchIRI(self,sub,master):
        """
        Make all occurrences of sub become occurrences of master
        :type sub: IRI
        :type master: IRI
        """
        if sub in self[K_OCCURRENCES]:
            diagramKeyList = [key for key in self[K_OCCURRENCES][sub]]
            for diagName in diagramKeyList:
                for node in self[K_OCCURRENCES][sub][diagName]:
                    node.iri = master
                    self.addIRIOccurenceToDiagram(node.diagram,node)
                self[K_OCCURRENCES][sub][diagName] = None
                del self[K_OCCURRENCES][sub][diagName]
            del self[K_OCCURRENCES][sub]
        self.removeAllOccurrencesOfType(sub, K_CLASS_OCCURRENCES, K_IRI_CLASS)
        self.removeAllOccurrencesOfType(sub, K_DATATYPE_OCCURRENCES, K_IRI_DATATYPE)
        self.removeAllOccurrencesOfType(sub, K_OBJ_PROP_OCCURRENCES, K_IRI_OBJ_PROP)
        self.removeAllOccurrencesOfType(sub, K_DATA_PROP_OCCURRENCES, K_IRI_DATA_PROP)
        self.removeAllOccurrencesOfType(sub, K_INDIVIDUAL_OCCURRENCES, K_IRI_INDIVIDUAL)

    def removeAllOccurrencesOfType(self,iri,k_metatype, k_iri_metatype):
        if iri in self[k_metatype]:
            diagramKeyList = [key for key in self[k_metatype][iri]]
            for diagName in diagramKeyList:
                self[k_metatype][iri][diagName] = None
                del self[k_metatype][iri][diagName]
            del self[k_metatype][iri]

        diagramKeyList = [key for key in self[k_iri_metatype]]
        for diagName in diagramKeyList:
            if iri in self[k_iri_metatype][diagName]:
                self[k_iri_metatype][diagName].remove(iri)

    def addIRIOccurenceToDiagram(self, diagram, node):
        """
        Set node as occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: PredicateNodeMixin
        """
        iri = node.iri
        if iri in self[K_OCCURRENCES]:
            if diagram.name in self[K_OCCURRENCES][iri]:
                self[K_OCCURRENCES][iri][diagram.name].add(node)
            else:
                currSet = set()
                currSet.add(node)
                self[K_OCCURRENCES][iri][diagram.name] = currSet
        else:
            currDict = {}
            currSet = set()
            currSet.add(node)
            currDict[diagram.name] = currSet
            self[K_OCCURRENCES][iri] = currDict

        '''
        if diagram.name in self[K_NODE]:
            self[K_NODE][diagram.name].add(node)
        else:
            currSet = set()
            currSet.add(node)
            self[K_NODE][diagram.name] = currSet
        '''

        k_metatype = ''
        k_iri_metatype = ''
        if isinstance(node, ConceptNode):
            k_metatype = K_CLASS_OCCURRENCES
            k_iri_metatype = K_IRI_CLASS
        elif isinstance(node, RoleNode):
            k_metatype = K_OBJ_PROP_OCCURRENCES
            k_iri_metatype = K_IRI_OBJ_PROP
        elif isinstance(node, AttributeNode):
            k_metatype = K_DATA_PROP_OCCURRENCES
            k_iri_metatype = K_IRI_DATA_PROP
        elif isinstance(node, ValueDomainNode):
            k_metatype = K_DATATYPE_OCCURRENCES
            k_iri_metatype = K_IRI_DATATYPE
        elif isinstance(node, IndividualNode):
            k_metatype = K_INDIVIDUAL_OCCURRENCES
            k_iri_metatype = K_IRI_INDIVIDUAL
        self.addTypedIRIOccurrenceToDiagram(diagram,node,k_metatype,k_iri_metatype)

    def addTypedIRIOccurrenceToDiagram(self, diagram, node, k_metatype, k_iri_metatype):
        """
        Set node as typed occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: PredicateNodeMixin
        :type k_metatype: str
        """
        iri = node.iri
        if iri in self[k_metatype]:
            if diagram.name in self[k_metatype][iri]:
                self[k_metatype][iri][diagram.name].add(node)
            else:
                currSet = set()
                currSet.add(node)
                self[k_metatype][iri][diagram.name] = currSet
        else:
            currDict = {}
            currSet = set()
            currSet.add(node)
            currDict[diagram.name] = currSet
            self[k_metatype][iri] = currDict

        if diagram.name in self[k_iri_metatype]:
            self[k_iri_metatype][diagram.name].add(iri)
        else:
            currSet = set()
            currSet.add(iri)
            self[k_iri_metatype][diagram.name]=currSet

    def removeIRIOccurenceFromDiagram(self, diagram, node):
        """
        Remove node as occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: PredicateNodeMixin
        """
        '''
        if diagram.name in self[K_NODE]:
            if node in self[K_NODE][diagram.name]:
                self[K_NODE][diagram.name].remove(node)
        '''

        iri = node.iri
        k_metatype = ''
        k_iri_metatype = ''
        if isinstance(node, ConceptNode):
            k_metatype = K_CLASS_OCCURRENCES
            k_iri_metatype = K_IRI_CLASS
        elif isinstance(node, RoleNode):
            k_metatype = K_OBJ_PROP_OCCURRENCES
            k_iri_metatype = K_IRI_OBJ_PROP
        elif isinstance(node, AttributeNode):
            k_metatype = K_DATA_PROP_OCCURRENCES
            k_iri_metatype = K_IRI_DATA_PROP
        elif isinstance(node, ValueDomainNode):
            k_metatype = K_DATATYPE_OCCURRENCES
            k_iri_metatype = K_IRI_DATATYPE
        elif isinstance(node, IndividualNode):
            k_metatype = K_INDIVIDUAL_OCCURRENCES
            k_iri_metatype = K_IRI_INDIVIDUAL
        self.removeTypedIRIOccurenceFromDiagram(diagram, node, k_metatype, k_iri_metatype)

        if iri in self[K_OCCURRENCES]:
            if diagram.name in self[K_OCCURRENCES][iri]:
                self[K_OCCURRENCES][iri][diagram.name].remove(node)
                if not self[K_OCCURRENCES][iri][diagram.name]:
                    self[K_OCCURRENCES][iri].pop(diagram.name)
                    if not self[K_OCCURRENCES][iri]:
                        self[K_OCCURRENCES].pop(iri)
                        return True
        return False

    def removeTypedIRIOccurenceFromDiagram(self, diagram, node, k_metatype, k_iri_metatype):
        """
        Remove node as typed occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: PredicateNodeMixin
        :type k_metatype: str
        """
        iri = node.iri
        if iri in self[k_metatype]:
            if diagram.name in self[k_metatype][iri]:
                self[k_metatype][iri][diagram.name].remove(node)
                if not self[k_metatype][iri][diagram.name]:
                    self[k_metatype][iri].pop(diagram.name)
                    if node.iri in self[k_iri_metatype][diagram.name]:
                        self[k_iri_metatype][diagram.name].remove(node.iri)
                    if not self[k_metatype][iri]:
                        self[k_metatype].pop(iri)
                        return True
        return False


    def itemIRIs(self,item, diagram=None):
        """
        Returns the set of IRIs occurring as item in the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        :type diagram: Diagram
        :item: Item
        :rtype: set
        """
        try:
            k_metatype = None
            if item is Item.ConceptNode:
                k_metatype = K_IRI_CLASS
            elif item is Item.RoleNode:
                k_metatype = K_IRI_OBJ_PROP
            elif item is Item.AttributeNode:
                k_metatype = K_IRI_DATA_PROP
            elif item is Item.IndividualNode:
                k_metatype = K_IRI_INDIVIDUAL
            elif item is Item.ValueDomainNode:
                k_metatype = K_IRI_DATATYPE
            if not diagram:
                result = set()
                for diag,diagSet in self[k_metatype].items():
                    result = result|diagSet
                return result
            else:
                return self[k_metatype][diagram.name]
        except (KeyError, TypeError):
            return set()

    def iriOccurrences(self,item=None, iri=None,diagram=None):
        """
        Returns a collection of nodes of type k_metatype identified by the given IRI belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        If no type is supplied the lookup is performed across all the nodes.
        If no iri is supplied the lookup is performed across all the alphabet of the ontology
        :type iri: IRI
        :type diagram: Diagram
        :item: Item
        :rtype: set
        """
        try:
            k_metatype = None
            if item:
                if item is Item.ConceptNode:
                    k_metatype = K_CLASS_OCCURRENCES
                elif item is Item.RoleNode:
                    k_metatype = K_OBJ_PROP_OCCURRENCES
                elif item is Item.AttributeNode:
                    k_metatype = K_DATA_PROP_OCCURRENCES
                elif item is Item.IndividualNode:
                    k_metatype = K_INDIVIDUAL_OCCURRENCES
            if not k_metatype:
                k_metatype = K_OCCURRENCES
            result = set()
            if not iri:
                if not diagram:
                    for occIRI in self[k_metatype]:
                        for diag in self[k_metatype][occIRI]:
                            result.update(self[k_metatype][occIRI][diag])
                else:
                    for occIRI in self[k_metatype]:
                        if diagram.name in self[k_metatype][occIRI]:
                            result.update(self[k_metatype][occIRI][diagram.name])
            else:
                if not diagram:
                    if iri in self[k_metatype]:
                        for diag in self[k_metatype][iri]:
                            result.update(self[k_metatype][iri][diag])
                else:
                    if iri in self[k_metatype]:
                        if diagram.name in self[k_metatype][iri]:
                            result.update(self[k_metatype][iri][diagram.name])
            return result
        except KeyError:
            return set()

    def existIriOccurrence(self, iri, item=None, diagram=None):
        """
        Returns True if exist a node of type k_metatype identified by the given IRI belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        If no type is supplied the lookup is performed across all the nodes.
        :type iri: IRI
        :type diagram: Diagram
        :item: Item
        :rtype: bool
        """
        try:
            k_metatype = None
            if item:
                if item is Item.ConceptNode:
                    k_metatype = K_CLASS_OCCURRENCES
                elif item is Item.RoleNode:
                    k_metatype = K_OBJ_PROP_OCCURRENCES
                elif item is Item.AttributeNode:
                    k_metatype = K_DATA_PROP_OCCURRENCES
                elif item is Item.IndividualNode:
                    k_metatype = K_INDIVIDUAL_OCCURRENCES
            if not k_metatype:
                k_metatype = K_OCCURRENCES
            if not diagram:
                if iri in self[k_metatype]:
                    if self[k_metatype][iri]:
                        return True
            else:
                if iri in self[k_metatype]:
                    if diagram.name in self[k_metatype][iri]:
                        return True
            return False
        except KeyError:
            return False

    def isDLCompliant(self):
        objPropNodes = self.iriOccurrences(item=Item.RoleNode)
        dataPropNodes = self.iriOccurrences(item=Item.AttributeNode)
        for objPropNode in objPropNodes:
            objPropIri = objPropNode.iri
            if not (objPropIri.isTopObjectProperty or objPropIri.isBottomObjectProperty) and self.project.isFromReservedVocabulary(objPropIri):
                return False
            for dataPropNode in dataPropNodes:
                dataPropIri = dataPropNode.iri
                if not (dataPropIri.isTopDataProperty or dataPropIri.isBottomDataProperty) and self.project.isFromReservedVocabulary(dataPropIri):
                    return False
                if dataPropIri==objPropIri:
                    return False

        classNodes = self.iriOccurrences(item=Item.ConceptNode)
        datatypeNodes = self.iriOccurrences(item=Item.ValueDomainNode)
        for classNode in classNodes:
            classIri = classNode.iri
            if not (classIri.isOwlThing or classIri.isOwlNothing) and self.project.isFromReservedVocabulary(classIri):
                return False
            for datatypeNode in datatypeNodes:
                if datatypeNode.iri == classIri:
                    return False
        return True


class ProjectNotFoundError(RuntimeError):
    """
    Raised whenever we are not able to find a project given its path.
    """
    pass


class ProjectNotValidError(RuntimeError):
    """
    Raised whenever a found project has an invalid structure.
    """
    pass


class ProjectStopLoadingError(RuntimeError):
    """
    Used to signal that a project loading needs to be interrupted.
    """
    pass


class ProjectStopImportingError(RuntimeError):
    """
    Used to signal that a project import needs to be interrupted.
    """
    pass


class ProjectVersionError(RuntimeError):
    """
    Raised whenever we have a project version mismatch.
    """
    pass
