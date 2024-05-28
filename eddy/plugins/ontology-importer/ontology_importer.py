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

import ast
import os
import sqlite3
import sys
import textwrap
from typing import Optional

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.diagram import CommandDiagramResize, CommandDiagramAdd
from eddy.core.commands.edges import CommandEdgeAdd, CommandEdgeBreakpointAdd, \
    CommandEdgeBreakpointMove, CommandEdgeBreakpointRemove
from eddy.core.commands.iri import CommandChangeIRIOfNode
from eddy.core.commands.iri import CommandIRIAddAnnotationAssertion
from eddy.core.commands.nodes import CommandNodeAdd, CommandNodeSetDepth
from eddy.core.commands.project import CommandProjectAddAnnotationProperty, CommandProjectAddPrefix
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.functions.fsystem import fremove
from eddy.core.functions.misc import snapF, first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.nodes.attribute import AttributeNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.items.nodes.complement import ComplementNode
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.datatype_restriction import DatatypeRestrictionNode
from eddy.core.items.nodes.disjoint_union import DisjointUnionNode
from eddy.core.items.nodes.domain_restriction import DomainRestrictionNode
from eddy.core.items.nodes.enumeration import EnumerationNode
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.items.nodes.has_key import HasKeyNode
from eddy.core.items.nodes.individual import IndividualNode
from eddy.core.items.nodes.intersection import IntersectionNode
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.items.nodes.property_assertion import PropertyAssertionNode
from eddy.core.items.nodes.range_restriction import RangeRestrictionNode
from eddy.core.items.nodes.role import RoleNode
from eddy.core.items.nodes.role_chain import RoleChainNode
from eddy.core.items.nodes.role_inverse import RoleInverseNode
from eddy.core.items.nodes.union import UnionNode
from eddy.core.items.nodes.value_domain import ValueDomainNode
from eddy.core.jvm import getJavaVM
from eddy.core.loaders.owl2 import OwlOntologyImportSetWorker
from eddy.core.owl import (
    AnnotationAssertion,
    IllegalNamespaceError,
    Facet, ImportedOntology,
)
from eddy.core.owl import IRI
from eddy.core.owl import Literal
from eddy.core.plugin import AbstractPlugin
from eddy.ui.file import FileDialog
from eddy.ui.forms import NewDiagramForm
from eddy.ui.progress import BusyProgressDialog

K_IMPORTS_DB = '@data/imports.sqlite'
K_SCHEMA_SCRIPT = """
PRAGMA user_version = {version};

CREATE TABLE IF NOT EXISTS ontology (
    iri              TEXT,
    version          TEXT,
    PRIMARY KEY (iri, version)
);

CREATE TABLE IF NOT EXISTS project (
    iri              TEXT,
    version          TEXT,
    PRIMARY KEY (iri, version)
);

CREATE TABLE IF NOT EXISTS importation (
    project_iri      TEXT,
    project_version  TEXT,
    ontology_iri     TEXT,
    ontology_version TEXT,
    session_id       TEXT,
    PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version),
    FOREIGN KEY (project_iri, project_version)
        REFERENCES project(iri, version),
    FOREIGN KEY (ontology_iri, ontology_version)
        REFERENCES ontology(iri, version)
);

CREATE TABLE IF NOT EXISTS axiom (
    axiom            TEXT,
    type_of_axiom    TEXT,
    manch_axiom       TEXT,
    ontology_iri     TEXT,
    ontology_version TEXT,
    iri_dict         TEXT,
    PRIMARY KEY (axiom, ontology_iri, ontology_version),
    FOREIGN KEY (ontology_iri, ontology_version)
        REFERENCES ontology(iri, version)
);

CREATE TABLE IF NOT EXISTS drawn (
    project_iri      TEXT,
    project_version  TEXT,
    ontology_iri     TEXT,
    ontology_version TEXT,
    axiom            TEXT,
    session_id       TEXT,
    PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version, axiom),
    FOREIGN KEY (project_iri, project_version, ontology_iri, ontology_version, session_id)
        REFERENCES importation(project_iri, project_version,
                               ontology_iri, ontology_version,
                               session_id)
        ON DELETE CASCADE,
    FOREIGN KEY (axiom, ontology_iri, ontology_version)
        REFERENCES axiom(axiom, ontology_iri, ontology_version)
);
"""


class OntologyImporterPlugin(AbstractPlugin):

    def __init__(self, spec, session):
        """
        Initialize the plugin.
        :type spec: PluginSpec
        :type session: session
        """
        super().__init__(spec, session)
        self.afwset = set()
        self.vm = None
        self.space = DiagramPropertiesForm.MinSpace
        self.filePath = None

    def printConceptNode(self, iri, x, y, diagram):

        QtCore.QCoreApplication.processEvents()
        ## AVOID OVERLAPPING ##
        while not self.isEmpty(x, y, diagram):
            x = x+self.space

        ## AVOID SPACE EXCEEDING ##
        sceneRect = diagram.sceneRect()
        width = sceneRect.width()
        ## if x out of scene, increase scene width
        if x >= width or x <= width:

            size2 = width + self.space
            sceneRect.width = size2
            self.session.undostack.push(CommandDiagramResize(diagram, QtCore.QRectF(-size2 / 2, -size2 / 2, size2, size2)))


        ## DEFINE CONCEPT NODE ##
        classs = ConceptNode(iri=IRI(iri), diagram=diagram)
        classs.iri = IRI(iri)
        classs.setPos(x, y)

        ## CALL CommandAddNode TO PRINT NODE AND ADD IT TO THE ONTOLOGY EXPLORER ##

        self.session.undostack.push(CommandNodeAdd(diagram, classs))

        #print(iri)
        return classs

    def printISA(self, source_iri, target_iri, diagram):
        QtCore.QCoreApplication.processEvents()

        ## GET SOURCE NODE ##
        source_node = self.findNode(source_iri, diagram)

        ## GET TARGET NODE ##
        target_node = self.findNode(target_iri, diagram)

        ## ADD ISA ##
        isa = diagram.factory.create(Item.InclusionEdge, source=source_node, target=target_node)
        source_node.addEdge(isa)
        target_node.addEdge(isa)


        ## CALL CommandEdgeAdd TO ADD ISA ##

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))
        if source_node.pos().x() != target_node.pos().x():

            #y = source_node.pos().y() + (target_node.pos().y() - source_node.pos().y())/2
            y = target_node.pos().y() + 40

            bp1 = QtCore.QPointF(source_node.pos().x(), y)
            b1 = CommandEdgeBreakpointAdd(diagram, isa, 0, bp1)

            bp2 = QtCore.QPointF(target_node.pos().x(), y)
            b2 = CommandEdgeBreakpointAdd(diagram, isa, 1, bp2)

            self.session.undostack.push(b1)
            self.session.undostack.push(b2)


    def findNode(self, iri, diagram):

        ### FIND NODE BY IRI IN THE DIAGRAM ###
        for el in diagram.items():
            QtCore.QCoreApplication.processEvents()

            if el.isNode() and el.type() == Item.ConceptNode and str(iri) == str(el.iri):

                return el
        # IF NOT FOUND, RETURN 'NULL'
        return 'null'

    def isEmpty(self, x, y, diagram):

        ### CHECK WHETHER POSITION OF THE DIAGRAM IS EMPTY (ACCURATE) ###
        for el in diagram.items():
            QtCore.QCoreApplication.processEvents()

            if el.isNode() and el.type() == Item.ConceptNode and el.pos().y() == y and abs(el.pos().x() - x) < 113.25:
                return False
        return True

    def getLevel(self, c, p):
        QtCore.QCoreApplication.processEvents()

        ### CREATE TREE ENTRY FOR THE NODE ###
        # if node doesn't exist, OR is a root, AND his father is not a duplicate
        if (c not in self.tree.keys() or p == 'Thing' or p in self.roots) and 'Duplicate@' not in str(p):

            lev = self.tree[p]['level']
            set_of_sib = self.tree[p]['children']
            self.tree[c] = {'children': [], 'level': lev+1, 'parent': p, 'siblings': set_of_sib}

            ## GET CHILDREN OF THE NODE ##
            for ax in self.axioms:
                QtCore.QCoreApplication.processEvents()
                if isinstance(ax, self.OWLSubClassOfAxiom):
                    if not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous():

                        if 'Duplicate@' in c:
                            dupl_srt = c.find('Duplicate@')
                            if str(ax.getSuperClass().getIRI()) == c[0:dupl_srt]:

                                sub_element = ax.getSubClass()
                                # print(sub_element)
                                sub_iri = str(sub_element.getIRI())

                                if sub_iri not in self.tree[c]['children']:
                                    self.tree[c]['children'].append(sub_iri)
                        else:
                            if str(ax.getSuperClass().getIRI()) == c:

                                sub_element = ax.getSubClass()
                                # print(sub_element)
                                sub_iri = str(sub_element.getIRI())

                                if sub_iri not in self.tree[c]['children']:
                                    self.tree[c]['children'].append(sub_iri)

            ### RECURSIVELY VISIT ALL THE CHILDREN OF THE CHILDREN ###
            for ch in self.tree[c]['children']:
                self.getLevel(ch, c)

        else:
            # if node already in the tree with a different father, OR father is a duplicate
            if (c in self.tree.keys() and p != self.tree[c]['parent']) or 'Duplicate@' in str(p):

                # check number of duplicates to create duplicate_iri
                duplicate_num = 1 + sum(map(lambda x: c+'Duplicate@' in x, list(self.tree.keys())))
                c_dup = c + 'Duplicate@' + str(duplicate_num)

                lev = self.tree[p]['level']
                # replace child_iri with duplicate_iri in father's children
                children_replaced = [c_dup if x == c else x for x in self.tree[p]['children']]
                self.tree[p]['children'] = children_replaced

                set_of_sib = self.tree[p]['children']

                self.tree[c_dup] = {'children': [], 'level': lev + 1, 'parent': p, 'siblings': set_of_sib}

                # change set of siblings in other children of the current father
                for sib in set_of_sib:
                    QtCore.QCoreApplication.processEvents()

                    if sib in self.tree.keys() and self.tree[sib]['parent'] == p:
                        self.tree[sib]['siblings'] = set_of_sib

                ## GET CHILDREN OF THE NODE ##
                for ax in self.axioms:
                    QtCore.QCoreApplication.processEvents()

                    if isinstance(ax, self.OWLSubClassOfAxiom):
                        if not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous():

                            if str(ax.getSuperClass().getIRI()) == c:

                                sub_element = ax.getSubClass()
                                # print(sub_element)
                                sub_iri = str(sub_element.getIRI())

                                if sub_iri not in self.tree[c_dup]['children']:
                                    self.tree[c_dup]['children'].append(sub_iri)

                ### RECURSIVELY VISIT ALL THE CHILDREN OF THE CHILDREN ###
                for ch in self.tree[c_dup]['children']:
                    self.getLevel(ch, c_dup)

    def getTree(self):
        QtCore.QCoreApplication.processEvents()

        ### GET ROOTS OF HIERARCHY ###
        self.roots = []
        not_roots = []
        # GET NOT_ROOTS
        for ax in self.axioms:
            QtCore.QCoreApplication.processEvents()

            ## CONSIDER SUBCLASS_OF AXIOMS -> SUBCLASSES: NOT ROOTS ##
            if isinstance(ax, self.OWLSubClassOfAxiom):
                if not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous():

                    sub_element = ax.getSubClass()
                    sub_iri = str(sub_element.getIRI())

                    if sub_iri in self.roots:
                        self.roots.remove(sub_iri)
                    if sub_iri not in not_roots:
                        not_roots.append(sub_iri);
        # GET ROOTS
        for ax in self.axioms:
            QtCore.QCoreApplication.processEvents()

            ## CONSIDER SUBCLASS_OF AXIOMS -> SUPCLASSES: ROOTS ##
            if isinstance(ax, self.OWLSubClassOfAxiom):
                if not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous():

                    sup_element = ax.getSuperClass()
                    sup_iri = str(sup_element.getIRI())

                    if sup_iri not in not_roots and sup_iri not in self.roots:
                        self.roots.append(sup_iri)

            ## CONSIDER DECLARATION AXIOMS -> CLASSES: ROOTS ##
            if isinstance(ax, self.OWLDeclarationAxiom) and ax.getEntity().isType(self.EntityType.CLASS):

                cl = ax.getEntity()
                cl_iri = str(cl.getIRI())

                if cl_iri not in not_roots and cl_iri not in self.roots:
                    self.roots.append(cl_iri)

        if 'http://www.w3.org/2002/07/owl#Thing' in self.roots:
            self.roots.remove('http://www.w3.org/2002/07/owl#Thing')
        #print('roots:', self.roots)

        ### INITIALIZE TREE AS A DICT ###

        self.tree = {}
        self.tree['Thing'] = {'children': [], 'level': 0, 'parent': 'none', 'siblings': []}
        for el in self.roots:
            self.tree[el] = {'children': [], 'level': 0, 'parent': 'none', 'siblings': []}


        for ax in self.axioms:
            QtCore.QCoreApplication.processEvents()

            ## CONSIDER SUBCLASS_OF AXIOMS ##
            if isinstance(ax, self.OWLSubClassOfAxiom):
                if not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous():

                    ### GET OWLThing CHILDREN ###
                    if ax.getSuperClass().isOWLThing():

                        sub_element = ax.getSubClass()
                        sub_iri = str(sub_element.getIRI())
                        # if duplicate
                        if (sub_iri in self.tree.keys() and 'Thing' != self.tree[sub_iri]['parent']):
                            # check number of duplicates to create duplicate_iri
                            duplicate_num = 1 + sum(
                                map(lambda x: sub_iri + 'Duplicate@' in x, list(self.tree.keys())))
                            c_dup = sub_iri + 'Duplicate@' + str(duplicate_num)


                            if sub_iri not in self.tree['Thing']['children'] and c_dup not in self.tree['Thing']['children']:
                                self.tree['Thing']['children'].append(c_dup)
                                self.tree[c_dup] = {'children': [], 'level': 1, 'parent': 'Thing', 'siblings': []}

                        else:
                            if sub_iri not in self.tree['Thing']['children']:

                                self.tree['Thing']['children'].append(sub_iri)
                                self.tree[sub_iri] = {'children': [], 'level': 1, 'parent': 'Thing', 'siblings': []}


                    ### GET ROOTS CHILDREN ###
                    if str(ax.getSuperClass().getIRI()) in self.roots:

                        root_iri = str(ax.getSuperClass().getIRI())

                        sub_element = ax.getSubClass()
                        sub_iri = str(sub_element.getIRI())

                        if (sub_iri in self.tree.keys() and root_iri != self.tree[sub_iri]['parent']):
                            # check number of duplicates to create duplicate_iri
                            duplicate_num = 1 + sum(
                                map(lambda x: sub_iri + 'Duplicate@' in x, list(self.tree.keys())))
                            c_dup = sub_iri + 'Duplicate@' + str(duplicate_num)

                            if sub_iri not in self.tree[root_iri]['children'] and c_dup not in self.tree[root_iri]['children']:

                                self.tree[root_iri]['children'].append(c_dup)
                                self.tree[c_dup] = {'children': [], 'level': 1, 'parent': root_iri, 'siblings': []}

                        else:

                            if sub_iri not in self.tree[root_iri]['children']:

                                self.tree[root_iri]['children'].append(sub_iri)
                                self.tree[sub_iri] = {'children': [], 'level': 1, 'parent': root_iri, 'siblings': []}


        ### RECURSIVELY GET THE CHILDREN OF THE CHILDREN ###
        if len(self.tree['Thing']['children']) != 0:

            for c in self.tree['Thing']['children']:

                self.tree[c]['siblings'] = self.tree['Thing']['children']
                self.getLevel(c, 'Thing')

            for r in self.roots:

                self.tree[r]['siblings'] = self.roots
                for c in self.tree[r]['children']:
                    self.tree[c]['siblings'] = self.tree[r]['children']
                    self.getLevel(c, r)
        else:

            self.tree.pop('Thing')
            for r in self.roots:
                self.tree[r]['siblings'] = self.roots
                for c in self.tree[r]['children']:
                    self.tree[c]['siblings'] = self.tree[r]['children']
                    self.getLevel(c, r)

        self.tree['none'] = {'children': self.roots, 'level': 0, 'parent': 'n', 'siblings': []}
        # print(self.tree)

        ### REVERSE-SORT OF THE TREE -> leaves first ###
        sorted_tree = sorted(self.tree.items(), key=lambda x: (x[1]['level'], x[1]['parent']), reverse=True)

        ### GET MAX DEPTH FROM THE SORTED TREE ###
        max_depth = sorted_tree[0][1]['level']

        return sorted_tree

    def getWidthOfLevel(self, y, diagram):

        ## GET max X GIVEN A Y ##
        Xs = []
        for el in diagram.items():
            QtCore.QCoreApplication.processEvents()

            if el.isNode() and el.type() == Item.ConceptNode and el.pos().y() == y:
                Xs.append(el.pos().x())
        return max(Xs) if len(Xs) != 0 else 0

    def getMinMaxSib(self, father, drawn, diagram):

        Xs = []
        ## GET ALL THE CHILDREN'S POSITIONS ##
        for child in self.tree[father]['children']:
            if child in drawn:
                child_node = self.findNode(child, diagram)
                x_child = child_node.pos().x()
                Xs.append(int(x_child))
        positions = []

        ## GET ALL THE POSITIONS IN BETWEEN THE FIRST AND LAST CHILD DRAWN ##
        # SO THAT BROTHERS WITH NO CHILDREN FILL THE EMPTY SPACES IN BETWEEN
        if len(Xs) > 0:
            x_min = min(Xs)
            x_max = max(Xs)
            positions = range(x_min+self.space, x_max, self.space)

        return positions

    def draw(self, node, diagram, x, y, drawn):

        n_iri = node[0]
        n_info = node[1]

        father_iri = n_info['parent']
        ## determine Y based on level ##
        y = n_info['level']*self.space

        ## determine x ##
        # check if any sibling is already drawn, to determine x
        no_drawn = True
        for sib_iri in n_info['siblings']:

            if sib_iri in drawn:
                no_drawn = False
                break;

        # if no sibling drawn and no children -> X is the max between the max depth of the current and the higher levels
        if len(n_info['children']) == 0 and no_drawn:
            max_x = max(self.getWidthOfLevel(y, diagram), self.getWidthOfLevel(y-self.space, diagram))
            for l in range(0, n_info['level']):
                max_x = max(max_x, self.getWidthOfLevel(l*self.space, diagram))
            x = max_x + self.space

        ### CHILDREN ###
        if n_iri not in drawn and n_iri != 'none':
            ### IF CHILDREN, DRAW CHILDREN BEFORE ###
            if len(self.tree[n_iri]['children']) > 0:
                for child_iri in self.tree[n_iri]['children']:

                    if child_iri not in drawn:
                        # IF CHILD NOT DRAWN
                        child_idx = [idx for idx, element in enumerate(self.sorted_tree) if
                                     element[0] == child_iri][0]
                        child = self.sorted_tree[child_idx]
                        x_child = self.getWidthOfLevel(y + self.space, diagram) + self.space
                        ## DRAW CHILD
                        self.draw(child, diagram, x_child, y, drawn)

        ### THEN, IF NODE NOT DRAWN, PRINT NODE ###
        if n_iri not in drawn and n_iri != 'none' and n_iri != 'Thing':

            # IF NODE HAS CHILDREN
            if len(self.tree[n_iri]['children']) > 0:

                ### PRINT NODE in MIDDLE_POS OF CHILDREN ###
                x_min = min([self.findNode(child_iri, diagram).pos().x()
                             for child_iri in self.tree[n_iri]['children']])
                x_max = max([self.findNode(child_iri, diagram).pos().x()
                             for child_iri in self.tree[n_iri]['children']])
                x_new = (x_max + x_min) / 2

                self.printConceptNode(n_iri, x_new, y, diagram)
                #print(n_iri)
                #print(self.tree[n_iri])
                drawn.append(n_iri)

                ### PRINT ALL ISAs ###
                for child_iri in self.tree[n_iri]['children']:
                    self.printISA(child_iri, n_iri, diagram)
            else:

                if n_iri != 'none' and n_iri != 'Thing':
                    ### PRINT NODE in X ###
                    self.printConceptNode(n_iri, x, y, diagram)
                    #print(n_iri)
                    #print(self.tree[n_iri])
                    drawn.append(n_iri)

        # check if all siblings drawn
        all_drawn = True
        for sib_iri in n_info['siblings']:

            if sib_iri not in drawn:
                all_drawn = False
                break;

        ### WHEN ALL SIBLINGS DRAWN, DRAW FATHER ###
        if all_drawn and father_iri != 'none' and father_iri != 'n' and father_iri != 'Thing' and father_iri not in drawn:

            father_idx = [idx for idx, element in enumerate(self.sorted_tree) if element[0] == father_iri][0]
            father = self.sorted_tree[father_idx]

            x_min = min([self.findNode(child_iri, diagram).pos().x()
                         for child_iri in self.tree[father_iri]['children']])
            x_max = max([self.findNode(child_iri, diagram).pos().x()
                         for child_iri in self.tree[father_iri]['children']])
            x_new = (x_max + x_min) / 2

            self.draw(father, diagram, x_new, y, drawn)

        ### OTHERWISE, SIBLINGS ###
        else:
            if len(n_info['siblings']) > 1:
                # IF HAS SIBLINGS
                ## FIRST SIBLINGS WITH CHILDREN
                for sib_iri in n_info['siblings']:

                    if sib_iri not in drawn and sib_iri != n_iri:
                    # IF SIBLING NOT DRAWN

                        if len(self.tree[sib_iri]['children']) > 0:
                            # IF SIBLING HAS CHILDREN
                            x_sib = self.getWidthOfLevel(y, diagram) + self.space
                            sib_idx = [idx for idx, element in enumerate(self.sorted_tree) if
                                       element[0] == sib_iri][0]
                            sibling = self.sorted_tree[sib_idx]
                            ## DRAW SIBLING
                            self.draw(sibling, diagram, x_sib, y, drawn)

                ## THEN SIBLINGS WITHOUT CHILDREN TO FILL SPACES
                for sib_iri in n_info['siblings']:

                    if sib_iri not in drawn and sib_iri != n_iri:
                    # IF SIBLING NOT DRAWN
                        if len(self.tree[sib_iri]['children']) == 0:
                        # IF SIBLING DOESN'T HAVE CHILDREN

                            x_sib = self.getWidthOfLevel(y, diagram) + self.space
                            # check if empty spaces between siblings already drawn
                            positions = self.getMinMaxSib(father_iri, drawn, diagram)
                            for pos in positions:
                                if self.isEmpty(pos, y, diagram):
                                    x_sib = pos
                                    break

                            sib_idx = [idx for idx, element in enumerate(self.sorted_tree) if
                                              element[0] == sib_iri][0]
                            sibling = self.sorted_tree[sib_idx]
                            ## DRAW SIBLING IN HOLES
                            self.draw(sibling, diagram, x_sib, y, drawn)

    def getAnnotations(self):
        ### GET ANNOTATION ASSERTION AXIOMS ###
        annotations = []
        for ax in self.axioms:
            QtCore.QCoreApplication.processEvents()

            if isinstance(ax, self.OWLAnnotationAssertionAxiom):
                annotations.append(ax)
        return annotations

    def importAnnotations(self, diagram):
        rejected = []

        # FOR EACH ANNOTATION AXIOM
        self.session.undostack.beginMacro(f'Import annotations from {self.ontology_iri}')
        for ax in self.getAnnotations():
            QtCore.QCoreApplication.processEvents()
            if not self.importAnnotation(ax):
                rejected.append(ax)

        # ONTOLOGY ANNOTATIONS
        for ax in self.ontology.getAnnotations():
            QtCore.QCoreApplication.processEvents()
            if not self.importAnnotation(ax, subject=self.ontology_iri):
                rejected.append(ax)
        self.session.undostack.endMacro()

        # FEEDBACK FOR REJECTED TRIPLES
        details = []
        for ax in rejected:
            if isinstance(ax, self.OWLAnnotationAssertionAxiom):
                details.append(f"{ax.getSubject()} {ax.getProperty()} {ax.getValue()}")
            elif isinstance(ax, self.OWLAnnotation):
                details.append(f"{self.ontology_iri} {ax.getProperty()} {ax.getValue()}")
        detailsMsg = '\n'.join(details)
        msgbox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning,
            'Rejected Annotations',
            'The imported ontology contains annotations of anonymous individuals which are '
            'currently not supported. The ontology import will continue, but these annotations '
            'will be rejected.',
            QtWidgets.QMessageBox.Close,
        )
        msgbox.setDetailedText(
            'The following annotations where rejected during import:\n\n'
            f'{detailsMsg}'
        )
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.exec_()

    def importAnnotation(self, ax, subject=None):
        """Imports an OWLAPI annotation axiom in the project."""
        # GET SUBJECT
        if isinstance(ax, self.OWLAnnotation):
            if not subject:
                raise ValueError('OWLAnnotation require an explicit subject')
            subject = self.project.getIRI(subject)
        elif ax.getSubject().isIRI():
            subject = self.project.getIRI(str(ax.getSubject().asIRI().get()))
        else:  # is anonymous
            return False

        # GET PREDICATE
        predicate = self.project.getIRI(str(ax.getProperty().getIRI()))
        # Add annotation property if not already in project
        if predicate not in self.project.getAnnotationPropertyIRIs():
            command = CommandProjectAddAnnotationProperty(self.project, str(predicate))
            self.session.undostack.push(command)

        # GET VALUE
        value = ax.getValue()
        if value.isLiteral():
            jliteral = value.asLiteral().get()
            value = Literal(
                jliteral.getLiteral(),
                datatype=self.project.getIRI(str(jliteral.getDatatype().getIRI())),
                language=jliteral.getLang(),
            )
        elif value.isIRI():
            value = self.project.getIRI(str(value.asIRI().get()))
        else:  # is anonymous
            return False

        # INSTANCE OF ANNOTATION WITH IRI, PROPERTY, VALUE, LANGUAGE
        # FIXME: Why does an AnnotationAssertion not take a Literal instance????
        if isinstance(value, IRI):
            assertion = AnnotationAssertion(subject, predicate, value)
        else:
            assertion = AnnotationAssertion(
                subject,
                predicate,
                value.lexicalForm,
                language=value.language,
                type=value.datatype,
            )

        processed = set()  # To avoid adding multiple times
        # FOR EACH NODE WITH NODE.IRI == IRI
        for el in self.project.iriOccurrences():
            if el.iri in processed:
                continue
            if el.isNode() and el.type() == Item.ConceptNode and el.iri is assertion.subject:
                # ADD ANNOTATION
                command = CommandIRIAddAnnotationAssertion(self.project, el.iri, assertion)
                self.session.undostack.push(command)
                processed.add(el.iri)
        return True

    def removeDuplicateFromIRI(self, diagram):

        ### REMOVE 'Duplicate@n' FROM IRIs ###
        for el in diagram.items():
            QtCore.QCoreApplication.processEvents()

            if el.isNode() and el.type() == Item.ConceptNode and 'Duplicate@' in str(el.iri):

                old_iri = str(el.iri)
                dupl_srt = old_iri.find('Duplicate@')
                new_iri = el.iri[0:dupl_srt]
                # with the Command changes the Ontology Explorer as well
                self.session.undostack.push(
                    CommandChangeIRIOfNode(self.project, el, new_iri, old_iri))

    def importPrefixes(self):
        format = self.manager.getOntologyFormat(self.ontology)
        if format:
            prefixMap = format.getPrefixName2PrefixMap()
            currentPrefixes = self.project.getManagedPrefixes()

            for k in prefixMap.keys():
                prefix = k[:-1]
                namespace = prefixMap[k]

                if prefix and self.project.isValidPrefixEntry(prefix, namespace):
                    if prefix not in currentPrefixes:
                        command = CommandProjectAddPrefix(self.project, prefix, namespace)
                        self.session.undostack.push(command)

    def getImportedOntologies(self):
        """
        Get set of Imported Ontologies.
        """
        folder = self.File(str(os.path.expanduser('~')))
        iriMapper = self.AutoIRIMapper(folder, True)
        self.manager.getIRIMappers().add(iriMapper)

        directImports = self.ontology.getDirectImports()
        importedOnto = set()
        for imp in directImports:
            ontologyID = imp.getOntologyID()
            if not ontologyID.isAnonymous():
                ontologyIRI = ontologyID.getOntologyIRI().get().toString()
                ontologyURI = ontologyID.getOntologyIRI().get().toURI().toString()
                if ontologyID.getVersionIRI().isPresent():
                    ontologyV = ontologyID.getVersionIRI().get().toString()
                else:
                    ontologyV = None
                ontologyPath = iriMapper.getDocumentIRI(ontologyID.getOntologyIRI().get())
                if ontologyPath:
                    ontologyPath = ontologyPath.toString().replace('file:', '', 1)
                    impOnto = ImportedOntology(ontologyIRI, ontologyPath, ontologyV, True)
                    importedOnto.add(impOnto)
                else:
                    impOnto = ImportedOntology(ontologyIRI, ontologyURI, ontologyV, False)
                    importedOnto.add(impOnto)
        return importedOnto

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def doOpenOntologyFile(self, my_owl_file: Optional[str] = None):
        """
        Starts the import process by selecting an OWL 2 ontology file.
        """
        if my_owl_file:
            self.filePath = [my_owl_file]
        else:
            dialog = FileDialog(self.session)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.setNameFilters([File.Owl.value, File.Any.value])

            if dialog.exec_():
                self.filePath = dialog.selectedFiles()

        if self.filePath:
            ### SET SPACE BETWEEN ITEMS ###
            form = DiagramPropertiesForm(self.project, parent=self.session)
            if form.exec_():
                self.space = form.spacing()

                ### CREATE NEW DIAGRAM ###
                diagram = Diagram.create(form.name(), form.diagramSize(), self.project)
                connect(diagram.sgnItemAdded, self.project.doAddItem)
                connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
                connect(diagram.selectionChanged, self.session.doUpdateState)
                self.session.undostack.push(CommandDiagramAdd(diagram, self.project))
                self.session.sgnFocusDiagram.emit(diagram)

                self.vm = getJavaVM()
                if not self.vm.isRunning():
                    self.vm.initialize()
                self.vm.attachThreadToJVM()

                ### IMPORT OWL API ###
                self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
                self.MissingImportHandlingStrategy = self.vm.getJavaClass('org.semanticweb.owlapi.model.MissingImportHandlingStrategy')
                self.AutoIRIMapper = self.vm.getJavaClass('org.semanticweb.owlapi.util.AutoIRIMapper')
                self.File = self.vm.getJavaClass('java.io.File')
                self.Type = self.vm.getJavaClass('org.semanticweb.owlapi.model.AxiomType')
                self.Set = self.vm.getJavaClass('java.util.Set')
                self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
                self.Searcher = self.vm.getJavaClass('org.semanticweb.owlapi.search.Searcher')
                self.OWLObjectInverseOf = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectInverseOf')
                self.OWLEquivalence = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLEquivalentObjectPropertiesAxiom')
                self.OWLSubObjectPropertyOf = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubObjectPropertyOfAxiom')
                self.OWLSubDataPropertyOf = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubDataPropertyOfAxiom')
                self.OWLEquivalentAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLEquivalentClassesAxiom')
                self.OWLDataSomeValuesFrom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDataSomeValuesFrom')
                self.OWLSubClassOfAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubClassOfAxiom')
                self.OWLObjectUnionOf = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectUnionOf')
                self.OWLDisjointClassesAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDisjointClassesAxiom')
                self.OWLObjectSomeValuesFrom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectSomeValuesFrom')
                self.OWLObjectPropertyDomainAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectPropertyDomainAxiom')
                self.OWLObjectPropertyRangeAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectPropertyRangeAxiom')
                self.OWLEquivalentObjectProperties = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLEquivalentObjectPropertiesAxiom')
                self.OWLObjectAllValuesFrom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectAllValuesFrom')
                self.OWLRestriction = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLRestriction')
                self.OWLObjectMaxCardinality = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectMaxCardinality')
                self.OWLObjectMinCardinality = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectMinCardinality')
                self.OWLObjectComplementOf = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectComplementOf')
                self.OWLDeclarationAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDeclarationAxiom')
                self.SetOntologyID = self.vm.getJavaClass('org.semanticweb.owlapi.model.SetOntologyID')
                self.EntityType = self.vm.getJavaClass('org.semanticweb.owlapi.model.EntityType')
                self.OWLAnnotation = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAnnotation')
                self.OWLAnnotationAssertionAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAnnotationAssertionAxiom')
                self.AxiomType = self.vm.getJavaClass('org.semanticweb.owlapi.model.AxiomType')
                self.ManchesterOWLSyntaxOWLObjectRendererImpl = self.vm.getJavaClass('org.semanticweb.owlapi.manchestersyntax.renderer.ManchesterOWLSyntaxOWLObjectRendererImpl')
                self.OWLSubAnnotationPropertyOfAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubAnnotationPropertyOfAxiom')
                self.AnnotationPropertyDomainAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAnnotationPropertyDomainAxiom')
                self.AnnotationPropertyRangeAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAnnotationPropertyRangeAxiom')

                if diagram:

                    ## show progress bar while drawing hierarchy ##
                    with BusyProgressDialog('Loading Ontology', 0.5):

                        try:

                            for path in self.filePath:
                                QtCore.QCoreApplication.processEvents()

                                self.fileInstance = self.File(path)
                                QtCore.QCoreApplication.processEvents()

                                self.manager = self.OWLManager().createOWLOntologyManager()
                                config = self.manager.getOntologyLoaderConfiguration()
                                config = config.setMissingImportHandlingStrategy(
                                    self.MissingImportHandlingStrategy.SILENT)
                                self.manager.setOntologyLoaderConfiguration(config)
                                QtCore.QCoreApplication.processEvents()

                                self.ontology = self.manager.loadOntologyFromOntologyDocument(
                                    self.fileInstance)

                                if self.ontology.isAnonymous():
                                    self.ontology_iri = f'file://{expandPath(path)}'
                                    self.ontology_version = f'file://{expandPath(path)}'
                                    self.ontology.applyChange(self.SetOntologyID(
                                        self.ontology,
                                        self.IRI.create(self.ontology_iri)
                                    ))
                                else:
                                    self.ontology_iri = self.ontology.getOntologyID().getOntologyIRI().get().toString()
                                    try:
                                        self.ontology_version = self.ontology.getOntologyID().getVersionIRI().get().toString()
                                    except Exception:
                                        self.ontology_version = self.ontology_iri

                                QtCore.QCoreApplication.processEvents()

                                db_filename = expandPath(K_IMPORTS_DB)
                                dir = os.path.dirname(db_filename)
                                if not os.path.exists(dir):
                                    os.makedirs(dir)

                                db_is_new = not os.path.exists(db_filename)
                                conn = sqlite3.connect(db_filename)
                                cursor = conn.cursor()
                                QtCore.QCoreApplication.processEvents()

                                # TODO: Move to plugin init()
                                if db_is_new:
                                    conn.executescript(K_SCHEMA_SCRIPT.format(
                                        version=self.spec.get('database', 'version')))
                                    conn.commit()

                                QtCore.QCoreApplication.processEvents()

                                self.project.version = self.project.version if len(
                                    self.project.version) > 0 else '1.0'

                                importation = Importation(self.project)
                                already = importation.insertInDB(self.ontology)
                                if already:
                                    return

                                QtCore.QCoreApplication.processEvents()

                                self.df = self.OWLManager.getOWLDataFactory()

                            QtCore.QCoreApplication.processEvents()

                            ### GET ONTOLOGY AXIOMS ###
                            self.axioms = self.ontology.getAxioms()
                            QtCore.QCoreApplication.processEvents()

                            ### BUILD TREE STRUCTURE FROM AXIOMS ###
                            self.sorted_tree = self.getTree()
                            QtCore.QCoreApplication.processEvents()

                            y = -500.0
                            x = 0.0
                            drawn = []

                            ### DRAW HIERARCHY ###
                            for node in self.sorted_tree:
                                self.draw(node, diagram, x, y, drawn)

                            ## CENTER DIAGRAM ##
                            self.session.doCenterDiagram()
                            QtCore.QCoreApplication.processEvents()

                            ## SNAP TO GRID ##
                            self.session.doSnapTopGrid()
                            QtCore.QCoreApplication.processEvents()

                            ### REMOVE DUPLICATE FROM IRI ###
                            self.removeDuplicateFromIRI(diagram)
                            QtCore.QCoreApplication.processEvents()

                            ### IMPORT PREFIXES ###
                            self.importPrefixes()
                            QtCore.QCoreApplication.processEvents()

                            ### IMPORT ANNOTATIONS ###
                            self.importAnnotations(diagram)
                            QtCore.QCoreApplication.processEvents()

                            ### IMPORT IMPORTED ONTOLOGIES ###
                            imported = self.getImportedOntologies()
                            for imp in imported:
                                self.project.addImportedOntology(imp)
                                QtCore.QCoreApplication.processEvents()
                            worker = OwlOntologyImportSetWorker(self.project)
                            worker.run()
                            self.session.owlOntologyImportSize = worker.importSize
                            self.session.owlOntologyImportLoadedCount = worker.loadCount
                            if self.session.owlOntologyImportSize > self.session.owlOntologyImportLoadedCount:
                                self.session.owlOntologyImportErrors = worker.owlOntologyImportErrors

                            renderer = self.ManchesterOWLSyntaxOWLObjectRendererImpl()

                            ### COUNT PROCESSED AXIOMS ###
                            processed = []
                            not_processed = []
                            total = []
                            conn.executescript("""CREATE TABLE IF NOT EXISTS temp_drawn (
                                                project_iri      TEXT,
                                                project_version  TEXT,
                                                ontology_iri     TEXT,
                                                ontology_version TEXT,
                                                axiom            TEXT,
                                                session_id       TEXT,
                                                PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version, axiom));""")
                            conn.commit()
                            for ax in self.axioms:

                                total.append(ax)

                                if isinstance(ax, self.OWLAnnotationAssertionAxiom) or (isinstance(ax,
                                                                                                   self.OWLSubClassOfAxiom) and not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous()) or (
                                    isinstance(ax, self.OWLDeclarationAxiom) and ax.getEntity().isType(
                                    self.EntityType.CLASS)) or (
                                    isinstance(ax, self.OWLDeclarationAxiom) and ax.getEntity().isType(
                                    self.EntityType.ANNOTATION_PROPERTY)) or (
                                isinstance(ax, self.OWLSubAnnotationPropertyOfAxiom)) or (isinstance(ax, self.AnnotationPropertyDomainAxiom)) or (isinstance(ax, self.AnnotationPropertyRangeAxiom)):
                                    ### INSERT DRAWN AXIOMS IN Drawn Table ###
                                    # GET AXIOM IN Manchester Syntax #
                                    axiom = renderer.render(ax)
                                    # INSERT #
                                    conn.execute("""
                                                                insert or ignore into drawn (project_iri, project_version, ontology_iri, ontology_version, axiom, session_id)
                                                                values (?, ?, ?, ?, ?, ?)
                                                                """, (
                                    str(self.project.ontologyIRI), self.project.version,
                                    self.ontology_iri, self.ontology_version, str(ax),
                                    str(self.session)))
                                    conn.commit()
                                    conn.execute("""insert or ignore into temp_drawn (project_iri, project_version, ontology_iri, ontology_version, axiom, session_id)
                                                 values (?, ?, ?, ?, ?, ?)""",
                                                 (
                                                     str(self.project.ontologyIRI),
                                                     self.project.version,
                                                     self.ontology_iri, self.ontology_version,
                                                     str(ax),
                                                     str(self.session)))
                                    conn.commit()
                                    processed.append(ax)
                                    QtCore.QCoreApplication.processEvents()

                                else:

                                    not_processed.append(ax)

                            QtCore.QCoreApplication.processEvents()

                            conn.commit()
                            conn.close()

                        except Exception as e:
                            raise e

    def doOpenAxiomImportDialog(self):
        """
        Opens the axioms import dialog.
        """
        try:
            # TRY TO OPEN IMPORTATIONS ASSOCIATED WITH THIS PROJECT #
            importation = Importation(self.project)
            axs, not_dr, dr = importation.open()
            if not_dr:
                dialog = AxiomSelectionDialog(not_dr, self.project)
                dialog.exec_()
            else:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('No Ontology Imported')
                msgbox.setText('There is no ontology imported in the current project')
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()

        except Exception as e:

            # IF NO IMPORTATIONS ASSOCIATED WITH THIS PROJECT -> WARNING #
            print(e)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('No Ontology Imported')
            msgbox.setText('There is no ontology imported in the current project')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()

    def onNoSave(self):

        importation = Importation(self.project)
        importation.removeFromDB()
        self.onSave()

    @QtCore.pyqtSlot()
    def onSave(self):
        db = expandPath(K_IMPORTS_DB)
        if os.path.exists(db):
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            # check if there is any temporary importation
            cursor.execute(
                """SELECT name FROM sqlite_master WHERE type='table' AND name='temp_importation';""")
            temp_impo = len(cursor.fetchall()) > 0
            if temp_impo:
                # remove all the importations of the saved session from temp table -> make them permanent
                cursor.execute("delete from temp_importation where session_id = ?", (str(self.project.session),))
                conn.commit()
                cursor.execute("select * from temp_importation")
                if not cursor.fetchall():
                    # if no more temporary importations -> drop temp table
                    conn.executescript("""DROP TABLE IF EXISTS temp_importation;""")
                    conn.commit()
            # check if there is any temporary draw
            cursor.execute(
                        """SELECT name FROM sqlite_master WHERE type='table' AND name='temp_drawn';""")
            temp_drawn = len(cursor.fetchall()) > 0
            if temp_drawn:
                # remove all the drawn axioms of the saved session from temp table -> make them permanent
                cursor.execute("delete from temp_drawn where session_id = ?",
                               (str(self.project.session),))
                conn.commit()
                cursor.execute("select * from temp_drawn")
                if not cursor.fetchall():
                    # if no more temporary drawn -> drop temp table
                    conn.executescript("""DROP TABLE IF EXISTS temp_drawn;""")
                    conn.commit()
            conn.close()

    def checkDatabase(self):
        """
        Checks whether the currently stored import database is compatible
        with the current version supported by the plugin.
        """
        db = expandPath(K_IMPORTS_DB)
        if os.path.exists(db):
            # CHECK THAT VERSION IS COMPATIBLE
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            version = self.spec.getint('database', 'version')
            nversion = int(cursor.execute('PRAGMA user_version').fetchone()[0])
            upgrade_commands = {1 : """
                                BEGIN TRANSACTION;

                                UPDATE drawn
                                SET axiom = (SELECT a.func_axiom
                                    FROM axiom a
                                    WHERE a.axiom = drawn.axiom
                                      AND a.ontology_iri = drawn.ontology_iri
                                      AND a.ontology_version = drawn.ontology_version
                                    );

                                -- Scambia axiom con func_axiom nella tabella axiom

                                UPDATE axiom SET axiom = func_axiom, func_axiom = axiom;

                                -- Rinomina func_axiom

                                ALTER TABLE axiom RENAME COLUMN func_axiom TO manch_axiom;

                                COMMIT;
                                """}
            if nversion > self.spec.getint('database', 'version'):
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Error initializing plugin: {}'.format(self.name()))
                msgbox.setText(textwrap.dedent("""
                    Incompatible import database version {nversion} > {version}.<br><br>
                    This means that it was opened with a more recent version
                    of the {name} plugin.<br><br>
                    In order to use this version of the {name} plugin you will
                    need to recreate the import database.<br>
                    Do you want to proceed?<br><br>
                    <b>WARNING: this will delete all the OWL 2 imports in progress!</b>
                    """.format(version=version, nversion=nversion, name=self.name())))
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if msgbox.exec_() == QtWidgets.QMessageBox.Yes:
                    fremove(db)
                else:
                    raise DatabaseError(
                        'Incompatible import database version {} > {}'.format(nversion, version))
            else:
                while nversion != version:
                    cursor.executescript(upgrade_commands[nversion])
                    nversion = nversion + 1
                    conn.executescript("PRAGMA user_version = {version};".format(
                        version=nversion))
    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT SIGNALS/SLOTS
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnNoSaveProject, self.onNoSave)
        disconnect(self.session.sgnProjectSaved, self.onSave)

        # UNINSTALL WIDGETS FROM THE ACTIVE SESSION
        self.debug('Uninstalling OWL 2 importer controls from "view" toolbar')
        for action in self.afwset:
            self.session.widget('view_toolbar').removeAction(action)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # VERIFY EXISTING DATABASE COMPATIBILITY
        self.checkDatabase()

        # INITIALIZE THE WIDGETS
        self.debug('Creating OWL 2 importer control widgets')
        # noinspection PyArgumentList
        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/24/ic_system_update'),
            statusTip='Import OWL file', toolTip='Import OWL file',
            enabled=True, checkable=False, clicked=self.doOpenOntologyFile,
            objectName='owl2_importer_open'))
        # noinspection PyArgumentList
        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/48/ic_format_list_bulleted_black'),
            statusTip='Select axioms from imported ontologies',
            toolTip='Select axioms from imported ontologies',
            enabled=True, checkable=False, clicked=self.doOpenAxiomImportDialog,
            objectName='owl2_importer_axioms'))

        # CREATE VIEW TOOLBAR BUTTONS
        self.debug('Installing OWL 2 importer control widgets')
        toolbar = self.session.widget('view_toolbar')
        self.afwset.add(toolbar.addSeparator())
        self.afwset.add(toolbar.addWidget(self.widget('owl2_importer_open')))
        self.afwset.add(toolbar.addWidget(self.widget('owl2_importer_axioms')))

        # CONFIGURE SIGNALS/SLOTS
        connect(self.session.sgnNoSaveProject, self.onNoSave)
        connect(self.session.sgnProjectSaved, self.onSave)
        connect(self.session.sgnStartOwlImport, self.doOpenOntologyFile)

# importation in DB #
class Importation():

    def __init__(self, project):

        self.project = project
        self.project_iri = str(self.project.ontologyIRI)
        self.project_version = self.project.version if len(self.project.version) > 0 else '1.0'

        self.db_filename = expandPath(K_IMPORTS_DB)
        dir = os.path.dirname(self.db_filename)
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.ManchesterOWLSyntaxOWLObjectRendererImpl = self.vm.getJavaClass(
            "org.semanticweb.owlapi.manchestersyntax.renderer.ManchesterOWLSyntaxOWLObjectRendererImpl")
        self.FunctionalOWLSyntaxOWLObjectRendererImpl = self.vm.getJavaClass("org.semanticweb.owlapi.functional.renderer.OWLFunctionalSyntaxRenderer")
        self.ShortFormProvider = self.vm.getJavaClass("org.semanticweb.owlapi.util.SimpleShortFormProvider")
        self.OWLEntity = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLEntity")
        self.DataFactoryImpl = self.vm.getJavaClass("uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl")

    def insertInDB(self, ontology):

        QtCore.QCoreApplication.processEvents()

        ## GET ONTOLOGY ID ##
        ontology_iri = str(ontology.getOntologyID().getOntologyIRI().get())
        try:
            ontology_version = str(ontology.getOntologyID().getVersionIRI().get())

        except Exception:
            ontology_version = str(ontology.getOntologyID().getOntologyIRI().get())

        conn = sqlite3.connect(self.db_filename)

        cursor = conn.cursor()

        # CHECK if ONTOLOGY IN Ontology Table #
        cursor.execute('''SELECT iri, version
                       FROM ontology
                       WHERE iri = ? and version = ?''', (ontology_iri, ontology_version))

        already_ontology = len(cursor.fetchall()) > 0
        # IF IMPORTED ONTOLOGY NOT IN DB YET #
        if not already_ontology:

            # INSERT ONTOLOGY IN DB #
            conn.execute("""
                        insert into ontology (iri, version)
                        values (?, ?)
                        """, (ontology_iri, ontology_version))
            conn.commit()
            QtCore.QCoreApplication.processEvents()

            axioms = ontology.getAxioms()
            renderer = self.ManchesterOWLSyntaxOWLObjectRendererImpl()

            #funcRenderer = self.FunctionalOWLSyntaxOWLObjectRendererImpl()

            # INSERT ALL AXIOMS OF IMPORTED ONTOLOGY IN DB #
            df = self.DataFactoryImpl()
            sfp = self.ShortFormProvider()
            for ax in axioms:
                # get axiom type #
                ax_type = ax.getAxiomType()
                # get all IRIs in axiom #
                classes = ax.getClassesInSignature()
                dataProperties = ax.getDataPropertiesInSignature()
                objProperties = ax.getObjectPropertiesInSignature()
                individuals = ax.getIndividualsInSignature()

                QtCore.QCoreApplication.processEvents()

                # to keep track of IRIs:
                # associate dictionary to axiom -> k: shortName, value: fullIRI #
                d = {}
                for el in classes:
                    iri = el.getIRI()
                    type = el.getEntityType()
                    entity = df.getOWLEntity(type, iri)
                    shortName = sfp.getShortForm(entity)
                    d[shortName] = str(iri)
                for el in dataProperties:
                    iri = el.getIRI()
                    type = el.getEntityType()
                    entity = df.getOWLEntity(type, iri)
                    shortName = sfp.getShortForm(entity)
                    d[shortName] = str(iri)
                for el in objProperties:
                    iri = el.getIRI()
                    type = el.getEntityType()
                    entity = df.getOWLEntity(type, iri)
                    shortName = sfp.getShortForm(entity)
                    d[shortName] = str(iri)
                for el in individuals:
                    iri = el.getIRI()
                    type = el.getEntityType()
                    entity = df.getOWLEntity(type, iri)
                    shortName = sfp.getShortForm(entity)
                    d[shortName] = str(iri)

                if str(ax_type) == 'AnnotationAssertion':
                    d = {}
                    iri = ax.getSubject()
                    d['subject'] = str(iri)

                    prop = ax.getProperty().getIRI()
                    d['property'] = str(prop)

                    value = ax.getValue()
                    d['value'] = str(value)


                iri_dict = str(d)
                #print(iri_dict)


                # getting the axiom in Manchester Syntax #
                manch_axiom = renderer.render(ax)
                # keep the original form (Functional Syntax #
                funcAxiom = ax
                QtCore.QCoreApplication.processEvents()

                # INSERT AXIOM IN DB #
                conn.execute("""
                            insert or ignore into axiom (axiom, type_of_axiom, manch_axiom, ontology_iri, ontology_version, iri_dict)
                            values (?, ?, ?, ?, ?, ?)
                            """, (str(funcAxiom).strip(), str(ax_type), str(manch_axiom).strip(), ontology_iri, ontology_version, iri_dict))

            conn.commit()
            QtCore.QCoreApplication.processEvents()

        # CHECK if IMPORTATION IN Importation Table #
        session = self.project.session
        cursor.execute('''SELECT project_iri, project_version, ontology_iri, ontology_version, session_id
                               FROM importation
                               WHERE project_iri = ? and project_version = ? and ontology_iri = ? and ontology_version = ?''',
                       (self.project_iri, self.project_version, ontology_iri, ontology_version))
        already_importation = len(cursor.fetchall()) > 0

        # IF IMPORTATION ALREADY IN DB -> MESSAGE ERROR + REMOVE NEW DIAGRAM FROM PROJECT #
        if already_importation:
            # MESSAGE ERROR #
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Ontology Already Imported')
            msgbox.setText('This imported ontology is already associated with the current project')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            # REMOVE CURRENT DIAGRAM #
            diagram = session.mdi.activeDiagram()
            self.project.removeDiagram(diagram)
            return True

        else:
            # INSERT IMPORTATION IN DB #
            conn.execute("""
                            insert into importation (project_iri, project_version, ontology_iri, ontology_version, session_id)
                            values (?, ?, ?, ?, ?)
                            """, (self.project_iri, self.project_version, ontology_iri, ontology_version, str(session)))
            conn.commit()
            conn.executescript("""CREATE TABLE IF NOT EXISTS temp_importation(
                          project_iri      TEXT,
                            project_version  TEXT,
                            ontology_iri     TEXT,
                            ontology_version TEXT,
                            session_id       TEXT,
                            PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version)
                        );""")
            conn.commit()
            conn.execute("""
                            insert into temp_importation (project_iri, project_version, ontology_iri, ontology_version, session_id)
                            values (?, ?, ?, ?, ?)
                            """, (self.project_iri, self.project_version, ontology_iri, ontology_version, str(session)))
            conn.commit()

            conn.close()
            return False

    def open(self):

        db_exists = os.path.exists(self.db_filename)
        if db_exists:
            # GET ALL AXIOMS OF IMPORTED ONTOLOGIES #
            # (making distinction between drawn and not drawn)
            conn = sqlite3.connect(self.db_filename)

            cursor = conn.cursor()

            # get ontologies imported in the current project #
            cursor.execute('''SELECT ontology_iri, ontology_version
                            FROM importation
                            WHERE project_iri = ? and project_version = ?
                            ''', (self.project_iri, self.project_version))

            rows = cursor.fetchall()
            imported_ontologies = []
            for row in rows:
                imported_ontologies.append((row[0], row[1]))

            # dictionaries of axioms -> k: Ontology, value: Axioms
            axioms = {}
            not_drawn = {}
            drawn = {}

            # for each ontology : get ALL axioms, DRAWN axioms, NOT DRAWN axioms #
            for ontology in imported_ontologies:

                # ALL #
                ontology_iri, ontology_version = ontology
                cursor.execute('''SELECT axiom, iri_dict
                                FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ?''', (ontology_iri, ontology_version))
                rows = cursor.fetchall()
                axioms[ontology] = []
                all_dicts = []
                for row in rows:
                    axioms[ontology].append(row[0])
                    iri_dict = row[1]
                    d = ast.literal_eval(iri_dict)
                    iris = [d[k] for k in d.keys()]
                    all_dicts.append(iris)

                # NOT DRAWN #
                cursor.execute('''SELECT axiom, type_of_axiom, manch_axiom, iri_dict
                                FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ?
                                and type_of_axiom != 'FunctionalObjectProperty'
                                and type_of_axiom != 'TransitiveObjectProperty'
                                and type_of_axiom != 'SymmetricObjectProperty'
                                and type_of_axiom != 'AsymmetricObjectProperty'
                                and type_of_axiom != 'ReflexiveObjectProperty'
                                and type_of_axiom != 'IrreflexiveObjectProperty'
                                and type_of_axiom != 'InverseFunctionalObjectProperty'
                                and type_of_axiom != 'FunctionalDataProperty'
                                and (?, ?,  axiom) not in (SELECT project_iri, project_version, axiom
                                                                                        FROM drawn)''', (ontology_iri, ontology_version, self.project_iri, self.project_version))
                rows = cursor.fetchall()
                not_drawn[ontology] = []
                for r in rows:
                    if r[1] == 'Declaration':
                        iri_dict = r[3]
                        d = ast.literal_eval(iri_dict)
                        if d:
                            entityIRI = d[list(d.keys())[0]]
                            countList = [entityIRI in el for el in all_dicts]
                            cnt = countList.count(True)
                            if cnt == 1:
                                not_drawn[ontology].append([r[0], r[1], r[2]])
                    else:
                        not_drawn[ontology].append([r[0], r[1], r[2]])

                # DRAWN #
                drawn[ontology] = [a for a in axioms[ontology] if a not in not_drawn[ontology]]

            return axioms, not_drawn, drawn

    def removeFromDB(self):

        db_exists = os.path.exists(self.db_filename)
        if db_exists:
            conn = sqlite3.connect(self.db_filename)

            with conn:
                cursor = conn.cursor()
                # check if there are temporary importations
                cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='temp_importation';""")
                temp_impo = len(cursor.fetchall()) > 0
                if temp_impo:
                    # get the temporary importations of the current session
                    cursor.execute('''SELECT project_iri, project_version, ontology_iri, ontology_version, session_id
                                                FROM temp_importation where session_id = ?''', (str(self.project.session),))
                    rows = cursor.fetchall()
                    ### REMOVE IMPORTATIONS NOT SAVED ###
                    for row in rows:
                        conn.execute(
                                'delete from importation where project_iri = ? and project_version = ? and ontology_iri = ? and ontology_version = ? and session_id = ?',
                                (row[0], row[1], row[2], row[3], row[4]))
                        conn.commit()

                # check if there are temporary drawn axioms
                cursor.execute(
                    """SELECT name FROM sqlite_master WHERE type='table' AND name='temp_drawn';""")
                temp_drawn = len(cursor.fetchall()) > 0
                if temp_drawn:
                    # get the temporary draws of the current session
                    cursor.execute('''SELECT project_iri, project_version, ontology_iri, ontology_version, axiom, session_id
                                                                FROM temp_drawn where session_id = ?''', (str(self.project.session),))
                    rows = cursor.fetchall()
                    ### REMOVE DRAWS NOT SAVED ###
                    for row in rows:
                        conn.execute(
                            'delete from drawn where project_iri = ? and project_version = ? and ontology_iri = ? and ontology_version = ? and axiom = ? and session_id = ?',
                            (row[0], row[1], row[2], row[3], row[4], row[5]))
                        conn.commit()


class AxiomSelectionDialog(QtWidgets.QDialog, HasWidgetSystem):

    def __init__(self, not_drawn, project):

        super().__init__()
        self.resize(600, 600)
        self.setWindowTitle("Other Axioms")

        # IMPORT FROM OWLAPI #
        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        if True:
            self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
            self.ManchesterOWLSyntaxParserImpl = self.vm.getJavaClass('org.semanticweb.owlapi.manchestersyntax.parser.ManchesterOWLSyntaxParserImpl')
            self.SimpleShortFormProvider = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleShortFormProvider')
            self.BidirectionalShortFormProviderAdapter = self.vm.getJavaClass('org.semanticweb.owlapi.util.BidirectionalShortFormProviderAdapter')
            self.ShortFormEntityChecker = self.vm.getJavaClass('org.semanticweb.owlapi.expression.ShortFormEntityChecker')
            self.OWLClassImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLClassImpl')
            self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
            self.OWLObjectPropertyImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLObjectPropertyImpl')
            self.OWLDataPropertyImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLDataPropertyImpl')
            self.OWLDisjointClassesAxiomImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLDisjointClassesAxiomImpl')
            self.OWLNamedIndividualImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLNamedIndividualImpl')
            self.OWLDatatypeImpl = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLDatatypeImpl')
            self.EntityType = self.vm.getJavaClass("org.semanticweb.owlapi.model.EntityType")
            self.OWLLiteral = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLLiteral")
            self.Type = self.vm.getJavaClass("org.semanticweb.owlapi.model.ClassExpressionType")
            self.Expression = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLClassExpression")
            self.Axiom = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLAxiom")
            self.ObjPropertyExpr = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLObjectInverseOf")
            self.OWLClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
            self.OWLObjectProperty = self.vm.getJavaClass(
                'org.semanticweb.owlapi.model.OWLObjectProperty')
            self.OWLInverseObjectOf = self.vm.getJavaClass('uk.ac.manchester.cs.owl.owlapi.OWLObjectInverseOfImpl')
            self.OWLDataProperty = self.vm.getJavaClass(
                'org.semanticweb.owlapi.model.OWLDataProperty')
            self.OWLNamedIndividual = self.vm.getJavaClass(
                'org.semanticweb.owlapi.model.OWLNamedIndividual')
            self.OWLDatatype = self.vm.getJavaClass(
                'org.semanticweb.owlapi.model.OWLDatatype')
            self.DatatypeRestriction = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLDatatypeRestriction")
            self.DataOneOf = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLDataOneOf")
            self.DataUnionOf = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLDataUnionOf")

        self.db_filename = expandPath(K_IMPORTS_DB)
        dir = os.path.dirname(self.db_filename)
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.project = project
        self.project_iri = str(project.ontologyIRI)
        self.project_version = project.version if len(project.version) > 0 else '1.0'
        self.session = project.session

        self.not_drawn = not_drawn

        self.checkedAxioms = []
        self.hiddenItems = []
        self.labels = []

        ## create layout ##
        # Create an outer layout
        self.table = QtWidgets.QTreeWidget(objectName='axioms_table_widget')
        self.addWidget(self.table)

        # add buttons

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='button_box')

        selectBtn = QtWidgets.QPushButton('Select All',
                                          objectName='axioms_selectall_button')
        self.confirmationBox.addButton(selectBtn, QtWidgets.QDialogButtonBox.ActionRole)
        connect(selectBtn.clicked, self.selectAllAxioms)

        deselectBtn = QtWidgets.QPushButton('Deselect All',
                                          objectName='axioms_deselectall_button')
        self.confirmationBox.addButton(deselectBtn, QtWidgets.QDialogButtonBox.ActionRole)
        connect(deselectBtn.clicked, self.deselectAllAxioms)

        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        # add Searchbar
        self.searchbar = QtWidgets.QLineEdit(objectName='axioms_searchbar')
        self.searchbar.setPlaceholderText("Search...")
        self.searchbar.textChanged.connect(self.update_display)
        self.addWidget(self.searchbar)

        # Add some checkboxes to the layout
        self.checkBoxes = []

        # add checkboxes with axioms
        # grouped by ontology
        for k in not_drawn.keys():

            onto = k[1]
            self.labels.append(onto)
            ontoLabel = QtWidgets.QTreeWidgetItem(self.table, [str(onto)])
            ontoLabel.setFont(0, Font(bold=True, scale=1.25))

            class_axioms = []
            objProp_axioms = []
            dataProp_axioms = []
            individual_axioms = []
            others = []

            for pair in not_drawn[k]:

                ax = pair[2]
                ax_type = pair[1]

                if ax_type in ['SubClassOf', 'EquivalentClasses', 'DisjointClasses']:
                    class_axioms.append(ax)
                elif ax_type in ['SubObjectPropertyOf', 'EquivalentObjectProperties', 'InverseObjectProperties', 'DisjointObjectProperties', 'ObjectPropertyDomain', 'ObjectPropertyRange', 'SubPropertyChainOf']:
                    objProp_axioms.append(ax)
                elif ax_type in ['SubDataPropertyOf', 'EquivalentDataProperties', 'DisjointDataProperties', 'DataPropertyDomain', 'DataPropertyRange']:
                    dataProp_axioms.append(ax)
                elif ax_type in ['ClassAssertion', 'ObjectPropertyAssertion', 'DataPropertyAssertion', 'NegativeObjectPropertyAssertion', 'NegativeDataPropertyAssertion', 'SameIndividual', 'DifferentIndividuals']:
                    individual_axioms.append(ax)
                else:
                    others.append(ax)

            classLabel = QtWidgets.QTreeWidgetItem(ontoLabel, ['Class Axioms'])
            classLabel.setFont(0, Font(scale=1.25))
            self.labels.append('Class Axioms')

            for ax in class_axioms:

                check = QtWidgets.QTreeWidgetItem(classLabel, [str(ax)])
                basefont = check.font(0).family()
                check.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                check.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

                self.checkBoxes.append(check)

            objPropLabel = QtWidgets.QTreeWidgetItem(ontoLabel, ['Object Property Axioms'])
            objPropLabel.setFont(0, Font(scale=1.25))
            self.labels.append('Object Property Axioms')

            for ax in objProp_axioms:
                check = QtWidgets.QTreeWidgetItem(objPropLabel, [str(ax)])
                basefont = check.font(0).family()
                check.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                check.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

                self.checkBoxes.append(check)

            dataPropLabel = QtWidgets.QTreeWidgetItem(ontoLabel, ['Data Property Axioms'])
            dataPropLabel.setFont(0, Font(scale=1.25))
            self.labels.append('Data Property Axioms')

            for ax in dataProp_axioms:
                check = QtWidgets.QTreeWidgetItem(dataPropLabel, [str(ax)])
                basefont = check.font(0).family()
                check.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                check.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

                self.checkBoxes.append(check)

            indivLabel = QtWidgets.QTreeWidgetItem(ontoLabel, ['Individual Axioms'])
            indivLabel.setFont(0, Font(scale=1.25))
            self.labels.append('Individual Axioms')

            for ax in individual_axioms:
                check = QtWidgets.QTreeWidgetItem(indivLabel, [str(ax)])
                basefont = check.font(0).family()
                check.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                check.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

                self.checkBoxes.append(check)

            if others:
                othersLabel = QtWidgets.QTreeWidgetItem(ontoLabel, ['Other Axioms'])
                othersLabel.setFont(0, Font(scale=1.25))
                self.labels.append('Other Axioms')

                for ax in others:
                    check = QtWidgets.QTreeWidgetItem(othersLabel, [str(ax)])
                    basefont = check.font(0).family()
                    check.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                    check.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

                    self.checkBoxes.append(check)

            self.table.sortItems(0, QtCore.Qt.AscendingOrder)

        self.table.setHeaderHidden(True)
        self.table.header().setStretchLastSection(False)
        self.table.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.table.doubleClicked.connect(self.checkOnClick)
        self.table.itemChanged.connect(self.checkAxiom)

        connect(self.confirmationBox.rejected, self.reject)
        connect(self.confirmationBox.accepted, self.accept)

        self.addWidget(self.confirmationBox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('axioms_searchbar'))
        formlayout.addRow(self.widget('axioms_table_widget'))
        formlayout.addRow(self.confirmationBox)
        groupbox = QtWidgets.QGroupBox('Choose Axioms:', self,
                                       objectName='axioms_widget')
        groupbox.setLayout(formlayout)
        groupbox.setMinimumSize(500, 550)
        self.addWidget(groupbox)

        # ANNOTATION ASSERTIONS TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('axioms_widget'), 0, QtCore.Qt.AlignTop)

        self.setLayout(layout)


    def update_display(self, text):

        # searchbar function #
        topcount = self.table.topLevelItemCount()

        for top in range(topcount):

            topItem = self.table.topLevelItem(top)
            self.table.collapseItem(topItem)
            middleChildCount = topItem.childCount()

            for middleChild in range(middleChildCount):

                middleChildItem = topItem.child(middleChild)
                self.table.collapseItem(middleChildItem)
                childCount = middleChildItem.childCount()

                for child in range(childCount):

                    childItem = middleChildItem.child(child)
                    childItem.setHidden(False)

        self.hiddenItems = []

        for top in range(topcount):

            topItem = self.table.topLevelItem(top)
            middleChildCount = topItem.childCount()

            for middleChild in range(middleChildCount):

                middleChildItem = topItem.child(middleChild)
                childCount = middleChildItem.childCount()

                for child in range(childCount):
                    childItem = middleChildItem.child(child)
                    item = childItem.text(0)

                    if text.lower() in item.lower():
                        self.table.expandItem(topItem)
                        self.table.expandItem(middleChildItem)
                    else:
                        childItem.setHidden(True)
                        self.hiddenItems.append(childItem)

    def checkOnClick(self, index):

        item = self.table.itemFromIndex(index)
        axiom = item.text(0)
        state = item.checkState(0)

        if axiom not in self.labels:
            if state == QtCore.Qt.Checked:
                item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            else:
                item.setCheckState(0, QtCore.Qt.CheckState.Checked)

    def checkAxiom(self, item, column):

        axiom = item.text(column)
        state = item.checkState(column)

        if state == QtCore.Qt.Checked:

            # ON SELECTION OF AN AXIOM -> ADD TO CHECKEDAXIOMS and enable OK #
            self.checkedAxioms.append(axiom)
            self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        else:
            # ON de-SELECTION OF AN AXIOM -> REMOVE FROM CHECKEDAXIOMS and if empty: disable OK #
            if axiom in self.checkedAxioms:
                self.checkedAxioms.remove(axiom)
            if len(self.checkedAxioms) == 0:
                self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def selectAllAxioms(self):

        self.table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.table.clearSelection()

        topcount = self.table.topLevelItemCount()

        for top in range(topcount):

            topItem = self.table.topLevelItem(top)
            middleChildCount = topItem.childCount()
            if topItem.isExpanded():

                for middleChild in range(middleChildCount):

                    middleChildItem = topItem.child(middleChild)
                    childCount = middleChildItem.childCount()

                    if middleChildItem.isExpanded():

                        for child in range(childCount):
                            childItem = middleChildItem.child(child)

                            if childItem not in self.hiddenItems:
                                childItem.setCheckState(0, QtCore.Qt.Checked)
                                #self.table.expandItem(topItem)

        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def deselectAllAxioms(self):

        self.table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.table.clearSelection()

        topcount = self.table.topLevelItemCount()

        for top in range(topcount):

            topItem = self.table.topLevelItem(top)
            middleChildCount = topItem.childCount()

            if topItem.isExpanded():

                for middleChild in range(middleChildCount):

                    middleChildItem = topItem.child(middleChild)
                    childCount = middleChildItem.childCount()

                    if middleChildItem.isExpanded():

                        for child in range(childCount):
                            childItem = middleChildItem.child(child)

                            if childItem not in self.hiddenItems:
                                childItem.setCheckState(0, QtCore.Qt.Unchecked)

        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)


    def reject(self):

        self.checkedAxioms = []
        super().reject()

    def accept(self):
        # k: axiom (::string), value: manchester_axiom (::Axiom)
        # (to keep track of the string axiom to insert in DRAWN table)
        super().accept()

        with BusyProgressDialog('Drawing Axioms', 0.5):

            axiomsToDraw = {}
            cantDraw = []
            for ax in self.checkedAxioms:
                # for each checked axiom:
                QtCore.QCoreApplication.processEvents()
                functional_axiom = None
                manchester_axiom = None

                for k in self.not_drawn.keys():
                    for triple in self.not_drawn[k]:
                        manch_ax = triple[2]
                        func_ax = triple[0]
                        if manch_ax == ax and func_ax not in axiomsToDraw.keys():
                            # try to parse Functional axiom string into Axiom #
                            functional_axiom = self.string2axiom2(func_ax)
                            break;

                if functional_axiom:
                    axiomsToDraw[func_ax] = functional_axiom
                else:
                    # if problems with Functional parsing -> try to parse Manchester axiom string into Axiom #
                    manchester_axiom = self.string2axiom(ax)
                    if manchester_axiom:
                        axiomsToDraw[func_ax] = manchester_axiom
                    else:
                        # if axioms can't be parsed -> can't draw message #
                        cantDraw.append(ax)

            if cantDraw:

                invalid = ', '.join(cantDraw)
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Wrong syntax')
                msgbox.setText("The current axioms can't be parsed: "+ invalid+'. These axioms will be ignored in the importation process.')
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()

            if axiomsToDraw:
                self.getInvolvedDiagrams(axiomsToDraw)

    def string2axiom2(self, ax):

        StringDocumentSource = self.vm.getJavaClass('org.semanticweb.owlapi.io.StringDocumentSource')
        conn = None
        try:
            conn = sqlite3.connect(self.db_filename)
        except Exception as e:
            print(e)

        cursor = conn.cursor()
        # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
        cursor.execute('''SELECT ontology_iri, ontology_version
                                        FROM importation
                                        WHERE project_iri = ? and project_version = ?
                                        ''', (self.project_iri, self.project_version))
        QtCore.QCoreApplication.processEvents()

        project_ontologies = []
        rows = cursor.fetchall()
        for row in rows:
            project_ontologies.append((row[0], row[1]))

        for ontology in project_ontologies:
            # for each imported ontology:
            # CHECK if AXIOM belongs to ONTOLOGY  #
            QtCore.QCoreApplication.processEvents()

            ontology_iri, ontology_version = ontology

            cursor = conn.cursor()
            cursor.execute('''SELECT *
                                    FROM axiom
                                    WHERE ontology_iri = ? and ontology_version = ? and axiom = ?
                                    ''', (ontology_iri, ontology_version, ax))

            if len(cursor.fetchall()) > 0:
                # IF BELONGS to Ontology:
                QtCore.QCoreApplication.processEvents()

                # create ontology manager #
                manager = self.OWLManager().createOWLOntologyManager()

                # get all declaration axioms of the ontology to pass to parser #
                cursor.execute('''SELECT manch_axiom, iri_dict, axiom
                                       FROM axiom
                                        WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = ?
                                        ''',
                               (ontology_iri, ontology_version, 'Declaration'))
                rows = cursor.fetchall()
                # DECLARE ENTITIES of the ONTOLOGY #
                ontostr = 'Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>) Prefix(owl:=<http://www.w3.org/2002/07/owl#>) Ontology(<'+ ontology_iri+'> '
                for row in rows:
                    # for each declaration axiom :

                    # get axiom string #
                    declaration_axiom = str(row[2])
                    ontostr = ontostr + declaration_axiom + ' '


                ontostr = ontostr + 'Declaration(Class(<http://www.w3.org/2002/07/owl#Thing>)) Declaration(Class(<http://www.w3.org/2002/07/owl#Nothing>)) Declaration(ObjectProperty(<http://www.w3.org/2002/07/owl#topObjectProperty>)) Declaration(ObjectProperty(<http://www.w3.org/2002/07/owl#bottomObjectProperty>)) Declaration(DataProperty(<http://www.w3.org/2002/07/owl#topDataProperty>)) Declaration(DataProperty(<http://www.w3.org/2002/07/owl#bottomDataProperty>))'

                new_ax = ax
                while '(InverseOf(' in new_ax:
                    idx = new_ax.find('(InverseOf(')
                    idxEnd = new_ax.find(')', idx)
                    prop = new_ax[idx+11: idxEnd]
                    objProp = 'Declaration(ObjectProperty('+prop+'))' in ontostr
                    if objProp:
                        new_ax = new_ax.replace('(InverseOf(', '(ObjectInverseOf(', 1)
                    else:
                        dataProp = 'Declaration(DataProperty('+prop+'))' in ontostr
                        if dataProp:
                            new_ax = new_ax.replace('(InverseOf(', '(DataInverseOf(', 1)


                ontostr = ontostr + new_ax + ')'

                cursor.execute('''SELECT iri_dict, type_of_axiom
                                                FROM axiom
                                                WHERE ontology_iri = ? and ontology_version = ? and axiom = ?
                                                ''',
                               (ontology_iri, ontology_version, ax))
                rows = cursor.fetchall()
                for row in rows:

                    axiom_type = row[1]

                try:
                    # build ontology from string #
                    input = StringDocumentSource(ontostr)
                    ontology = manager.loadOntologyFromOntologyDocument(input)
                    # get functional axioms from ontology #
                    axioms = ontology.getAxioms()
                    for axiom in axioms:
                        QtCore.QCoreApplication.processEvents()
                        # get axiom we needed to parse by filtering on type #
                        if axiom_type == 'Declaration':
                            if str(axiom) == ax:
                                return axiom
                        elif str(axiom.getAxiomType()) == axiom_type:
                            functional_axiom = axiom
                            return functional_axiom
                    return None
                except Exception as e:
                    print(e)

    def string2axiom(self, ax):

        conn = None
        try:
            conn = sqlite3.connect(self.db_filename)
        except Exception as e:
            print(e)

        cursor = conn.cursor()
        # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
        cursor.execute('''SELECT ontology_iri, ontology_version
                                FROM importation
                                WHERE project_iri = ? and project_version = ?
                                ''', (self.project_iri, self.project_version))

        project_ontologies = []
        rows = cursor.fetchall()
        for row in rows:
            project_ontologies.append((row[0], row[1]))

        for ontology in project_ontologies:
            # for each imported ontology:
            # CHECK if AXIOM belongs to ONTOLOGY  #

            ontology_iri, ontology_version = ontology

            cursor = conn.cursor()
            cursor.execute('''SELECT *
                            FROM axiom
                            WHERE ontology_iri = ? and ontology_version = ? and manch_axiom = ?
                            ''', (ontology_iri, ontology_version, ax))

            if len(cursor.fetchall()) > 0:
                # IF BELONGS to Ontology:

                # create ontology manager #
                manager = self.OWLManager().createOWLOntologyManager()
                # create data factory #
                df = manager.getOWLDataFactory()
                # create new ontology #
                o = manager.createOntology()
                # get all declaration axioms of the ontology to pass to parser #
                cursor.execute('''SELECT manch_axiom, iri_dict
                               FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = ?
                                ''',
                               (ontology_iri, ontology_version, 'Declaration'))
                rows = cursor.fetchall()
                # DECLARE ENTITIES of the ONTOLOGY #
                for row in rows:
                    # for each declaration axiom :

                    # get axiom string #
                    declaration_axiom = str(row[0])
                    # get dict with fullIRIs #
                    iri_dict = row[1]
                    d = ast.literal_eval(iri_dict)

                    # for each type of entity: create entity + add declaration to ontology o #
                    if 'Class:' in declaration_axiom:
                        # get class name #
                        declaration_axiom = declaration_axiom[7:]
                        # IRI =  d[class name] #
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        # create class with IRI #
                        owlClass = self.OWLClassImpl(iri)
                        # add declaration of class to ontology #
                        manager.addAxiom(o, df.getOWLDeclarationAxiom(owlClass))
                    if 'ObjectProperty:' in declaration_axiom:
                        # get class name #
                        declaration_axiom = declaration_axiom[16:]
                        # IRI =  d[class name] #
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        # create class with IRI #
                        owlObjProp = self.OWLObjectPropertyImpl(iri)
                        # add declaration of class to ontology #
                        manager.addAxiom(o, df.getOWLDeclarationAxiom(owlObjProp))
                    if 'DataProperty:' in declaration_axiom:
                        # get class name #
                        declaration_axiom = declaration_axiom[14:]
                        # IRI =  d[class name] #
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        # create class with IRI #
                        owlDataProp = self.OWLDataPropertyImpl(iri)
                        # add declaration of class to ontology #
                        manager.addAxiom(o, df.getOWLDeclarationAxiom(owlDataProp))
                    if 'Individual:' in declaration_axiom:
                        # get class name #
                        declaration_axiom = declaration_axiom[12:]
                        # IRI =  d[class name] #
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        # create class with IRI #
                        owlNamedInd = self.OWLNamedIndividualImpl(iri)
                        # add declaration of class to ontology #
                        manager.addAxiom(o, df.getOWLDeclarationAxiom(owlNamedInd))

                # declare owl:Thing  and other top/bottom #
                if 'Thing' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#Thing')
                    # create class with IRI #
                    owlClass = self.OWLClassImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlClass))
                if 'Nothing' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#Nothing')
                    # create class with IRI #
                    owlClass = self.OWLClassImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlClass))
                if 'topObjectProperty' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#topObjectProperty')
                    # create class with IRI #
                    owlObjProp = self.OWLObjectPropertyImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlObjProp))
                if 'bottomObjectProperty' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#bottomObjectProperty')
                    # create class with IRI #
                    owlObjProp = self.OWLObjectPropertyImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlObjProp))
                if 'topDataProperty' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#topDataProperty')
                    # create class with IRI #
                    owlDataProp = self.OWLDataPropertyImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlDataProp))
                if 'bottomDataProperty' in ax:

                    iri = self.IRI.create('http://www.w3.org/2002/07/owl#bottomDataProperty')
                    # create class with IRI #
                    owlDataProp = self.OWLDataPropertyImpl(iri)
                    # add declaration of class to ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlDataProp))

                # declare datatypes #
                datatypes_iri = ['owl:real', 'owl:rational', 'xsd:decimal', 'xsd:integer',
                                 'xsd:nonNegativeInteger', 'xsd:nonPositiveInteger',
                                 'xsd:positiveInteger', 'xsd:negativeInteger', 'xsd:long',
                                 'xsd:int', 'xsd:short', 'xsd:byte', 'xsd:unsignedLong',
                                 'xsd:unsignedInt', 'xsd:unsignedShort', 'xsd:unsignedByte',
                                 'xsd:double', 'xsd:float', 'xsd:string',
                                 'xsd:normalizedString', 'xsd:token', 'xsd:language', 'xsd:Name',
                                 'xsd:NCName', 'xsd:NMTOKEN', 'xsd:boolean', 'xsd:hexBinary',
                                 'xsd:base64Binary',
                                 'xsd:dateTime', 'xsd:dateTimeStamp', 'rdf:XMLLiteral',
                                 'rdf:PlainLiteral', 'rdfs:Literal', 'xsd:anyURI']
                for datatype_iri in datatypes_iri:
                    # create iri for each datatype #
                    iri = self.IRI.create(datatype_iri)
                    # create datatype with iri #
                    owlDatatype = self.OWLDatatypeImpl(iri)
                    # declare datatype in my ontology #
                    manager.addAxiom(o, df.getOWLDeclarationAxiom(owlDatatype))

                # create bidirectional short form provider #
                sfp = self.SimpleShortFormProvider()
                shortFormProvider = self.BidirectionalShortFormProviderAdapter(manager.getOntologies(), sfp)
                # create manchester parser #
                parser = self.OWLManager().createManchesterParser()

                # REFINE the AXIOM #
                new_ax = ax
                # handle wrong ':' #
                range_domain = ['Domain', 'Range', 'InverseOf', 'Type', 'EquivalentTo']
                for r in range_domain:
                    if ' ' + r + ' ' in new_ax:
                        new_ax = new_ax.replace(' ' + r + ' ', ' ' + r + ': ')
                obj_prop_char = ['Functional', 'Transitive', 'Reflexive', 'Irreflexive',
                                 'Asymmetric', 'Symmetric', 'inverseFunctional']
                for c in obj_prop_char:
                    if c + ':' in new_ax:
                        new_ax = new_ax.replace(c + ':', c)

                # get fullIRIs dict and type of axiom #
                cursor.execute('''SELECT iri_dict, type_of_axiom
                                FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ? and manch_axiom = ?
                                ''',
                               (ontology_iri, ontology_version, ax))
                rows = cursor.fetchall()
                for row in rows:
                    iri_dict = row[0]
                    d = ast.literal_eval(iri_dict)
                    axiom_type = row[1]

                try:
                    manchester_axiom = False
                    ## handle DisjointClasses and DifferentIndividuals axiom ##
                    # for each class/individual : get fullIRI, create class/individual
                    # -> machester_axiom = disjoint/different of classes/individuals
                    if new_ax[:16] == 'DisjointClasses:':
                        classes = [x.strip() for x in new_ax[17:].split(',')]

                        owlClasses = []
                        for cl in classes:
                            # IRI =  d[class name] #
                            entity = d[cl]
                            iri = self.IRI.create(entity)
                            owlClass = self.OWLClassImpl(iri)
                            owlClasses.append(owlClass)

                        manchester_axiom = df.getOWLDisjointClassesAxiom(owlClasses)
                    if new_ax[:21] == 'DifferentIndividuals:':
                        individuals = [x.strip() for x in new_ax[22:].split(',')]

                        owlIndividuals = []
                        for ind in individuals:
                            # IRI =  d[individual name] #
                            entity = d[ind]
                            iri = self.IRI.create(entity)
                            owlIndiv = self.OWLNamedIndividualImpl(iri)
                            owlIndividuals.append(owlIndiv)

                        manchester_axiom = df.getOWLDifferentIndividualsAxiom(owlIndividuals)
                    # handle i1 DifferentFrom/SameAs i2 #
                    if ' DifferentFrom ' in new_ax:

                        idx = new_ax.find(' DifferentFrom ')
                        i1 = new_ax[0:idx]
                        i2 = new_ax[idx+15:]

                        individuals = [i1, i2]
                        owlIndividuals = []
                        for ind in individuals:
                            # IRI =  d[individual name] #
                            entity = d[ind]
                            iri = self.IRI.create(entity)
                            owlIndiv = self.OWLNamedIndividualImpl(iri)
                            owlIndividuals.append(owlIndiv)

                        manchester_axiom = df.getOWLDifferentIndividualsAxiom(owlIndividuals)
                    if ' SameAs ' in new_ax:

                        idx = new_ax.find(' SameAs ')
                        i1 = new_ax[0:idx]
                        i2 = new_ax[idx+8:]

                        individuals = [i1, i2]
                        owlIndividuals = []
                        for ind in individuals:
                            # IRI =  d[individual name] #
                            entity = d[ind]
                            iri = self.IRI.create(entity)
                            owlIndiv = self.OWLNamedIndividualImpl(iri)
                            owlIndividuals.append(owlIndiv)

                        manchester_axiom = df.getOWLSameIndividualAxiom(owlIndividuals)
                    # handle hasKey #
                    if ' HasKey ' in new_ax:

                        idx = new_ax.find(' HasKey ')
                        ce = new_ax[0:idx]
                        # check if object complement of #
                        complement = False
                        if ce.find('not (') > -1:
                            complement = True
                            ce = ce.replace('not (', '')
                            ce = ce.replace(')', '')

                        # get ClassExpression #
                        if ce in d.keys():

                            entity = d[ce]
                            iri = self.IRI.create(entity)
                            owlClass = df.getOWLClass(iri)
                            if complement:
                                owlClass = df.getOWLObjectComplementOf(owlClass)

                        inverse = []
                        inStart = new_ax.find(' inverse (')

                        while inStart > -1:
                            inEnd = new_ax.find(')', inStart)
                            prop = new_ax[inStart+10:inEnd]
                            inverse.append(prop)
                            new_ax = new_ax.replace(' inverse (', ' ', 1)
                            new_ax = new_ax.replace(')', '', 1)
                            inStart = new_ax.find(' inverse (')
                            #print(new_ax, inStart)

                        properties = new_ax[idx+8:]
                        # get Key Properties #
                        owlProperties = []
                        # get object properties of ontology to check if key property is object or data
                        objectProperties = [str(x.getIRI()) for x in o.getObjectPropertiesInSignature()]


                        for k in d.keys():
                            # for shortIRI in dict
                            if k in properties and k != ce:
                                # if shortIRI in properties
                                entity = d[k]
                                iri = self.IRI.create(entity)
                                # get Property #
                                if str(iri) in objectProperties:
                                    owlProp = self.OWLObjectPropertyImpl(iri)
                                    if k in inverse:
                                        owlProp = self.OWLInverseObjectOf(owlProp)
                                else:
                                    owlProp = self.OWLDataPropertyImpl(iri)
                                owlProperties.append(owlProp)

                        manchester_axiom = df.getOWLHasKeyAxiom(owlClass, owlProperties)
                    # handle (Negative)PropertyAssertions #
                    if axiom_type == 'ObjectPropertyAssertion':

                        # check if property is inverse #
                        inStart = new_ax.find(' inverse (')
                        if inStart > -1:
                            new_ax = new_ax.replace(' inverse (', ' ')
                            new_ax = new_ax.replace(') ', ' ')
                            inverse = True
                        else:
                            inverse = False

                        # get object properties and individuals of ontology
                        objectProperties = [str(x.getIRI()) for x in o.getObjectPropertiesInSignature()]
                        individuals = [str(x.getIRI()) for x in o.getIndividualsInSignature()]

                        axSplit = new_ax.split()
                        i = 0
                        for el in axSplit:
                            i = i + 1

                            if i == 2 and d[el] in objectProperties:
                                # get ObjProperty #
                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlProp = self.OWLObjectPropertyImpl(iri)
                                if inverse:
                                    owlProp = self.OWLInverseObjectOf(owlProp)

                            if d[el] in individuals:
                                # get individuals #
                                if i == 1:
                                    entity = d[el]
                                    iri = self.IRI.create(entity)
                                    owlInd1 = self.OWLNamedIndividualImpl(iri)

                                if i > 2:
                                    entity = d[el]
                                    iri = self.IRI.create(entity)
                                    owlInd2 = self.OWLNamedIndividualImpl(iri)

                        manchester_axiom = df.getOWLObjectPropertyAssertionAxiom(owlProp, owlInd1, owlInd2)
                    if axiom_type == 'NegativeObjectPropertyAssertion':

                        start = new_ax.find('(')
                        end = new_ax.rfind(')')
                        new_ax = new_ax[start+1:end]

                        inStart = new_ax.find(' inverse (')
                        if inStart > -1:
                            new_ax = new_ax.replace(' inverse (', ' ')
                            new_ax = new_ax.replace(') ', ' ')
                            inverse = True
                        else:
                            inverse = False

                        objectProperties = [str(x.getIRI()) for x in o.getObjectPropertiesInSignature()]
                        individuals = [str(x.getIRI()) for x in o.getIndividualsInSignature()]

                        axSplit = new_ax.split()
                        i = 0
                        for el in axSplit:
                            i = i + 1
                            #print(el, i)
                            if i == 2 and d[el] in objectProperties:
                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlProp = self.OWLObjectPropertyImpl(iri)
                                if inverse:
                                    owlProp = self.OWLInverseObjectOf(owlProp)

                            if d[el] in individuals:
                                if i == 1:
                                    entity = d[el]
                                    iri = self.IRI.create(entity)
                                    owlInd1 = self.OWLNamedIndividualImpl(iri)

                                if i > 2:
                                    entity = d[el]
                                    iri = self.IRI.create(entity)
                                    owlInd2 = self.OWLNamedIndividualImpl(iri)

                        manchester_axiom = df.getOWLNegativeObjectPropertyAssertionAxiom(owlProp, owlInd1, owlInd2)

                    if axiom_type == 'DataPropertyAssertion':

                        dataProperties = [str(x.getIRI()) for x in o.getDataPropertiesInSignature()]
                        individuals = [str(x.getIRI()) for x in o.getIndividualsInSignature()]
                        #print('objproperties', objectProperties)
                        #print('d', d)

                        axSplit = new_ax.split()
                        #print('axsplit', axSplit)
                        i = 0
                        for el in axSplit:
                            i = i + 1
                            #print(el, i)
                            if i == 2 and d[el] in dataProperties:
                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlProp = self.OWLDataPropertyImpl(iri)

                            if i == 1 and d[el] in individuals:

                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlInd1 = self.OWLNamedIndividualImpl(iri)

                            if i > 2:

                                lit = el
                                #print(el, el.isdigit())

                                if el.isdigit() or ((el[0] == '+' or el[0] == '-') and el[1:].isdigit()):
                                    lit = int(el)

                                if el.replace(".", "", 1).isdigit() or ((el[0] == '+' or el[0] == '-') and el[1:].replace(".", "", 1).isdigit()):
                                    lit = float(el)

                                owlLit = df.getOWLLiteral(lit)

                        manchester_axiom = df.getOWLDataPropertyAssertionAxiom(owlProp, owlInd1, owlLit)
                    if axiom_type == 'NegativeDataPropertyAssertion':

                        start = new_ax.find('(')
                        end = new_ax.rfind(')')
                        new_ax = new_ax[start + 1:end]

                        dataProperties = [str(x.getIRI()) for x in o.getDataPropertiesInSignature()]
                        individuals = [str(x.getIRI()) for x in o.getIndividualsInSignature()]
                        #print('objproperties', objectProperties)
                        #print('d', d)

                        axSplit = new_ax.split()
                        #print('axsplit', axSplit)
                        i = 0
                        for el in axSplit:
                            i = i + 1
                            #print(el, i)
                            if i == 2 and d[el] in dataProperties:
                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlProp = self.OWLDataPropertyImpl(iri)

                            if i == 1 and d[el] in individuals:

                                entity = d[el]
                                iri = self.IRI.create(entity)
                                owlInd1 = self.OWLNamedIndividualImpl(iri)

                            if i > 2:

                                lit = el
                                #print(el, el.isdigit())

                                if el.isdigit() or ((el[0] == '+' or el[0] == '-') and el[1:].isdigit()):
                                    lit = int(el)

                                if el.replace(".", "", 1).isdigit() or ((el[0] == '+' or el[0] == '-') and el[1:].replace(".", "", 1).isdigit()):
                                    lit = float(el)

                                owlLit = df.getOWLLiteral(lit)

                        manchester_axiom = df.getOWLNegativeDataPropertyAssertionAxiom(owlProp, owlInd1, owlLit)

                    if not manchester_axiom:
                        # set string to parse #
                        parser.setStringToParse(new_ax)
                        # create entity checker #
                        owlEntityChecker = self.ShortFormEntityChecker(shortFormProvider)
                        parser.setOWLEntityChecker(owlEntityChecker)
                        parser.setDefaultOntology(o)
                        # parse string to axiom #
                        manchester_axiom = parser.parseAxiom()

                except Exception as e:
                    '''
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle("Axiom Can't be Drawn")
                    msgbox.setText(str(e))
                    #msgbox.setText('This axiom: \n' + ax + "\n can't be drawn")
                    msgbox.setTextFormat(QtCore.Qt.RichText)
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msgbox.exec_()
                    '''
                    print(e)

        return manchester_axiom

    def getInvolvedDiagrams(self, axioms):
        # axioms : {k:str_axiom, value: ManchesterAxiom}

        # GET ALL ELEMENTS INVOLVED IN AXIOMS #
        elements = {}
        for str_ax in axioms.keys():
            QtCore.QCoreApplication.processEvents()

            # for each axiom :
            elements[str_ax] = []
            ax = axioms[str_ax]
            # get all IRIs in axiom #
            classes = ax.getClassesInSignature()
            dataProperties = ax.getDataPropertiesInSignature()
            objProperties = ax.getObjectPropertiesInSignature()
            individuals = ax.getIndividualsInSignature()

            # add elements to the list of elements #
            elements[str_ax].extend(classes)
            elements[str_ax].extend(dataProperties)
            elements[str_ax].extend(objProperties)
            elements[str_ax].extend(individuals)

        involvedDiagrams = {}
        # get all diagrams of the current project #
        project_diagrams = self.project.diagrams()

        # CHECK WHICH DIAGRAMS CONTAIN ONE OF THE ELEMENTS INVOLVED #
        for k in elements.keys():
        # for each axiom :
            involvedDiagrams[k] = []
            for el in elements[k]:
            # each element involved :
                # get element iri #
                if not el.isTopEntity() and not el.isBottomEntity():
                    iri = el.getIRI()
                    for diagram in project_diagrams:
                    # for each diagram of the project:
                        if diagram.name not in involvedDiagrams[k]:
                        # if not already involved:
                            # check if there is an item with same IRI as element
                            for item in diagram.items():
                                QtCore.QCoreApplication.processEvents()

                                if item.isNode() and (item.type() == Item.ConceptNode or item.type() == Item.IndividualNode or item.type() == Item.AttributeNode or item.type == Item.RoleNode) and str(iri) == str(item.iri):
                                    involvedDiagrams[k].append(diagram.name)

        axiomsDict = {}
        for str_ax in axioms.keys():
            QtCore.QCoreApplication.processEvents()

            axiomsDict[str_ax] = {}
            axiomsDict[str_ax]['axiom'] = axioms[str_ax]
            axiomsDict[str_ax]['involvedDiagrams'] = involvedDiagrams[str_ax]

        try:
            # axiomsDict : {k: str_axiom, value: {k: 'axiom'|'involvedDiagrams', value: ManchesterAxiom | [involvedDiagram]}}
            self.drawAxioms(axiomsDict)

        except Exception as e:

            # IF NO IMPORTATIONS ASSOCIATED WITH THIS PROJECT -> WARNING #
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('No Ontology Imported')
            msgbox.setText(str(e))
            #msgbox.setText("It is not possible to draw the selected axioms in the selected diagrams")
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()

    def drawAxioms(self, dict):
        '''
        Draw each axiom in the related diagram and insert in db.
        '''
        conn = None
        try:
            conn = sqlite3.connect(self.db_filename)
        except Exception as e:
            print(e)

        conn.executescript("""CREATE TABLE IF NOT EXISTS temp_drawn (
                                                        project_iri      TEXT,
                                                        project_version  TEXT,
                                                        ontology_iri     TEXT,
                                                        ontology_version TEXT,
                                                        axiom            TEXT,
                                                        session_id       TEXT,
                                                        PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version, axiom));""")
        conn.commit()

        # INSERT AXIOMS IN THE DRAWN TABLE #
        cursor = conn.cursor()
        # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
        cursor.execute('''SELECT ontology_iri, ontology_version
                                FROM importation
                                WHERE project_iri = ? and project_version = ?
                                ''', (self.project_iri, self.project_version))

        project_ontologies = []
        rows = cursor.fetchall()
        for row in rows:
            project_ontologies.append((row[0], row[1]))

        with conn:
            for ax in dict.keys():
            # for each checked axiom:
                QtCore.QCoreApplication.processEvents()

                axiom = dict[ax]['axiom']
                diagrams = dict[ax]['involvedDiagrams']
                # print(axiom, diagrams)
                if len(diagrams) == 0:
                    # if no diagram involved:
                    # draw on the activeOne
                    diag = self.session.mdi.activeDiagram()
                    if diag:
                        res = self.draw(axiom, diag)
                        n = res[0]
                    else:
                        project_diagrams = list(self.project.diagrams())
                        diag = project_diagrams[0]
                        res = self.draw(axiom, diag)
                        n = res[0]

                if len(diagrams) == 1:
                    # if only one diagram involved:
                    # draw on the one
                    diag = diagrams[0]
                    project_diagrams = self.project.diagrams()
                    for d in project_diagrams:
                        if d.name == diag:
                            diagram = d
                            break
                    res = self.draw(axiom, diagram)
                    n = res[0]

                if len(diagrams) > 1:
                    # if more than one diagram involved:
                    # draw on the activeOne if involved
                    diag = self.session.mdi.activeDiagram()
                    if diag:
                        if diag.name in diagrams:
                            res = self.draw(axiom, diag)
                            n = res[0]
                    # else draw on any of the involved ones
                    else:
                        diag = diagrams[0]
                        project_diagrams = self.project.diagrams()
                        for d in project_diagrams:
                            if d.name == diag:
                                diagram = d
                                break
                        res = self.draw(axiom, diagram)
                        n = res[0]

                for ontology in project_ontologies:
                # for each imported ontology:
                    # CHECK if AXIOM belongs to ONTOLOGY  #
                    QtCore.QCoreApplication.processEvents()

                    ontology_iri, ontology_version = ontology

                    cursor = conn.cursor()
                    cursor.execute('''SELECT *
                                    FROM axiom
                                    WHERE ontology_iri = ? and ontology_version = ? and axiom = ?
                                    ''', (ontology_iri, ontology_version, str(ax)))


                    if len(cursor.fetchall()) > 0:

                        sql = 'INSERT INTO drawn (project_iri, project_version, ontology_iri, ontology_version, axiom, session_id) VALUES (?, ?, ?, ?, ?, ?)'
                        cur = conn.cursor()
                        cur.execute(sql, (
                        self.project_iri, self.project_version, ontology_iri, ontology_version, str(ax), str(self.session)))
                        conn.commit()
                        sql2 = 'INSERT INTO temp_drawn (project_iri, project_version, ontology_iri, ontology_version, axiom, session_id) VALUES (?, ?, ?, ?, ?, ?)'
                        cur.execute(sql2, (
                            self.project_iri, self.project_version, ontology_iri, ontology_version,
                            str(ax), str(self.session)))
                        conn.commit()
        conn.close()

        # snap to grid #
        self.session.doSnapTopGrid()

        # focus on the last drawn element #
        self.session.doFocusItem(n)

    def draw(self, axiom, diagram, x=0, y=0):
        QtCore.QCoreApplication.processEvents()

        #print(axiom)
        #print('processing')
        if isinstance(axiom, self.Axiom):
            return self.drawAxiom(axiom, diagram, x, y)

        if isinstance(axiom, self.Expression):
            return self.drawExpression(axiom, diagram, x, y)

        if isinstance(axiom, self.ObjPropertyExpr):
            return self.drawPropertyExpression(axiom, diagram, x, y)

        if isinstance(axiom, self.DatatypeRestriction):
            datatype = axiom.getDatatype()
            facetRestrictions = axiom.getFacetRestrictions()
            n = self.drawDatatypeRestriction(datatype, facetRestrictions, diagram, x, y)
            return n

        if isinstance(axiom, self.DataOneOf):
            values = axiom.getValues()
            n = self.drawDataOneOf(values, diagram, x, y)
            return n

        if isinstance(axiom, self.DataUnionOf):
            operands = list(axiom.getOperands())
            n = self.drawDataUnionOf(operands, diagram, x, y)
            return n
    # DRAW AXIOM, CLASS EXPRESSIONS, ... #

    def drawPropertyExpression(self, axiom, diagram, x, y):

        prop = axiom.getInverse()

        if self.isAtomic(prop):

            propIRI = prop.getIRI()

            propNode = self.findNode(prop, diagram) if self.findNode(prop, diagram) != 'null' else self.createNode(prop, diagram, x, y)

        else:
            res = self.draw(prop, diagram, x, y)
            propNode = res[0]

        edges = propNode.edges
        inputEdges = [e for e in edges if e.type() is Item.InputEdge]
        for e in inputEdges:
            if e.target.type() is Item.RoleInverseNode:
                return [e.target]


        inv = RoleInverseNode(diagram=diagram)
        x = propNode.pos().x() + propNode.width() + 50
        y = propNode.pos().y()
        starting_y = y
        while not self.isEmpty(x, y, diagram):
            y = y - 50
            if abs(starting_y - y) >1000:
                y = starting_y
                break

        inv.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, inv))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=inv)
        propNode.addEdge(input)
        inv.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if propNode.pos().y() != inv.pos().y():

            x = propNode.pos().x() + 68
            y1 = propNode.pos().y()
            y2 = inv.pos().y()

            bp1 = QtCore.QPointF(x, y1)
            bp2 = QtCore.QPointF(x, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))

        return [inv]

    def drawDatatypeRestriction(self, datatype, facets, diagram, x, y):

        datatypes_iri = {'owl:real':'http://www.w3.org/2002/07/owl#real', 'owl:rational':'http://www.w3.org/2002/07/owl#rational', 'xsd:decimal':'http://www.w3.org/2001/XMLSchema#decimal', 'xsd:integer':'http://www.w3.org/2001/XMLSchema#integer',
                         'xsd:nonNegativeInteger':'http://www.w3.org/2001/XMLSchema#nonNegativeInteger', 'xsd:nonPositiveInteger':'http://www.w3.org/2001/XMLSchema#nonPositiveInteger',
                         'xsd:positiveInteger':'http://www.w3.org/2001/XMLSchema#positiveInteger', 'xsd:negativeInteger':'http://www.w3.org/2001/XMLSchema#negativeInteger', 'xsd:long':'http://www.w3.org/2001/XMLSchema#long',
                         'xsd:int':'http://www.w3.org/2001/XMLSchema#int', 'xsd:short':'http://www.w3.org/2001/XMLSchema#short', 'xsd:byte':'http://www.w3.org/2001/XMLSchema#byte', 'xsd:unsignedLong':'http://www.w3.org/2001/XMLSchema#unsignedLong',
                         'xsd:unsignedInt':'http://www.w3.org/2001/XMLSchema#unsignedInt', 'xsd:unsignedShort':'http://www.w3.org/2001/XMLSchema#unsignedShort', 'xsd:unsignedByte':'http://www.w3.org/2001/XMLSchema#unsignedByte',
                         'xsd:double':'http://www.w3.org/2001/XMLSchema#double', 'xsd:float':'http://www.w3.org/2001/XMLSchema#float', 'xsd:string':'http://www.w3.org/2001/XMLSchema#string',
                         'xsd:normalizedString':'http://www.w3.org/2001/XMLSchema#normalizedString', 'xsd:token':'http://www.w3.org/2001/XMLSchema#token', 'xsd:language':'http://www.w3.org/2001/XMLSchema#language', 'xsd:Name':'http://www.w3.org/2001/XMLSchema#Name',
                         'xsd:NCName':'http://www.w3.org/2001/XMLSchema#NCName', 'xsd:NMTOKEN':'http://www.w3.org/2001/XMLSchema#NMTOKEN', 'xsd:boolean':'http://www.w3.org/2001/XMLSchema#boolean', 'xsd:hexBinary':'http://www.w3.org/2001/XMLSchema#hexBinary',
                         'xsd:base64Binary':'http://www.w3.org/2001/XMLSchema#base64Binary',
                         'xsd:dateTime':'http://www.w3.org/2001/XMLSchema#dateTime', 'xsd:dateTimeStamp':'http://www.w3.org/2001/XMLSchema#dateTimeStamp', 'rdf:XMLLiteral':'http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral',
                         'rdf:PlainLiteral':'http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral', 'rdfs:Literal':'http://www.w3.org/2000/01/rdf-schema#Literal', 'xsd:anyURI':'http://www.w3.org/2001/XMLSchema#anyURI'}

        dataNode = DatatypeRestrictionNode(diagram=diagram)
        starting_y = y
        while not self.isEmpty(x, y, diagram):
            y = y - 50
            if abs(starting_y - y) > 1000:
                y = starting_y
                break
        dataNode.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, dataNode))

        if not self.isAtomic(datatype):
            res = self.draw(datatype, x+180, y)
            dNode = res[0]

        else:
            dNode = self.createNode(datatype, diagram, x+180, y)

        input = diagram.factory.create(Item.InputEdge, source=dNode, target=dataNode)
        dNode.addEdge(input)
        dataNode.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        for f in facets:

            constrFacet = self.project.getIRI(str(f.getFacet().getIRI()))

            value = f.getFacetValue()
            lexicalForm = value.getLiteral()
            dtype = value.getDatatype().getIRI()
            dtypeIRI = self.project.getIRI(datatypes_iri[str(dtype)])
            lang = value.getLang()

            literal = Literal(lexicalForm, datatype=dtypeIRI, language=lang)

            facet = Facet(constrFacet, literal)

            fNode = FacetNode(facet=facet, diagram=diagram)

            x = x + 180
            y = y + 125
            starting_y = y
            while not self.isEmpty(x, y, diagram):
                y = y - 50

                if abs(starting_y - y) > 1000:
                    y = starting_y
                    break
            fNode.setPos(x, y)
            fNode.doUpdateNodeLabel()
            self.session.undostack.push(CommandNodeAdd(diagram, fNode))

            inp = diagram.factory.create(Item.InputEdge, source=fNode, target=dataNode)
            fNode.addEdge(inp)
            dataNode.addEdge(inp)
            self.session.undostack.push(CommandEdgeAdd(diagram, inp))

            x1 = fNode.pos().x()
            y1 = dataNode.pos().y()

            bp = QtCore.QPointF(x1, y1)
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, inp, 0, bp))

        return [dataNode]

    def drawExpression(self, ex, diagram, x, y):

        QtCore.QCoreApplication.processEvents()

        ex_type = str(ex.getClassExpressionType())

        if ex_type == 'ObjectUnionOf':

            operands = ex.getOperandsAsList()
            n = self.drawObjUnionOf(operands, diagram, x, y)
            return n

        if ex_type == 'DataUnionOf':

            operands = ex.getOperandsAsList()
            n = self.drawDataUnionOf(operands, diagram, x, y)
            return n

        if ex_type == 'ObjectOneOf':

            operands = ex.getIndividuals()
            n = self.drawObjOneOf(operands, diagram, x, y)
            return n

        if ex_type == 'DataOneOf':
            values = ex.getValues()
            n = self.drawDataOneOf(values, diagram, x, y)
            return n

        if ex_type == 'ObjectIntersectionOf':

            operands = ex.getOperandsAsList()
            n = self.drawObjIntersectionOf(operands, diagram, x, y)
            return n

        if ex_type == 'ObjectSomeValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjSomeValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'DataSomeValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataSomeValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectAllValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjAllValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'DataAllValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataAllValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectComplementOf':

            operand = ex.getOperand()
            n = self.drawObjComplementOf(operand, diagram, x, y)
            return n

        if ex_type == 'ObjectMinCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjMinCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'DataMinCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataMinCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectMaxCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjMaxCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'DataMaxCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataMaxCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectExactCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjExactCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'DataExactCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataExactCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectHasSelf':

            property = ex.getProperty()
            n = self.drawObjHasSelf(property, diagram, x, y)
            return n

        if ex_type == 'ObjectHasValue':

            ex  = ex.asSomeValuesFrom()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjSomeValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'DataHasValue':

            ex  = ex.asSomeValuesFrom()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawDataSomeValuesFrom(property, ce, diagram, x, y)
            return n

    def drawAxiom(self, axiom, diagram, x, y):
        QtCore.QCoreApplication.processEvents()
        if isinstance(axiom, self.Axiom):

            ax_type = str(axiom.getAxiomType())
            #print(ax_type)
            if ax_type == 'Declaration':
                entity = axiom.getEntity()
                return [self.createNode(entity, diagram, x, y)]

            if ax_type == 'HasKey':

                ce = axiom.getClassExpression()
                keys = axiom.getPropertyExpressions()
                n = self.drawHasKey(ce, keys, diagram, x, y)
                return n

            if ax_type == 'DisjointClasses':

                expressions = axiom.getClassExpressionsAsList()

                if len(expressions) == 2:

                    node = self.drawDisjointClasses(expressions, diagram, x, y)
                    return node

                else:

                    list_of_disjoints = axiom.asPairwiseAxioms()
                    for disjoint_axiom in list_of_disjoints:

                        n = self.draw(disjoint_axiom, diagram, x, y)

                    return n

            if ax_type == 'DisjointUnion':

                classes = axiom.getClassExpressions()
                classs = axiom.getOWLClass()
                n = self.drawDisjointUnion(classes, classs, diagram, x, y)
                return n

            if ax_type == 'DisjointDataProperties':

                expressions = axiom.getClassExpressionsAsList()

                if len(expressions) == 2:

                    node = self.drawDisjointDataProperties(expressions, diagram, x, y)
                    return node

                else:

                    list_of_disjoints = axiom.asPairwiseAxioms()
                    for disjoint_axiom in list_of_disjoints:

                        n = self.draw(disjoint_axiom, diagram, x, y)

                    return n

            if ax_type == 'DisjointObjectProperties':

                expressions = axiom.getClassExpressionsAsList()

                if len(expressions) == 2:

                    node = self.drawDisjointDataProperties(expressions, diagram, x, y)
                    return node

                else:

                    list_of_disjoints = axiom.asPairwiseAxioms()
                    for disjoint_axiom in list_of_disjoints:

                        n = self.draw(disjoint_axiom, diagram, x, y)

                    return n

            if ax_type == 'DifferentIndividuals':

                individuals = axiom.getIndividualsAsList()

                if len(individuals) == 2:

                    #print(ax_type, individuals, diagram)
                    return self.drawDiffIndiv(individuals, diagram, x, y)

                else:

                    list_of_different = axiom.asPairwiseAxioms()
                    for different_axiom in list_of_different:

                        e = self.draw(different_axiom, diagram, x, y)

                    return e

            if ax_type == 'SameIndividual':

                individuals = axiom.getIndividualsAsList()

                if len(individuals) == 2:

                    #print(ax_type, individuals, diagram)
                    return self.drawSameIndiv(individuals, diagram, x, y)

                else:

                    list_of_same = axiom.asPairwiseAxioms()
                    for same_axiom in list_of_same:

                        e =self.draw(same_axiom, diagram, x, y)

                    return e

            if ax_type == 'ClassAssertion':

                indiv = axiom.getIndividual()
                classs = axiom.getClassExpression()
                return self.drawClassAssertion(indiv, classs, diagram, x, y)

            if ax_type == 'DataPropertyAssertion' or ax_type == 'ObjectPropertyAssertion':

                value = axiom.getObject()
                indiv = axiom.getSubject()
                prop = axiom.getProperty()

                n = self.drawPropertyAssertion(prop, indiv, value, diagram, x, y)
                return n

            if ax_type == 'NegativeDataPropertyAssertion' or ax_type == 'NegativeObjectPropertyAssertion':

                value = axiom.getObject()
                indiv = axiom.getSubject()
                prop = axiom.getProperty()

                n = self.drawNegativePropertyAssertion(prop, indiv, value, diagram, x, y)
                return n

            if ax_type == 'EquivalentClasses':

                expressions = axiom.getClassExpressionsAsList()

                if len(expressions) == 2:

                    return self.drawEquivalentClasses(expressions, diagram, x, y)

                else:

                    list_of_equivalents = axiom.asPairwiseAxioms()
                    for equivalence_axiom in list_of_equivalents:

                        e = self.draw(equivalence_axiom, diagram, x, y)

                    return e

            if ax_type == 'EquivalentObjectProperties':

                expressions = axiom.getProperties()

                if len(expressions) == 2:

                    return self.drawEquivalentProperties(expressions, diagram, x, y)

                else:

                    list_of_equivalents = axiom.asPairwiseAxioms()
                    for equivalence_axiom in list_of_equivalents:

                        e = self.draw(equivalence_axiom, diagram, x, y)

                    return e

            if ax_type == 'EquivalentDataProperties':

                expressions = axiom.getProperties()

                if len(expressions) == 2:

                    return self.drawEquivalentProperties(expressions, diagram, x, y)

                else:

                    list_of_equivalents = axiom.asPairwiseAxioms()
                    for equivalence_axiom in list_of_equivalents:

                        e = self.draw(equivalence_axiom, diagram, x, y)

                    return e

            if ax_type == 'SubObjectPropertyOf':

                sub_prop = axiom.getSubProperty()
                sup_prop = axiom.getSuperProperty()

                return self.drawSubProperty(sub_prop, sup_prop, diagram, x, y)

            if ax_type == 'SubDataPropertyOf':

                sub_prop = axiom.getSubProperty()
                sup_prop = axiom.getSuperProperty()

                return self.drawSubProperty(sub_prop, sup_prop, diagram, x, y)

            if ax_type == 'InverseObjectProperties':

                properties = axiom.getProperties()
                if len(properties) == 2:

                    first = axiom.getFirstProperty()
                    second = axiom.getSecondProperty()
                    n = self.drawInverseObjProperties(first, second, diagram, x, y)
                    return n

                else:

                    pairs = axiom.asPairwiseAxioms()
                    for pair in pairs:

                        n = self.draw(pair, diagram, x, y)

                    return n

            if ax_type == 'DataPropertyDomain':

                domain = axiom.getDomain()
                property = axiom.getProperty()
                n = self.drawDataPropertyDomain(property, domain, diagram, x, y)
                return n

            if ax_type == 'ObjectPropertyDomain':

                domain = axiom.getDomain()
                property = axiom.getProperty()
                n = self.drawObjPropertyDomain(property, domain, diagram, x, y)
                return n

            if ax_type == 'DataPropertyRange':

                range = axiom.getRange()
                property = axiom.getProperty()
                n = self.drawDataPropertyRange(property, range, diagram, x, y)
                return n

            if ax_type == 'ObjectPropertyRange':

                range = axiom.getRange()
                property = axiom.getProperty()
                n = self.drawObjPropertyRange(property, range, diagram, x, y)
                return n

            if ax_type == 'SubPropertyChainOf':

                chain = axiom.getPropertyChain()
                property = axiom.getSuperProperty()

                n = self.drawChain(chain, property, diagram, x, y)
                return n

            if ax_type == 'SubClassOf':

                sub = axiom.getSubClass()
                sup = axiom.getSuperClass()

                subDrawn = False
                supDrawn = False
                found = None
                propNode = None

                if self.isAtomic(sub):

                    subIRI = sub.getIRI()
                    subNode = self.findNode(sub, diagram)
                    if subNode != 'null':

                        subDrawn = True

                if self.isAtomic(sup):

                    supIRI = sup.getIRI()
                    supNode = self.findNode(sup, diagram)
                    if supNode != 'null':
                        supDrawn = True

                if supDrawn:

                    if subDrawn:

                        if self.isIsolated(subNode):

                            x_tomove = supNode.pos().x()
                            y_tomove = supNode.pos().y() +150
                            while not self.isEmpty(x_tomove, y_tomove, diagram):

                                x_tomove = x_tomove + 100
                                if abs(supNode.pos().x() - x_tomove) > 1000:
                                    x_tomove = supNode.pos().x()
                                    break

                            subNode.setPos(x_tomove, y_tomove)

                        else:
                            if self.isIsolated(supNode):

                                x_tomove = subNode.pos().x()
                                y_tomove = subNode.pos().y() - 150
                                while not self.isEmpty(x_tomove, y_tomove, diagram):

                                    x_tomove = x_tomove + 100
                                    if abs(subNode.pos().x() - x_tomove) > 1000:
                                        x_tomove = subNode.pos().x()
                                        break

                                supNode.setPos(x_tomove, y_tomove)
                            else:
                                pass

                    else:

                        x = supNode.pos().x()
                        y = supNode.pos().y()
                        if self.isAtomic(sub):

                            subNode = self.createNode(sub, diagram, x, y)
                            subDrawn = True

                        else:

                            res = self.draw(sub, diagram, x, y)
                            if len(res) > 1:
                                subNode = res[0]
                                propNode = res[1]
                            else:
                                subNode = res[0]
                            subDrawn = True

                            cl = supNode
                            n = subNode

                            if len(res) == 2:
                                if n.type() is Item.DomainRestrictionNode or n.type() is Item.RangeRestrictionNode:
                                    type = n.type()
                                    restr = n.restriction()
                                    items = []
                                    for e in n.edges:
                                        items.append(e.source)

                                    clEdges = [e for e in cl.edges if
                                               e.type() is Item.InclusionEdge or e.type() is Item.EquivalenceEdge]
                                    for e in clEdges:
                                        node = None
                                        if e.source.type() is type and e.source.restriction() is restr:
                                            node = e.source
                                        elif e.target.type() is type and e.target.restriction() is restr:
                                            node = e.target
                                        else:
                                            pass

                                        if node:
                                            found = node
                                            inputEdges = [ie for ie in node.edges if
                                                          ie.type() is Item.InputEdge]
                                            for ie in inputEdges:
                                                if ie.source not in items:
                                                    found = None
                                            if found:
                                                break

                        if found:

                            subNode = found
                            remove = list(n.edges)
                            remove.append(n)
                            self.session.undostack.push(CommandItemsRemove(diagram, remove))

                else:

                    if subDrawn:

                        x = subNode.pos().x()
                        y = subNode.pos().y()
                        if self.isAtomic(sup):

                            supNode = self.createNode(sup, diagram, x, y)
                            supDrawn = True

                        else:

                            res = self.draw(sup, diagram, x, y)
                            if len(res) > 1:
                                supNode = res[0]
                                propNode = res[1]
                            else:
                                supNode = res[0]
                            supDrawn = True

                            cl = subNode
                            n = supNode

                            if len(res) == 2:
                                if n.type() is Item.DomainRestrictionNode or n.type() is Item.RangeRestrictionNode:
                                    type = n.type()
                                    restr = n.restriction()
                                    items = []
                                    for e in n.edges:
                                        items.append(e.source)

                                    clEdges = [e for e in cl.edges if
                                               e.type() is Item.InclusionEdge or e.type() is Item.EquivalenceEdge]
                                    for e in clEdges:
                                        node = None
                                        if e.source.type() is type and e.source.restriction() is restr:
                                            node = e.source
                                        elif e.target.type() is type and e.target.restriction() is restr:
                                            node = e.target
                                        else:
                                            pass

                                        if node:
                                            found = node
                                            inputEdges = [ie for ie in node.edges if
                                                          ie.type() is Item.InputEdge]
                                            for ie in inputEdges:
                                                if ie.source not in items:
                                                    found = None
                                            if found:
                                                break

                        if found:
                            supNode = found
                            remove = list(n.edges)
                            remove.append(n)
                            self.session.undostack.push(CommandItemsRemove(diagram, remove))

                    else:

                        x = x
                        y = y
                        if self.isAtomic(sup):

                            supNode = self.createNode(sup, diagram, x, y)
                            supDrawn = True

                        else:

                            res = self.draw(sup, diagram, x, y)
                            if len(res) > 1:
                                supNode = res[0]
                                propNode = res[1]
                            else:
                                supNode = res[0]
                            supDrawn = True

                        x = supNode.pos().x()
                        y = supNode.pos().y()
                        if self.isAtomic(sub):

                            subNode = self.createNode(sub, diagram, x, y)
                            subDrawn = True

                        else:

                            res = self.draw(sub, diagram, x, y)
                            if len(res) > 1:
                                subNode = res[0]
                                propNode = res[1]
                            else:
                                subNode = res[0]
                            subDrawn = True

                if found:
                    eqEdges = [e for e in found.edges if e.type() is Item.EquivalenceEdge]
                    if eqEdges:

                        return eqEdges[0]
                    else:
                        for e in found.edges:
                            if e.type() is Item.InclusionEdge:
                                if e.source is supNode:
                                    breakpoints = e.breakpoints
                                    self.session.undostack.push(CommandItemsRemove(diagram, [e]))
                                    isa = diagram.factory.create(Item.EquivalenceEdge,
                                                                         source=subNode,
                                                                         target=supNode)
                                    found.addEdge(isa)
                                    supNode.addEdge(isa)
                                    self.session.undostack.push(CommandEdgeAdd(diagram, isa))

                                    i = 0
                                    breakpoints.reverse()
                                    for b in breakpoints:
                                        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, i, b))
                                        i = i +1

                                elif e.target is supNode:
                                    isa = e
                else:
                    isa = diagram.factory.create(Item.InclusionEdge, source=subNode, target=supNode)
                    self.session.undostack.push(CommandEdgeAdd(diagram, isa))

                    if propNode:
                        bps = self.addBreakpoints(diagram, propNode, supNode, subNode, None)
                        bps.reverse()

                        i = len(isa.breakpoints)
                        for b in bps:
                            self.session.undostack.push(
                                CommandEdgeBreakpointAdd(diagram, isa, i, b))
                            i = i + 1

                return [isa]

    # DRAW CLASS EXPRESSIONS #

    def drawObjHasSelf(self, property, diagram, x, y):

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram) if self.findNode(property, diagram) != 'null' else self.createNode(property, diagram, x, y)

        else:

            res = self.draw(property, diagram, x, y+125)
            propNode = res[0]

        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        n.setText('self')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return [n, propNode]

    def drawDataMinCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':
                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() - 180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()
                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x, y)

                if self.isAtomic(property):

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

                #x = x - 100
                #y = y
                if ceDrawn:
                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                else:
                    x = x -180
                    y = y
                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)

        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(' + card + ' , -)')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]
        return [n, propNode]

    def drawObjMinCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':

                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:
                # DRAW CE
                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() -180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x - 180, y)

                if self.isAtomic(property):

                    x = x
                    y = y + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = x
                    y = y + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x + 180
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True


                if ceDrawn:
                    x = x
                    y = y + 125

                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
        '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:

                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(' + card + ' , -)')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]
        return [n, propNode]

    def drawDataMaxCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':
                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() - 180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()
                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x, y)

                if self.isAtomic(property):

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

                #x = x - 100
                #y = y
                if ceDrawn:
                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                else:
                    x = x -180
                    y = y
                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)

        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(- , ' + card + ')')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]

        return [n, propNode]

    def drawObjMaxCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':

                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:
                # DRAW CE
                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() -180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x - 180, y)

                if self.isAtomic(property):

                    x = x
                    y = y + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = x
                    y = y + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x + 180
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True


                if ceDrawn:
                    x = x
                    y = y + 125

                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
        '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:

                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(- , ' + card + ')')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]
        return [n, propNode]

    def drawDataExactCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':
                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() - 180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()
                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x, y)

                if self.isAtomic(property):

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

                #x = x - 100
                #y = y
                if ceDrawn:
                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                else:
                    x = x -180
                    y = y
                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)

        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(' + card + ' , ' + card + ')')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]
        return [n, propNode]

    def drawObjExactCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':

                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:
                # DRAW CE
                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() -180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x - 180, y)

                if self.isAtomic(property):

                    x = x
                    y = y + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = x
                    y = y + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x + 180
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True


                if ceDrawn:
                    x = x
                    y = y + 125

                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
        '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:

                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        card = str(card)
        n.setText('(' + card + ' , ' + card + ')')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]

        return [n, propNode]

    def drawObjComplementOf(self, operand, diagram, x, y):

        if self.isAtomic(operand):

            iri = operand.getIRI()
            node = self.findNode(operand, diagram) if self.findNode(operand, diagram) !='null' else self.createNode(operand, diagram, x, y)

        else:

            res = self.draw(operand, diagram)
            node = res[0]

        notDrawn = False
        edges = node.edges
        inputEdges = [e for e in edges if e.type() is Item.InputEdge]
        for e in inputEdges:
            if e.target.type() is Item.ComplementNode:
                notNode = e.target
                notDrawn = True

        if not notDrawn:

            notNode = ComplementNode(diagram=diagram)
            x = node.pos().x()+70
            y = node.pos().y()
            starting_y = y
            while not self.isEmpty(x, y, diagram):
                y = y - 50
                if abs(starting_y - y) > 1000:
                    y = starting_y
                    break
            notNode.setPos(x, y)
            self.session.undostack.push(CommandNodeAdd(diagram, notNode))

            input = diagram.factory.create(Item.InputEdge, source=node, target=notNode)
            node.addEdge(input)
            notNode.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            if notNode.pos().y() != node.pos().y():
                x1 = node.pos().x() + 60
                y1 = node.pos().y()
                y2 = notNode.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x1, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))

        return [notNode]

    def drawObjSomeValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':

                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:
                # DRAW CE
                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() -180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x - 180, y)

                if self.isAtomic(property):

                    x = x
                    y = y + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = x
                    y = y + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x + 180
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True


                if ceDrawn:
                    x = x
                    y = y + 125

                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
        '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:

                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]

        return [n, propNode]

    def drawDataSomeValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':
                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() - 180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() - 180
                    y = propNode.pos().y()
                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x, y)

                if self.isAtomic(property):

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

                #x = x - 100
                #y = y
                if ceDrawn:
                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                else:
                    x = x -180
                    y = y
                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
            '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]

        return [n, propNode]

    def drawObjAllValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':

                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:
                # DRAW CE
                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() -180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x - 180, y)

                if self.isAtomic(property):

                    x = x
                    y = y + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = x
                    y = y + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x + 180
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True


                if ceDrawn:
                    x = x
                    y = y + 125

                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
        '''
        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:

                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        n.setText('forall')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]
        return [n, propNode]

    def drawDataAllValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(property, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce):

            ceIri = ce.getIRI()
            isLiteral = False
            if str(ceIri) == 'rdfs:Literal':
                isLiteral = True
            if not ce.isTopEntity() and not isLiteral:

                ceNode = self.findNode(ce, diagram)
                if ceNode != 'null':
                    ceDrawn = True

        if propDrawn:

            if ceDrawn:
                if self.isIsolated(ceNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    ceNode.setPos(x_tomove, y_tomove)
                else:
                    pass

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = propNode.pos().x() - 180
                        y = propNode.pos().y()
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:
                    x = propNode.pos().x() -180
                    y = propNode.pos().y()
                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isIsolated(ceNode):
                    ceNode.setPos(x, y)

                if self.isAtomic(property):

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(ce):
                    if not ce.isTopEntity() and not isLiteral:

                        x = x
                        y = y
                        ceNode = self.createNode(ce, diagram, x, y)
                        ceDrawn = True
                else:

                    res = self.draw(ce, diagram, x, y)
                    ceNode = res[0]
                    ceDrawn = True

                #x = x - 100
                #y = y
                if ceDrawn:
                    x = ceNode.pos().x() + 180
                    y = ceNode.pos().y()

                else:
                    x = x -180
                    y = y
                if self.isAtomic(property):

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            if ceDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = ceNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - ceNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)

        if propNode.type() == Item.RoleInverseNode:

            edges = propNode.edges
            inputEdges = [e for e in edges if e.type() is Item.InputEdge]
            for e in inputEdges:
                if e.source.type() is Item.RoleNode:
                    self.session.undostack.push(CommandItemsRemove(diagram, [propNode, e]))
                    propNode = e.source
                    n = RangeRestrictionNode(diagram=diagram)

        else:

            n = DomainRestrictionNode(diagram=diagram)

        n.setText('forall')

        pos = self.restrictionPos(n, propNode, diagram)
        n.setPos(pos)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if ceDrawn:
            input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
            n.addEdge(input2)
            ceNode.addEdge(input2)

            self.session.undostack.push(CommandEdgeAdd(diagram, input2))

            bps = self.addBreakpoints(diagram, propNode, n, ceNode, None)
            bps.reverse()

            i = len(input2.breakpoints)
            for b in bps:
                self.session.undostack.push(
                    CommandEdgeBreakpointAdd(diagram, input2, i, b))
                i = i + 1
            return [n, propNode, ceNode]

        return [n, propNode]

    def drawObjUnionOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []
        original_x = x
        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':

                    nodes.append(node)
                    xPos.append(node.pos().x())
                    yPos.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = min(xPos)
            starting_y = min(yPos)

        for op in operands:

            if self.isAtomic(op):

                nIri = op.getIRI()
                if self.findNode(op, diagram) == 'null':
                    x = starting_x + 150
                    y = starting_y

                    starting_x = x
                    starting_y = y

                    n = self.createNode(op, diagram, x, y)

                    nodes.append(n)
                    xPos.append(n.pos().x())
                    yPos.append(n.pos().y())
            else:
                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(op, diagram, x, y)
                n = res[0]
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        #x_med = (max(xPos) + min(xPos)) / 2
        x_med = original_x + 130
        #y_med = (max(yPos) + min(yPos)) / 2 - 100
        y_med = max(yPos) - 50
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        union_node = UnionNode(diagram=diagram)
        union_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, union_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=union_node)
            n.addEdge(input)
            union_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            if n.pos().x() != union_node.pos().x():

                if n.pos().x() > union_node.pos().x():
                    x1 = union_node.pos().x() + 60
                    x3 = n.pos().x() - 70

                else:
                    x1 = union_node.pos().x() - 60
                    x3 = n.pos().x() + 70

                y1 = union_node.pos().y()
                x2 = x1
                y2 = union_node.pos().y() + 12
                y3 = y2
                x4 = x3
                y4 = n.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)
                bp4 = QtCore.QPointF(x4, y4)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))

        return [union_node]

    def drawDataUnionOf(self, operands, diagram, x, y):

        x_med = x + 130
        # y_med = (max(yPos) + min(yPos)) / 2 - 100
        y_med = max(y) - 50
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        union_node = UnionNode(diagram=diagram)
        union_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, union_node))

        nodes = []
        xPos = []
        yPos = []

        starting_x = union_node.pos().x() + 130
        starting_y = union_node.pos().y()

        for op in operands:

            if self.isAtomic(op):

                x = starting_x
                y = starting_y

                starting_x = x
                starting_y = y + 50

                n = self.createNode(op, diagram, x, y)

                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

            else:
                x = starting_x
                y = starting_y

                starting_x = x
                starting_y = y + 50

                res = self.draw(op, diagram, x, y)
                n = res[0]
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())


        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=union_node)
            n.addEdge(input)
            union_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            x = union_node.pos().x() + 60
            y2 = union_node.pos().y()
            y1 = n.pos().y()
            if y1 != y2:
                bp1 = QtCore.QPointF(x, y1)
                bp2 = QtCore.QPointF(x, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))

        return [union_node]

    def drawObjOneOf(self, operands, diagram, x, y):

        oneof_node = EnumerationNode(diagram=diagram)
        one_x = x +120
        one_y = y +125

        starting_y = one_y
        while not self.isEmpty(one_x, one_y, diagram):
            one_y = one_y + 50
            if abs(starting_y - one_y) > 1000:
                one_y = starting_y
                break

        oneof_node.setPos(one_x, one_y)
        self.session.undostack.push(CommandNodeAdd(diagram, oneof_node))

        nodes = []
        xPos = []
        yPos = []

        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':

                    nodes.append(node)
                    xPos.append(node.pos().x())
                    yPos.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = min(xPos)
            starting_y = min(yPos)

        starting_x = oneof_node.pos().x() + 130
        starting_y = oneof_node.pos().y()

        for op in operands:

            if self.isAtomic(op):

                nIri = op.getIRI()
                if self.findNode(op, diagram) == 'null':

                    x = starting_x
                    y = starting_y

                    starting_x = x
                    starting_y = y + 75

                    n = self.createNode(op, diagram, x, y)

                    nodes.append(n)
                    xPos.append(n.pos().x())
                    yPos.append(n.pos().y())

            else:

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(op, diagram, x, y)
                n = res[0]
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())


        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=oneof_node)
            n.addEdge(input)
            oneof_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            x = oneof_node.pos().x() + 60
            y2 = oneof_node.pos().y()
            y1 = n.pos().y()
            if y1 != y2:
                bp1 = QtCore.QPointF(x, y1)
                bp2 = QtCore.QPointF(x, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))


        return [oneof_node]

    def drawDataOneOf(self, operands, diagram, x, y):

        oneof_node = EnumerationNode(diagram=diagram)
        one_x = x +120
        one_y = y +125

        starting_y = one_y
        while not self.isEmpty(one_x, one_y, diagram):
            one_y = one_y + 50
            if abs(starting_y - one_y) > 1000:
                one_y = starting_y
                break

        oneof_node.setPos(one_x, one_y)
        self.session.undostack.push(CommandNodeAdd(diagram, oneof_node))

        nodes = []
        xPos = []
        yPos = []

        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':

                    nodes.append(node)
                    xPos.append(node.pos().x())
                    yPos.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = min(xPos)
            starting_y = min(yPos)

        starting_x = oneof_node.pos().x() + 130
        starting_y = oneof_node.pos().y()

        for op in operands:

            if isinstance(op, self.OWLLiteral):

                x = starting_x
                y = starting_y

                starting_x = x
                starting_y = y + 75

                n = self.createNode(op, diagram, x, y)

                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

            elif self.isAtomic(op):

                nIri = op.getIRI()
                if self.findNode(op, diagram) == 'null':

                    x = starting_x
                    y = starting_y

                    starting_x = x
                    starting_y = y + 75

                    n = self.createNode(op, diagram, x, y)

                    nodes.append(n)
                    xPos.append(n.pos().x())
                    yPos.append(n.pos().y())

            else:

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(op, diagram, x, y)
                n = res[0]
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())


        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=oneof_node)
            n.addEdge(input)
            oneof_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            x = oneof_node.pos().x() + 60
            y2 = oneof_node.pos().y()
            y1 = n.pos().y()
            if y1 != y2:
                bp1 = QtCore.QPointF(x, y1)
                bp2 = QtCore.QPointF(x, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))


        return [oneof_node]

    def drawObjIntersectionOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []
        original_x = x
        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    xPos.append(node.pos().x())
                    yPos.append(node.pos().y())

        if len(nodes) == 0:
            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:
            starting_x = min(xPos)
            starting_y = min(yPos)

        for op in operands:

            if self.isAtomic(op):

                nIri = op.getIRI()
                if self.findNode(op, diagram) == 'null':
                    x = starting_x + 150
                    y = starting_y

                    starting_x = x
                    starting_y = y

                    n = self.createNode(op, diagram, x, y)

                    nodes.append(n)
                    xPos.append(n.pos().x())
                    yPos.append(n.pos().y())
            else:
                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(op, diagram, x, y)
                n = res[0]
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        # x_med = (max(xPos) + min(xPos)) / 2
        x_med = original_x + 130
        # y_med = (max(yPos) + min(yPos)) / 2 - 100
        y_med = max(yPos) - 50
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        intersect_node = IntersectionNode(diagram=diagram)
        intersect_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, intersect_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=intersect_node)
            n.addEdge(input)
            intersect_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            if n.pos().x() != intersect_node.pos().x():

                if n.pos().x() > intersect_node.pos().x():
                    x1 = intersect_node.pos().x() + 60
                    x3 = n.pos().x() - 70

                else:
                    x1 = intersect_node.pos().x() - 60
                    x3 = n.pos().x() + 70

                y1 = intersect_node.pos().y()
                x2 = x1
                y2 = intersect_node.pos().y() + 12
                y3 = y2
                x4 = x3
                y4 = n.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)
                bp4 = QtCore.QPointF(x4, y4)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))


        return [intersect_node]

    # DRAW AXIOMS #

    def drawHasKey(self, ce, keys, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in keys:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

            if self.isAtomic(ce):

                cIRI = ce.getIRI()
                cNode = self.findNode(ce, diagram)

                if cNode != 'null':
                    starting_x = cNode.pos().x() - (125 * len(keys)/2)
                    starting_y = cNode.pos().y() + 125


        if len(nodes) > 0:
            starting_x = min(x_positions)
            starting_y = min(y_positions)

        for c in keys:

            if not self.isAtomic(c):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(c, diagram, x, y)
                n = res[0]
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if self.isAtomic(c):

                    iri = c.getIRI()
                    node = self.findNode(c, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(c, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

        # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX + minX) / 2
        # y_med = sum(y_positions) / len(y_positions) -100
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY + minY) / 2
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med + 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        key_node = HasKeyNode(diagram=diagram)
        key_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, key_node))

        for n in nodes:

            input = diagram.factory.create(Item.InputEdge, source=n, target=key_node)
            n.addEdge(input)
            key_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            x = n.pos().x()
            y = key_node.pos().y()
            bp = QtCore.QPointF(x, y)
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp))

        if self.isAtomic(ce):

            cIri = ce.getIRI()
            cNode = self.findNode(ce, diagram) if self.findNode(ce, diagram) != 'null' else self.createNode(ce, diagram, x_med, y_med-75)

            if self.isIsolated(cNode):
                cNode.setPos(x_med, y_med-75)

        else:

            res = self.draw(ce, diagram)
            cNode = res[0]

        in2 = diagram.factory.create(Item.InputEdge, source=cNode, target=key_node)
        self.session.undostack.push(CommandEdgeAdd(diagram, in2))

        return [key_node]

    def drawChain(self, chain, property, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in chain:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 125
            starting_y = y
            if self.isAtomic(property):

                cIRI = property.getIRI()
                cNode = self.findNode(property, diagram)

                if cNode != 'null':

                    starting_x = cNode.pos().x() - (125*len(chain)/2)
                    starting_y = cNode.pos().x() + 125



        if len(nodes) > 0:

            starting_x = min(x_positions)
            starting_y = min(y_positions)

        for prop in chain:

            #if not prop.isType(self.EntityType.OBJECT_PROPERTY):
            if not self.isAtomic(prop):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(prop, diagram, x, y)
                n = res[0]
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:

                iri = prop.getIRI()
                node = self.findNode(prop, diagram)

                if node == 'null':

                    x = starting_x + 125
                    y = starting_y

                    starting_x = x
                    starting_y = y

                    node = self.createNode(prop, diagram, x, y)
                    nodes.append(node)

                    x = node.pos().x()
                    x_positions.append(x)

                    y = node.pos().y()
                    y_positions.append(y)

        x_med = (max(x_positions) + min(x_positions)) / 2
        y_med = ((max(y_positions) + min(y_positions)) / 2) - 100
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med + 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        chain_node = RoleChainNode(diagram=diagram)
        chain_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, chain_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=chain_node)
            n.addEdge(input)
            chain_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            x = n.pos().x()
            y = chain_node.pos().y()
            bp = QtCore.QPointF(x, y)
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp))

        if self.isAtomic(property):
            pIri = property.getIRI()
            pNode = self.findNode(property, diagram) if self.findNode(property,
                                                                  diagram) != 'null' else self.createNode(
                property, diagram, x_med, y_med - 75)

        else:
            res = self.draw(property, diagram)
            pNode = res[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=chain_node, target=pNode)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return [chain_node]

    def drawObjPropertyRange(self, property, rang, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(property, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(rang) and not isinstance(rang, self.OWLLiteral):

            iri = rang.getIRI()
            domainNode = self.findNode(rang, diagram)

            if domainNode != 'null':
                domDrawn = True

        if propDrawn:

            if domDrawn:

                edges = propNode.edges
                inputEdges = [e for e in edges if e.type() is Item.InputEdge]
                for e in inputEdges:
                    if e.source is propNode and e.target.type() is Item.RangeRestrictionNode:
                        node = e.target
                        inputEdges = [e for e in node.edges if e.type() is Item.InputEdge]
                        if len(inputEdges) == 1:
                            for e in node.edges:
                                if e.target is domainNode or e.source is domainNode and e.type() is Item.EquivalenceEdge:
                                    return [node]
                                elif e.target is domainNode and e.type() is Item.InclusionEdge:
                                    return [node]
                                elif e.source is domainNode and e.type() is Item.InclusionEdge:
                                    e_breakpoints = e.breakpoints
                                    command = CommandItemsRemove(diagram, [e])
                                    self.session.undostack.push(command)
                                    equiv = diagram.factory.create(Item.EquivalenceEdge,
                                                                   source=node,
                                                                   target=domainNode)
                                    domainNode.addEdge(equiv)
                                    node.addEdge(equiv)
                                    self.session.undostack.push(CommandEdgeAdd(diagram, equiv))
                                    i = len(equiv.breakpoints)
                                    for b in e_breakpoints:
                                        self.session.undostack.push(
                                            CommandEdgeBreakpointAdd(diagram, equiv, i, b))
                                        i = i + 1

                                    return [node]
                                else:
                                    pass

                if self.isIsolated(domainNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    domainNode.setPos(x_tomove, y_tomove)

            else:

                if self.isAtomic(rang):

                    x = propNode.pos().x()
                    y = propNode.pos().y() - 125
                    domainNode = self.createNode(rang, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x()
                    y = propNode.pos().y() - 125

                    res = self.draw(rang, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(rang):

                    x = x
                    y = y
                    domainNode = self.createNode(rang, diagram, x, y)
                    domDrawn = True

                else:
                    res = self.draw(rang, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            '''
            if domDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = domainNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - domainNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
            '''

        restrNode = RangeRestrictionNode(diagram=diagram)
        pos = self.restrictionPos(restrNode, propNode, diagram)
        restrNode.setPos(pos)

        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        self.addBreakpoints(diagram, propNode, restrNode, domainNode, isa)

        return [restrNode]

    def drawDataPropertyRange(self, property, range, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(property, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(range) and not isinstance(range, self.OWLLiteral):

            iri = range.getIRI()
            domainNode = self.findNode(range, diagram)

            if domainNode != 'null':
                domDrawn = True

        if propDrawn:

            if domDrawn:

                edges = propNode.edges
                inputEdges = [e for e in edges if e.type() is Item.InputEdge]
                for e in inputEdges:
                    if e.source is propNode and e.target.type() is Item.RangeRestrictionNode:
                        node = e.target
                        inputEdges = [e for e in node.edges if e.type() is Item.InputEdge]
                        if len(inputEdges) == 1:
                            for e in node.edges:
                                if e.target is domainNode or e.source is domainNode and e.type() is Item.EquivalenceEdge:
                                    return [node]
                                elif e.target is domainNode and e.type() is Item.InclusionEdge:
                                    return [node]
                                elif e.source is domainNode and e.type() is Item.InclusionEdge:
                                    e_breakpoints = e.breakpoints
                                    command = CommandItemsRemove(diagram, [e])
                                    self.session.undostack.push(command)
                                    equiv = diagram.factory.create(Item.EquivalenceEdge,
                                                                   source=node,
                                                                   target=domainNode)
                                    domainNode.addEdge(equiv)
                                    node.addEdge(equiv)
                                    self.session.undostack.push(CommandEdgeAdd(diagram, equiv))
                                    i = len(equiv.breakpoints)
                                    for b in e_breakpoints:
                                        self.session.undostack.push(
                                            CommandEdgeBreakpointAdd(diagram, equiv, i, b))
                                        i = i + 1
                                    return [node]
                                else:
                                    pass

                if self.isIsolated(domainNode):

                    x_tomove = propNode.pos().x() - 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    domainNode.setPos(x_tomove, y_tomove)

            else:

                if self.isAtomic(range):

                    x = propNode.pos().x() - 180
                    y = propNode.pos().y()
                    domainNode = self.createNode(range, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x() - 180
                    y = propNode.pos().y()

                    res = self.draw(range, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x() + 180
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() + 180
                    y = domainNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(range):

                    x = x
                    y = y
                    domainNode = self.createNode(range, diagram, x, y)
                    domDrawn = True

                else:
                    res = self.draw(range, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x() + 180
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() + 180
                    y = domainNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            if domDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = domainNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - domainNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)

        restrNode = RangeRestrictionNode(diagram=diagram)
        pos = self.restrictionPos(restrNode, propNode, diagram)
        restrNode.setPos(pos)

        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        if domainNode.pos().x() != restrNode.pos().x() and domainNode.pos().y() != restrNode.pos().y():

            bp1 = QtCore.QPointF(domainNode.pos().x() + 50, restrNode.pos().y())
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))

            bp2 = QtCore.QPointF(domainNode.pos().x() + 50, domainNode.pos().y())
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

        return [restrNode]

    def drawObjPropertyDomain(self, property, domain, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(property, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(domain) and not isinstance(domain, self.OWLLiteral):

            iri = domain.getIRI()
            domainNode = self.findNode(domain, diagram)

            if domainNode != 'null':

                domDrawn = True

        if propDrawn:

            if domDrawn:

                edges = propNode.edges
                inputEdges = [e for e in edges if e.type() is Item.InputEdge]
                for e in inputEdges:
                    if e.source is propNode and e.target.type() is Item.DomainRestrictionNode:
                        node = e.target
                        inputEdges = [e for e in node.edges if e.type() is Item.InputEdge]
                        if len(inputEdges) == 1:
                           for e in node.edges:
                                if e.target is domainNode or e.source is domainNode and e.type() is Item.EquivalenceEdge:
                                    return [node]
                                elif e.target is domainNode and e.type() is Item.InclusionEdge:
                                    return [node]
                                elif e.source is domainNode and e.type() is Item.InclusionEdge:
                                    e_breakpoints = e.breakpoints
                                    command = CommandItemsRemove(diagram, [e])
                                    self.session.undostack.push(command)
                                    equiv = diagram.factory.create(Item.EquivalenceEdge,
                                                                 source=node,
                                                                 target=domainNode)
                                    domainNode.addEdge(equiv)
                                    node.addEdge(equiv)
                                    self.session.undostack.push(CommandEdgeAdd(diagram, equiv))
                                    i = len(equiv.breakpoints)
                                    for b in e_breakpoints:
                                        self.session.undostack.push(
                                            CommandEdgeBreakpointAdd(diagram, equiv, i, b))
                                        i = i + 1
                                    return [node]
                                else:
                                    pass

                if self.isIsolated(domainNode):

                    x_tomove = propNode.pos().x() + 200
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    domainNode.setPos(x_tomove, y_tomove)

            else:

                if self.isAtomic(domain):

                    x = propNode.pos().x()
                    y = propNode.pos().y() - 125
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x()
                    y = propNode.pos().y() - 125

                    res = self.draw(domain, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(domain):

                    x = x
                    y = y
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:

                    res = self.draw(domain, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x()
                    y = domainNode.pos().y() + 125

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if domDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 50, Diagram.GridSize), snapF(+propNode.height() / 2 + 50, Diagram.GridSize))
                pos = domainNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+50, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - domainNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
            '''

        restrNode = DomainRestrictionNode(diagram=diagram)
        pos = self.restrictionPos(restrNode, propNode, diagram)
        restrNode.setPos(pos)


        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        self.addBreakpoints(diagram, propNode, restrNode, domainNode, isa)

        return [restrNode]

    def drawDataPropertyDomain(self, property, domain, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(property, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(domain) and not isinstance(domain, self.OWLLiteral):

            iri = domain.getIRI()
            domainNode = self.findNode(domain, diagram)

            if domainNode != 'null':

                domDrawn = True

        if propDrawn:

            if domDrawn:

                edges = propNode.edges
                inputEdges = [e for e in edges if e.type() is Item.InputEdge]
                for e in inputEdges:
                    if e.source is propNode and e.target.type() is Item.DomainRestrictionNode:
                        node = e.target
                        inputEdges = [e for e in node.edges if e.type() is Item.InputEdge]
                        if len(inputEdges) == 1:
                           for e in node.edges:
                                if e.target is domainNode or e.source is domainNode and e.type() is Item.EquivalenceEdge:
                                    return [node]
                                elif e.target is domainNode and e.type() is Item.InclusionEdge:
                                    return [node]
                                elif e.source is domainNode and e.type() is Item.InclusionEdge:
                                    e_breakpoints = e.breakpoints
                                    command = CommandItemsRemove(diagram, [e])
                                    self.session.undostack.push(command)
                                    equiv = diagram.factory.create(Item.EquivalenceEdge,
                                                                 source=node,
                                                                 target=domainNode)
                                    domainNode.addEdge(equiv)
                                    node.addEdge(equiv)
                                    self.session.undostack.push(CommandEdgeAdd(diagram, equiv))
                                    i = len(equiv.breakpoints)
                                    for b in e_breakpoints:
                                        self.session.undostack.push(
                                            CommandEdgeBreakpointAdd(diagram, equiv, i, b))
                                        i = i + 1
                                    return [node]
                                else:
                                    pass

                if self.isIsolated(domainNode):

                    x_tomove = propNode.pos().x() + 180
                    y_tomove = propNode.pos().y()
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 70
                        if abs(propNode.pos().y() - y_tomove) > 1000:
                            y_tomove = propNode.pos().y()
                            break
                    domainNode.setPos(x_tomove, y_tomove)

            else:

                if self.isAtomic(domain):

                    x = propNode.pos().x() + 180
                    y = propNode.pos().y()
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x() + 180
                    y = propNode.pos().y()

                    res = self.draw(domain, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x() - 180
                    y = domainNode.pos().y()

                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() - 180
                    y = domainNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True

            else:

                if self.isAtomic(domain):

                    x = x
                    y = y
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:

                    res = self.draw(domain, diagram, x, y)
                    domainNode = res[0]
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x() - 180
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() - 180
                    y = domainNode.pos().y()

                    res = self.draw(property, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
            '''
            if domDrawn and propDrawn:
                offset = QtCore.QPointF(snapF(-propNode.width() / 2 - 70, Diagram.GridSize), snapF(+propNode.height() / 2 + 70, Diagram.GridSize))
                pos = domainNode.pos() + offset

                while not self.isEmpty(pos.x(), pos.y(), diagram):
                    diff = QtCore.QPointF(0, snapF(+70, Diagram.GridSize))
                    pos = pos + diff
                    if abs(pos.y() - domainNode.pos().y()) > 1000:
                        break

                propNode.setPos(pos)
            '''

        restrNode = DomainRestrictionNode(diagram=diagram)
        pos = self.restrictionPos(restrNode, propNode, diagram)
        restrNode.setPos(pos)


        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        if domainNode.pos().x() != restrNode.pos().x() and domainNode.pos().y() != restrNode.pos().y():

            bp1 = QtCore.QPointF(domainNode.pos().x() - 70, restrNode.pos().y())
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))

            bp2 = QtCore.QPointF(domainNode.pos().x() - 70, domainNode.pos().y())
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))


        return [restrNode]

    def drawInverseObjProperties(self, first, second, diagram, x, y):

        firstDrawn = False
        secondDrawn = False

        if self.isAtomic(first):

            firstIRI = first.getIRI()
            firstNode = self.findNode(first, diagram)
            if firstNode != 'null':

                firstDrawn = True

        if self.isAtomic(second):

            secondIRI = second.getIRI()
            secondNode = self.findNode(second, diagram)

            if secondNode != 'null':
                secondDrawn = True

        if firstDrawn:

            if secondDrawn:

                pass

            else:

                if self.isAtomic(second):

                    x = firstNode.pos().x() + 125
                    y = firstNode.pos().y()
                    secondNode = self.createNode(second, diagram, x, y)
                    secondDrawn = True

                else:

                    x = firstNode.pos().x() + 125
                    y = firstNode.pos().y()

                    res = self.draw(second, diagram, x, y)
                    secondNode = res[0]
                    secondDrawn = True

        else:

            if secondDrawn:

                if self.isAtomic(first):

                    x = secondNode.pos().x() - 125
                    y = secondNode.pos().y()
                    firstNode = self.createNode(first, diagram, x, y)
                    firstDrawn = True

                else:
                    x = secondNode.pos().x() - 125
                    y = secondNode.pos().y()
                    res = self.draw(second, diagram, x, y)
                    firstNode = res[0]
                    firstDrawn = True

            else:

                if self.isAtomic(first):

                    x = x + 125
                    y = y
                    firstNode = self.createNode(first, diagram, x, y)
                    firstDrawn = True

                else:

                    res = self.draw(second, diagram, x+125, y)
                    firstNode = res[0]
                    firstDrawn = True

                if self.isAtomic(second):

                    x = firstNode.pos().x() + 125
                    y = firstNode.pos().y()
                    secondNode = self.createNode(second, diagram, x, y)
                    secondDrawn = True

                else:
                    x = firstNode.pos().x() + 125
                    y = firstNode.pos().y()
                    res = self.draw(second, diagram, x, y)
                    secondNode = res[0]
                    secondDrawn = True

        inv = RoleInverseNode(diagram=diagram)
        #x = (firstNode.pos().x() + secondNode.pos().x()) /2
        x = firstNode.pos().x() + 125
        #y = (firstNode.pos().y() + secondNode.pos().y()) /2
        y = firstNode.pos().y()
        starting_y = y
        while not self.isEmpty(x, y, diagram):
            y = y - 50
            if abs(starting_y - y) > 1000:
                y = starting_y
                break
        inv.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, inv))

        equiv = diagram.factory.create(Item.EquivalenceEdge, source=firstNode, target=inv)
        inv.addEdge(equiv)
        firstNode.addEdge(equiv)
        self.session.undostack.push(CommandEdgeAdd(diagram, equiv))

        if inv.pos().y() != firstNode.pos().y():
            x = firstNode.pos().x() + 70
            y1 = firstNode.pos().y()
            y2 = inv.pos().y()

            bp1 = QtCore.QPointF(x, y1)
            bp2 = QtCore.QPointF(x, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equiv, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equiv, 1, bp2))

        input = diagram.factory.create(Item.InputEdge, source=secondNode, target=inv)
        secondNode.addEdge(input)
        inv.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        x1 = inv.pos().x() + 65
        y1 = inv.pos().y()
        bp1 = QtCore.QPointF(x1, y1)

        if inv.pos().y() == secondNode.pos().y():
            x2 = x1
            y2 = inv.pos().y() - 30

            y3 = y2
            x3 = secondNode.pos().x() - 70

            x4 = x3
            y4 = secondNode.pos().y()

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)
            bp4 = QtCore.QPointF(x4, y4)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))

        elif secondNode.pos().x() == firstNode.pos().x():

            x2 = x1
            y2 = secondNode.pos().y()
            bp2 = QtCore.QPointF(x2, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp1))

        else:

            x2 = x1
            y2 = secondNode.pos().y() + 40

            x3 = secondNode.pos().x()
            y3 = y2

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp1))

        return [inv]

    def drawSubProperty(self, sub, sup, diagram, x, y):

        subDrawn = False
        supDrawn = False

        if self.isAtomic(sub):

            sub_iri = sub.getIRI()
            node0 = self.findNode(sub, diagram)
            if node0 != 'null':
                subDrawn = True

        if self.isAtomic(sup):

            sup_iri = sup.getIRI()
            node1 = self.findNode(sup, diagram)
            if node1 != 'null':
                supDrawn = True

        if subDrawn:

            if supDrawn:

                pass

            else:

                if self.isAtomic(sup):

                    x = node0.pos().x()
                    y = node0.pos().y() - 250
                    node1 = self.createNode(sup, diagram, x, y)
                    supDrawn = True

                else:
                    x = node0.pos().x()
                    y = node0.pos().y() - 250
                    res = self.draw(sup, diagram, x, y)
                    node1 = res[0]
                    supDrawn = True

        else:

            if supDrawn:

                if self.isAtomic(sub):

                    x = node1.pos().x()
                    y = node1.pos().y() + 250
                    node0 = self.createNode(sub, diagram, x, y)
                    subDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 250
                    res = self.draw(sub, diagram, x, y)
                    node0 = res[0]
                    subDrawn = True

            else:

                if self.isAtomic(sup):

                    x = x
                    y = y
                    node1 = self.createNode(sup, diagram, x, y)
                    supDrawn = True

                else:

                    res = self.draw(sup, diagram, x, y)
                    node1 = res[0]
                    supDrawn = True

                if self.isAtomic(sub):

                    x = node1.pos().x()
                    y = node1.pos().y() + 250
                    node0 = self.createNode(sub, diagram, x, y)
                    subDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 250
                    res = self.draw(sub, diagram, x, y)
                    node0 = res[0]
                    subDrawn = True

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=node1)
        node0.addEdge(isa)
        node1.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        if node0.type() is Item.RoleNode:
            if node0.pos().y() == node1.pos().y() and abs(node0.pos().x() - node1.pos().x()) < 130:
                pass

            elif node0.pos().x() == node1.pos().x():

                x1 = node0.pos().x() - 70
                y1 = node0.pos().y()
                y2 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x1, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

            elif node0.pos().y() == node1.pos().y():

                x1 = node0.pos().x() - 40
                y1 = node0.pos().y()
                x2 = x1
                y2 = node0.pos().y() - 35
                x3 = node1.pos().x() + 40
                y3 = y2
                x4 = x3
                y4 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)
                bp4 = QtCore.QPointF(x4, y4)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 2, bp3))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 3, bp4))

            else:

                x1 = node0.pos().x() - 70
                y1 = node0.pos().y()
                x2 = x1
                y2 = node1.pos().y() + 35
                x3 = node1.pos().x()
                y3 = y2

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 2, bp3))

        else:
            if node0.pos().x() == node1.pos().x():

                x1 = node0.pos().x() + 30
                y1 = node0.pos().y()
                x2 = x1
                y2 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))


            else:
                x1 = node0.pos().x() + 30
                y1 = node0.pos().y()
                x2 = node1.pos().x() + 30
                y2 = y1
                x3 = x2
                y3 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 2, bp3))

        return [isa]

    def drawEquivalentClasses(self, expressions, diagram, x, y):

        nodes = []
        singletons = []
        found = None
        propNode = None

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    if self.isIsolated(node):
                        singletons.append(node)

        if len(nodes) == 0:
            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x() - 125
            starting_y = nodes[0].pos().y() + 125

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(ex, diagram, x, y)
                n = res[0]
                if len(res) > 1:
                    restrNode = res[0]
                    propNode = res[1]
                if nodes:
                    cl = nodes[0]

                    if len(res) == 2:
                        if n.type() is Item.DomainRestrictionNode or n.type() is Item.RangeRestrictionNode:
                            type = n.type()
                            restr = n.restriction()
                            items = []
                            for e in n.edges:
                                items.append(e.source)

                            clEdges = [e for e in cl.edges if e.type() is Item.InclusionEdge or e.type() is Item.EquivalenceEdge]
                            for e in clEdges:
                                node = None
                                if e.source.type() is type and e.source.restriction() is restr:
                                    node = e.source
                                elif e.target.type() is type and e.target.restriction() is restr:
                                    node = e.target
                                else:
                                    pass

                                if node:
                                    found = node
                                    inputEdges = [ie for ie in node.edges if ie.type() is Item.InputEdge]
                                    for ie in inputEdges:
                                        if ie.source not in items:
                                            found = None
                                    if found:
                                        break

                if found:
                    nodes.append(found)
                    remove = list(n.edges)
                    remove.append(n)
                    self.session.undostack.push(CommandItemsRemove(diagram, remove))
                else:
                    nodes.append(n)

            else:

                if ex.isType(self.EntityType.CLASS):

                    iri = ex.getIRI()
                    node = self.findNode(ex, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

        node0 = nodes[1] if nodes[0].type() == Item.ConceptNode else nodes[0]
        node1 = nodes[1] if node0 != nodes[1] else nodes[0]

        if singletons:

            toMove = singletons[0]
            fixed = node0 if node0 != toMove else node1

            x_tomove = fixed.pos().x()
            y_tomove = fixed.pos().y() - 125
            while not self.isEmpty(x_tomove, y_tomove, diagram):

                y_tomove = y_tomove + 125
                if abs(fixed.pos().y() - y_tomove) > 1000:

                    y_tomove = fixed.pos().y()
                    break

            toMove.setPos(x_tomove, y_tomove)

        breakpoints = None
        if found:
            eqEdges = [e for e in found.edges if e.type() is Item.EquivalenceEdge]
            if eqEdges:

                return [eqEdges[0]]
            else:
                for e in found.edges:
                    if e.type() is Item.InclusionEdge and (e.source is cl or e.target is cl):
                        self.session.undostack.push(CommandItemsRemove(diagram, [e]))
                        breakpoints = e.breakpoints
                        equivalence = diagram.factory.create(Item.EquivalenceEdge, source=node0,
                                                             target=node1)
                        node0.addEdge(equivalence)
                        node1.addEdge(equivalence)
                        self.session.undostack.push(CommandEdgeAdd(diagram, equivalence))
                        i = 0
                        for b in breakpoints:
                            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, i, b))
                            i = i + 1


        else:
            equivalence = diagram.factory.create(Item.EquivalenceEdge, source=node0, target=node1)
            node0.addEdge(equivalence)
            node1.addEdge(equivalence)

            self.session.undostack.push(CommandEdgeAdd(diagram, equivalence))

        if not breakpoints:
            if propNode:
                if propNode.type() is Item.RoleNode:
                    bps = self.addBreakpoints(diagram, propNode, restrNode, node1, None)

                    #bps.reverse()

                    i = len(equivalence.breakpoints)
                    for b in bps:
                        self.session.undostack.push(
                            CommandEdgeBreakpointAdd(diagram, equivalence, i, b))
                        i = i + 1
                else:
                    if node1.pos().x() != restrNode.pos().x() and node1.pos().y() != restrNode.pos().y():
                        bp1 = QtCore.QPointF(node1.pos().x() - 70, restrNode.pos().y())
                        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))

                        bp2 = QtCore.QPointF(node1.pos().x() - 70, node1.pos().y())
                        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))

            else:
                if node0.pos().y() == node1.pos().y() and abs(node0.pos().x() - node1.pos().x()) < 130:
                    pass

                elif node0.pos().x() == node1.pos().x():

                    x1 = node0.pos().x() + 68
                    y1 = node0.pos().y()
                    y2 = node1.pos().y()


                    bp1 = QtCore.QPointF(x1, y1)
                    bp2 = QtCore.QPointF(x1, y2)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))

                elif node0.pos().y() == node1.pos().y():

                    x1 = node0.pos().x() + 68
                    y1 = node0.pos().y()
                    x2 = x1
                    y2 = node0.pos().y() - 35
                    x3 = node1.pos().x() - 70
                    y3 = y2
                    x4 = x3
                    y4 = node1.pos().y()

                    bp1 = QtCore.QPointF(x1, y1)
                    bp2 = QtCore.QPointF(x2, y2)
                    bp3 = QtCore.QPointF(x3, y3)
                    bp4 = QtCore.QPointF(x4, y4)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 2, bp3))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 3, bp4))

                else:

                    x1 = node0.pos().x() + 68
                    y1 = node0.pos().y()
                    x2 = x1
                    y2 = node1.pos().y() + 40
                    x3 = node1.pos().x()
                    y3 = y2

                    bp1 = QtCore.QPointF(x1, y1)
                    bp2 = QtCore.QPointF(x2, y2)
                    bp3 = QtCore.QPointF(x3, y3)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 2, bp3))

        return [equivalence]

    def drawEquivalentProperties(self, expressions, diagram, x, y):

        nodes = []
        propNode = None

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)

        if len(nodes) == 0:
            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().x()

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y
                res = self.draw(ex, diagram, x, y)
                n = res[0]
                nodes.append(n)

            else:

                if ex.isType(self.EntityType.DATA_PROPERTY) or ex.isType(self.EntityType.OBJECT_PROPERTY):

                    iri = ex.getIRI()
                    node = self.findNode(ex, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

        node0 = nodes[0]
        node1 = nodes[1]

        equivalence = diagram.factory.create(Item.EquivalenceEdge, source=node0, target=node1)
        node0.addEdge(equivalence)
        node1.addEdge(equivalence)

        self.session.undostack.push(CommandEdgeAdd(diagram, equivalence))

        if node0.type() is Item.RoleNode:
            if node0.pos().y() == node1.pos().y() and abs(node0.pos().x() - node1.pos().x()) < 130:
                pass

            elif node0.pos().x() == node1.pos().x():

                x1 = node0.pos().x() - 70
                y1 = node0.pos().y()
                y2 = node1.pos().y()


                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x1, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))

            elif node0.pos().y() == node1.pos().y():

                x1 = node0.pos().x() - 40
                y1 = node0.pos().y()
                x2 = x1
                y2 = node0.pos().y() - 35
                x3 = node1.pos().x() + 40
                y3 = y2
                x4 = x3
                y4 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)
                bp4 = QtCore.QPointF(x4, y4)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 2, bp3))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 3, bp4))

            else:

                x1 = node0.pos().x() - 70
                y1 = node0.pos().y()
                x2 = x1
                y2 = node1.pos().y() + 35
                x3 = node1.pos().x()
                y3 = y2

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 2, bp3))

        else:
            if node0.pos().x() == node1.pos().x():

                x1 = node0.pos().x() + 30
                y1 = node0.pos().y()
                x2 = x1
                y2 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))


            else:
                x1 = node0.pos().x() + 30
                y1 = node0.pos().y()
                x2 = node1.pos().x() + 30
                y2 = y1
                x3 = x2
                y3 = node1.pos().y()

                bp1 = QtCore.QPointF(x1, y1)
                bp2 = QtCore.QPointF(x2, y2)
                bp3 = QtCore.QPointF(x3, y3)

                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, equivalence, 2, bp3))

        return [equivalence]

    def drawClassAssertion(self, indiv, classs, diagram, x, y):

        classDrawn = False
        indivDrawn = False

        if self.isAtomic(classs):

            class_iri = classs.getIRI()
            if self.findNode(classs, diagram) != 'null':

                node1 = self.findNode(classs, diagram)
                classDrawn = True

        if self.isAtomic(indiv):

            indiv_iri = indiv.getIRI()
            if self.findNode(indiv, diagram) != 'null':

                node0 = self.findNode(indiv, diagram)
                indivDrawn = True

        if classDrawn:

            if indivDrawn:

                if self.isIsolated(node0):

                    x_tomove = node1.pos().x()
                    y_tomove = node1.pos().y() + 125
                    while not self.isEmpty(x_tomove, y_tomove, diagram):

                        y_tomove = y_tomove + 125
                        if abs(node1.pos().y() - y_tomove) > 1000:
                            y_tomove = node1.pos().y()
                            break

                    node0.setPos(x_tomove, y_tomove)



                else:

                    if self.isIsolated(node1):

                        x_tomove = node0.pos().x()
                        y_tomove = node0.pos().y() - 125
                        while not self.isEmpty(x_tomove, y_tomove, diagram):

                            y_tomove = y_tomove + 125
                            if abs(node0.pos().y() - y_tomove) > 1000:
                                y_tomove = node0.pos().y()
                                break

                        node1.setPos(x_tomove, y_tomove)

                    else:
                        pass

            else:

                if self.isAtomic(indiv):

                    x = node1.pos().x()
                    y = node1.pos().y() + 125
                    node0 = self.createNode(indiv, diagram, x, y)
                    indivDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 125
                    res = self.draw(indiv, diagram, x, y)
                    node0 = res[0]
                    indivDrawn = True

        else:

            if indivDrawn:

                if self.isAtomic(classs):

                    x = node0.pos().x()
                    y = node0.pos().y() - 125
                    node1 = self.createNode(classs, diagram, x, y)
                    classDrawn = True

                else:

                    x = node0.pos().x()
                    y = node0.pos().y() - 125
                    res = self.draw(classs, diagram, x, y)
                    node1 = res[0]
                    classDrawn = True

            else:

                if self.isAtomic(classs):

                    x = x
                    y = y
                    node1 = self.createNode(classs, diagram, x, y)
                    classDrawn = True

                else:

                    res = self.draw(classs, diagram, x, y)
                    node1 = res[0]
                    classDrawn = True

                if self.isAtomic(indiv):

                    x = node1.pos().x()
                    y = node1.pos().y() + 125
                    node0 = self.createNode(indiv, diagram, x, y)
                    indivDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 125

                    res = self.draw(indiv, diagram, x, y)
                    node0 = res[0]
                    indivDrawn = True

        isa = diagram.factory.create(Item.MembershipEdge, source=node0, target=node1)
        node0.addEdge(isa)
        node1.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        x = node0.pos().x() + 68
        y1 = node0.pos().y()
        y2 = node1.pos().y()

        bp1 = QtCore.QPointF(x, y1)
        bp2 = QtCore.QPointF(x, y2)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))


        return [isa]

    def drawPropertyAssertion(self, prop, indiv, value, diagram, x, y):

        propDrawn = False
        indivDrawn = False
        valueDrawn = False


        if self.isAtomic(prop):
            propIri = prop.getIRI()
            propNode = self.findNode(prop, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(indiv):

            indvIri = indiv.getIRI()
            indivNode = self.findNode(indiv, diagram)
            if indivNode != 'null':
                indivDrawn = True

        if self.isAtomic(value):

            if isinstance(value, self.OWLNamedIndividual):

                valueIri = value.getIRI()
                valueNode = self.findNode(value, diagram)

                if valueNode != 'null':
                    valueDrawn = True

        if propDrawn:

            if indivDrawn:

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width()/2 + 50
                        y = propNode.pos().y() + propNode.height()/2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True
                    else:

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True
                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True


                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True
        else:

            if indivDrawn:

                if self.isAtomic(prop):

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    propNode = self.createNode(prop, diagram, x, y)
                    propDrawn = True
                    x = indivNode.pos().x() + propNode.width()/2 + 50
                    y = indivNode.pos().y() - propNode.height()/2 - 50
                    propNode.setPos(x, y)

                else:

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    res = self.draw(prop, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
                    x = indivNode.pos().x() + propNode.width() / 2 + 50
                    y = indivNode.pos().y() - propNode.height() / 2 - 50
                    propNode.setPos(x, y)

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        propDrawn = True
                        x = valueNode.pos().x() - propNode.width() / 2 - 50
                        y = valueNode.pos().y() - propNode.height() / 2 - 50
                        propNode.setPos(x, y)

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        res = self.draw(prop, diagram, x, y)
                        propNode = res[0]
                        x = valueNode.pos().x() - propNode.width() / 2 - 50
                        y = valueNode.pos().y() - propNode.height() / 2 - 50
                        propNode.setPos(x, y)

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:
                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True


                else:

                    if self.isAtomic(prop):

                        x = x
                        y = y
                        propNode = self.createNode(prop, diagram, x, y)
                        #print(propNode)
                        propDrawn = True

                    else:

                        x = x
                        y = y
                        res = self.draw(prop, diagram, x, y)
                        propNode = res[0]
                        propDrawn = True

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        #print(indivNode)
                        indivDrawn = True

                    else:
                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True

        instanceNode = PropertyAssertionNode(diagram=diagram)
        x = propNode.pos().x()
        y = propNode.pos().y() + propNode.width()/2 + 50
        starting_y = y
        while not self.isEmpty(x, y, diagram):
            y = y + 125
            if abs(starting_y - y) > 1000:
                y = starting_y
                break
        instanceNode.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, instanceNode))

        input1 = diagram.factory.create(Item.InputEdge, source=indivNode, target=instanceNode)
        indivNode.addEdge(input1)
        instanceNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))


        input2 = diagram.factory.create(Item.InputEdge, source=valueNode, target=instanceNode)
        valueNode.addEdge(input2)
        instanceNode.addEdge(input2)
        self.session.undostack.push(CommandEdgeAdd(diagram, input2))


        isa = diagram.factory.create(Item.MembershipEdge, source=instanceNode, target=propNode)
        instanceNode.addEdge(isa)
        propNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        x = propNode.pos().x() + 68
        y1 = instanceNode.pos().y()
        y2 = propNode.pos().y()

        bp1 = QtCore.QPointF(x, y1)
        bp2 = QtCore.QPointF(x, y2)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

        x1 = instanceNode.pos().x()
        y1 = instanceNode.pos().y() - 40
        x2 = instanceNode.pos().x() + 70
        y2 = y1
        x3 = x2
        y3 = indivNode.pos().y()

        bp3 = QtCore.QPointF(x1, y1)
        bp2 = QtCore.QPointF(x2, y2)
        bp1 = QtCore.QPointF(x3, y3)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 1, bp2))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 2, bp3))

        x1 = instanceNode.pos().x()
        y1 = instanceNode.pos().y() - 40
        x2 = instanceNode.pos().x() - 70
        y2 = y1
        x3 = x2
        y3 = valueNode.pos().y()

        bp3 = QtCore.QPointF(x1, y1)
        bp2 = QtCore.QPointF(x2, y2)
        bp1 = QtCore.QPointF(x3, y3)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 1, bp2))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 2, bp3))

        return [instanceNode]

    def drawNegativePropertyAssertion(self, prop, indiv, value, diagram, x, y):

        propDrawn = False
        indivDrawn = False
        valueDrawn = False


        if self.isAtomic(prop):
            propIri = prop.getIRI()
            propNode = self.findNode(prop, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(indiv):

            indvIri = indiv.getIRI()
            indivNode = self.findNode(indiv, diagram)
            if indivNode != 'null':
                indivDrawn = True

        if self.isAtomic(value):

            if isinstance(value, self.OWLNamedIndividual):

                valueIri = value.getIRI()
                valueNode = self.findNode(value, diagram)

                if valueNode != 'null':
                    valueDrawn = True

        if propDrawn:

            if indivDrawn:

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width()/2 + 50
                        y = propNode.pos().y() + propNode.height()/2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True
                    else:

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True
                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True


                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True
        else:

            if indivDrawn:

                if self.isAtomic(prop):

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    propNode = self.createNode(prop, diagram, x, y)
                    propDrawn = True
                    x = indivNode.pos().x() + propNode.width()/2 + 50
                    y = indivNode.pos().y() - propNode.height()/2 - 50
                    propNode.setPos(x, y)

                else:

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    res = self.draw(prop, diagram, x, y)
                    propNode = res[0]
                    propDrawn = True
                    x = indivNode.pos().x() + propNode.width() / 2 + 50
                    y = indivNode.pos().y() - propNode.height() / 2 - 50
                    propNode.setPos(x, y)

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        propDrawn = True
                        x = valueNode.pos().x() - propNode.width() / 2 - 50
                        y = valueNode.pos().y() - propNode.height() / 2 - 50
                        propNode.setPos(x, y)

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        res = self.draw(prop, diagram, x, y)
                        propNode = res[0]
                        x = valueNode.pos().x() - propNode.width() / 2 - 50
                        y = valueNode.pos().y() - propNode.height() / 2 - 50
                        propNode.setPos(x, y)

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:
                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True


                else:

                    if self.isAtomic(prop):

                        x = x
                        y = y
                        propNode = self.createNode(prop, diagram, x, y)
                        #print(propNode)
                        propDrawn = True

                    else:

                        x = x
                        y = y
                        res = self.draw(prop, diagram, x, y)
                        propNode = res[0]
                        propDrawn = True

                    if self.isAtomic(value):

                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() + propNode.width() / 2 + 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(value, diagram, x, y)
                        valueNode = res[0]
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        indivNode = self.createNode(indiv, diagram, x, y)
                        #print(indivNode)
                        indivDrawn = True

                    else:
                        x = propNode.pos().x() - propNode.width() / 2 - 50
                        y = propNode.pos().y() + propNode.height() / 2 + 50
                        res = self.draw(indiv, diagram, x, y)
                        indivNode = res[0]
                        indivDrawn = True

        notNode = self.drawObjComplementOf(propNode, diagram, propNode.x(), propNode.y())

        instanceNode = PropertyAssertionNode(diagram=diagram)
        x = propNode.pos().x()
        y = propNode.pos().y() + propNode.width()/2 + 50
        starting_y = y
        while not self.isEmpty(x, y, diagram):
            y = y + 125
            if abs(starting_y - y) > 1000:
                y = starting_y
                break
        instanceNode.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, instanceNode))

        input1 = diagram.factory.create(Item.InputEdge, source=indivNode, target=instanceNode)
        indivNode.addEdge(input1)
        instanceNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))


        input2 = diagram.factory.create(Item.InputEdge, source=valueNode, target=instanceNode)
        valueNode.addEdge(input2)
        instanceNode.addEdge(input2)
        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        input3 = diagram.factory.create(Item.InputEdge, source=propNode, target=notNode)
        propNode.addEdge(input3)
        notNode.addEdge(input3)
        self.session.undostack.push(CommandEdgeAdd(diagram, input3))

        isa = diagram.factory.create(Item.MembershipEdge, source=instanceNode, target=notNode)
        instanceNode.addEdge(isa)
        propNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        x = propNode.pos().x() + 65
        y1 = instanceNode.pos().y()
        y2 = propNode.pos().y()

        bp1 = QtCore.QPointF(x, y1)
        bp2 = QtCore.QPointF(x, y2)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

        x1 = instanceNode.pos().x()
        y1 = instanceNode.pos().y() - 40
        x2 = indivNode.pos().x() + 70
        y2 = y1
        x3 = x2
        y3 = indivNode.pos().y()

        bp3 = QtCore.QPointF(x1, y1)
        bp2 = QtCore.QPointF(x2, y2)
        bp1 = QtCore.QPointF(x3, y3)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 1, bp2))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input1, 2, bp3))

        x1 = instanceNode.pos().x()
        y1 = instanceNode.pos().y() - 40
        x2 = valueNode.pos().x() - 70
        y2 = y1
        x3 = x2
        y3 = valueNode.pos().y()

        bp3 = QtCore.QPointF(x1, y1)
        bp2 = QtCore.QPointF(x2, y2)
        bp1 = QtCore.QPointF(x3, y3)

        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 0, bp1))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 1, bp2))
        self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input2, 2, bp3))

        return [instanceNode]

    def drawDiffIndiv(self, individuals, diagram, x, y):

        nodes = []
        for e in individuals:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)

        if len(nodes) == 0:
            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().y()

        for i in individuals:

            # if not i.isType(self.EntityType.NAMED_INDIVIDUAL):
            if not self.isAtomic(i):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(i, diagram, x, y)
                n = res[0]
                nodes.append(n)

            else:
                if i.isType(self.EntityType.NAMED_INDIVIDUAL):

                    iri = i.getIRI()
                    node = self.findNode(i, diagram)

                    if node == 'null':
                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(i, diagram, x, y)

                        nodes.append(node)

        node0 = nodes[0]
        node1 = nodes[1]

        different = diagram.factory.create(Item.DifferentEdge, source=node0, target=node1)
        node0.addEdge(different)
        node1.addEdge(different)

        self.session.undostack.push(CommandEdgeAdd(diagram, different))

        if node0.pos().y() == node1.pos().y() and abs(node0.pos().x() - node1.pos().x()) < 130:
            pass

        elif node0.pos().x() == node1.pos().x():

            x1 = node0.pos().x() + 70
            y1 = node0.pos().y()
            y2 = node1.pos().y()


            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x1, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 1, bp2))

        elif node0.pos().y() == node1.pos().y():

            x1 = node0.pos().x() + 68
            y1 = node0.pos().y()
            x2 = x1
            y2 = node0.pos().y() - 35
            x3 = node1.pos().x() - 70
            y3 = y2
            x4 = x3
            y4 = node1.pos().y()

            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)
            bp4 = QtCore.QPointF(x4, y4)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 2, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 3, bp4))

        else:

            x1 = node0.pos().x() + 68
            y1 = node0.pos().y()
            x2 = x1
            y2 = node1.pos().y() + 35
            x3 = node1.pos().x()
            y3 = y2

            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, different, 2, bp3))

        return [different]

    def drawSameIndiv(self, individuals, diagram, x, y):

        nodes = []

        for e in individuals:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)


        if len(nodes) == 0:

            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:

            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().y()

        for i in individuals:

            if not self.isAtomic(i):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(i, diagram, x, y)
                n = res[0]
                nodes.append(n)

            else:
                if i.isType(self.EntityType.NAMED_INDIVIDUAL):

                    iri = i.getIRI()
                    node = self.findNode(i, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(i, diagram, x, y)

                        nodes.append(node)

        node0 = nodes[0]
        node1 = nodes[1]

        same = diagram.factory.create(Item.SameEdge, source=node0, target=node1)
        node0.addEdge(same)
        node1.addEdge(same)

        self.session.undostack.push(CommandEdgeAdd(diagram, same))

        if node0.pos().y() == node1.pos().y() and abs(node0.pos().x() - node1.pos().x()) < 130:
            pass

        elif node0.pos().x() == node1.pos().x():

            x1 = node0.pos().x() + 70
            y1 = node0.pos().y()
            y2 = node1.pos().y()


            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x1, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 1, bp2))

        elif node0.pos().y() == node1.pos().y():

            x1 = node0.pos().x() + 68
            y1 = node0.pos().y()
            x2 = x1
            y2 = node0.pos().y() - 35
            x3 = node1.pos().x() - 70
            y3 = y2
            x4 = x3
            y4 = node1.pos().y()

            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)
            bp4 = QtCore.QPointF(x4, y4)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 2, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 3, bp4))

        else:

            x1 = node0.pos().x() + 68
            y1 = node0.pos().y()
            x2 = x1
            y2 = node1.pos().y() + 35
            x3 = node1.pos().x()
            y3 = y2

            bp1 = QtCore.QPointF(x1, y1)
            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, same, 2, bp3))

        return [same]

    def drawDisjointClasses(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []
        singletons = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':

                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

                    if self.isIsolated(node):
                        singletons.append(node)

        if len(nodes) == 0:

            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 125
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(ex, diagram, x, y)
                n = res[0]
                nodes.append(n)

            else:

                if ex.isType(self.EntityType.CLASS):

                    iri = ex.getIRI()
                    node = self.findNode(ex, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

        fixed = nodes[0]
        if singletons:

            toMove = singletons[0]
            fixed = nodes[0] if nodes[0] != toMove else nodes[1]

            x_tomove = fixed.pos().x()
            y_tomove = fixed.pos().y() - 125
            while not self.isEmpty(x_tomove, y_tomove, diagram):

                x_tomove = x_tomove + 125
                if abs(fixed.pos().x() - x_tomove) > 1000:

                    x_tomove = fixed.pos().x()
                    break

            toMove.setPos(x_tomove, y_tomove)

        x_positions = [n.pos().x() for n in nodes]
        y_positions = [n.pos().y() for n in nodes]

        #x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        #x_med = (maxX + minX) / 2
        x_med = fixed.pos().x() + 125
        # y_med = sum(y_positions) / len(y_positions)
        maxY = max(y_positions)
        minY = min(y_positions)
        #y_med = (maxY + minY) / 2
        y_med = fixed.pos().y()
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        dis_node = ComplementNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        node0 = nodes[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
        node0.addEdge(isa)
        dis_node.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        if dis_node.pos().y() != node0.pos().y():
            x = node0.pos().x() + 70
            y1 = node0.pos().y()
            y2 = dis_node.pos().y()

            bp1 = QtCore.QPointF(x, y1)
            bp2 = QtCore.QPointF(x, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))


        node1 = nodes[1]

        input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
        node1.addEdge(input)
        dis_node.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        x1 = dis_node.pos().x() + 65
        y1 = dis_node.pos().y()
        bp1 = QtCore.QPointF(x1, y1)

        if dis_node.pos().y() == node1.pos().y():
            x2 = x1
            y2 = dis_node.pos().y() - 30

            y3 = y2
            x3 = node1.pos().x() - 70

            x4 = x3
            y4 = node1.pos().y()

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)
            bp4 = QtCore.QPointF(x4, y4)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))

        elif node1.pos().x() == node0.pos().x():

            x2 = x1
            y2 = node1.pos().y()
            bp2 = QtCore.QPointF(x2, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp1))

        else:

            x2 = x1
            y2 = node1.pos().y() + 40

            x3 = node1.pos().x()
            y3 = y2

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp1))

        return [dis_node]

    def drawDisjointUnion(self, classes, classs, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in classes:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

            if self.isAtomic(classs):

                cIRI = classs.getIRI()
                cNode = self.findNode(classs, diagram)

                if cNode != 'null':

                    starting_x = cNode.pos().x() - (150*len(classes))
                    starting_y = cNode.pos().x() + 150


        if len(nodes) > 0:

            starting_x = min(x_positions)
            starting_y = min(y_positions)

        for c in classes:

            if not self.isAtomic(c):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                res = self.draw(c, diagram, x, y)
                n = res[0]
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if c.isType(self.EntityType.CLASS):

                    iri = c.getIRI()
                    node = self.findNode(c, diagram)

                    if node == 'null':

                        x = starting_x + 150
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(c, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

        singletons = [n for n in nodes if self.isIsolated(n)]
        fixed = [n for n in nodes if not self.isIsolated(n)]
        if singletons:
            if fixed:
                point_x = fixed[0].pos().x()
                point_y = fixed[0].pos().y() + 50
            else:
                point_x = x - 150
                point_y = y

            for s in singletons:
                s.setPos(point_x, point_y)
                point_x = point_x + 100

        x_positions = [n.pos().x() for n in nodes]
        y_positions = [n.pos().y() for n in nodes]
        # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX - minX) / 2
        # y_med = sum(y_positions) / len(y_positions) -100
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY - minY) / 2


        if self.isAtomic(classs):

            cIri = classs.getIRI()
            cNode = self.findNode(classs, diagram) if self.findNode(classs, diagram) != 'null' else self.createNode(classs, diagram, x_med, y_med-100)

            if self.isIsolated(cNode):
                cNode.setPos(x_med, y_med-100)
            else:
                if singletons and not fixed:
                    point_x = cNode.pos().x() - 150*len(singletons)
                    point_y = cNode.pos().y() + 200
                    for s in singletons:
                        s.setPos(point_x, point_y)
                        point_x = point_x + 100

                    x_positions = [n.pos().x() for n in nodes]
                    y_positions = [n.pos().y() for n in nodes]
                    # x_med = sum(x_positions) / len(x_positions)
                    maxX = max(x_positions)
                    minX = min(x_positions)
                    x_med = (maxX - minX) / 2
                    # y_med = sum(y_positions) / len(y_positions) -100
                    maxY = max(y_positions)
                    minY = min(y_positions)
                    y_med = (maxY - minY) / 2

        else:

            res = self.draw(classs, diagram)
            cNode = res[0]

        x_med = cNode.pos().x()
        y_med = cNode.pos().y() + 40

        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        dis_node = DisjointUnionNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=dis_node)
            n.addEdge(input)
            dis_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

            y = dis_node.pos().y()

            bp1 = QtCore.QPointF(n.pos().x(), y)
            b1 = CommandEdgeBreakpointAdd(diagram, input, 0, bp1)

            self.session.undostack.push(b1)

        equiv = diagram.factory.create(Item.EquivalenceEdge, source=cNode, target=dis_node)
        self.session.undostack.push(CommandEdgeAdd(diagram, equiv))

        return [dis_node]

    def drawDisjointDataProperties(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x
            starting_y = y - 50

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x
                y = starting_y + 50

                starting_x = x
                starting_y = y

                res = self.draw(ex, diagram, x, y)
                n = res[0]
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if ex.isType(self.EntityType.DATA_PROPERTY):
                    iri = ex.getIRI()
                    node = self.findNode(ex, diagram)

                    if node == 'null':

                        x = starting_x
                        y = starting_y + 50

                        starting_x = x
                        starting_y = y
                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

                fixed = nodes[0]
                # x_med = sum(x_positions) / len(x_positions)
                maxX = max(x_positions)
                minX = min(x_positions)
                # x_med = (maxX + minX) / 2
                x_med = fixed.pos().x() - 180
                # y_med = sum(y_positions) / len(y_positions)
                maxY = max(y_positions)
                minY = min(y_positions)
                # y_med = (maxY + minY) / 2
                y_med = fixed.pos().y()
                starting_y = y_med
                while not self.isEmpty(x_med, y_med, diagram):
                    y_med = y_med - 50
                    if abs(starting_y - y_med) > 1000:
                        y_med = starting_y
                        break
                dis_node = ComplementNode(diagram=diagram)
                dis_node.setPos(x_med, y_med)
                self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

                node0 = nodes[0]

                isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
                node0.addEdge(isa)
                dis_node.addEdge(isa)

                self.session.undostack.push(CommandEdgeAdd(diagram, isa))

                if dis_node.pos().y() != node0.pos().y():
                    x = node0.pos().x() - 12
                    y1 = node0.pos().y()
                    y2 = dis_node.pos().y()

                    bp1 = QtCore.QPointF(x, y1)
                    bp2 = QtCore.QPointF(x, y2)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

                node1 = nodes[1]

                input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
                node1.addEdge(input)
                dis_node.addEdge(input)

                self.session.undostack.push(CommandEdgeAdd(diagram, input))

                x1 = dis_node.pos().x() + 30
                y1 = dis_node.pos().y()
                bp1 = QtCore.QPointF(x1, y1)


                if node1.pos().x() == node0.pos().x():

                    x2 = x1
                    y2 = node1.pos().y()
                    bp2 = QtCore.QPointF(x2, y2)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp2))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp1))

                else:

                    x2 = x1
                    y2 = node1.pos().y() + 40

                    x3 = node1.pos().x() - 12
                    y3 = y2

                    x4 = x3
                    y4 = node1.pos().y()

                    bp2 = QtCore.QPointF(x2, y2)
                    bp3 = QtCore.QPointF(x3, y3)
                    bp4 = QtCore.QPointF(x4, y4)

                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
                    self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))

                return [dis_node]

    def drawDisjointObjectProperties(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(e, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 125
            starting_y = y

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]


        for ex in expressions:

            if not self.isAtomic(ex):

                res = self.draw(ex, diagram, starting_x+125, starting_y)
                n = res[0]

                starting_x = starting_x+125

                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if ex.isType(self.EntityType.OBJECT_PROPERTY):

                    iri = ex.getIRI()
                    node = self.findNode(ex, diagram)

                    if node == 'null':

                        x = starting_x + 125
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

        fixed = nodes[0]
        # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        # x_med = (maxX + minX) / 2
        x_med = fixed.pos().x() + 125
        # y_med = sum(y_positions) / len(y_positions)
        maxY = max(y_positions)
        minY = min(y_positions)
        # y_med = (maxY + minY) / 2
        y_med = fixed.pos().y()
        starting_y = y_med
        while not self.isEmpty(x_med, y_med, diagram):
            y_med = y_med - 50
            if abs(starting_y - y_med) > 1000:
                y_med = starting_y
                break
        dis_node = ComplementNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        node0 = nodes[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
        node0.addEdge(isa)
        dis_node.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        if dis_node.pos().y() != node0.pos().y():
            x = node0.pos().x() + 70
            y1 = node0.pos().y()
            y2 = dis_node.pos().y()

            bp1 = QtCore.QPointF(x, y1)
            bp2 = QtCore.QPointF(x, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

        node1 = nodes[1]

        input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
        node1.addEdge(input)
        dis_node.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        x1 = dis_node.pos().x() + 65
        y1 = dis_node.pos().y()
        bp1 = QtCore.QPointF(x1, y1)

        if dis_node.pos().y() == node1.pos().y():
            x2 = x1
            y2 = dis_node.pos().y() - 30

            y3 = y2
            x3 = node1.pos().x() - 70

            x4 = x3
            y4 = node1.pos().y()

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)
            bp4 = QtCore.QPointF(x4, y4)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp4))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 3, bp1))

        elif node1.pos().x() == node0.pos().x():

            x2 = x1
            y2 = node1.pos().y()
            bp2 = QtCore.QPointF(x2, y2)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp1))

        else:

            x2 = x1
            y2 = node1.pos().y() + 40

            x3 = node1.pos().x()
            y3 = y2

            bp2 = QtCore.QPointF(x2, y2)
            bp3 = QtCore.QPointF(x3, y3)

            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 0, bp3))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 1, bp2))
            self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, input, 2, bp1))

        return [dis_node]

    # ATOMIC OPERATIONS #

    def createNode(self, ex, diagram, x, y):

        # create atomic node: Class, Attribute, Role, Individual, Literal, Datatype #
        move = 70
        if isinstance(ex, self.OWLLiteral):
            move = 50
        elif ex.isType(self.EntityType.DATA_PROPERTY):
            move = -50
        elif ex.isType(self.EntityType.OBJECT_PROPERTY) or ex.isType(self.EntityType.NAMED_INDIVIDUAL):
            move = 125
        elif ex.isType(self.EntityType.CLASS):
            move = 250
        starting_y = y
        while not self.isEmpty(x, y, diagram):

            y = y + move
            if abs(starting_y - y) > 1000:

                y = starting_y
                break

        if isinstance(ex, self.OWLLiteral):

            lit = str(ex.getLiteral())
            DP = ex.getDatatype()

            iri = DP.getIRI()

            d = self.project.getIRI(str(iri))
            lang = None
            literal = Literal(lit, d, lang)

            literalNode = LiteralNode(literal=literal, diagram=diagram)
            literalNode.setPos(x, y)

            literalNode._literal = literal
            self.session.undostack.push(CommandNodeAdd(diagram, literalNode))

            labelString = str(literal)
            labelPos = lambda: literalNode.label.pos()
            literalNode.label.diagram.removeItem(literalNode.label)
            literalNode.label = NodeLabel(template=labelString, pos=labelPos, editable=False)
            diagram.sgnUpdated.emit()

            literalNode.doUpdateNodeLabel()

            return literalNode

        if ex.isType(self.EntityType.CLASS):

            iri = IRI(str(ex.getIRI()))
            classs = ConceptNode(iri= iri, diagram=diagram)
            classs.iri = iri
            classs.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, classs))

            classs.doUpdateNodeLabel()

            return classs

        if ex.isType(self.EntityType.NAMED_INDIVIDUAL):

            iri = IRI(str(ex.getIRI()))
            indiv = IndividualNode(iri=iri, diagram=diagram)
            indiv.iri = iri
            indiv.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, indiv))
            # ANNOTATIONS #
            self.addAnnotationAssertions(iri)

            indiv.doUpdateNodeLabel()
            return indiv

        if ex.isType(self.EntityType.DATA_PROPERTY):

            iri = IRI(str(ex.getIRI()))
            dataProp = AttributeNode(iri=iri, diagram=diagram)
            dataProp.iri = iri
            dataProp.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, dataProp))

            conn = None
            try:
                conn = sqlite3.connect(self.db_filename)
            except Exception as e:
                print(e)

            cursor = conn.cursor()
            # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
            cursor.execute('''SELECT ontology_iri, ontology_version
                                    FROM importation
                                    WHERE project_iri = ? and project_version = ?
                                    ''', (self.project_iri, self.project_version))

            project_ontologies = []
            rows = cursor.fetchall()
            for row in rows:
                project_ontologies.append((row[0], row[1]))

            with conn:
                functional_dataProp = []

                for ontology in project_ontologies:
                    # for each imported ontology:
                    # get the functional data properties
                    ontology_iri, ontology_version = ontology

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                        FROM axiom
                                        WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'FunctionalDataProperty'
                                        ''', (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        functional_dataProp.extend(d.values())

            if str(iri) in functional_dataProp:

                dataProp.setFunctional(True)

            # ANNOTATIONS #
            self.addAnnotationAssertions(iri)

            dataProp.doUpdateNodeLabel()

            return dataProp

        if ex.isType(self.EntityType.OBJECT_PROPERTY):

            iri = IRI(str(ex.getIRI()))
            objectProp = RoleNode(iri=iri, diagram=diagram)
            objectProp.iri = iri
            objectProp.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, objectProp))

            conn = None
            try:
                conn = sqlite3.connect(self.db_filename)
            except Exception as e:
                print(e)

            cursor = conn.cursor()
            # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
            cursor.execute('''SELECT ontology_iri, ontology_version
                                                FROM importation
                                                WHERE project_iri = ? and project_version = ?
                                                ''', (self.project_iri, self.project_version))

            project_ontologies = []
            rows = cursor.fetchall()
            for row in rows:
                project_ontologies.append((row[0], row[1]))

            with conn:
                functional_objProp = []
                transitive_objProp = []
                symmetric_objProp = []
                asymmetric_objProp = []
                reflexive_objProp = []
                irreflexive_objProp = []
                inverseFunc_objProp = []

                for ontology in project_ontologies:
                    # for each imported ontology:
                    # get the functional data properties
                    ontology_iri, ontology_version = ontology

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                                    FROM axiom
                                                    WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'FunctionalObjectProperty'
                                                    ''', (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        functional_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                    FROM axiom
                                    WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'InverseFunctionalObjectProperty'
                                    ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        inverseFunc_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                   FROM axiom
                                  WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'TransitiveObjectProperty'
                                  ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        transitive_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                  FROM axiom
                                  WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'SymmetricObjectProperty'
                                  ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        symmetric_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                   FROM axiom
                                   WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'AsymmetricObjectProperty'
                                   ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        asymmetric_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                                      FROM axiom
                                                      WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'ReflexiveObjectProperty'
                                                      ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        reflexive_objProp.extend(d.values())

                    cursor = conn.cursor()
                    cursor.execute('''SELECT iri_dict
                                   FROM axiom
                                   WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom = 'IrreflexiveObjectProperty'
                                    ''',
                                   (ontology_iri, ontology_version))

                    rows = cursor.fetchall()

                    for row in rows:
                        iri_dict = row[0]
                        d = ast.literal_eval(iri_dict)
                        irreflexive_objProp.extend(d.values())


            if str(iri) in functional_objProp:
                objectProp.setFunctional(True)
            if str(iri) in inverseFunc_objProp:
                objectProp.setInverseFunctional(True)
            if str(iri) in transitive_objProp:
                objectProp.setTransitive(True)
            if str(iri) in symmetric_objProp:
                objectProp.setSymmetric(True)
            if str(iri) in asymmetric_objProp:
                objectProp.setAsymmetric(True)
            if str(iri) in reflexive_objProp:
                objectProp.setReflexive(True)
            if str(iri) in irreflexive_objProp:
                objectProp.setIrreflexive(True)

            # ANNOTATIONS #
            self.addAnnotationAssertions(iri)

            objectProp.doUpdateNodeLabel()

            return objectProp

        if ex.isType(self.EntityType.DATATYPE):

            iri = IRI(str(ex.getIRI()))
            datatype = ValueDomainNode(iri=iri, diagram=diagram)
            datatype.iri = iri
            datatype.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, datatype))

            datatype.doUpdateNodeLabel()

            return datatype

        return

    def findNode(self, item, diagram):
        Types = {
            Item.AttributeNode: 'DataProperty',
            Item.ConceptNode: 'Class',
            Item.IndividualNode: 'NamedIndividual',
            Item.RoleNode: 'ObjectProperty',
        }

        ### FIND NODE BY IRI IN THE DIAGRAM ###
        for el in diagram.items():

            if el.isNode() and  el.type() in Types.keys() and (Types[el.type()] == str(item.getEntityType())) and str(item.getIRI()) == str(el.iri):
                return el

        # IF NOT FOUND, RETURN 'NULL'
        return 'null'

    def isEmpty(self, x, y, diagram):
        # check if position x, y of diagram is empty #
        for el in diagram.items():

            if el.isNode() and el.type() == Item.ConceptNode and abs(el.pos().y() - y) < 52 and abs(
                el.pos().x() - x) < 112:
                return False

            if el.isNode() and (
                el.type() == Item.IndividualNode or el.type() == Item.LiteralNode) and abs(
                el.pos().y() - y) < 62 and abs(el.pos().x() - x) < 62:
                return False

            if el.isNode() and el.type() == Item.RoleNode and abs(el.pos().y() - y) < 52 and abs(
                el.pos().x() - x) < 72:
                return False

            if el.isNode() and el.type() == Item.AttributeNode and abs(
                el.pos().y() - y) < 22 and abs(el.pos().x() - x) < 22:
                return False

            if el.isNode() and (
                el.type() == Item.RangeRestrictionNode or el.type() == Item.DomainRestrictionNode) and abs(
                el.pos().y() - y) < 22 and abs(el.pos().x() - x) < 22:
                return False

            if el.isNode() and el.type() == Item.ValueDomainNode and abs(
                el.pos().y() - y) < 42 and abs(el.pos().x() - x) < 92:
                return False

            if el.isNode() and el.type() in [Item.ComplementNode, Item.RoleInverseNode,
                                             Item.RoleChainNode, Item.DisjointUnionNode,
                                             Item.ConceptNode, Item.UnionNode,
                                             Item.IntersectionNode, Item.HasKeyNode,
                                             Item.EnumerationNode,
                                             Item.DatatypeRestrictionNode] and abs(
                el.pos().y() - y) < 32 and abs(el.pos().x() - x) < 52:
                return False

            if el.isNode() and el.type() == Item.PropertyAssertionNode and abs(
                el.pos().y() - y) < 32 and abs(el.pos().x() - x) < 54:
                return False

            if el.isNode() and el.type() == Item.FacetNode and abs(
                el.pos().y() - y) < 42 and abs(el.pos().x() - x) < 82:
                return False

        return True

    def isAtomic(self, operand):
        # check if operand is atomic #
        if isinstance(operand, self.OWLClass) or isinstance(operand, self.OWLObjectProperty) or isinstance(operand, self.OWLDataProperty) or isinstance(operand, self.OWLDatatype) or isinstance(operand, self.OWLLiteral) or isinstance(operand, self.OWLNamedIndividual):

            return True

        else:

            return False

    def isIsolated(self, node):

        edges = node.edges
        if edges:
            return False
        else:
            return True

    def restrictionPos(self, restriction, source, scene):

        size = Diagram.GridSize
        offsets = (
            QtCore.QPointF(snapF(+source.width() / 2 + 50, size), 0),
            QtCore.QPointF(snapF(-source.width() / 2 - 50, size), 0),
            QtCore.QPointF(0, snapF(-source.height() / 2 - 50, size)),
            QtCore.QPointF(0, snapF(+source.height() / 2 + 50, size)),
            QtCore.QPointF(snapF(-source.width() / 2 - 50, size),
                           snapF(-source.height() / 2 - 50, size)),
            QtCore.QPointF(snapF(+source.width() / 2 + 50, size),
                           snapF(-source.height() / 2 - 50, size)),
            QtCore.QPointF(snapF(-source.width() / 2 - 50, size),
                           snapF(+source.height() / 2 + 50, size)),
            QtCore.QPointF(snapF(+source.width() / 2 + 50, size),
                           snapF(+source.height() / 2 + 50, size)),
        )
        pos = source.pos() + offsets[0]
        num = sys.maxsize
        rad = QtCore.QPointF(restriction.width() / 2, restriction.height() / 2)
        for o in offsets:
            p = source.pos() + o
            if self.isEmpty(p.x(), p.y(), scene):
                count = len(scene.items(
                    QtCore.QRectF(source.pos() + o - rad, source.pos() + o + rad)))
                if count < num:
                    num = count
                    pos = source.pos() + o
                    return pos
        return pos

    def addAnnotationAssertions(self, iri):
        conn = None
        try:
            conn = sqlite3.connect(self.db_filename)
        except Exception as e:
            print(e)

        cursor = conn.cursor()
        # GET ALL THE ONTOLOGIES IMPORTED IN THE PROJECT #
        cursor.execute('''SELECT ontology_iri, ontology_version
                                                        FROM importation
                                                        WHERE project_iri = ? and project_version = ?
                                                        ''',
                       (self.project_iri, self.project_version))

        project_ontologies = []
        rows = cursor.fetchall()
        for row in rows:
            project_ontologies.append((row[0], row[1]))

        with conn:
            for ontology in project_ontologies:
                # for each imported ontology:
                ontology_iri, ontology_version = ontology
                cursor = conn.cursor()
                # get all annotationAssertion axioms #
                cursor.execute('''select iri_dict
                                    from axiom
                                    where ontology_iri = ? and ontology_version = ? and type_of_axiom = 'AnnotationAssertion'
                                    ''', (ontology_iri, ontology_version))

                rows = cursor.fetchall()
                annotations = []
                for row in rows:
                    # for each annAss axiom, get iri_dict #
                    iri_dict = row[0]
                    d = ast.literal_eval(iri_dict)
                    # if current iri == subject -> keep annAss axiom #
                    if str(iri) == d['subject']:
                        annotations.append(d)

                for annAss in annotations:

                    sub = annAss['subject']
                    subjectIRI = self.project.getIRI(sub)
                    # GET PROPERTY
                    property = annAss['property']
                    # GET VALUE
                    value = annAss['value']
                    # IF LANGUAGE, GET LANGUAGE
                    lang_srt = value.find('"@')
                    lang = None
                    if lang_srt > 0:
                        lang = value[lang_srt + 2:]
                        value = value[0: lang_srt + 1]

                    value = value.strip('"')

                    if value == '' or value is None:
                        continue

                    else:

                        annotation = str(property)
                        annotation = annotation.replace('<', '')
                        annotation = annotation.replace('>', '')

                        annotationIRI = self.project.getIRI(annotation)

                        try:

                            if annotationIRI not in self.project.getAnnotationPropertyIRIs():

                                self.project.isValidIdentifier(annotation)

                                command = CommandProjectAddAnnotationProperty(self.project,
                                                                              annotation)
                                self.session.undostack.beginMacro(
                                    'Add annotation property {0} '.format(annotation))
                                if command:
                                    self.session.undostack.push(command)
                                self.session.undostack.endMacro()

                        except IllegalNamespaceError as e:
                            # noinspection PyArgumentList
                            msgBox = QtWidgets.QMessageBox(
                                QtWidgets.QMessageBox.Warning,
                                'Entity Definition Error',
                                'Illegal namespace defined.',
                                informativeText='The string "{}" is not a legal IRI'.format(
                                    annotation),
                                detailedText=str(e),
                                parent=self,
                            )
                            msgBox.exec_()


                        # INSTANCE OF ANNOTATION WITH IRI, PROPERTY, VALUE, LANGUAGE
                        annotationAss = AnnotationAssertion(subjectIRI, annotationIRI, value,
                                                            language=lang)

                        self.session.undostack.push(
                            CommandIRIAddAnnotationAssertion(self.project, iri, annotationAss))

    def addBreakpoints(self, diagram, propNode, restrNode, domainNode, isa):

        bps = []

        if propNode.pos().x() == domainNode.pos().x():
            if restrNode.pos().x() > domainNode.pos().x():
                # x = restrNode.pos().x() + 40
                x = domainNode.pos().x() + 68
            else:
                # x = restrNode.pos().x() - 40
                x = domainNode.pos().x() - 68

            y1 = restrNode.pos().y()
            y2 = domainNode.pos().y()

            bp1 = QtCore.QPointF(x, y1)
            bps.append(bp1)

            bp2 = QtCore.QPointF(x, y2)
            bps.append(bp2)

            if isa:
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))

        elif restrNode.pos().y() == domainNode.pos().y():

            if restrNode.pos().x() > domainNode.pos().x():
                # x = restrNode.pos().x() + 40
                x = restrNode.pos().x() + 30
            else:
                # x = restrNode.pos().x() - 40
                x = restrNode.pos().x() - 30

            y1 = restrNode.pos().y()
            y2 = restrNode.pos().y() - 40
            x3 = domainNode.pos().x()
            y3 = y2

            bp1 = QtCore.QPointF(x, y1)
            bps.append(bp1)

            bp2 = QtCore.QPointF(x, y2)
            bps.append(bp2)

            bp3 = QtCore.QPointF(x3, y3)
            bps.append(bp3)

            if isa:
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 2, bp3))

        elif propNode.pos().x() != domainNode.pos().x() and restrNode.pos().y() != domainNode.pos().y():

            if restrNode.pos().x() > propNode.pos().x():
                x1 = restrNode.pos().x() + 30

            else:
                x1 = restrNode.pos().x() - 30

            y1 = restrNode.pos().y()
            x2 = x1
            # y2 = restrNode.pos().y() - 28
            y2 = restrNode.pos().y() - 40
            if restrNode.pos().y() != propNode.pos().y():
                if restrNode.pos().y() > propNode.pos().y():
                    y2 = restrNode.pos().y() - 30
                else:
                    y2 = restrNode.pos().y() + 40
            x3 = domainNode.pos().x() + 70
            y3 = y2
            x4 = x3
            y4 = domainNode.pos().y()

            bp1 = QtCore.QPointF(x1, y1)
            bps.append(bp1)

            bp2 = QtCore.QPointF(x2, y2)
            bps.append(bp2)

            bp3 = QtCore.QPointF(x3, y3)
            bps.append(bp3)

            bp4 = QtCore.QPointF(x4, y4)
            bps.append(bp4)

            if isa:
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 0, bp1))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 1, bp2))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 2, bp3))
                self.session.undostack.push(CommandEdgeBreakpointAdd(diagram, isa, 3, bp4))

        return bps


class DiagramPropertiesForm(NewDiagramForm):
    """
    Subclass of `NewDiagramForm` which allows also to input the
    spacing between class items in the generated diagram.
    """
    MinSize = 5000
    MaxSize = 50000
    MinSpace = 250
    MaxSpace = 500

    def __init__(self, project=None, **kwargs):
        """
        Initialize the new diagram properties dialog.
        """
        super().__init__(project, **kwargs)

        self.sizeLabel = QtWidgets.QLabel('Diagram size:', self)
        # noinspection PyArgumentList
        self.sizeSlider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, self, toolTip='New diagram size',
            minimum=DiagramPropertiesForm.MinSize, maximum=DiagramPropertiesForm.MaxSize,
            objectName='size_slider')
        self.sizeValue = QtWidgets.QLabel(f'{self.sizeSlider.value()} px', self)
        self.spaceLabel = QtWidgets.QLabel('Item spacing:', self)
        # noinspection PyArgumentList
        self.spaceSlider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, self, toolTip='Spacing between class items',
            minimum=DiagramPropertiesForm.MinSpace, maximum=DiagramPropertiesForm.MaxSpace,
            objectName='spacing_slider')
        self.valueLabel = QtWidgets.QLabel(f'{self.spaceSlider.value()} px', self)

        self.propertiesGroup = QtWidgets.QGroupBox('Properties', self)
        self.sizeLayout = QtWidgets.QHBoxLayout()
        self.sizeLayout.addWidget(self.sizeLabel)
        self.sizeLayout.addWidget(self.sizeSlider)
        self.sizeLayout.addWidget(self.sizeValue)
        self.spacingLayout = QtWidgets.QHBoxLayout()
        self.spacingLayout.addWidget(self.spaceLabel)
        self.spacingLayout.addWidget(self.spaceSlider)
        self.spacingLayout.addWidget(self.valueLabel)
        self.propertiesLayout = QtWidgets.QVBoxLayout(self.propertiesGroup)
        self.propertiesLayout.addLayout(self.sizeLayout)
        self.propertiesLayout.addLayout(self.spacingLayout)

        self.mainLayout.insertWidget(self.mainLayout.indexOf(self.warnLabel), self.propertiesGroup)
        self.mainLayout.insertSpacing(self.mainLayout.indexOf(self.warnLabel), 4)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Set new diagram properties')
        connect(self.sizeSlider.valueChanged, self.onSizeChanged)
        connect(self.spaceSlider.valueChanged, self.onSpacingChanged)

    #############################################
    #   SLOTS
    #################################

    def onSizeChanged(self, value: int) -> None:
        """
        Executed when the size slider value changes.
        """
        self.sizeValue.setText(f'{self.diagramSize()} px')

    def onSpacingChanged(self, value: int) -> None:
        """
        Executed when the spacing slider value changes.
        """
        self.valueLabel.setText(f'{self.spacing()} px')

    #############################################
    #   INTERFACE
    #################################

    def diagramSize(self) -> int:
        """
        Returns the currently selected diagram size.
        """
        return self.sizeSlider.value()

    def spacing(self) -> int:
        """
        Returns the currently selected spacing.
        """
        return self.spaceSlider.value()


class DatabaseError(RuntimeError):
    """Raised whenever there is a problem with the import database."""
    pass
