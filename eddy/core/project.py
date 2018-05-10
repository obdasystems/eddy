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
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.nodes import CommandNodeSetMeta
from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict
from eddy.core.commands.labels import GenerateNewLabel, CommandLabelChange
from eddy.core.commands.project import CommandProjectDisconnectSpecificSignals, CommandProjectConnectSpecificSignals
#from eddy.core.functions.owl import OWLText
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.core.items.common import AbstractItem
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.ui.DiagramsSelectionDialog import DiagramsSelectionDialog
from eddy.ui.resolvers import PredicateBooleanConflictResolver
from eddy.ui.resolvers import PredicateDocumentationConflictResolver
from jnius import autoclass, cast, detach

from rfc3987 import parse


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
K_DESCRIPTION_STATUS = 'status'

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

    sgnIRIPrefixesEntryModified = QtCore.pyqtSignal(str,str,str,str)
    sgnIRIPrefixEntryAdded = QtCore.pyqtSignal(str,str,str)
    sgnIRIPrefixEntryRemoved = QtCore.pyqtSignal(str,str,str)
    sgnIRIPrefixesEntryIgnored = QtCore.pyqtSignal(str,str,str)

    sgnIRINodeEntryAdded = QtCore.pyqtSignal(str,str,str)
    sgnIRINodeEntryRemoved = QtCore.pyqtSignal(str,str,str)
    sgnIRINodeEntryIgnored = QtCore.pyqtSignal(str,str,str)

    sgnIRIVersionEntryAdded = QtCore.pyqtSignal(str,str,str)
    sgnIRIVersionEntryRemoved = QtCore.pyqtSignal(str,str,str)
    sgnIRIVersionEntryIgnored = QtCore.pyqtSignal(str,str,str)

    sgnIRIPrefixNodeDictionaryUpdated = QtCore.pyqtSignal(str,str,str)
    #sgnPreferedPrefixListUpdated = QtCore.pyqtSignal(str,str,str)

    def __init__(self, **kwargs):
        """
        Initialize the graphol project.
        """
        super().__init__(kwargs.get('session'))
        self.index = ProjectIndex()
        #self.iri = kwargs.get('iri', 'NULL')
        self.name = kwargs.get('name')
        self.path = expandPath(kwargs.get('path'))
        #self.prefix = kwargs.get('prefix', 'NULL')
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

        ### $$ END $$ variables controlled by reasoners $$ END $$ ###

        self.brush_blue = QtGui.QBrush(QtGui.QColor(43, 63, 173, 160))
        self.brush_light_red = QtGui.QBrush(QtGui.QColor(250, 150, 150, 100))
        self.brush_orange = QtGui.QBrush(QtGui.QColor(255, 165, 0, 160))
        ############  variables for IRI-prefixes management #############

        self.IRI_prefixes_nodes_dict = kwargs.get('IRI_prefixes_nodes_dict')
        self.init_IRI_prefixes_nodes_dict_with_std_data()

        self.iri_of_cut_nodes = []
        #self.iri_of_imported_nodes = []
        #self.prefered_prefix_list = kwargs.get('prefered_prefix_list')

        connect(self.sgnItemAdded, self.add_item_to_IRI_prefixes_nodes_dict)
        connect(self.sgnItemRemoved, self.remove_item_from_IRI_prefixes_nodes_dict)
        #connect(self.sgnItemRemoved, self.remove_item_from_prefered_prefix_list)
        connect(self.sgnIRIPrefixNodeDictionaryUpdated, self.regenerate_label_of_nodes_for_iri)

    @property
    def iri(self):

        #print('Project >> iri')

        return_list = []

        for iri in self.IRI_prefixes_nodes_dict:
            properties = self.IRI_prefixes_nodes_dict[iri][2]
            #print('iri',iri,'properties',properties)
            if 'Project_IRI' in properties:
                return_list.append(iri)

        #print('Project >> iri >> return_list',return_list)

        if len(return_list) == 0:
            return None
        elif len(return_list) == 1:
            return return_list[0]
        else:
            LOGGER.critical('Multiple project IRIs found'+str(return_list))
            return return_list[0]

        #print('Project >> iri END')

    @property
    def prefix(self):

        project_prefixes = self.prefixes

        if len(project_prefixes) == 0:
            if 'display_in_widget' in self.IRI_prefixes_nodes_dict[self.iri][2]:
                return ''
            else:
                return None
        else:
            return project_prefixes[len(project_prefixes)-1]

    @property
    def prefixes(self):

        project_iri = self.iri

        if project_iri is None:
            return None

        project_prefixes = self.IRI_prefixes_nodes_dict[project_iri][0]

        return project_prefixes

    def get_iri_of_node(self,node_inp):

        iris = set()

        # print('self',self)
        for iri in self.IRI_prefixes_nodes_dict.keys():
            nodes = self.IRI_prefixes_nodes_dict[iri][1]

            if (node_inp in nodes) or (str(node_inp) in str(nodes)):
                iris.add(iri)
            else:
                for n in nodes:
                    if (node_inp is n) or (str(node_inp) == str(n)):
                        iris.add(iri)

        if len(iris) == 1:
            return list(iris)[0]
        if len(iris) == 0:
            return None

        return str('Error multiple IRIS-' + str(iris))

    def get_prefixes_of_node(self, node_inp):
        """
        Returns the value value associated with this node.
        :rtype: str ||  'Error multiple IRIS-'* | None | a single prefix
        """
        iri = self.get_iri_of_node(node_inp)

        if iri is None:
            return None
        if 'Error multiple IRIS-' in iri:
            return iri

        prefixes = self.IRI_prefixes_nodes_dict[iri][0]
        return prefixes

    def get_prefix_of_node(self,node_inp):

        node_prefixes = self.get_prefixes_of_node(node_inp)
        node_properties = self.get_properties_of_node(node_inp)

        if node_prefixes is None:
            if 'display_in_widget' in node_properties:
                return ''
            else:
                return None
        if 'Error multiple IRIS-' in node_prefixes:
            return node_prefixes

        if len(node_prefixes) == 0:
            if 'display_in_widget' in node_properties:
                return ''
            else:
                return None
        else:
            return node_prefixes[len(node_prefixes)-1]

    def get_properties_of_node(self,node_inp):

        iri = self.get_iri_of_node(node_inp)

        if iri is None:
            return None
        if 'Error multiple IRIS-' in iri:
            return iri

        properties = self.IRI_prefixes_nodes_dict[iri][2]
        return sorted(list(properties))

    def get_full_IRI(self,iri,version,remaining_characters):

        if (version is None) or (version == ''):
            if iri[len(iri)-1] == '#' or iri[len(iri)-1] == '/':
                return iri + remaining_characters
            else:
                return iri + '#' + remaining_characters
        else:
            if iri[len(iri) - 1] == '/':
                return iri + version + '#' + remaining_characters
            else:
                return iri + '/' + version + '#' + remaining_characters

    def get_iri_for_prefix(self,prefix_inp):

        if prefix_inp is None:
            return None

        return_list = []

        for iri in self.IRI_prefixes_nodes_dict.keys():
            prefixes = self.IRI_prefixes_nodes_dict[iri][0]
            properties = self.IRI_prefixes_nodes_dict[iri][2]
            if prefix_inp in prefixes:
                return_list.append(iri)
            if ('display_in_widget' in properties) and prefix_inp == '':
                return_list.append(iri)

        if len(return_list) == 1:
            return return_list[0]
        elif len(return_list) == 0:
            return None
        else:
            LOGGER.critical('prefix mapped to multiple IRI(s)')
            return return_list

    def get_prefix_for_iri(self,inp_iri):

        prefixes = self.IRI_prefixes_nodes_dict[inp_iri][0]
        #sorted_lst_prefixes = sorted(list(prefixes))
        if 'display_in_widget' in self.IRI_prefixes_nodes_dict[inp_iri][2]:
            return ''

        if len(prefixes) == 0:
            return None

        return prefixes[len(prefixes)-1]

    def get_iri_with_no_prefix_displayed_in_widget(self,dictionary):

        return_list = []

        for iri in dictionary.keys():
            properties = dictionary[iri][2]
            if 'display_in_widget' in properties:
                return_list.append(iri)

        if len(return_list) == 0:
            return None
        elif len(return_list) == 1:
            return return_list[0]
        else:
            return 'error_multiple_occurences'+str(return_list)

    def print_dictionary_2(self, dictionary):

        LOGGER.info('<<<<<<<<<          print_dictionary        >>>>>>>>')
        LOGGER.info('size of the dictionary - '+str(len(dictionary.keys())))

        LOGGER.info('Project_IRI - '+str(self.iri))
        LOGGER.info('Project_prefix(es) - '+str(self.prefixes))
        LOGGER.info('Project_prefix - '+str(self.prefix))

        for iri in dictionary.keys():
            prefixes = dictionary[iri][0]
            nodes = dictionary[iri][1]
            properties = dictionary[iri][2]
            #version = dictionary[iri][3]

            #print(iri, '-', prefixes, '-', nodes, '-', properties, '-', version)
            LOGGER.info(str(iri)+ ' - '+ str(prefixes)+ ' - '+ str(nodes)+ ' - '+ str(properties))
        LOGGER.info('********************')

        for p in self.nodes():
            LOGGER.info(str(p.text()))

        LOGGER.info('********************')

        for n in self.nodes():
            #if (n.Type is Item.AttributeNode) or (n.Type is Item.ConceptNode) or (n.Type is Item.IndividualNode) or (n.Type is Item.RoleNode):
            if (('AttributeNode' in str(type(n))) or ('ConceptNode' in str(type(n))) or (
                            'IndividualNode' in str(type(n))) or ('RoleNode' in str(type(n)))):
                if n.Type is Item.IndividualNode:
                    LOGGER.info(str(n.type())+ ' , '+ str(n.id)+ ' , '+ str(self.get_iri_of_node(n))+ ' , '+ str(self.get_prefix_of_node(n))+ ' , '+ str(n.remaining_characters)+ ' , '+ str(n.identity()))
                else:
                    LOGGER.info(str(n.type())+ ' , '+ str(n.id)+ ' , '+ str(self.get_iri_of_node(n))+ ' , '+ str(self.get_prefix_of_node(n))+ ' , '+ str(n.remaining_characters))

        LOGGER.info('<<<<<<<<<          print_dictionary (END)       >>>>>>>>')

    def print_dictionary(self, dictionary):

        print('<<<<<<<<<          print_dictionary        >>>>>>>>')
        print('size of the dictionary - '+str(len(dictionary.keys())))

        print('Project_IRI - '+str(self.iri))
        print('Project_prefix(es) - '+str(self.prefixes))
        print('Project_prefix - '+str(self.prefix))

        for iri in dictionary.keys():
            prefixes = dictionary[iri][0]
            nodes = dictionary[iri][1]
            properties = dictionary[iri][2]

            print(str(iri)+ ' - '+ str(prefixes)+ ' - '+ str(nodes)+ ' - '+ str(properties))
        print('********************')

        print('*********        No IRI for Nodes        ***********')

        for n in self.nodes():
            #if (n.Type is Item.AttributeNode) or (n.Type is Item.ConceptNode) or (n.Type is Item.IndividualNode) or (n.Type is Item.RoleNode):
            if (('AttributeNode' in str(type(n))) or ('ConceptNode' in str(type(n))) or (
                            'IndividualNode' in str(type(n))) or ('RoleNode' in str(type(n)))):

                if self.get_iri_of_node(n) is None:
                    print('No IRI for ',n.id,' ',n.text())

        print('*********        No IRI for Nodes (END)       ***********')

        for n in self.nodes():
            #if (n.Type is Item.AttributeNode) or (n.Type is Item.ConceptNode) or (n.Type is Item.IndividualNode) or (n.Type is Item.RoleNode):
            print('                                     n.id,str(type(n))',n.id,'-',str(type(n)))

            if (('AttributeNode' in str(type(n))) or ('ConceptNode' in str(type(n))) or (
                            'IndividualNode' in str(type(n))) or ('RoleNode' in str(type(n)))):

                if n.Type is Item.IndividualNode:
                    print(str(n.type()), ',', str(n.id), ',', str(n.diagram.name),',', str(self.get_iri_of_node(n)), ',', str(self.get_prefix_of_node(n)), ',', str(n.remaining_characters), ',', str(n.identity()))
                else:
                    print(str(n.type()), ',', str(n.id), ',', str(n.diagram.name),',' , str(self.get_iri_of_node(n)), ',', str(self.get_prefix_of_node(n)), ',', str(n.remaining_characters))

        print('<<<<<<<<<          print_dictionary (END)       >>>>>>>>')
        print('<<<<<<<<<          iri_of_cut_nodes       >>>>>>>>')
        print('len(self.iri_of_cut_nodes)',len(self.iri_of_cut_nodes))
        for ele in self.iri_of_cut_nodes:
            print('ele',ele)

        print('<<<<<<<<<          iri_of_cut_nodes (END)       >>>>>>>>')

        """
        print('*********      metas        ***********')

        for m in self.metas():
            print(m)

        print('**')

        for n in self.predicates():
            meta = self.meta(n.type(), n.text())
            if meta is not None:
                print(n.text,'-',meta)

        print('*********      metas(END)        ***********')
        """

    #not used
    def copy_prefered_prefix_dictionaries(self, from_dict, to_dict):

        # entity = ontology_IRI | str(node)
        for entity in from_dict.keys():

            prefered_prefix = from_dict[entity]

            to_dict[entity] = prefered_prefix

        return to_dict

    def copy_IRI_prefixes_nodes_dictionaries(self, from_dict, to_dict):

        # dict[key] = [set(),set()]
        for iri in from_dict.keys():
            prefixes = from_dict[iri][0]
            nodes = from_dict[iri][1]
            properties = from_dict[iri][2]
            #version = from_dict[iri][3]

            values = []
            to_prefixes = []
            to_nodes = set()
            to_properties = set()
            #to_version = None

            to_prefixes.extend(prefixes)
            to_nodes = to_nodes.union(nodes)
            to_properties = to_properties.union(properties)
            #to_version = version

            values.append(to_prefixes)
            values.append(to_nodes)
            values.append(to_properties)
            #values.append(to_version)

            to_dict[iri] = values

        return to_dict

    def copy_list(self, from_list, to_list):

        for ele in from_list:
            to_list.append(ele)

        return to_list

    def init_IRI_prefixes_nodes_dict_with_std_data(self):

        #print('init_IRI_prefixes_nodes_dict_with_std_data')

        for std_iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():

            if std_iri in self.IRI_prefixes_nodes_dict.keys():
                continue

            std_prefix = OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[std_iri]
            prefixes = []

            #print('std_iri, std_prefix, prefixes',std_iri, std_prefix, prefixes)

            if std_prefix not in prefixes:
                prefixes.append(std_prefix)

            #print('std_iri, std_prefix, prefixes',std_iri, std_prefix, prefixes)

            nodes = set()
            properties = set()
            properties.add('Standard_IRI')

            values = []
            values.append(prefixes)
            values.append(nodes)
            values.append(properties)

            self.IRI_prefixes_nodes_dict[std_iri] = values

        #print('init_IRI_prefixes_nodes_dict_with_std_data END')

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def add_item_to_IRI_prefixes_nodes_dict(self, diagram, item):

        #print('>>>     add_item_to_IRI_prefixes_nodes_dict         ', item)
        #print('self.iri_of_cut_nodes',self.iri_of_cut_nodes)

        #if item.type() in {Item.AttributeNode, Item.ConceptNode, Item.IndividualNode, Item.RoleNode}:
        if (('AttributeNode' in str(type(item))) or ('ConceptNode' in str(type(item))) or (
                    'IndividualNode' in str(type(item))) or ('RoleNode' in str(type(item)))):
            #print('item.type() in {Item.AttributeNode, Item.ConceptNode, Item.IndividualNode, Item.RoleNode}:')

            node = item
            corr_iri = None

            flag = False

            #print('item.remaining_characters',item.remaining_characters)
            """
            if item.remaining_characters is not None:
                if item.remaining_characters in self.iri_of_imported_nodes:
                    ind = self.iri_of_imported_nodes.index(item.remaining_characters)
                    corr_iri = self.iri_of_imported_nodes[ind-1]
                    flag = True
            """
            for c,ele in enumerate(self.iri_of_cut_nodes):
                if (node is ele) or str(node) == str(ele):
                    corr_iri = self.iri_of_cut_nodes[c+1]
                    flag = True
                    break

            if flag is False:
                if (node.type() is Item.IndividualNode) and (node.identity() is Identity.Value):

                    # print('if           (node.type() is Item.IndividualNode) and (item.identity() is Identity.Value):')
                    if (self.get_iri_of_node(node) is None):
                        prefix = str(node.datatype.value)[0:str(node.datatype.value).index(':')]

                        std_iri_prefix = ['http://www.w3.org/1999/02/22-rdf-syntax-ns', 'rdf',
                                          'http://www.w3.org/2000/01/rdf-schema', 'rdfs',
                                          'http://www.w3.org/2001/XMLSchema', 'xsd',
                                          'http://www.w3.org/2002/07/owl', 'owl']

                        ind_prefix = std_iri_prefix.index(prefix)
                        ind_iri = ind_prefix - 1
                        corr_iri = std_iri_prefix[ind_iri]
                    else:
                        pass
                else:

                    # print('else          (node.type() is Item.IndividualNode) and (item.identity() is Identity.Value):')

                    if (self.get_iri_of_node(node) is None):

                        # print('if       (self.get_iri_of_node(node) is None):')

                        if (node.type() is not (Item.IndividualNode)) and (node.special() is not None):

                            # print('if       (node.type() is not (Item.IndividualNode)) and (node.special() is not None):')

                            corr_iri = 'http://www.w3.org/2002/07/owl'
                        else:

                            # print('else       (node.type() is not (Item.IndividualNode)) and (node.special() is not None):')

                            corr_iri = self.iri
                    else:

                        # print('else       (self.get_iri_of_node(node) is None):')

                        corr_iri = None

            # print('corr_iri',corr_iri)

            if corr_iri is not None:
                self.IRI_prefixes_nodes_dict[corr_iri][1].add(node)
                if node.diagram is not None:
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit(corr_iri,str(node),str(node.diagram.name))
                else:
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit(corr_iri, str(node), None)
            #print('self.IRI_prefixes_nodes_dict',self.IRI_prefixes_nodes_dict)

        #print('>>>     add_item_to_IRI_prefixes_nodes_dict       END', item)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def remove_item_from_IRI_prefixes_nodes_dict(self, diagram, node):

        #print('>>>     remove_item_from_IRI_prefixes_nodes_dict        ',node)
        #remove the node in all the indices of the dictionary
        if (('AttributeNode' in str(type(node))) or ('ConceptNode' in str(type(node))) or (
                    'IndividualNode' in str(type(node))) or ('RoleNode' in str(type(node)))):
            corr_iris = []

            for IRI_in_dict in self.IRI_prefixes_nodes_dict.keys():
                if (node in self.IRI_prefixes_nodes_dict[IRI_in_dict][1]) or\
                   (self.check_if_node_is_present_in_set(node, self.IRI_prefixes_nodes_dict[IRI_in_dict][1])):
                        corr_iris.append(IRI_in_dict)

            if len(corr_iris) == 1:
                self.IRI_prefixes_nodes_dict[corr_iris[0]][1].remove(node)
                if node.diagram is not None:
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit(corr_iris[0], str(node), str(node.diagram.name))
                else:
                    self.sgnIRIPrefixNodeDictionaryUpdated.emit(corr_iris[0], str(node), None)
            elif len(corr_iris) == 0:
                LOGGER.warning('node is not present in the dictionary')
            else:
                LOGGER.critical('multiple IRIs found for node')

        #print('>>>     remove_item_from_IRI_prefixes_nodes_dict    END    ',node)

    #not used
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def remove_item_from_prefered_prefix_dict(self, diagram, node):

        if str(node) in self.prefered_prefix_dict.keys():
            self.prefered_prefix_dict.pop(str(node))

    def generate_new_prefix(self,dictionary):

        new_integer = 0
        new_prefix = 'p'+str(new_integer)
        prefixes_in_dict = []

        for iri in dictionary.keys():
            prefixes = dictionary[iri][0]
            prefixes_in_dict.extend(prefixes)

        while(new_prefix in prefixes_in_dict):
            new_prefix = 'p'+str(new_integer+1)
            new_integer = new_integer+1

        return new_prefix

    def check_validity_of_IRI(self,iri_inp):

        try:
            #d=parse('https://protege.stanford.edu/ontologies/pizza/pizza.owl', rule='IRI')
            d = parse(iri_inp, rule='IRI')
        except (ValueError):
            return False
        else:
            LOGGER.info(str(d))
            if d['authority'] == '':
                return False
            return True

    """
    #not used as of now
    def AddORremoveORmodifyVersionforIRI(self, iri_inp, version_to, dictionary, **kwargs):

        task = kwargs.get('task', None)

        if iri_inp in dictionary.keys():
            version_from = dictionary[iri_inp][3]
            if task == 'add':
                if version_to is None:
                    self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_to,'Nothing to add')
                    return None
                else:
                    if version_from is None:
                        dictionary[iri_inp][3] = version_to
                        self.sgnIRIVersionEntryAdded.emit(iri_inp, version_to, 'Version added')
                        return dictionary
                    else:
                        if version_from == version_to:
                            self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_to, 'Current and new value for the versions are the same. Nothing to change')
                            return None
                        else:
                            self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_to, 'Another value present. (Remove_old_val + Add_new_val) or Modify_old_val.')
                            return None
            elif task == 'remove':
                if version_from is None:
                    self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_from, 'Nothing to remove')
                    return None
                else:
                    dictionary[iri_inp][3] = None
                    self.sgnIRIVersionEntryRemoved.emit(iri_inp, version_from, 'Version added')
                    return dictionary
            elif task == 'modify':
                if version_from is None:
                    if version_to is None:
                        self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_from, 'Nothing to change')
                        return None
                    else:
                        dictionary[iri_inp][3] = version_to
                        self.sgnIRIVersionEntryRemoved.emit(iri_inp, version_from, 'Version modified')
                        return dictionary
                else:
                    if version_to is None:
                        dictionary[iri_inp][3] = version_to
                        self.sgnIRIVersionEntryRemoved.emit(iri_inp, version_from, 'Version modified')
                        return dictionary
                    else:
                        if version_to == version_from:
                            self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_from, 'Nothing to change')
                            return None
                        else:
                            dictionary[iri_inp][3] = version_to
                            self.sgnIRIVersionEntryRemoved.emit(iri_inp, version_from, 'Version modified')
                            return dictionary
            else:
                self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_from, 'Programming error/ contact developer')
                LOGGER.critical('Programming error/ contact developer   >>>  AddORremoveORmodifyVersionforIRI')
                return None
        else:
            self.sgnIRIVersionEntryIgnored.emit(iri_inp, version_to, 'IRI not present in dictionary')
            return None
    """
    def modifyIRIPrefixesEntry(self,iri_from_val,prefixes_from_val,iri_to_val,prefixes_to_val, dictionary):

        None_1 = (iri_from_val is None)
        None_2 = (prefixes_from_val is None)
        None_3 = (iri_to_val is None)
        None_4 = (prefixes_to_val is None)

        ENTRY_ADD_OK_var = set()
        ENTRY_REMOVE_OK_var = set()
        ENTRY_IGNORE_var = set()

        @QtCore.pyqtSlot(str, str, str)
        def entry_ADD_ok(iri, prefix, message):

            ENTRY_ADD_OK_var.add(True)
            #print('modifyIRIPrefixesEntry   >>>     entry_ADD_ok(self): ', iri, ',', prefix, ',', message)

        @QtCore.pyqtSlot(str, str, str)
        def entry_REMOVE_OK(iri, prefix, message):

            ENTRY_REMOVE_OK_var.add(True)
            #print('modifyIRIPrefixesEntry   >>>     entry_REMOVE_ok(self): ', iri, ',', prefix, ',', message)

        @QtCore.pyqtSlot(str, str, str)
        def entry_NOT_OK(iri, prefix, message):

            ENTRY_IGNORE_var.add(True)
            #print('modifyIRIPrefixesEntry   >>>     entry_NOT_OK(self): ', iri, ',', prefix, ',', message)

        connect(self.sgnIRIPrefixEntryAdded, entry_ADD_ok)
        connect(self.sgnIRIPrefixEntryRemoved, entry_REMOVE_OK)
        connect(self.sgnIRIPrefixesEntryIgnored, entry_NOT_OK)

        def modify_iri(from_iri, to_iri, dictionary):

            if from_iri == to_iri:
                return 'Nothing to modify in IRI'

            #msg needed

            temp_prefixes = dictionary[from_iri][0]
            temp_nodes = dictionary[from_iri][1]
            temp_properties = dictionary[from_iri][2]

            dictionary[from_iri][0] = []
            dictionary[from_iri][1] = set()
            dictionary[from_iri][2] = set()

            #self.removeIRIPrefixEntry(dictionary,from_iri,None)
            self.addORremoveIRIPrefixEntry(dictionary, from_iri, None, 'remove_entry',remove_project_iri=True)

            if (False in ENTRY_REMOVE_OK_var) or (True in ENTRY_IGNORE_var):
                return str('Error could not modify IRI from '+from_iri+' to '+to_iri)

            if to_iri not in dictionary.keys():
                #self.addIRIPrefixEntry(dictionary,to_iri,None)
                self.addORremoveIRIPrefixEntry(dictionary, to_iri, None, 'add_entry')

            if (False in ENTRY_ADD_OK_var) or (True in ENTRY_IGNORE_var):
                return str('Error could not modify IRI from '+from_iri+' to '+to_iri)

            #dictionary[to_iri][0] = dictionary[to_iri][0].extend(temp_prefixes)
            for p in temp_prefixes:
                if p not in dictionary[to_iri][0]:
                    dictionary[to_iri][0].append(p)

            dictionary[to_iri][1] = dictionary[to_iri][1].union(temp_nodes)
            dictionary[to_iri][2] = dictionary[to_iri][2].union(temp_properties)

            return 'Success'

        def modify_prefixes(iri_inp, from_prefixes, to_prefixes, dictionary):

            flag = set()
            if len(from_prefixes) == len(to_prefixes):
                for c,p in enumerate(from_prefixes):
                    if to_prefixes[c] == p:
                        flag.add(True)
                    else:
                        flag.add(False)
            else:
                flag.add(False)

            #if (to_prefixes.issubset(from_prefixes) and from_prefixes.issubset(to_prefixes)):
            if False not in flag:
                return 'Nothing to modify in prefixes'

            prefixes = dictionary[iri_inp][0]
            #equal = (prefixes.issubset(from_prefixes) and from_prefixes.issubset(prefixes))
            # check if inp_iri maps to from_prefixes

            flag_2 = set()
            if len(from_prefixes) == len(prefixes):
                for c,p in enumerate(from_prefixes):
                    if prefixes[c] == p:
                        flag_2.add(True)
                    else:
                        flag_2.add(False)
            else:
                flag_2.add(False)

            if False not in flag_2:
                # dictionary[i][1] = set()
                for p in from_prefixes:
                    # self.removeIRIPrefixEntry(dictionary, i, p)
                    self.addORremoveIRIPrefixEntry(dictionary, iri_inp, p, 'remove_entry', remove_project_prefixes=True)
                    if (False in ENTRY_REMOVE_OK_var) or (True in ENTRY_IGNORE_var):
                        return 'Error could not modify prefixes from ' + str(from_prefixes) + ' to ' + str(to_prefixes)

                for p in to_prefixes:
                    # self.addIRIPrefixEntry(dictionary,i,p)
                    self.addORremoveIRIPrefixEntry(dictionary, iri_inp, p, 'add_entry')
                    if (False in ENTRY_ADD_OK_var) or (True in ENTRY_IGNORE_var):
                        return 'Error could not modify prefixes from ' + str(from_prefixes) + ' to ' + str(to_prefixes)
            else:
                return 'Error IRI(input) does not correspond to var from_prefixes ' + str(iri_inp) + ' , ' + str(from_prefixes)

            return 'Success'

        msg_1=None
        msg_2=None

        #Case1
        if (not None_1) and (None_2) and (not None_3) and (None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case1')
            msg_1 = modify_iri(iri_from_val,iri_to_val,dictionary)

        #Case2
        elif (not None_1) and (None_2) and (not None_3) and (not None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case2')
            msg_1 = modify_iri(iri_from_val, iri_to_val,dictionary)
            if 'Error' not in msg_1:
                msg_2 = modify_prefixes(iri_to_val,prefixes_from_val,prefixes_to_val,dictionary)

        #Case3
        elif (None_1) and (not None_2) and (None_3) and (not None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case3')

            iri_keys = []

            for iri_key in dictionary.keys():
                prefixes_of_iri_key =  dictionary[iri_key][0]
                #if prefixes_of_iri_key.issubset(prefixes_from_val) and prefixes_from_val.issubset(prefixes_of_iri_key):
                flag = set()
                if len(prefixes_of_iri_key) == len(prefixes_from_val):
                    for c, p in enumerate(prefixes_of_iri_key):
                        if prefixes_from_val[c] == p:
                            flag.add(True)
                        else:
                            flag.add(False)
                else:
                    flag.add(False)

                if False not in flag:
                    iri_keys.append(iri_key)

            if len(iri_keys) > 1:
                msg_2 = 'Error, multiple iris found for prefixes - '+str(iri_keys)
            elif len(iri_keys) == 0:
                msg_2 = 'Error, IRI not found for the prefixes'
            else:
                msg_2 = modify_prefixes(iri_keys[0], prefixes_from_val, prefixes_to_val, dictionary)

        #Case4
        elif (not None_1) and (not None_2) and (not None_3) and (None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case4')
            msg_1 = modify_iri(iri_from_val, iri_to_val,dictionary)
            if 'Error' not in msg_1:
                msg_2 = modify_prefixes(iri_to_val,prefixes_from_val,set(),dictionary)

        #Case5
        elif (not None_1) and (not None_2) and (None_3) and (not None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case5')
            msg_2 = modify_prefixes(iri_from_val, prefixes_from_val, prefixes_to_val, dictionary)

        #Case6
        elif (not None_1) and (not None_2) and (not None_3) and (not None_4):
            #print('modifyIRIPrefixesEntry   >>>    Case6')
            msg_1 = modify_iri(iri_from_val, iri_to_val, dictionary)
            #print('msg_1',msg_1)
            if 'Error' not in msg_1:
                msg_2 = modify_prefixes(iri_to_val, prefixes_from_val, prefixes_to_val, dictionary)
                #print('msg_2', msg_2)
        #None of the cases
        else:
            LOGGER.critical('Case not dealt with/ Design fault; please contact programmer')
            self.sgnIRIPrefixesEntryIgnored.emit('', '', 'Case not dealt with/ Design fault; please contact programmer')
            return None

        error_C1 = (msg_1 is not None) and ('Error' in msg_1)
        error_C2 = (msg_2 is not None) and ('Error' in msg_2)

        if error_C1 or error_C2:
            msg_error = ''
            if error_C1:
                msg_error = msg_error + msg_1
            if error_C2:
                msg_error = msg_error + ' ; ' + msg_2

            msg_iris = 'From: '+ str(iri_from_val) +' To: '+ str(iri_to_val)
            msg_prefixes = 'From: ' + str(prefixes_from_val) + ' To: ' + str(prefixes_to_val)

            self.sgnIRIPrefixesEntryIgnored.emit(msg_iris,msg_prefixes,msg_error)
            return None
        else:
            self.sgnIRIPrefixesEntryModified.emit(iri_from_val,str(prefixes_from_val),iri_to_val,str(prefixes_to_val))
            return dictionary

    def addORremoveIRIPrefixEntry(self, dictionary, IRI_inp, Prefix_inp, inp, **kwargs):

        remove_project_iri = kwargs.get('remove_project_iri',False)
        remove_project_prefixes = kwargs.get('remove_project_prefixes', False)

        display_in_widget = kwargs.get('display_in_widget',False)

        ### cannot add standart prefixes ###

        if (Prefix_inp is not None) and (Prefix_inp in {'rdf', 'rdfs', 'xsd', 'owl'}):
            self.sgnIRIPrefixesEntryIgnored.emit(IRI_inp, Prefix_inp, 'Cannot add/remove standard prefix(es)')
            return None
        ### cannot add standart IRI ###
        if (IRI_inp is not None) and (IRI_inp in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys()):
            self.sgnIRIPrefixesEntryIgnored.emit(IRI_inp, Prefix_inp, 'Cannot add/remove standard IRI(s)')
            return None

        if inp == 'add_entry':
            self.addIRIPrefixEntry(dictionary,IRI_inp,Prefix_inp,display_in_widget=display_in_widget)
        elif inp == 'remove_entry':
            self.removeIRIPrefixEntry(dictionary,IRI_inp,Prefix_inp,remove_project_iri=remove_project_iri,\
                                      remove_project_prefixes=remove_project_prefixes,display_in_widget=display_in_widget)
        else:
            LOGGER.error('PROJECT >> addORremoveIRIPrefixEntry >> invalid command')

    def addIRIPrefixEntry(self, dictionary, iri_inp, prefix_inp, **kwargs):

        display_in_widget = kwargs.get('display_in_widget',False)

        #print('addIRIPrefixEntry    >>>')
        #if [prefix_inp-IRI'] exists => addition is not possible
        #if [prefix_inp-IRI_inp] exists => addition not needed (duplicate entry)

        #corr_iri_of_prefix_inp = self.get_iri_for_prefix(prefix_inp)

        if prefix_inp is not None:

            corr_iri_of_prefix_inp_in_dict = []

            for i in dictionary.keys():
                if prefix_inp in dictionary[i][0]:
                    corr_iri_of_prefix_inp_in_dict.append(i)

            if (len(corr_iri_of_prefix_inp_in_dict) > 0):
                if(iri_inp not in corr_iri_of_prefix_inp_in_dict):
                    self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, str('prefix already mapped with IRI-' + str(corr_iri_of_prefix_inp_in_dict)))
                    return None
                else:
                    if display_in_widget is False:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, '[IRI-prefix] entry already exists in the records')
                        return None
                    else:
                        iri_Display = self.get_iri_with_no_prefix_displayed_in_widget(dictionary)
                        if iri_Display == iri_inp:
                            self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp,'[IRI-prefix] entry already visible in table')
                            return None
                        else:
                            #make the iri visible
                            if iri_Display is None:
                                dictionary[iri_inp][2].add('display_in_widget')
                                self.sgnIRIPrefixEntryAdded.emit(iri_inp, prefix_inp, 'IRI made visible in the table')
                                return dictionary
                            if 'error_multiple_occurences' in iri_Display:
                                self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, iri_Display)
                                return None
                            else:
                                self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, 'only 1 IRI in the table may not have a prefix')
                                return None

        if (prefix_inp is None) and (iri_inp in dictionary.keys()):

            if display_in_widget is False:
                self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, '[IRI] entry already exists in the records')
                return None
            else:
                iri_Display = self.get_iri_with_no_prefix_displayed_in_widget(dictionary)
                if iri_Display == iri_inp:
                    self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, '[IRI] entry already exists in table')
                    return None
                else:
                    # make the iri visible
                    if iri_Display is None:
                        dictionary[iri_inp][2].add('display_in_widget')
                        self.sgnIRIPrefixEntryAdded.emit(iri_inp, None, 'IRI made visible in the table')
                        return dictionary
                    elif 'error_multiple_occurences' in iri_Display:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, iri_Display)
                        return None
                    else:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, 'only 1 IRI in the table may not have a prefix')
                        return None

        #C1 prefix_inp !None
        #C2 prefix_inp None
        #CA key already present
        #CB key is a new one

        if iri_inp in dictionary.keys():
            if prefix_inp is not None:
                #Case A1
                #print('Case A1')
                dictionary[iri_inp][0].append(prefix_inp)
                if 'display_in_widget' in dictionary[iri_inp][2]:
                    dictionary[iri_inp][2].remove('display_in_widget')
                self.sgnIRIPrefixEntryAdded.emit(iri_inp, prefix_inp, 'prefix added to existing IRI')
                return dictionary
            else:
                #Case A2
                #print('Case A2')
                self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, 'Nothing to add')
                return None
        else:
            if prefix_inp is not None:
                #Case B1
                #print('Case B1')
                prefixes = []
                prefixes.append(prefix_inp)
                nodes = set()
                properties = set()


                #version = iri_version

                entry = []
                entry.append(prefixes)
                entry.append(nodes)
                entry.append(properties)
                #entry.append(version)

                dictionary[iri_inp] = entry
                self.sgnIRIPrefixEntryAdded.emit(iri_inp, prefix_inp, 'prefix added to new IRI')
                return dictionary
            else:
                # Case B2
                #print('Case B2')
                prefixes = []
                nodes = set()
                properties = set()

                if display_in_widget is True:

                    iri_Display = self.get_iri_with_no_prefix_displayed_in_widget(dictionary)
                    if iri_Display is None:
                        properties.add('display_in_widget')
                    elif 'error_multiple_occurences' in iri_Display:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, None, iri_Display)
                        return None
                    else:
                        #generate a new prefix
                        new_generated_prefix = self.generate_new_prefix(dictionary)
                        prefixes.append(new_generated_prefix)

                #version = iri_version

                entry = []
                entry.append(prefixes)
                entry.append(nodes)
                entry.append(properties)
                #entry.append(version)

                dictionary[iri_inp] = entry
                self.sgnIRIPrefixEntryAdded.emit(iri_inp, None, 'new IRI added')
                return dictionary

    def addIRINodeEntry(self, dictionary, iri_inp, node_inp):

        temp = set()

        for iri in dictionary.keys():
            nodes = dictionary[iri][1]
            if node_inp in nodes:
                temp.add(iri)

        # check if node is already present
        if len(temp) > 0:
            if (len(temp) == 1) and (iri_inp in temp):
                self.sgnIRINodeEntryIgnored.emit(iri_inp, str(node_inp), 'Same entry already present in the table')
                return None
            else:
                self.sgnIRINodeEntryIgnored.emit(iri_inp, str(node_inp), 'Node mapped to another IRI-'+str(temp))
                return None

        msg = ''

        if iri_inp in dictionary.keys():
            pass
        else:
            dict_2 = self.copy_IRI_prefixes_nodes_dictionaries(dictionary, dict())
            res = self.addIRIPrefixEntry(dict_2, iri_inp, None)
            if res is None:
                self.sgnIRINodeEntryIgnored.emit(iri_inp, str(node_inp), 'Failed to add IRI to the table.')
                return None
            else:
                self.addIRIPrefixEntry(dictionary, iri_inp, None)
                msg = str('IRI added-'+iri_inp+'; ')

        dictionary[iri_inp][1].add(node_inp)
        msg = msg + str('node mapped to IRI-'+iri_inp)

        self.sgnIRINodeEntryAdded.emit(iri_inp, str(node_inp), msg)
        return dictionary

    def removeIRIPrefixEntry(self, dictionary, iri_inp, prefix_inp, **kwargs):

        remove_project_IRI = kwargs.get('remove_project_IRI',False)
        remove_project_prefixes = kwargs.get('remove_project_prefixes',False)

        display_in_widget = kwargs.get('display_in_widget', False)

        # iri_inp does not exist => deletion not possible as key is absent
        #prefix_inp is None
            # nodes are mapped to IRI_inp =>  deletion not possible as nodes are linked to the IRI
        # prefix_inp is not None
            # [prefix_inp-iri_inp] does not exist => prefix not mapped with this IRI

        #print('removeIRIPrefixEntry >>>',iri_inp, ' - ',prefix_inp)

        if iri_inp not in dictionary.keys():
            self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, 'IRI is not present in the entry')
            return None

        if prefix_inp is None:
            if len(dictionary[iri_inp][1]) > 0:  # attempt to delete entire IRI record
                if display_in_widget is False:
                    self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp,
                                                         'Nodes are mapped to this IRI, deletion not possible. However it can be modified')
                    return None
                else:
                    #remove all prefixes
                    #disp->!disp
                    dictionary[iri_inp][0].clear()
                    if 'display_in_widget' in dictionary[iri_inp][2]:
                        dictionary[iri_inp][2].remove('display_in_widget')

                    self.sgnIRIPrefixEntryRemoved.emit(iri_inp, None, 'IRI removed from table')
                    return dictionary

            if remove_project_IRI is False:
                if 'Project_IRI' in dictionary[iri_inp][2]:
                    # if iri_inp == self.iri:
                    self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp,
                                                         'cannot remove project IRI; project IRI can only be modified')
                    return None
            # remove iri_inp i.e. a key
            dictionary.pop(iri_inp)
            self.sgnIRIPrefixEntryRemoved.emit(iri_inp, None, 'IRI removed from entry')
            return dictionary
        else:
            if prefix_inp not in dictionary[iri_inp][0]:
                self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, 'prefix not mapped with this IRI')
                return None
            if display_in_widget is False:
                # remove prefix_inp from prefixes of iri_inp
                dictionary[iri_inp][0].remove(prefix_inp)
                self.sgnIRIPrefixEntryRemoved.emit(iri_inp, prefix_inp, 'Prefix is no longer mapped to this IRI')
                return dictionary
            else:
                if len(dictionary[iri_inp][0]) > 1:
                    # remove prefix_inp from prefixes of iri_inp
                    dictionary[iri_inp][0].remove(prefix_inp)
                    self.sgnIRIPrefixEntryRemoved.emit(iri_inp, prefix_inp, 'Prefix is no longer mapped to this IRI')
                    return dictionary
                elif len(dictionary[iri_inp][0]) == 1:

                    iri_Display = self.get_iri_with_no_prefix_displayed_in_widget(dictionary)
                    if iri_Display is None:
                        dictionary[iri_inp][0].remove(prefix_inp)
                        dictionary[iri_inp][2].add('display_in_widget')
                        self.sgnIRIPrefixEntryRemoved.emit(iri_inp, prefix_inp, 'Prefix is no longer mapped to this IRI; This IRI is the only IRI in the table without a prefix')
                        return dictionary
                    elif 'error_multiple_occurences' in iri_Display:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, iri_Display)
                        return None
                    else:
                        self.sgnIRIPrefixesEntryIgnored.emit(iri_inp, prefix_inp, 'Cannot remove prefix as there is another IRI-'+str(iri_Display)+'without a prefix in the table. However it can be modified.')
                        return None

                else:
                    pass

    def removeIRINodeEntry(self, dictionary, iri_inp, node_inp):

        nodes = dictionary[iri_inp][1]

        if node_inp not in nodes:
            self.sgnIRINodeEntryIgnored.emit(iri_inp, str(node_inp), str('Node not mapped to IRI'+iri_inp+', deletion not possible'))
            return None

        dictionary[iri_inp][1].remove(node_inp)

        #print('node_inp',node_inp)
        self.sgnIRINodeEntryRemoved.emit(iri_inp, str(node_inp), str('Node no longer mapped to IRI'+iri_inp))
        return dictionary

    def node_label_update_core_code(self,node):

        #print('node_label_update_core_code   >>>>>')

        old_label = node.text()

        #print(' def node_label_update_core_code     >>> old_label', old_label)

        #if prefered_prefix is None:
        new_label = GenerateNewLabel(self, node, old_label=old_label).return_label()


        #else:
            #new_label = GenerateNewLabel(self, node,prefered_prefix=prefered_prefix).return_label()

        #print(' def node_label_update_core_code     >>> new_label', new_label)

        if old_label==new_label:
            return

        CommandLabelChange(node.diagram, node, old_label, new_label).redo()

        """
        # CHANGE THE CONTENT OF THE LABEL
        self.doRemoveItem(node.diagram, node)
        node.setText(new_label)
        self.doAddItem(node.diagram, node)

        # UPDATE PREDICATE NODE STATE TO REFLECT THE CHANGES
        for n in self.predicates(node.type(), old_label):
            n.updateNode()
        for n in self.predicates(node.type(), new_label):
            n.updateNode()

        # IDENTITFY NEIGHBOURS
        if node.type() is Item.IndividualNode:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() in {Item.EnumerationNode, Item.PropertyAssertionNode}
            for n in node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                node.diagram.sgnNodeIdentification.emit(n)
            f3 = lambda x: x.type() is Item.MembershipEdge
            f4 = lambda x: Identity.Neutral in x.identities()
            for n in node.outgoingNodes(filter_on_edges=f3, filter_on_nodes=f4):
                node.diagram.sgnNodeIdentification.emit(n)

        # EMIT UPDATED SIGNAL
        node.diagram.sgnUpdated.emit()
        """

    @QtCore.pyqtSlot(str,str,str)
    def regenerate_label_of_nodes_for_iri(self,iri_inp,node_inp,diag_name):

        # input string/string

        if ((node_inp is None) or (node_inp is '')) and ((iri_inp is None) or (iri_inp is '')):
            return
        #print('def regenerate_label_of_nodes_for_iri    >>>',iri_inp,' - ',node_inp)

        #disconnect(self.sgnItemAdded, self.add_item_to_IRI_prefixes_nodes_dict)
        #disconnect(self.sgnItemRemoved, self.remove_item_from_IRI_prefixes_nodes_dict)

        if (node_inp is None) or (node_inp is ''):
            #print('node_inp is None')
            if iri_inp in self.IRI_prefixes_nodes_dict.keys():
                nodes_to_update = self.IRI_prefixes_nodes_dict[iri_inp][1]
                #print('len(nodes_to_update)',len(nodes_to_update))

                nodes_to_update_copy = []
                for node in nodes_to_update:
                    nodes_to_update_copy.append(node)

                for node in nodes_to_update_copy:
                    self.node_label_update_core_code(node)
        else:
            #print('node_inp is not None')
            for n in self.nodes():
                if diag_name is not None:
                    if (str(n) == node_inp) and (str(n.diagram.name) == diag_name):
                        self.node_label_update_core_code(n)
                        break
                else:
                    if (str(n) == node_inp):
                        self.node_label_update_core_code(n)
                        break

        #connect(self.sgnItemAdded, self.add_item_to_IRI_prefixes_nodes_dict)
        #connect(self.sgnItemRemoved, self.remove_item_from_IRI_prefixes_nodes_dict)

    def check_if_reasoner_was_active(self):

        A = len(self.unsatisfiable_classes) > 0
        B = len(self.unsatisfiable_attributes)  > 0
        C = len(self.unsatisfiable_roles)  > 0

        D = self.inconsistent_ontology is not None

        if (A is True) and (B is True) and (C is True) and (D is True):

            return 'inactive'

        else:

            if (D is True) and ((A is False) or (B is False) or (C is False)):

                return 'was_unsatisfiable'

            elif (D is False) :

                return 'was_inconsistent'


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

        #print('self.nodes_of_unsatisfiable_entities',self.nodes_of_unsatisfiable_entities)

        for node_or_str in self.nodes_of_unsatisfiable_entities:

            if str(type(node_or_str)) != '<class \'str\'>':

                node_or_str.selection.setBrush(self.brush_orange)
                # node.updateNode(valid=False)
                node_or_str.setCacheMode(node_or_str.NoCache)
                node_or_str.setCacheMode(node_or_str.DeviceCoordinateCache)

                # SCHEDULE REPAINT
                node_or_str.update(node_or_str.boundingRect())

        for d in self.diagrams():
            self.diagram(d.name).sgnUpdated.emit()

    def check_if_node_is_present_in_set(self,node,set):

        list_inp = list(set)

        for e in list_inp:
            if node.id_with_diag is None:
                if str(node) in str(list_inp):
                    return True
            else:
                if e.id_with_diag == node.id_with_diag:
                    return True

        return False

    def getOWLtermfornode(self, node):

        # looks up the dict for the raw term and then..
        # returns the string portion without the IRI and special characters

        abs_nodes = self.nodes()

        for diag, val_in_diag in self.converted_nodes.items():
            #print('diag, val_in_diag',diag, val_in_diag)
            for nd in val_in_diag:

                abs_nd = None
                for i in abs_nodes:
                    #if i.id == nd:
                    if (i.id_with_diag == str(diag + '-' + nd)):
                        abs_nd = i
                        break

                if (val_in_diag[nd] is not None) and \
                    ((str(diag + '-' + nd) == node.id_with_diag) or ((abs_nd is not None) and (abs_nd.text() == node.text()))):
                    # ((nd==node.id) or ((abs_nd is not None) and (abs_nd.text()==node.text()))):
                    if str(type(val_in_diag[nd])) == '<class \'list\'>':

                        return_list = []
                        for ele in val_in_diag[nd]:
                            java_class = str(val_in_diag[nd])[2:str(val_in_diag[nd]).index(' ')]
                            cast(autoclass(java_class), ele)
                            detach()

                            return_list.append(ele.toString())

                        return return_list
                    else:
                        java_class = str(val_in_diag[nd])[1:str(val_in_diag[nd]).index(' ')]
                        cast(autoclass(java_class), val_in_diag[nd])
                        detach()

                        return val_in_diag[nd].toString()

        return None

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
        #print('Project >>> doAddItem')
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
        #print('Project >>> doRemoveItem')
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
                    #k = OWLText(item.text())
                    k = item.text().replace('\n','')
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
            #name = OWLText(name)
            name = name.replace('\n','')
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
                            #collection.update(self[K_PREDICATE][i][j][K_NODE][diagram.name])
                            if diagram.name in self[K_PREDICATE][i][j][K_NODE]:   #Ashwin
                                collection.update(self[K_PREDICATE][i][j][K_NODE][diagram.name])

                return collection

            if item and not name:

                collection = set()

                if item in self[K_PREDICATE]:    #Ashwin
                    if not diagram:
                        for i in self[K_PREDICATE][item]:
                            collection.update(*self[K_PREDICATE][item][i][K_NODE].values())
                    else:
                        for i in self[K_PREDICATE][item]:
                            #collection.update(self[K_PREDICATE][item][i][K_NODE][diagram.name])
                            if diagram.name in self[K_PREDICATE][item][i][K_NODE]:   #Ashwin
                                collection.update(self[K_PREDICATE][item][i][K_NODE][diagram.name])
                return collection

            if not item and name:

                collection = set()
                #name = OWLText(name)
                name = name.replace('\n','')

                if not diagram:
                    for i in self[K_PREDICATE]:
                        if name in self[K_PREDICATE][i]:  #Ashwin
                            collection.update(*self[K_PREDICATE][i][name][K_NODE].values())
                else:
                    for i in self[K_PREDICATE]:
                        if name in self[K_PREDICATE][i]:  # Ashwin
                            if diagram.name in self[K_PREDICATE][i][name][K_NODE]:  # Ashwin
                                collection.update(self[K_PREDICATE][i][name][K_NODE][diagram.name])

                return collection

            if item and name:

                name = name.replace('\n','')
                #name = OWLText(name)
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
                    #k = OWLText(item.text())
                    k = item.text().replace('\n','')
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
            #name = OWLText(name)
            name = name.replace('\n','')
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
        #name = OWLText(name)
        name = name.replace('\n','')
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

        self.old_dictionary = None
        self.new_dictionary = None

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

    def merge_prefixes(self, home_dictionary, foreign_prefixes, iri_key):

        old_display_in_widget = ('display_in_widget' in home_dictionary[iri_key][2])

        if old_display_in_widget is False:

            all_home_prefixes = []

            for iri in home_dictionary.keys():

                prefixes = home_dictionary[iri][0]

                if prefixes is not None:
                    all_home_prefixes.extend(prefixes)

            old_prefixes = home_dictionary[iri_key][0]

            new_prefixes = []

            new_prefixes.extend(old_prefixes)

            #print('all_home_prefixes',all_home_prefixes)

            foreign_prefixes_reversed = []

            for pr_foreign in foreign_prefixes:
                foreign_prefixes_reversed.insert(0,pr_foreign)

            for pr_foreign in foreign_prefixes_reversed:

                if pr_foreign not in all_home_prefixes:
                    #print('pr_foreign not in all_home_prefixes-',pr_foreign)
                    new_prefixes.insert(0,pr_foreign)

            home_dictionary[iri_key][0] = new_prefixes

            #print('old_prefixes',old_prefixes)
            #print('new_prefixes',new_prefixes)

    #not used
    def append_foreign_nodes_2(self, home_dictionary, foreign_nodes, iri_key):

        #home_nodes = home_dictionary[iri_key][1]
        #new_home_nodes = set()

        for n in foreign_nodes:
            self.project.iri_of_imported_nodes.append(iri_key)
            self.project.iri_of_imported_nodes.append(n.remaining_characters)

        #home_dictionary[iri_key][1] = new_home_nodes

    def append_foreign_nodes(self, home_dictionary, foreign_nodes, iri_key):

        home_nodes = home_dictionary[iri_key][1]

        #print('home_nodes',home_nodes)

        new_home_nodes = set()

        new_home_nodes = new_home_nodes.union(home_nodes)
        new_home_nodes = new_home_nodes.union(foreign_nodes)

        #print('new_home_nodes', new_home_nodes)

        home_dictionary[iri_key][1] = new_home_nodes

    def merge_properties(self, home_dictionary, foreign_properties, iri_key, home_contains_display_in_widget):

        home_properties = home_dictionary[iri_key][2]

        new_home_properties = set()

        new_home_properties = new_home_properties.union(home_properties)

        for p in foreign_properties:
            if home_contains_display_in_widget is True:
                if (p != 'Project_IRI') and (p != 'display_in_widget'):
                    new_home_properties.add(p)
            else:
                if (p != 'Project_IRI'):
                    new_home_properties.add(p)

        home_dictionary[iri_key][2] = new_home_properties

        #print('home_properties',home_properties)
        #print('new_home_properties',new_home_properties)

    def merge_IRI_prefixes_nodes_dictionary(self):

        other_dictionary = self.project.copy_IRI_prefixes_nodes_dictionaries(self.other.IRI_prefixes_nodes_dict, dict())
        home_dictionary = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
        home_dictionary_old = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
        #self.old_dictionary = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

        home_contains_display_in_widget = False

        for home_iri in home_dictionary.keys():
            home_properties = home_dictionary[home_iri][2]
            if 'display_in_widget' in home_properties:
                home_contains_display_in_widget = True
                break


        iris_to_update = []

        for foreign_iri in other_dictionary.keys():

            iris_to_update.append(foreign_iri)

            foreign_iri_entry = other_dictionary[foreign_iri]

            foreign_prefixes = foreign_iri_entry[0]
            foreign_nodes = foreign_iri_entry[1]
            foreign_properties = foreign_iri_entry[2]

            #print('')
            #print('foreign_iri',foreign_iri)
            #print('foreign_prefixes',foreign_prefixes)
            #print('foreign_nodes', foreign_nodes)
            #print('foreign_properties', foreign_properties)

            if foreign_iri not in home_dictionary.keys():

                #print('foreign_iri not in home_dictionary.keys()')

                empty_prefixes = []
                empty_nodes = set()
                empty_properties = set()

                value = []

                value.append(empty_prefixes)
                value.append(empty_nodes)
                value.append(empty_properties)

                home_dictionary[foreign_iri] = value

            self.merge_prefixes(home_dictionary, foreign_prefixes, foreign_iri)
            self.append_foreign_nodes(home_dictionary, foreign_nodes, foreign_iri)
            self.merge_properties(home_dictionary, foreign_properties, foreign_iri, home_contains_display_in_widget)

            #print('home_dictionary[foreign_iri][0]',home_dictionary[foreign_iri][0])
            #print('home_dictionary[foreign_iri][1]', home_dictionary[foreign_iri][1])
            #print('home_dictionary[foreign_iri][2]', home_dictionary[foreign_iri][2])

        self.commands.append(CommandProjectDisconnectSpecificSignals(self.project))
        self.commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project,home_dictionary_old,home_dictionary,iris_to_update,None))
        self.commands.append(CommandProjectConnectSpecificSignals(self.project))

    def mergeDiagrams(self):
        """
        Perform the merge of the diagrams by importing all the diagrams in the 'other' project in the loaded one.
        """
        diagrams_selection_dialog = DiagramsSelectionDialog(self.other, self.session)
        diagrams_selection_dialog.exec_()
        self.selected_diagrams = diagrams_selection_dialog.diagrams_selected

        #for diagram in self.other.diagrams():
        for diagram in self.selected_diagrams:
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

        #self.project.iri_of_imported_nodes = []

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

            self.merge_IRI_prefixes_nodes_dictionary()

            #print('self.project.iri_of_imported_nodes',self.project.iri_of_imported_nodes)

            self.mergeDiagrams()

            #print('self.project.iri_of_imported_nodes', self.project.iri_of_imported_nodes)

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