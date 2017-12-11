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


from PyQt5 import QtCore,QtGui,QtWidgets

from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.nodes import CommandNodeSetMeta
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.owl import OWLText
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.core.items.common import AbstractItem
from eddy.core.items.nodes.common.base import AbstractNode

from eddy.ui.resolvers import PredicateBooleanConflictResolver
from eddy.ui.resolvers import PredicateDocumentationConflictResolver


LOGGER = getLogger()


# PROJECT INDEX
K_DIAGRAM = 'diagrams'
K_EDGE = 'edges'
K_ITEMS = 'items'
K_META = 'meta'
K_NODE = 'nodes'
K_PREDICATE = 'predicates'
K_TYPE = 'types'

# PROJECT MERGE
K_CURRENT = 'current'
K_FINAL = 'final'
K_IMPORTING = 'importing'
K_REDO = 'redo'
K_UNDO = 'undo'
K_ITEM = 'item'
K_NAME = 'name'
K_PROPERTY = 'property'

# PREDICATES META KEYS
K_DESCRIPTION = 'description'
K_IRI = 'iri'
K_PREFIX = 'prefix'
K_FUNCTIONAL = 'functional'
K_ASYMMETRIC = 'asymmetric'
K_INVERSE_FUNCTIONAL = 'inverseFunctional'
K_IRREFLEXIVE = 'irreflexive'
K_REFLEXIVE = 'reflexive'
K_SYMMETRIC = 'symmetric'
K_TRANSITIVE = 'transitive'


# noinspection PyTypeChecker
class Project(QtCore.QObject):
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
    sgnDiagramAdded = QtCore.pyqtSignal('QGraphicsScene')
    sgnDiagramRemoved = QtCore.pyqtSignal('QGraphicsScene')
    sgnItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnItemRemoved = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnMetaAdded = QtCore.pyqtSignal(Item, str)
    sgnMetaRemoved = QtCore.pyqtSignal(Item, str)
    sgnUpdated = QtCore.pyqtSignal()

    sgnIRIPrefixNodeEntryAdded = QtCore.pyqtSignal(str,str,AbstractNode)
    sgnIRIPrefixNodeEntryRemoved = QtCore.pyqtSignal(str,str,AbstractNode,str)
    sgnIRIPrefixNodeEntryIgnored = QtCore.pyqtSignal(str,str,AbstractNode,str)
    sgnIRIPrefixNodeDictionaryUpdated = QtCore.pyqtSignal()

    def __init__(self, **kwargs):
        """
        Initialize the graphol project.
        """
        super().__init__(kwargs.get('session'))
        self.index = ProjectIndex()
        self.iri = kwargs.get('iri', 'NULL')
        self.name = kwargs.get('name')
        self.path = expandPath(kwargs.get('path'))
        self.prefix = kwargs.get('prefix', 'NULL')
        self.profile = kwargs.get('profile')
        self.profile.setParent(self)
        self.version = kwargs.get('version', '1.0')

        ###  variables controlled by reasoners  ###
        self.ontology_OWL = None
        self.axioms_to_nodes_edges_mapping = None

        self.unsatisfiable_classes = []
        self.explanations_for_unsatisfiable_classes = []
        self.unsatisfiable_attributes = []
        self.explanations_for_unsatisfiable_attributes = []
        self.unsatisfiable_roles = []
        self.explanations_for_unsatisfiable_roles = []

        self.inconsistent_ontology = None
        self.explanations_for_inconsistent_ontology = []

        self.uc_as_input_for_explanation_explorer = None
        self.nodes_of_unsatisfiable_entities = []
        self.nodes_or_edges_of_axioms_to_display_in_widget = []
        self.nodes_or_edges_of_explanations_to_display_in_widget = []

        self.converted_nodes = dict()

        self.brush_blue = QtGui.QBrush(QtGui.QColor(43, 63, 173, 160))
        self.brush_light_red = QtGui.QBrush(QtGui.QColor(250, 150, 150, 100))

        ############  variables for IRI-prefixes management #############

        self.IRI_prefixes_nodes_dict = dict()
        self.init_IRI_prefixes_nodes_dict_with_std_data()

        connect(self.sgnItemAdded, self.add_item_to_IRI_prefixes_nodes_dict)
        connect(self.sgnItemRemoved, self.remove_item_from_IRI_prefixes_nodes_dict)

    def print_dictionary(self, dictionary):

        print('size of the dictionary', len(dictionary.keys()))

        for iri in dictionary.keys():
            prefixes = dictionary[iri][0]
            nodes = dictionary[iri][1]
            print(iri, '-', prefixes, '-', nodes)

        print('********************')

        for n in self.nodes():
            if (n.Type is Item.AttributeNode) or (n.Type is Item.ConceptNode) or (n.Type is Item.IndividualNode) or (
                n.Type is Item.RoleNode):
                print(n.type(), ',', n.id, ',', n.iri, ',', n.prefix, ',', n.remaining_characters)

    def init_IRI_prefixes_nodes_dict_with_std_data(self):

        for std_iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            std_prefix = OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[std_iri]
            prefixes = set()
            prefixes.add(std_prefix)
            nodes = set()
            values = []
            values.append(prefixes)
            values.append(nodes)
            self.IRI_prefixes_nodes_dict[std_iri] = values

        project_prefixes = set()
        project_prefixes.add(self.prefix)
        project_nodes = set()
        values = []
        values.append(project_prefixes)
        values.append(project_nodes)
        self.IRI_prefixes_nodes_dict[self.iri] = values

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def add_item_to_IRI_prefixes_nodes_dict(self, diagram, item):

        print('add_item_to_IRI_prefixes_nodes_dict >>>',item)

        print(str(type(item)))
        print('ConceptNode' in str(type(item)))

        if item.type() in {Item.AttributeNode, Item.ConceptNode, Item.IndividualNode, Item.RoleNode}:

            node = item
            print('ConceptNode' in str(type(node)))

            if (('AttributeNode' in str(type(node))) or ('ConceptNode' in str(type(node))) or ('IndividualNode' in str(type(node))) or ('RoleNode' in str(type(node)))):

                print('self.iri', self.iri)
                print('self.prefix', self.prefix)

                print('node.iri',node.iri)

                if node.iri is '':
                    node.iri = self.iri

                print('node.iri', node.iri)
                print('node.prefix', node.prefix)

                if (node.iri is self.iri) and (node.prefix is ''):
                    node.prefix = self.prefix

                print('node.prefix', node.prefix)

                #initial text of label is :Concept etc
                #change it to prefix:concept or iri#concept

                if node.prefix is not '':
                    node.setText(node.prefix + ':' + node.text())
                else:
                    if node.iri is self.iri:
                        node.setText(self.prefix + ':' + node.text())
                    else:
                        node.setText(node.iri + '#' + node.text())

                if node.iri in self.IRI_prefixes_nodes_dict.keys():
                    self.IRI_prefixes_nodes_dict[node.iri][0].add(node.prefix)
                    self.IRI_prefixes_nodes_dict[node.iri][1].add(node)
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit()
                else:
                    prefixes = set()
                    prefixes.add(node.prefix)
                    nodes = set()
                    nodes.add(node)
                    values = []
                    values.append(prefixes)
                    values.append(nodes)
                    self.IRI_prefixes_nodes_dict[node.iri] = values
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit()

        print('add_item_to_IRI_prefixes_nodes_dict >>>  END',item)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def remove_item_from_IRI_prefixes_nodes_dict(self, diagram, node):

        #remove the node in all the indices of the dictionary

        corr_iris = []

        for IRI_in_dict in self.IRI_prefixes_nodes_dict.keys():
            if node in self.IRI_prefixes_nodes_dict[IRI_in_dict][1]:
                self.IRI_prefixes_nodes_dict[IRI_in_dict][1].remove(node)
                corr_iris.append(IRI_in_dict)

        if len(corr_iris) > 0:
            self.sgnIRIPrefixNodeDictionaryUpdated.emit()
        else:
            LOGGER.warning('node is not present in the dictionary')

    def copy_IRI_prefixes_nodes_dictionaries(self, from_dict, to_dict):

        # dict[key] = [set(),set()]
        for iri in from_dict.keys():
            prefixes = from_dict[iri][0]
            nodes = from_dict[iri][1]

            values = []
            to_prefixes = set()
            to_nodes = set()

            to_prefixes = to_prefixes.union(prefixes)
            to_nodes = to_nodes.union(nodes)

            values.append(to_prefixes)
            values.append(to_nodes)

            to_dict[iri] = values

        return to_dict

    def addIRIPrefixNodeEntry_OnlyNode(self, dictionary, iri, prefix='', node='', **kwargs):

        print('>>> addIRIPrefixNodeEntry_OnlyNode',iri,',',prefix,',',node.id)

        iri_added = kwargs.get('iri_added',False)
        prefix_added = kwargs.get('prefix_added',False)

        if prefix is None:
            prefix = ''

        if ((node is not '') and (node is not None)):
            if node in dictionary[iri][1]:
                if (prefix_added is False) and (iri_added is False):
                    self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, '[IRI-prefix-node] mapping already exists')
                    return dictionary
                else:
                    self.sgnIRIPrefixNodeEntryAdded.emit(iri, prefix, None)
                    return dictionary
            else:
                dictionary[iri][1].add(node)
                self.sgnIRIPrefixNodeEntryAdded.emit(iri, prefix, node)
                return dictionary
        elif (node is '') or (node is None):
            if prefix is not '':
                if (prefix_added is False) and (iri_added is False):
                    self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None, '[IRI-prefix] mapping already exists')
                    return dictionary
                else:
                    self.sgnIRIPrefixNodeEntryAdded.emit(iri, prefix, None)
                    return dictionary
            else:
                if (prefix_added is False) and (iri_added is False):
                    self.sgnIRIPrefixNodeEntryIgnored.emit(iri, '', None, '[IRI-''] mapping already exists')
                    return dictionary
                else:
                    self.sgnIRIPrefixNodeEntryAdded.emit(iri, prefix, None)
                    return dictionary

        print('>>> addIRIPrefixNodeEntry_OnlyNode END')

    def addIRIPrefixNodeEntry(self, dictionary, iri, prefix='', node=''):

        if node is None:
            print('>>> addIRIPrefixNodeEntry', iri, ',', prefix, ', None')
        else:
            print('>>> addIRIPrefixNodeEntry',iri,',',prefix,',',node.id)

        if iri is None:
            LOGGER.error('iri is None')
            return

        if (iri is ''):
            iri = self.iri

        ### cannot add standart IRI ###
        if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'Cannot modify standard IRI(s)')
            return dictionary
        ### cannot add standart prefixes ###
        std_prefixes = set()
        for k in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            std_prefixes.add(OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[k])

        if prefix in std_prefixes:
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'Cannot modify standard prefix(es)')
            return dictionary

        iri_is_default = False
        prefix_is_default = False

        if (iri is self.iri): #default IRI
            iri_is_default = True
        if (prefix is self.prefix): # default prefix
            prefix_is_default = True
        if iri_is_default and prefix is '':
            prefix_is_default = True

        if (iri_is_default is True) and (prefix_is_default is False):
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'Cannot assign multiple project prefixes')
            return dictionary
        elif (iri_is_default is False) and (prefix_is_default is True):
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'Cannot assign a non-project IRI to project prefix')
            return dictionary
        else:

            IRIs = dictionary.keys()
            prefixes_in_dict = set()
            for iri_itr in IRIs:
                prefixes_in_dict = prefixes_in_dict.union(dictionary[iri_itr][0])

            print('prefixes_in_dict',prefixes_in_dict)

            if iri in IRIs:   #IRI is present
                if ((prefix is not None) and (prefix is not '')):  # E. str for prefix
                    if (prefix in prefixes_in_dict): # prefix is present
                        #case 1
                        #E.[IRI-prefix]|E.[[IRI'-prefix]^[IRI-''|prefix']]
                        if prefix in dictionary[iri][0] : #case 1.1 - [IRI-prefix]
                            self.addIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node)
                        else: # case 1.2 - E.[[IRI'-prefix]^[IRI-''|prefix']]
                            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'prefix mapped with another IRI')
                            return dictionary
                    else:  # prefix is absent
                        #case 2
                        #E.[IRI-''|prefix']
                        dictionary[iri][0].add(prefix)
                        self.addIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node, prefix_added=True)
                else:   # None-prefix (prefix is None) or (prefix is '')
                        # case 3 prefix=None is present # E.[IRI-''] | [IRI-prefix'] ^^ [lst(IRI')-'']
                        # case 4 prefix=None is absent # E.[IRI-prefix']
                        self.addIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node) # case 3|4
            else: #IRI is absent
                if ((prefix is not None) and (prefix is not '')):  # E. str for prefix
                    if (prefix in prefixes_in_dict): # prefix is present
                        # case 1
                        # E. [IRI'-prefix]
                        self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'prefix mapped with another IRI')
                        return dictionary
                    else: # prefix is absent
                        # case 2
                        temp = set()
                        temp.add(prefix)
                        temp_2 = set()
                        values = []
                        values.append(temp)
                        values.append(temp_2)
                        dictionary[iri] = values
                        self.addIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node, iri_added=True, prefix_added=True)
                else:  # None-prefix (prefix is None) or (prefix is '')
                    # case 3|4
                    temp = set()
                    temp_2 = set()
                    values = []
                    values.append(temp)
                    values.append(temp_2)
                    dictionary[iri] = values
                    self.addIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node, iri_added=True)

        print('>>> addIRIPrefixNodeEntry END')

    def removeIRIPrefixNodeEntry_OnlyNode(self, dictionary, iri, prefix, node):

        print('>>> removeIRIPrefixNodeEntry_OnlyNode',iri,',',prefix,',',node.id)

        if node in dictionary[iri][1]:
            dictionary[iri][1].remove(node)
            self.sgnIRIPrefixNodeEntryRemoved.emit(iri, prefix, node, 'node removed')
        else:
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None, 'Error! node is not present in the list')

        print('>>> removeIRIPrefixNodeEntry_OnlyNode END')

    def removeIRIPrefixNodeEntry(self, dictionary, iri, prefix, node):

        if node is None:
            print('>>> removeIRIPrefixNodeEntry', iri, ',', prefix, ', None')
        else:
            print('>>> removeIRIPrefixNodeEntry',iri,',',prefix,',',node.id)

        # iri [present|absent] - absent iri handled in the function above
        # prefix [None|E.str] ^^ [present|absent]
        # node [none|E.str_present|E.str_absent]

        if iri is '':
            iri = self.iri

        ### cannot remove standart IRI ###
        if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'cannot remove standard IRI')
            return dictionary
        ### cannot remove standart prefixes ###
        std_prefixes = set()
        for k in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            std_prefixes.add(OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[k])

        if prefix in std_prefixes:
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, node, 'cannot remove standard prefixes')
            return dictionary

        if (iri in dictionary.keys()) is False:
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None,'Error! IRI is not present in the list')
            return dictionary

        iri_is_default = False
        prefix_is_default = False

        if (iri is self.iri):  # default IRI
            iri_is_default = True
        if (prefix is self.prefix):  # default prefix
            prefix_is_default = True
        if iri_is_default and ((prefix is '') or (prefix is None)):
            prefix_is_default = True

        if (iri_is_default is True) and (prefix_is_default is True) and (node is None):
            self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None, 'Cannot remove project IRI and project prefix. Please use info widget')
            return dictionary

        if (prefix is '') and (len(dictionary[iri][1]) >= 1):
            if node is None:
                self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None,
                                                   'Cannot remove this IRI because there are nodes present in this project with this IRI.')
            else:
                pass
                #remove only the node
                self.removeIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node)

        elif (prefix is '') and (len(dictionary[iri][1]) == 0):
            if node is None:
                popped_element = dictionary.pop(iri)
                self.sgnIRIPrefixNodeEntryRemoved.emit(iri, prefix, None, 'IRI removed-'+str(popped_element))
            else:
                # node has to be none because len(dictionary[iri][1]) == 0
                self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None, 'Error! node is not present in the list')

        elif (prefix is not ''):
            if node is None:
                if prefix in dictionary[iri][0]:
                    dictionary[iri][0].remove(prefix)
                    self.sgnIRIPrefixNodeEntryRemoved.emit(iri, prefix, None, 'prefix removed')
                else:
                    self.sgnIRIPrefixNodeEntryIgnored.emit(iri, prefix, None, 'Error! prefix is not present in the list')
            else:
                # remove only the node
                self.removeIRIPrefixNodeEntry_OnlyNode(dictionary, iri, prefix, node)

        print('>>> removeIRIPrefixNodeEntry END')

    def colour_items_in_case_of_unsatisfiability_or_inconsistent_ontology(self):

        for node_or_edge in self.nodes_or_edges_of_explanations_to_display_in_widget:

            node_or_edge.selection.setBrush(self.brush_light_red)
            node_or_edge.setCacheMode(AbstractItem.NoCache)
            node_or_edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
            node_or_edge.update(node_or_edge.boundingRect())

        for node_or_edge in self.nodes_or_edges_of_axioms_to_display_in_widget:

            node_or_edge.selection.setBrush(self.brush_blue)
            node_or_edge.setCacheMode(AbstractItem.NoCache)
            node_or_edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
            node_or_edge.update(node_or_edge.boundingRect())

        for entity in self.nodes_of_unsatisfiable_entities:

            for node in entity:
                # node.selection.setBrush(self.brush)
                node.updateNode(valid=False)

        for d in self.diagrams():
            self.diagram(d.name).sgnUpdated.emit()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for Project.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def addDiagram(self, diagram):
        """
        Add the given diagram to the Project, together with all its items.
        :type diagram: Diagram
        """
        if self.index.addDiagram(diagram):
            self.sgnDiagramAdded.emit(diagram)
            for item in diagram.items():
                if item.isNode() or item.isEdge():
                    diagram.sgnItemAdded.emit(diagram, item)

    def diagram_from_its_name(self, d_name):
        """
        Retrieves a diagram given its id.
        :type did: str
        :rtype: Diagram
        """
        diags = self.diagrams()

        for d in diags:
            if d.name == d_name:
                return d
        return None

    def diagram(self, did):
        """
        Returns the diagram matching the given id or None if no diagram is found.
        :type did: str
        :rtype: Diagram
        """
        return self.index.diagram(did)

    def diagrams(self):
        """
        Returns a collection with all the diagrams in this Project.
        :rtype: set
        """
        return self.index.diagrams()

    def edge(self, diagram, eid):
        """
        Returns the edge matching the given id or None if no edge is found.
        :type diagram: Diagram
        :type eid: str
        :rtype: AbstractEdge
        """
        return self.index.edge(diagram, eid)

    def edges(self, diagram=None):
        """
        Returns a collection with all the edges in the given diagram.
        If no diagram is supplied a collection with all the edges in the Project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        return self.index.edges(diagram)

    def isEmpty(self):
        """
        Returns True if the Project contains no element, False otherwise.
        :rtype: bool
        """
        return self.index.isEmpty()

    def item(self, diagram, iid):
        """
        Returns the item matching the given id or None if no item is found.
        :type diagram: Diagram
        :type iid: str
        :rtype: AbstractItem
        """
        return self.index.item(diagram, iid)

    def itemNum(self, item, diagram=None):
        """
        Returns the number of items of the given type which belongs to the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project.
        :type item: Item
        :type diagram: Diagram
        :rtype: int
        """
        return self.index.itemNum(item, diagram)

    def items(self, diagram=None):
        """
        Returns a collection with all the items in the given diagram.
        If no diagram is supplied a collection with all the items in the Project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        return self.index.items(diagram)

    def meta(self, item, name):
        """
        Returns metadata for the given predicate, expressed as pair (item, name).
        :type item: Item
        :type name: str
        :rtype: dict
        """
        return self.index.meta(item, name)

    def metas(self, *types):
        """
        Returns a collection of pairs 'item', 'name' for all the predicates with metadata.
        :type types: list
        :rtype: list
        """
        return self.index.metas(*types)

    def node(self, diagram, nid):
        """
        Returns the node matching the given id or None if no node is found.
        :type diagram: Diagram
        :type nid: str
        :rtype: AbstractNode
        """
        return self.index.node(diagram, nid)

    def nodes(self, diagram=None):
        """
        Returns a collection with all the nodes in the given diagram.
        If no diagram is supplied a collection with all the nodes in the Project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        return self.index.nodes(diagram)

    def predicateNum(self, item, diagram=None):
        """
        Returns the number of predicates of the given type which are defined in the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project.
        :type item: Item
        :type diagram: Diagram
        :rtype: int
        """
        return self.index.predicateNum(item, diagram)

    def predicates(self, item=None, name=None, diagram=None):
        """
        Returns a collection of predicate nodes belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project.
        :type item: Item
        :type name: str
        :type diagram: Diagram
        :rtype: set
        """
        return self.index.predicates(item, name, diagram)

    def removeDiagram(self, diagram):
        """
        Remove the given diagram from the project index, together with all its items.
        :type diagram: Diagram
        """
        if self.index.removeDiagram(diagram):
            for item in self.items(diagram):
                diagram.sgnItemRemoved.emit(diagram, item)
            self.sgnDiagramRemoved.emit(diagram)

    def setMeta(self, item, name, meta):
        """
        Set metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        :type meta: dict
        """
        if self.index.setMeta(item, name, meta):
            self.sgnMetaAdded.emit(item, name)

    def unsetMeta(self, item, name):
        """
        Remove metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        """
        if self.index.unsetMeta(item, name):
            self.sgnMetaRemoved.emit(item, name)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddItem(self, diagram, item):
        """
        Executed whenever an item is added to a diagram belonging to this Project.
        :type diagram: Diagram
        :type item: AbstractItem
        """
        if self.index.addItem(diagram, item):
            self.sgnItemAdded.emit(diagram, item)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveItem(self, diagram, item):
        """
        Executed whenever an item is removed from a diagram belonging to this project.
        This slot will remove the given element from the project index.
        :type diagram: Diagram
        :type item: AbstractItem
        """
        if self.index.removeItem(diagram, item):
            self.sgnItemRemoved.emit(diagram, item)


class ProjectIndex(dict):
    """
    Extends built-in dict and implements the Project index.
    """
    def __init__(self):
        """
        Initialize the Project Index.
        """
        super().__init__(self)
        self[K_DIAGRAM] = dict()
        self[K_EDGE] = dict()
        self[K_ITEMS] = dict()
        self[K_NODE] = dict()
        self[K_PREDICATE] = dict()
        self[K_TYPE] = dict()

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
                if item.isPredicate():
                    k = OWLText(item.text())
                    if i not in self[K_PREDICATE]:
                        self[K_PREDICATE][i] = dict()
                    if k not in self[K_PREDICATE][i]:
                        self[K_PREDICATE][i][k] = {K_NODE: dict()}
                    if diagram.name not in self[K_PREDICATE][i][k][K_NODE]:
                        self[K_PREDICATE][i][k][K_NODE][diagram.name] = set()
                    self[K_PREDICATE][i][k][K_NODE][diagram.name] |= {item}
            if item.isEdge():
                if diagram.name not in self[K_EDGE]:
                    self[K_EDGE][diagram.name] = dict()
                self[K_EDGE][diagram.name][item.id] = item
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

    def meta(self, item, name):
        """
        Retrieves metadata for the given predicate, expressed as pair (item, name).
        :type item: Item
        :type name: str
        :rtype: dict
        """
        try:
            name = OWLText(name)
            return self[K_PREDICATE][item][name][K_META]
        except KeyError:
            return dict()

    def metas(self, *types):
        """
        Retrieves a collection of pairs 'item', 'name' for all the predicates with metadata.
        :type types: list
        :rtype: list
        """
        filter_ = lambda x: not types or x in types
        return [(k1, k2) for k1 in self[K_PREDICATE] \
                            for k2 in self[K_PREDICATE][k1] \
                                if filter_(k1) and K_META in self[K_PREDICATE][k1][k2]]

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

    def predicateNum(self, item, diagram=None):
        """
        Count the number of predicates of the given type which are defined in the given diagram.
        If no diagram is supplied, the counting is extended to the whole Project Index.
        :type item: Item
        :type diagram: Diagram
        :rtype: int
        """
        try:
            subdict = self[K_PREDICATE]
            if not diagram:
                return len(subdict[item])
            return len({i for i in subdict[item] if diagram.name in subdict[item][i][K_NODE]})
        except (KeyError, TypeError):
            return 0
    
    def predicates(self, item=None, name=None, diagram=None):
        """
        Returns a collection of predicate nodes belonging to the given diagram.
        If no diagram is supplied the lookup is performed across the whole Project Index.
        :type item: Item
        :type name: str
        :type diagram: Diagram
        :rtype: set
        """
        try:

            if not item and not name:
                collection = set()
                if not diagram:
                    for i in self[K_PREDICATE]:
                        for j in self[K_PREDICATE][i]:
                            collection.update(*self[K_PREDICATE][i][j][K_NODE].values())
                else:
                    for i in self[K_PREDICATE]:
                        for j in self[K_PREDICATE][i]:
                            collection.update(self[K_PREDICATE][i][j][K_NODE][diagram.name])
                return collection

            if item and not name:
                collection = set()
                if not diagram:
                    for i in self[K_PREDICATE][item]:
                        collection.update(*self[K_PREDICATE][item][i][K_NODE].values())
                else:
                    for i in self[K_PREDICATE][item]:
                        collection.update(self[K_PREDICATE][item][i][K_NODE][diagram.name])
                return collection

            if not item and name:
                collection = set()
                name = OWLText(name)
                if not diagram:
                    for i in self[K_PREDICATE]:
                        collection.update(*self[K_PREDICATE][i][name][K_NODE].values())
                else:
                    for i in self[K_PREDICATE]:
                        collection.update(self[K_PREDICATE][i][name][K_NODE][diagram.name])
                return collection

            if item and name:
                name = OWLText(name)
                if not diagram:
                    return set.union(*self[K_PREDICATE][item][name][K_NODE].values())
                return self[K_PREDICATE][item][name][K_NODE][diagram.name]

        except KeyError:
            return set()
        
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
                if item.isPredicate():
                    k = OWLText(item.text())
                    if i in self[K_PREDICATE]:
                        if k in self[K_PREDICATE][i]:
                            if diagram.name in self[K_PREDICATE][i][k][K_NODE]:
                                self[K_PREDICATE][i][k][K_NODE][diagram.name] -= {item}
                                if not self[K_PREDICATE][i][k][K_NODE][diagram.name]:
                                    del self[K_PREDICATE][i][k][K_NODE][diagram.name]
                                    if not self[K_PREDICATE][i][k][K_NODE]:
                                        del self[K_PREDICATE][i][k]
                                        if not self[K_PREDICATE][i]:
                                            del self[K_PREDICATE][i]
            if item.isEdge():
                if diagram.name in self[K_EDGE]:
                    if item.id in self[K_EDGE][diagram.name]:
                        del self[K_EDGE][diagram.name][item.id]
                        if not self[K_EDGE][diagram.name]:
                            del self[K_EDGE][diagram.name]
            return True
        return False
                
    def setMeta(self, item, name, meta):
        """
        Set metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        :type meta: dict
        :rtype: bool
        """
        try:
            name = OWLText(name)
            self[K_PREDICATE][item][name][K_META] = meta
        except KeyError:
            return False
        else:
            return True

    def unsetMeta(self, item, name):
        """
        Unset metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        :rtype: bool
        """
        name = OWLText(name)
        if item in self[K_PREDICATE]:
            if name in self[K_PREDICATE][item]:
                if K_META in self[K_PREDICATE][item][name]:
                    del self[K_PREDICATE][item][name][K_META]
                    return True
        return False


class ProjectMergeWorker(QtCore.QObject):
    """
    Extends QObject with facilities to merge the content of 2 distinct projects.
    """
    def __init__(self, project, other, session):
        """
        Initialize the project merge worker.
        :type project: Project
        :type other: Project
        :type session: Session
        """
        super().__init__(session)
        self.commands = list()
        self.project = project
        self.other = other

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for ProjectMergeWorker.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def mergeDiagrams(self):
        """
        Perform the merge of the diagrams by importing all the diagrams in the 'other' project in the loaded one.
        """
        for diagram in self.other.diagrams():
            # We may be in the situation in which we are importing a diagram with name 'X'
            # even though we already have a diagram 'X' in our project. Because we do not
            # want to overwrite diagrams, we perform a rename of the diagram being imported,
            # to be sure to have a unique diagram name, in the current project namespace.
            occurrence = 1
            name = diagram.name
            while self.project.diagram(diagram.name):
                diagram.name = '{0}_{1}'.format(name, occurrence)
                occurrence += 1
            ## SWITCH SIGNAL SLOTS
            disconnect(diagram.sgnItemAdded, self.other.doAddItem)
            disconnect(diagram.sgnItemRemoved, self.other.doRemoveItem)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            ## MERGE THE DIAGRAM IN THE CURRENT PROJECT
            self.commands.append(CommandDiagramAdd(diagram, self.project))

    def mergeMeta(self):
        """
        Perform the merge of predicates metadata.
        """
        conflicts = dict()
        resolutions = dict()

        for item, name in self.other.metas():
            if not self.project.predicates(item, name):
                ## NO PREDICATE => NO CONFLICT
                undo = self.project.meta(item, name).copy()
                redo = self.other.meta(item, name).copy()
                self.commands.append(CommandNodeSetMeta(self.project, item, name, undo, redo))
            else:
                ## CHECK FOR POSSIBLE CONFLICTS
                metac = self.project.meta(item, name)
                metai = self.other.meta(item, name)
                if metac != metai:
                    if item not in conflicts:
                        conflicts[item] = dict()
                    conflicts[item][name] = {K_CURRENT: metac.copy(), K_IMPORTING: metai.copy()}
                    if item not in resolutions:
                        resolutions[item] = dict()
                    resolutions[item][name] = metac.copy()

        ## RESOLVE CONFLICTS
        aconflicts = []
        for item in conflicts:
            for name in conflicts[item]:
                metac = conflicts[item][name][K_CURRENT]
                metai = conflicts[item][name][K_IMPORTING]
                ## RESOLVE DOCUMENTATION CONFLICTS
                docc = metac.get(K_DESCRIPTION, '')
                doci = metai.get(K_DESCRIPTION, '')
                if docc != doci:
                    resolver = PredicateDocumentationConflictResolver(item, name, docc, doci)
                    if resolver.exec_() == PredicateDocumentationConflictResolver.Rejected:
                        raise ProjectStopImportingError
                    resolutions[item][name][K_DESCRIPTION] = resolver.result()
                ## COLLECT ASSERTIONS CONFLICTS FOR ATTRIBUTES
                if item is Item.AttributeNode:
                    vc = metac.get(K_FUNCTIONAL, False)
                    vi = metai.get(K_FUNCTIONAL, False)
                    if vc != vi:
                        aconflicts.append({
                            K_ITEM: item,
                            K_NAME: name,
                            K_PROPERTY: K_FUNCTIONAL,
                            K_CURRENT: vc,
                            K_IMPORTING: vi
                        })
                ## COLLECT ASSERTIONS CONFLICTS FOR ROLES
                if item is Item.RoleNode:
                    for k in (K_ASYMMETRIC, K_INVERSE_FUNCTIONAL, K_IRREFLEXIVE, K_REFLEXIVE, K_SYMMETRIC, K_TRANSITIVE):
                        vc = metac.get(k, False)
                        vi = metai.get(k, False)
                        if vc != vi:
                            aconflicts.append({
                                K_ITEM: item,
                                K_NAME: name,
                                K_PROPERTY: k,
                                K_CURRENT: vc,
                                K_IMPORTING: vi
                            })

        ## RESOLVE BOOLEAN PROPERTIES CONFLICTS
        if aconflicts:
            resolver = PredicateBooleanConflictResolver(aconflicts)
            if resolver.exec_() == PredicateBooleanConflictResolver.Rejected:
                raise ProjectStopImportingError
            for e in resolver.results():
                resolutions[e[K_ITEM]][e[K_NAME]][e[K_PROPERTY]] = e[K_FINAL]

        ## GENERATE UNDOCOMMANDS FOR RESOLUTIONS
        for item in resolutions:
            for name in resolutions[item]:
                undo = self.project.meta(item, name)
                redo = resolutions[item][name]
                self.commands.append(CommandNodeSetMeta(self.project, item, name, undo, redo))

    def mergeFinished(self):
        """
        Completes the merge by executing the commands in the buffer on the undostack.
        """
        if self.commands:
            self.session.undostack.beginMacro('import project "{0}" into "{1}"'.format(self.other.name, self.project.name))
            for command in self.commands:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

    def run(self):
        """
        Perform the merge of the 2 projects.
        """
        try:
            LOGGER.info('Performing project import: %s <- %s...', self.project.name, self.other.name)
            self.mergeDiagrams()
            self.mergeMeta()
        except ProjectStopImportingError:
            pass
        else:
            self.mergeFinished()


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


class CommandProjetSetIRIPrefixesNodesDict(QtWidgets.QUndoCommand):

    def __init__(self, project, dict_old_val, dict_new_val):

        print('CommandProjetSetIRIPrefixesNodesDict >>> __init__')

        super().__init__('update dictionary')

        self.project = project
        self.dict_old_val = dict_old_val
        self.dict_new_val = dict_new_val

    def redo(self):
        print('CommandProjetSetIRIPrefixesNodesDict >>> redo')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_new_val,self.project.IRI_prefixes_nodes_dict)
        self.project.sgnIRIPrefixNodeDictionaryUpdated.emit()

    def undo(self):
        print('CommandProjetSetIRIPrefixesNodesDict >>> undo')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_old_val,self.project.IRI_prefixes_nodes_dict)
        self.project.sgnIRIPrefixNodeDictionaryUpdated.emit()