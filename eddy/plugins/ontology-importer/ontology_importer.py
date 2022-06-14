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

from abc import ABCMeta
import ast
import os
import sqlite3

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.diagram import CommandDiagramResize
from eddy.core.commands.edges import CommandEdgeAdd
from eddy.core.commands.iri import CommandChangeIRIOfNode
from eddy.core.commands.iri import CommandIRIAddAnnotationAssertion
from eddy.core.commands.nodes import CommandNodeAdd
from eddy.core.commands.project import CommandProjectAddAnnotationProperty
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.attribute import AttributeNode
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
from eddy.core.owl import (
    AnnotationAssertion,
    IllegalNamespaceError,
    OWL2Datatype,
)
from eddy.core.owl import IRI
from eddy.core.owl import Literal
from eddy.core.plugin import AbstractPlugin
from eddy.ui.fields import IntegerField
from eddy.ui.progress import BusyProgressDialog


class OntologyImporterPlugin(AbstractPlugin):

    def __init__(self, spec, session):
        """
        Initialize the plugin.
        :type spec: PluginSpec
        :type session: session
        """
        super().__init__(spec, session)
        self.vm = None
        self.space = 150

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
                #print('annotation:', ax)
                annotations.append(ax)
        return annotations

    def importAnnotations(self, diagram):

        annotations = self.getAnnotations()
        # FOR EACH ANNOTATION
        for ann in annotations:
            QtCore.QCoreApplication.processEvents()

            # GET IRI
            iri = ann.getSubject()
            # GET PROPERTY
            property = ann.getProperty()
            # GET VALUE
            value = ann.getValue() if isinstance(ann.getValue(), str) else str(ann.getValue())

            try:
                annIRI = str(property)
                annIRI = annIRI.replace('<', '')
                annIRI = annIRI.replace('>', '')
                listProperties = [str(el) for el in list(self.project.annotationProperties)]

                if annIRI not in listProperties:
                    self.project.isValidIdentifier(annIRI)

                    command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                    self.session.undostack.beginMacro(
                        'Add annotation property {0} '.format(annIRI))
                    if command:
                        self.session.undostack.push(command)
                    self.session.undostack.endMacro()


            except IllegalNamespaceError as e:
                # noinspection PyArgumentList
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Entity Definition Error')
                msgbox.setText('The string "{}" is not a legal IRI'.format(annIRI)+'\n'+str(e))
                # msgbox.setText('There is no imported ontology associated with this Project')
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()


            # IF LANGUAGE, GET LANGUAGE
            lang_srt = value.find('"@')
            lang = None
            if lang_srt > 0:
                lang = value[lang_srt + 2:]
                value = value[0: lang_srt]

            # INSTANCE OF ANNOTATION WITH IRI, PROPERTY, VALUE, LANGUAGE
            annotation = AnnotationAssertion(iri, annIRI, value, language=lang)


            # FOR EACH NODE WITH NODE.IRI == IRI
            for el in diagram.items():

                if el.isNode() and el.type() == Item.ConceptNode and str(iri) == str(el.iri):
                    ## ADD ANNOTATION ##
                    #el.iri.addAnnotationAssertion(annotation)
                    self.session.undostack.push(CommandIRIAddAnnotationAssertion(self.project, el.iri, annotation))


        ontoAnno = self.ontology.getAnnotations()
        for ann in ontoAnno:
            QtCore.QCoreApplication.processEvents()

            # GET IRI
            iri = IRI(str(self.ontology_iri))
            # GET PROPERTY
            property = ann.getProperty()
            # GET VALUE
            value = ann.getValue() if isinstance(ann.getValue(), str) else str(ann.getValue())

            try:
                annIRI = str(property)
                annIRI = annIRI.replace('<', '')
                annIRI = annIRI.replace('>', '')
                listProperties = [str(el) for el in list(self.project.annotationProperties)]

                if annIRI not in listProperties:
                    self.project.isValidIdentifier(annIRI)

                    command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                    self.session.undostack.beginMacro(
                            'Add annotation property {0} '.format(annIRI))
                    if command:
                        self.session.undostack.push(command)
                    self.session.undostack.endMacro()


            except IllegalNamespaceError as e:
                # noinspection PyArgumentList
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Entity Definition Error')
                msgbox.setText(
                        'The string "{}" is not a legal IRI'.format(annIRI) + '\n' + str(e))
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()
            # IF LANGUAGE, GET LANGUAGE
            lang_srt = value.find('"@')
            lang = None
            if lang_srt > 0:
                lang = value[lang_srt + 2:]
                value = value[0: lang_srt]

            # INSTANCE OF ANNOTATION WITH IRI, PROPERTY, VALUE, LANGUAGE
            annotation = AnnotationAssertion(iri, annIRI, value, language=lang)

            self.session.undostack.push(CommandIRIAddAnnotationAssertion(self.project, self.project.ontologyIRI, annotation))

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

    def onToolbarButtonClick(self):

        ### IMPORT FILE OWL ###
        dialog = QtWidgets.QFileDialog(self.session.mdi, "open owl file", expandPath('~'), "owl file (*.owl)")

        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)

        if dialog.exec_():

            self.filePath = dialog.selectedFiles()

            ### SET SPACE BETWEEN ITEMS ###
            space_form = SpaceForm(self.session)
            if space_form.exec_():

                self.space = space_form.spaceField.value()

                ### CREATE NEW DIAGRAM ###
                self.session.doNewDiagram()
                diagram = self.session.mdi.activeDiagram()

                self.vm = getJavaVM()
                if not self.vm.isRunning():
                    self.vm.initialize()
                self.vm.attachThreadToJVM()

                ### IMPORT OWL API ###
                if True:
                    self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
                    self.JavaFileClass = self.vm.getJavaClass('java.io.File')
                    self.Type = self.vm.getJavaClass('org.semanticweb.owlapi.model.AxiomType')
                    self.Set = self.vm.getJavaClass('java.util.Set')
                    self.Searcher = self.vm.getJavaClass('org.semanticweb.owlapi.search.Searcher')
                    self.OWLObjectInverseOf = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectInverseOf")
                    self.OWLEquivalence = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLEquivalentObjectPropertiesAxiom")
                    self.OWLSubObjectPropertyOf = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLSubObjectPropertyOfAxiom")
                    self.OWLSubDataPropertyOf = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLSubDataPropertyOfAxiom")
                    self.OWLEquivalentAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLEquivalentClassesAxiom")
                    self.OWLDataSomeValuesFrom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLDataSomeValuesFrom")
                    self.OWLSubClassOfAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLSubClassOfAxiom")
                    self.OWLObjectUnionOf = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectUnionOf")
                    self.OWLDisjointClassesAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLDisjointClassesAxiom")
                    self.OWLObjectSomeValuesFrom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectSomeValuesFrom")
                    self.OWLObjectPropertyDomainAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectPropertyDomainAxiom")
                    self.OWLObjectPropertyRangeAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectPropertyRangeAxiom")
                    self.OWLEquivalentObjectProperties = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLEquivalentObjectPropertiesAxiom")
                    self.OWLObjectAllValuesFrom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectAllValuesFrom")
                    self.OWLRestriction = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLRestriction")
                    self.OWLObjectMaxCardinality = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectMaxCardinality")
                    self.OWLObjectMinCardinality = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectMinCardinality")
                    self.OWLObjectComplementOf = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLObjectComplementOf")
                    self.OWLDeclarationAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLDeclarationAxiom")
                    self.EntityType = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.EntityType")
                    self.OWLAnnotationAssertionAxiom = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.OWLAnnotationAssertionAxiom")
                    self.AxiomType = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.model.AxiomType")
                    self.ManchesterOWLSyntaxOWLObjectRendererImpl = self.vm.getJavaClass(
                        "org.semanticweb.owlapi.manchestersyntax.renderer.ManchesterOWLSyntaxOWLObjectRendererImpl")
                    self.OWLSubAnnotationPropertyOfAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubAnnotationPropertyOfAxiom')

                if diagram:

                    ## show progress bar while drawing hierarchy ##
                    with BusyProgressDialog('Loading Ontology', 0.5):

                        try:

                            for x in dialog.selectedFiles():

                                QtCore.QCoreApplication.processEvents()

                                self.fileInstance = self.JavaFileClass(x)
                                QtCore.QCoreApplication.processEvents()

                                self.manager = self.OWLManager().createOWLOntologyManager()
                                QtCore.QCoreApplication.processEvents()

                                self.ontology = self.manager.loadOntologyFromOntologyDocument(
                                    self.fileInstance)

                                self.ontology_iri = self.ontology.getOntologyID().getOntologyIRI().get().toString()
                                try:
                                    self.ontology_version = self.ontology.getOntologyID().getVersionIRI().get().toString()
                                except Exception:
                                    self.ontology_version = self.ontology.getOntologyID().getOntologyIRI().get().toString()


                                QtCore.QCoreApplication.processEvents()

                                db_filename = expandPath('@data/db.db')
                                dir = db_filename[:-6]
                                if not os.path.exists(dir):
                                    os.makedirs(dir)

                                schema_script = '''
                                                create table if not exists ontology (
                                                    iri     text,
                                                    version test,
                                                    PRIMARY KEY (iri, version)
                                                );

                                                create table if not exists project (
                                                    iri     text,
                                                    version test,
                                                    PRIMARY KEY (iri, version)
                                                );

                                                create table if not exists importation (
                                                    project_iri text,
                                                    project_version text,
                                                    ontology_iri text,
                                                    ontology_version    text,
                                                    session_id  text,
                                                    PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version),
                                                    FOREIGN KEY (project_iri, project_version) references project(iri, version),
                                                    FOREIGN KEY (ontology_iri, ontology_version) references ontology(iri, version)
                                                );

                                                create table if not exists axiom (
                                                    axiom       text,
                                                    type_of_axiom   text,
                                                    ontology_iri    text,
                                                    ontology_version text,
                                                    iri_dict text,
                                                    PRIMARY KEY (axiom, ontology_iri, ontology_version),
                                                    FOREIGN KEY (ontology_iri, ontology_version) references ontology(iri, version)
                                                );

                                                create table if not exists drawn (
                                                    project_iri text,
                                                    project_version text,
                                                    ontology_iri    text,
                                                    ontology_version text,
                                                    axiom text,
                                                    session_id  text,
                                                    PRIMARY KEY (project_iri, project_version, ontology_iri, ontology_version, axiom),
                                                    FOREIGN KEY (project_iri, project_version, ontology_iri, ontology_version, session_id) references importation(project_iri, project_version, ontology_iri, ontology_version, session_id) on delete cascade,
                                                    FOREIGN KEY (axiom, ontology_iri, ontology_version) references axiom(axiom, ontology_iri, ontology_version)
                                                );'''

                                db_is_new = not os.path.exists(db_filename)
                                conn = sqlite3.connect(db_filename)
                                cursor = conn.cursor()
                                QtCore.QCoreApplication.processEvents()

                                if db_is_new:
                                    #print('Creazione dello schema')
                                    conn.executescript(schema_script)
                                    conn.commit()


                                QtCore.QCoreApplication.processEvents()

                                #print('Nuova Importazione')
                                self.project.version = self.project.version if len(
                                    self.project.version) > 0 else '1.0'

                                importation = Importation(self.project)
                                importation.insertInDB(self.ontology)

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

                            ### REMOVE DUPLICATE FROM IRI ###
                            self.removeDuplicateFromIRI(diagram)
                            QtCore.QCoreApplication.processEvents()

                            ### IMPORT ANNOTATIONS ###
                            self.importAnnotations(diagram)
                            QtCore.QCoreApplication.processEvents()

                            renderer = self.ManchesterOWLSyntaxOWLObjectRendererImpl()

                            ### COUNT PROCESSED AXIOMS ###
                            processed = []
                            not_processed = []
                            total = []

                            for ax in self.axioms:

                                total.append(ax)

                                if isinstance(ax, self.OWLAnnotationAssertionAxiom) or (isinstance(ax,
                                                                                                   self.OWLSubClassOfAxiom) and not ax.getSuperClass().isAnonymous() and not ax.getSubClass().isAnonymous()) or (
                                    isinstance(ax, self.OWLDeclarationAxiom) and ax.getEntity().isType(
                                    self.EntityType.CLASS)) or (
                                    isinstance(ax, self.OWLDeclarationAxiom) and ax.getEntity().isType(
                                    self.EntityType.ANNOTATION_PROPERTY)) or (
                                isinstance(ax, self.OWLSubAnnotationPropertyOfAxiom)):
                                    ### INSERT DRAWN AXIOMS IN Drawn Table ###
                                    # GET AXIOM IN Manchester Syntax #
                                    axiom = renderer.render(ax)
                                    # INSERT #
                                    conn.execute("""
                                                                insert or ignore into drawn (project_iri, project_version, ontology_iri, ontology_version, axiom, session_id)
                                                                values (?, ?, ?, ?, ?, ?)
                                                                """, (
                                    str(self.project.ontologyIRI), self.project.version,
                                    self.ontology_iri, self.ontology_version, str(axiom),
                                    str(self.session)))
                                    conn.commit()
                                    processed.append(ax)
                                    QtCore.QCoreApplication.processEvents()

                                else:

                                    not_processed.append(ax)

                            # axs, not_dr, dr = importation.open()
                            QtCore.QCoreApplication.processEvents()

                            conn.commit()
                            conn.close()

                        except Exception as e:
                            raise e



    def onSecondButtonClick(self):

        try:
            # TRY TO OPEN IMPORTATIONS ASSOCIATED WITH THIS PROJECT #
            importation = Importation(self.project)
            axs, not_dr, dr = importation.open()
            if not_dr:
                window = AxiomsWindow(not_dr, self.project)
                if window.exec_():
                    print('ok')
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
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('No Ontology Imported')
            #msgbox.setText(str(e))
            msgbox.setText('There is no ontology imported in the current project')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()

    def onNoSave(self):

        importation = Importation(self.project)
        importation.removeFromDB()

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """

        # INITIALIZE THE WIDGETS
        self.myButton = QtWidgets.QToolButton(self.session, icon=QtGui.QIcon(':/icons/24/ic_system_update'))
        self.myButton2 = QtWidgets.QToolButton(self.session, icon=QtGui.QIcon(':/icons/48/ic_format_list_bulleted_black'))

        # CREATE VIEW TOOLBAR BUTTONS
        self.session.widget('view_toolbar').addSeparator()
        self.session.widget('view_toolbar').addWidget(self.myButton)
        # self.session.widget('view_toolbar').addSeparator()
        self.session.widget('view_toolbar').addWidget(self.myButton2)

        # CONFIGURE SIGNALS/SLOTS
        connect(self.myButton.clicked, self.onToolbarButtonClick)
        connect(self.myButton2.clicked, self.onSecondButtonClick)
        connect(self.session.sgnNoSaveProject, self.onNoSave)


# importation in DB #
class Importation():

    def __init__(self, project):

        self.project = project
        self.project_iri = str(self.project.ontologyIRI)
        self.project_version = self.project.version if len(self.project.version) > 0 else '1.0'

        self.db_filename = expandPath('@data/db.db')
        dir = self.db_filename[:-6]
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.ManchesterOWLSyntaxOWLObjectRendererImpl = self.vm.getJavaClass(
            "org.semanticweb.owlapi.manchestersyntax.renderer.ManchesterOWLSyntaxOWLObjectRendererImpl")
        self.ShortFormProvider = self.vm.getJavaClass("org.semanticweb.owlapi.util.SimpleShortFormProvider")
        self.OWLEntity = self.vm.getJavaClass("org.semanticweb.owlapi.model.OWLEntity")
        self.DataFactoryImpl = self.vm.getJavaClass("uk.ac.manchester.cs.owl.owlapi.OWLDataFactoryImpl")

        #self.insertInDB(project_name, diagram_name, ontology)

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
                iri_dict = str(d)
                #print(iri_dict)

                # getting the axiom in Manchester Syntax #
                axiom = renderer.render(ax)
                QtCore.QCoreApplication.processEvents()

                # INSERT AXIOM IN DB #
                conn.execute("""
                            insert or ignore into axiom (axiom, type_of_axiom, ontology_iri, ontology_version, iri_dict)
                            values (?, ?, ?, ?, ?)
                            """, (str(axiom), str(ax_type), ontology_iri, ontology_version, iri_dict))

            conn.commit()
            #print('Assiomi Inseriti')
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
            return

        else:
            # INSERT IMPORTATION IN DB #
            conn.execute("""
                            insert into importation (project_iri, project_version, ontology_iri, ontology_version, session_id)
                            values (?, ?, ?, ?, ?)
                            """, (self.project_iri, self.project_version, ontology_iri, ontology_version, str(session)))
            conn.commit()
            conn.close()
            #print('Importazione Inserita')

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
                cursor.execute('''SELECT axiom
                                FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ?''', (ontology_iri, ontology_version))
                rows = cursor.fetchall()
                axioms[ontology] = []
                for row in rows:
                    axioms[ontology].append(row[0])
                #print('Assiomi Estratti')

                # NOT DRAWN #
                cursor.execute('''SELECT axiom, type_of_axiom
                                FROM axiom
                                WHERE ontology_iri = ? and ontology_version = ? and type_of_axiom != 'Declaration'
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
                for row in rows:
                    not_drawn[ontology].append(row[0])
                    #print(row[0], row[1])

                # DRAWN #
                drawn[ontology] = [a for a in axioms[ontology] if a not in not_drawn[ontology]]

            #print('Distinzione Disegnati e non')
            return axioms, not_drawn, drawn

    def removeFromDB(self):

        db_exists = os.path.exists(self.db_filename)
        if db_exists:

            conn = sqlite3.connect(self.db_filename)

            with conn:
                ### REMOVE IMPORTATIONS NOT SAVED ###
                conn.execute(
                        'delete from importation where project_iri = ? and project_version = ? and session_id = ?',
                        (self.project_iri, self.project_version, str(self.project.session)))
                conn.commit()
                ### REMOVE DRAWS NOT SAVED ###
                conn.execute(
                        'delete from drawn where project_iri = ? and project_version = ? and session_id = ?',
                        (self.project_iri, self.project_version, str(self.project.session)))
                conn.commit()

class AxiomsWindow(QtWidgets.QDialog):

    def __init__(self, not_drawn, project):

        super().__init__()
        self.resize(500, 400)
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

        self.db_filename = expandPath('@data/db.db')
        dir = self.db_filename[:-6]
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.project = project
        self.project_iri = str(project.ontologyIRI)
        self.project_version = project.version if len(project.version) > 0 else '1.0'
        self.session = project.session

        self.checkedAxioms = []

        ## create layout ##
        # Create an outer layout
        layout1 = QtWidgets.QVBoxLayout()

        # create scroll_area
        scroll_area = QtWidgets.QScrollArea(widgetResizable=True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setWidgetResizable(True)

        scroll_area.setLayout(layout1)

        innerWidget = QtWidgets.QWidget()
        # Create a layout for the checkboxes
        layout2 = QtWidgets.QVBoxLayout()

        # add OK and Cancel buttons
        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        # add Searchbar
        self.searchbar = QtWidgets.QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)
        layout2.addWidget(self.searchbar)

        # Add some checkboxes to the layout
        self.checkBoxes = []

        # add checkboxes with axioms
        # grouped by ontology
        for k in not_drawn.keys():

            onto = k[1]+':'
            a = QtWidgets.QLabel(onto)
            a.setFont(QtGui.QFont('AnyStyle', 8, QtGui.QFont.DemiBold))
            layout1.addWidget(a)
            for ax in not_drawn[k]:

                check = QtWidgets.QCheckBox(str(ax))
                check.setChecked(False)
                check.stateChanged.connect(self.checkAxiom)
                layout1.addWidget(check)
                self.checkBoxes.append(check)

        # Nest the inner layouts into the outer layout
        layout2.addWidget(scroll_area)
        innerWidget.setLayout(layout1)
        scroll_area.setWidget(innerWidget)

        connect(self.confirmationBox.rejected, self.reject)
        connect(self.confirmationBox.accepted, self.accept)

        layout2.addWidget(self.confirmationBox)

        # Set the window's main layout
        self.setLayout(layout2)

    def update_display(self, text):

        # searchbar function #
        for check in self.checkBoxes:

            if text.lower() in check.text().lower():

                check.show()

            else:

                check.hide()

    def checkAxiom(self, state):

        axiom = self.sender().text()

        if state:

            # ON SELECTION OF AN AXIOM -> ADD TO CHECKEDAXIOMS and enable OK #
            self.checkedAxioms.append(axiom)
            self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        else:
            # ON de-SELECTION OF AN AXIOM -> REMOVE FROM CHECKEDAXIOMS and if empty: disable OK #
            self.checkedAxioms.remove(axiom)
            if len(self.checkedAxioms) == 0:
                self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def reject(self):

        self.checkedAxioms = []
        super().reject()

    def accept(self):

        # k: axiom (::string), value: manchester_axiom (::Axiom)
        # (to keep track of the string axiom to insert in DRAWN table)
        axiomsToDraw = {}

        for ax in self.checkedAxioms:
            # for each checked axiom:

            manchester_axiom = self.string2axiom(ax)
            axiomsToDraw[ax] = manchester_axiom

        super().accept()
        self.getInvolvedDiagrams(axiomsToDraw)

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
                            WHERE ontology_iri = ? and ontology_version = ? and axiom = ?
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
                cursor.execute('''SELECT axiom, iri_dict
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
                                 'xsd:dateTime', 'xsd: dateTimeStamp', 'rdf:XMLLiteral',
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
                                WHERE ontology_iri = ? and ontology_version = ? and axiom = ?
                                ''',
                               (ontology_iri, ontology_version, ax))
                rows = cursor.fetchall()
                for row in rows:
                    iri_dict = row[0]
                    d = ast.literal_eval(iri_dict)
                    axiom_type = row[1]

                try:
                    manchester_axiom = False
                    '''
                    ## handle declaration axioms ##
                    # for each type of entity declared: get fullIRI, create entity
                    # -> manchester_axiom = declaration of entity

                    if new_ax[:13] == 'DataProperty:':
                        declaration_axiom = new_ax[14:]
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        owlDataProp = self.OWLDataPropertyImpl(iri)
                        manchester_axiom = df.getOWLDeclarationAxiom(owlDataProp)
                    if new_ax[:15] == 'ObjectProperty:':
                        declaration_axiom = new_ax[16:]
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        owlObjProp = self.OWLObjectPropertyImpl(iri)
                        manchester_axiom = df.getOWLDeclarationAxiom(owlObjProp)
                    if new_ax[:11] == 'Individual:':
                        declaration_axiom = new_ax[12:]
                        entity = d[declaration_axiom]
                        iri = self.IRI.create(entity)
                        owlNamedInd = self.OWLNamedIndividualImpl(iri)
                        manchester_axiom = df.getOWLDeclarationAxiom(owlNamedInd)
                    '''
                    ## handle DisjointClasses and DifferentIndividuals axiom ##
                    # for each class/individual : get fullIRI, create class/individual
                    # -> machester_axiom = disjoint/different of classes/individuals
                    if new_ax[:17] == ' DisjointClasses:':
                        classes = [x.strip() for x in new_ax[18:].split(',')]

                        owlClasses = []
                        for cl in classes:
                            # IRI =  d[class name] #
                            entity = d[cl]
                            iri = self.IRI.create(entity)
                            owlClass = self.OWLClassImpl(iri)
                            owlClasses.append(owlClass)

                        manchester_axiom = df.getOWLDisjointClassesAxiom(owlClasses)
                    if new_ax[:22] == ' DifferentIndividuals:':
                        individuals = [x.strip() for x in new_ax[23:].split(',')]

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

                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle("Axiom Can't be Drawn")
                    msgbox.setText(str(e))
                    #msgbox.setText('This axiom: \n' + ax + "\n can't be drawn")
                    msgbox.setTextFormat(QtCore.Qt.RichText)
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msgbox.exec_()

        return manchester_axiom

    def getInvolvedDiagrams(self, axioms):
        # axioms : {k:str_axiom, value: ManchesterAxiom}

        # GET ALL ELEMENTS INVOLVED IN AXIOMS #
        elements = {}
        for str_ax in axioms.keys():
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
                iri = el.getIRI()
                for diagram in project_diagrams:
                # for each diagram of the project:
                    if diagram.name not in involvedDiagrams[k]:
                    # if not already involved:
                        # check if there is an item with same IRI as element
                        for item in diagram.items():
                            if item.isNode() and (item.type() == Item.ConceptNode or item.type() == Item.IndividualNode or item.type() == Item.AttributeNode or item.type == Item.RoleNode) and str(iri) == str(item.iri):
                                involvedDiagrams[k].append(diagram.name)

        axiomsDict = {}
        for str_ax in axioms.keys():

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

        for str_ax in dict.keys():
            axiom = dict[str_ax]['axiom']
            diagrams = dict[str_ax]['involvedDiagrams']
            #print(axiom, diagrams)

            if len(diagrams) == 0:
                # if no diagram involved:
                # draw on the activeOne
                diag = self.session.mdi.activeDiagram()
                n = self.draw(axiom, diag)

            if len(diagrams) == 1:
                # if only one diagram involved:
                # draw on the one
                diag = diagrams[0]
                project_diagrams = self.project.diagrams()
                for d in project_diagrams:
                    if d.name == diag:
                        diagram = d
                        break
                n = self.draw(axiom, diagram)

            if len(diagrams) > 1:
                # if more than one diagram involved:
                # draw on the activeOne if involved
                diag = self.session.mdi.activeDiagram()
                if diag.name in diagrams:

                    n = self.draw(axiom, diag)
                # else draw on any of the involved ones
                else:
                    diag = diagrams[0]
                    project_diagrams = self.project.diagrams()
                    for d in project_diagrams:
                        if d.name == diag:
                            diagram = d
                            break
                    n = self.draw(axiom, diagram)

        # focus on the last drawn element #
        self.session.doFocusItem(n)
        conn = None
        try:
            conn = sqlite3.connect(self.db_filename)
        except Exception as e:
            print(e)

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
                for ontology in project_ontologies:
                # for each imported ontology:
                    # CHECK if AXIOM belongs to ONTOLOGY  #

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
        conn.close()

    def draw(self, axiom, diagram, x=0, y=0):
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

    # DRAW AXIOM, CLASS EXPRESSIONS, ... #

    def drawPropertyExpression(self, axiom, diagram, x, y):

        prop = axiom.getInverse()

        if self.isAtomic(prop):

            propIRI = prop.getIRI()

            propNode = self.findNode(propIRI, diagram) if self.findNode(propIRI, diagram) != 'null' else self.createNode(prop, diagram, x, y)

        else:
            propNode = self.draw(prop, diagram, x, y)

        edges = propNode.edges
        inputEdges = [e for e in edges if e.type() is Item.InputEdge]
        for e in inputEdges:
            if e.target.type() is Item.RoleInverseNode:
                return e.target

        inv = RoleInverseNode(diagram=diagram)
        inv.setPos(propNode.pos().x()+150, propNode.pos().y())
        self.session.undostack.push(CommandNodeAdd(diagram, inv))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=inv)
        propNode.addEdge(input)
        inv.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return inv

    def drawDatatypeRestriction(self, datatype, facets, diagram, x, y):

        dataNode = DatatypeRestrictionNode(diagram=diagram)
        dataNode.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, dataNode))

        if not self.isAtomic(datatype):
            dNode = self.draw(datatype, x+150, y)

        else:
            dNode = self.createNode(datatype, diagram, x+150, y)

        input = diagram.factory.create(Item.InputEdge, source=dNode, target=dataNode)
        dNode.addEdge(input)
        dataNode.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        for f in facets:

            facet = f.getFacet()
            value = f.getFacetValue()

            fNode = FacetNode(diagram=diagram)
            fNode.facet.constrainingFacet = facet
            fNode.facet.literal = value
            fNode.setPos(x+150, y+150)
            self.session.undostack.push(CommandNodeAdd(diagram, fNode))

            inp = diagram.factory.create(Item.InputEdge, source=fNode, target=dataNode)
            fNode.addEdge(inp)
            dataNode.addEdge(inp)
            self.session.undostack.push(CommandEdgeAdd(diagram, inp))

        return dataNode

    def drawExpression(self, ex, diagram, x, y):

        ex_type = str(ex.getClassExpressionType())

        if ex_type == 'ObjectUnionOf':

            operands = ex.getOperandsAsList()
            n = self.drawObjUnionOf(operands, diagram, x, y)
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

        if ex_type == 'ObjectSomeValuesFrom' or ex_type == 'DataSomeValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjSomeValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectAllValuesFrom' or ex_type == 'DataAllValuesFrom':

            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjAllValuesFrom(property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectComplementOf':

            operand = ex.getOperand()
            n = self.drawObjComplementOf(operand, diagram, x, y)
            return n

        if ex_type == 'ObjectMinCardinality' or ex_type == 'DataMinCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjMinCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectMaxCardinality' or ex_type == 'DataMaxCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjMaxCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectExactCardinality' or ex_type == 'DataExactCardinality':

            card = ex.getCardinality()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjExactCardinality(card, property, ce, diagram, x, y)
            return n

        if ex_type == 'ObjectHasSelf':

            property = ex.getProperty()
            n = self.drawObjHasSelf(property, diagram, x, y)
            return n

        if ex_type == 'ObjectHasValue' or ex_type == 'DataHasValue':

            ex  = ex.asSomeValuesFrom()
            property = ex.getProperty()
            ce = ex.getFiller()
            n = self.drawObjSomeValuesFrom(property, ce, diagram, x, y)
            return n

    def drawAxiom(self, axiom, diagram, x, y):

        if isinstance(axiom, self.Axiom):

            ax_type = str(axiom.getAxiomType())
            #print(ax_type)

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

                        self.draw(disjoint_axiom, diagram, x, y)

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

                        self.draw(disjoint_axiom, diagram, x, y)

            if ax_type == 'DisjointObjectProperties':

                expressions = axiom.getClassExpressionsAsList()

                if len(expressions) == 2:

                    node = self.drawDisjointDataProperties(expressions, diagram, x, y)
                    return node

                else:

                    list_of_disjoints = axiom.asPairwiseAxioms()
                    for disjoint_axiom in list_of_disjoints:

                        self.draw(disjoint_axiom, diagram, x, y)

            if ax_type == 'DifferentIndividuals':

                individuals = axiom.getIndividualsAsList()

                if len(individuals) == 2:

                    #print(ax_type, individuals, diagram)
                    return self.drawDiffIndiv(individuals, diagram, x, y)

                else:

                    list_of_different = axiom.asPairwiseAxioms()
                    for different_axiom in list_of_different:
                        self.draw(different_axiom, diagram, x, y)

            if ax_type == 'SameIndividual':

                individuals = axiom.getIndividualsAsList()

                if len(individuals) == 2:

                    #print(ax_type, individuals, diagram)
                    return self.drawSameIndiv(individuals, diagram, x, y)

                else:

                    list_of_same = axiom.asPairwiseAxioms()
                    for same_axiom in list_of_same:
                        self.draw(same_axiom, diagram, x, y)

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
                        self.draw(equivalence_axiom, diagram, x, y)

            if ax_type == 'EquivalentObjectProperties':

                expressions = axiom.getProperties()

                if len(expressions) == 2:

                    return self.drawEquivalentProperties(expressions, diagram, x, y)

                else:

                    list_of_equivalents = axiom.asPairwiseAxioms()
                    for equivalence_axiom in list_of_equivalents:
                        self.draw(equivalence_axiom, diagram, x, y)

            if ax_type == 'EquivalentDataProperties':

                expressions = axiom.getProperties()

                if len(expressions) == 2:

                    return self.drawEquivalentProperties(expressions, diagram, x, y)

                else:

                    list_of_equivalents = axiom.asPairwiseAxioms()
                    for equivalence_axiom in list_of_equivalents:
                        self.draw(equivalence_axiom, diagram, x, y)

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
                        self.draw(pair, diagram, x, y)

            if ax_type == 'DataPropertyDomain' or ax_type == 'ObjectPropertyDomain':

                domain = axiom.getDomain()
                property = axiom.getProperty()
                n = self.drawPropertyDomain(property, domain, diagram, x, y)
                return n

            if ax_type == 'DataPropertyRange' or ax_type == 'ObjectPropertyRange':

                range = axiom.getRange()
                property = axiom.getProperty()
                n = self.drawPropertyRange(property, range, diagram, x, y)
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

                if self.isAtomic(sub):

                    subIRI = sub.getIRI()
                    subNode = self.findNode(subIRI, diagram)
                    if subNode != 'null':

                        subDrawn = True

                if self.isAtomic(sup):

                    supIRI = sup.getIRI()
                    supNode = self.findNode(supIRI, diagram)
                    if supNode != 'null':
                        supDrawn = True

                if supDrawn:

                    if subDrawn:

                        pass

                    else:

                        x = supNode.pos().x()
                        y = supNode.pos().y() + 150
                        if self.isAtomic(sub):

                            subNode = self.createNode(sub, diagram, x, y)
                            subDrawn = True

                        else:

                            subNode = self.draw(sub, diagram, x, y)
                            subDrawn = True
                else:

                    if subDrawn:

                        x = subNode.pos().x()
                        y = subNode.pos().y() - 150
                        if self.isAtomic(sup):

                            supNode = self.createNode(sup, diagram, x, y)
                            supDrawn = True

                        else:

                            supNode = self.draw(sup, diagram, x, y)
                            supDrawn = True

                    else:

                        x = x
                        y = y
                        if self.isAtomic(sup):

                            supNode = self.createNode(sup, diagram, x, y)
                            supDrawn = True

                        else:

                            supNode = self.draw(sup, diagram, x, y)
                            supDrawn = True

                        x = supNode.pos().x()
                        y = supNode.pos().y() + 150
                        if self.isAtomic(sub):

                            subNode = self.createNode(sub, diagram, x, y)
                            subDrawn = True

                        else:

                            subNode = self.draw(sub, diagram, x, y)
                            subDrawn = True

                isa = diagram.factory.create(Item.InclusionEdge, source=subNode, target=supNode)
                self.session.undostack.push(CommandEdgeAdd(diagram, isa))

                return isa

    # DRAW CLASS EXPRESSIONS #

    def drawObjHasSelf(self, property, diagram, x, y):

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram) if self.findNode(propIri, diagram) != 'null' else self.createNode(property, diagram, x, y)

        else:

            propNode = self.draw(property, diagram)

        n = DomainRestrictionNode(diagram=diagram)
        n.setText('self')
        n.setPos(propNode.pos().x()+50, propNode.pos().y() +50)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return n

    def drawObjMinCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property) :

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce) and not isinstance(ce, self.OWLLiteral):
            ceIri = ce.getIRI()
            ceNode = self.findNode(ceIri, diagram)
            if ceNode != 'null':
                ceDrawn = True

        if propDrawn:

            if ceDrawn:
                pass

            else:
                if self.isAtomic(ce):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(ce):

                    x = x
                    y = y
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True


        n = DomainRestrictionNode(diagram=diagram)
        card = str(card)
        n.setText('('+card+' , -)')
        xM = (ceNode.pos().x() + propNode.pos().x()) / 2
        yM = (ceNode.pos().y() + propNode.pos().y()) / 2
        n.setPos(xM, yM)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
        n.addEdge(input2)
        ceNode.addEdge(input2)

        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        return n

    def drawObjMaxCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce) and not isinstance(ce, self.OWLLiteral):
            ceIri = ce.getIRI()
            ceNode = self.findNode(ceIri, diagram)
            if ceNode != 'null':
                ceDrawn = True

        if propDrawn:

            if ceDrawn:
                pass

            else:
                if self.isAtomic(ce):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(ce):

                    x = x
                    y = y
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

        n = DomainRestrictionNode(diagram=diagram)
        card = str(card)
        n.setText('(- , '+card+')')
        xM = (ceNode.pos().x() + propNode.pos().x()) / 2
        yM = (ceNode.pos().y() + propNode.pos().y()) / 2
        n.setPos(xM, yM)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
        n.addEdge(input2)
        ceNode.addEdge(input2)

        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        return n

    def drawObjExactCardinality(self, card, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce) and not isinstance(ce, self.OWLLiteral):
            ceIri = ce.getIRI()
            ceNode = self.findNode(ceIri, diagram)
            if ceNode != 'null':
                ceDrawn = True

        if propDrawn:

            if ceDrawn:
                pass

            else:
                if self.isAtomic(ce):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(ce):

                    x = x
                    y = y
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

        n = DomainRestrictionNode(diagram=diagram)
        card = str(card)
        n.setText('('+card+' , '+card+')')
        xM = (ceNode.pos().x() + propNode.pos().x()) / 2
        yM = (ceNode.pos().y() + propNode.pos().y()) / 2
        n.setPos(xM, yM)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
        n.addEdge(input2)
        ceNode.addEdge(input2)

        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        return n

    def drawObjComplementOf(self, operand, diagram, x, y):

        if self.isAtomic(operand):

            iri = operand.getIRI()
            node = self.findNode(iri, diagram) if self.findNode(iri, diagram) !='null' else self.createNode(operand, diagram, x, y)

        else:

            node = self.draw(operand, diagram)

        notDrawn = False
        edges = node.edges
        inputEdges = [e for e in edges if e.type() is Item.InputEdge]
        for e in inputEdges:
            if e.target.type() is Item.ComplementNode:
                notNode = e.target
                notDrawn = True

        if not notDrawn:

            notNode = ComplementNode(diagram=diagram)
            notNode.setPos(node.pos().x()+50, node.pos().y())
            self.session.undostack.push(CommandNodeAdd(diagram, notNode))

            input = diagram.factory.create(Item.InputEdge, source=node, target=notNode)
            node.addEdge(input)
            notNode.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return notNode

    def drawObjSomeValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(ce) and not isinstance(ce, self.OWLLiteral):

            ceIri = ce.getIRI()
            ceNode = self.findNode(ceIri, diagram)
            if ceNode != 'null':
                ceDrawn = True

        if propDrawn:

            if ceDrawn:
                pass

            else:
                if self.isAtomic(ce):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(ce):

                    x = x
                    y = y
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

        n = DomainRestrictionNode(diagram=diagram)
        xM = (ceNode.pos().x() + propNode.pos().x()) / 2
        yM = (ceNode.pos().y() + propNode.pos().y()) / 2
        n.setPos(xM, yM)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
        n.addEdge(input2)
        ceNode.addEdge(input2)

        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        return n

    def drawObjAllValuesFrom(self, property, ce, diagram, x, y):

        propDrawn = False
        ceDrawn = False

        if self.isAtomic(property):

            propIri = property.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(ce) and not isinstance(ce, self.OWLLiteral):
            ceIri = ce.getIRI()
            ceNode = self.findNode(ceIri, diagram)
            if ceNode != 'null':

                ceDrawn = True

        if propDrawn:

            if ceDrawn:
                pass

            else:
                if self.isAtomic(ce):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

        else:

            if ceDrawn:

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(ce):

                    x = x
                    y = y
                    ceNode = self.createNode(ce, diagram, x, y)
                    ceDrawn = True
                else:

                    ceNode = self.draw(ce, diagram, x, y)
                    ceDrawn = True

                if self.isAtomic(property):

                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True
                else:
                    x = ceNode.pos().x() - 300
                    y = ceNode.pos().y()
                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

        n = DomainRestrictionNode(diagram=diagram)
        n.setText('forall')
        xM = (ceNode.pos().x() + propNode.pos().x()) / 2
        yM = (ceNode.pos().y() + propNode.pos().y()) / 2
        n.setPos(xM, yM)
        self.session.undostack.push(CommandNodeAdd(diagram, n))

        input = diagram.factory.create(Item.InputEdge, source=propNode, target=n)
        n.addEdge(input)
        propNode.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        input2 = diagram.factory.create(Item.InputEdge, source=ceNode, target=n)
        n.addEdge(input2)
        ceNode.addEdge(input2)

        self.session.undostack.push(CommandEdgeAdd(diagram, input2))

        return n

    def drawObjUnionOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []

        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
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
                if self.findNode(nIri, diagram) == 'null':
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

                n = self.draw(op, diagram, x, y)
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        x_med = (max(xPos) + min(xPos)) / 2
        y_med = (max(yPos) + min(yPos)) / 2 - 100

        union_node = UnionNode(diagram=diagram)
        union_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, union_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=union_node)
            n.addEdge(input)
            union_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return union_node

    def drawObjOneOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []

        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
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
                if self.findNode(nIri, diagram) == 'null':

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

                n = self.draw(op, diagram, x, y)
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        x_med = (max(xPos) + min(xPos)) / 2
        y_med = (max(yPos) + min(yPos)) / 2 - 100

        oneof_node = EnumerationNode(diagram=diagram)
        oneof_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, oneof_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=oneof_node)
            n.addEdge(input)
            oneof_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return oneof_node

    def drawDataOneOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []

        starting_x = x - 150
        starting_y = y

        for op in operands:

            if self.isAtomic(op):

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

                n = self.draw(op, diagram, x, y)
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        x_med = (max(xPos) + min(xPos)) / 2
        y_med = (max(yPos) + min(yPos)) / 2 - 100

        oneof_node = EnumerationNode(diagram=diagram)
        oneof_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, oneof_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=oneof_node)
            n.addEdge(input)
            oneof_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return oneof_node

    def drawObjIntersectionOf(self, operands, diagram, x, y):

        nodes = []
        xPos = []
        yPos = []

        for e in operands:

            if self.isAtomic(e) and not isinstance(e, self.OWLLiteral):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
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

                if self.findNode(nIri, diagram) == 'null':

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

                n = self.draw(op, diagram, x, y)
                nodes.append(n)
                xPos.append(n.pos().x())
                yPos.append(n.pos().y())

        x_med = (max(xPos)+min(xPos)) / 2
        y_med = (max(yPos)+min(yPos)) / 2 - 100

        intersect_node = IntersectionNode(diagram=diagram)
        intersect_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, intersect_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=intersect_node)
            n.addEdge(input)
            intersect_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return intersect_node

    # DRAW AXIOMS #

    def drawHasKey(self, ce, keys, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in keys:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

            if self.isAtomic(ce):

                cIRI = ce.getIRI()
                cNode = self.findNode(cIRI, diagram)

                if cNode != 'null':
                    starting_x = cNode.pos().x() - (150 * len(keys))
                    starting_y = cNode.pos().y() + 150


        if len(nodes) > 0:
            starting_x = min(x_positions)
            starting_y = min(y_positions)

        for c in keys:

            if not self.isAtomic(c):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(c, diagram, x, y)
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if self.isAtomic(c):

                    iri = c.getIRI()
                    node = self.findNode(iri, diagram)

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

        # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX + minX) / 2
        # y_med = sum(y_positions) / len(y_positions) -100
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY + minY) / 2

        key_node = HasKeyNode(diagram=diagram)
        key_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, key_node))

        for n in nodes:

            input = diagram.factory.create(Item.InputEdge, source=n, target=key_node)
            n.addEdge(input)
            key_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if self.isAtomic(ce):

            cIri = ce.getIRI()
            cNode = self.findNode(cIri, diagram) if self.findNode(cIri, diagram) != 'null' else self.createNode(ce, diagram, x_med, y_med-100)

        else:

            cNode = self.draw(ce, diagram)

        in2 = diagram.factory.create(Item.InputEdge, source=cNode, target=key_node)
        self.session.undostack.push(CommandEdgeAdd(diagram, in2))

        return key_node

    def drawChain(self, chain, property, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in chain:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y
            if self.isAtomic(property):

                cIRI = property.getIRI()
                cNode = self.findNode(cIRI, diagram)

                if cNode != 'null':

                    starting_x = cNode.pos().x() - (150*len(chain))
                    starting_y = cNode.pos().x() + 150



        if len(nodes) > 0:

            starting_x = min(x_positions)
            starting_y = min(y_positions)

        for prop in chain:

            #if not prop.isType(self.EntityType.OBJECT_PROPERTY):
            if not self.isAtomic(prop):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(prop, diagram, x, y)
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:

                iri = prop.getIRI()
                node = self.findNode(iri, diagram)

                if node == 'null':

                    x = starting_x + 150
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

        chain_node = RoleChainNode(diagram=diagram)
        chain_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, chain_node))

        for n in nodes:
            input = diagram.factory.create(Item.InputEdge, source=n, target=chain_node)
            n.addEdge(input)
            chain_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if self.isAtomic(property):
            pIri = property.getIRI()
            pNode = self.findNode(pIri, diagram) if self.findNode(pIri,
                                                                  diagram) != 'null' else self.createNode(
                property, diagram, x_med, y_med - 100)

        else:
            pNode = self.draw(property, diagram)

        isa = diagram.factory.create(Item.InclusionEdge, source=chain_node, target=pNode)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return chain_node

    def drawPropertyRange(self, property, range, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(iri, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(range) and not isinstance(range, self.OWLLiteral):

            iri = range.getIRI()
            domainNode = self.findNode(iri, diagram)

            if domainNode != 'null':
                domDrawn = True

        if propDrawn:

            if domDrawn:

                pass

            else:

                if self.isAtomic(range):

                    x = propNode.pos().x() - 300
                    y = propNode.pos().y()
                    domainNode = self.createNode(range, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x() - 300
                    y = propNode.pos().y()

                    domainNode = self.draw(range, diagram, x, y)
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x() + 300
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() + 300
                    y = domainNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(range):

                    x = x
                    y = y
                    domainNode = self.createNode(range, diagram, x, y)
                    domDrawn = True

                else:

                    domainNode = self.draw(range, diagram, x, y)
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x() + 300
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() + 300
                    y = domainNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

        x_med = (propNode.pos().x() + domainNode.pos().x()) /2
        y_med = (propNode.pos().y() + domainNode.pos().y()) /2

        restrNode = RangeRestrictionNode(diagram=diagram)
        restrNode.setPos(x_med, y_med)

        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return restrNode

    def drawPropertyDomain(self, property, domain, diagram, x, y):

        propDrawn = False
        domDrawn = False

        if self.isAtomic(property):

            iri = property.getIRI()
            propNode = self.findNode(iri, diagram)

            if propNode != 'null':
                propDrawn = True

        if self.isAtomic(domain) and not isinstance(domain, self.OWLLiteral):

            iri = domain.getIRI()
            domainNode = self.findNode(iri, diagram)

            if domainNode != 'null':

                domDrawn = True

        if propDrawn:

            if domDrawn:

                pass

            else:

                if self.isAtomic(domain):

                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:
                    x = propNode.pos().x() + 300
                    y = propNode.pos().y()

                    domainNode = self.draw(domain, diagram, x, y)
                    domDrawn = True

        else:

            if domDrawn:

                if self.isAtomic(property):

                    x = domainNode.pos().x() - 300
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() - 300
                    y = domainNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True

            else:

                if self.isAtomic(domain):

                    x = x
                    y = y
                    domainNode = self.createNode(domain, diagram, x, y)
                    domDrawn = True

                else:

                    domainNode = self.draw(domain, diagram, x, y)
                    domDrawn = True

                if self.isAtomic(property):

                    x = domainNode.pos().x() - 300
                    y = domainNode.pos().y()
                    propNode = self.createNode(property, diagram, x, y)
                    propDrawn = True

                else:
                    x = domainNode.pos().x() - 300
                    y = domainNode.pos().y()

                    propNode = self.draw(property, diagram, x, y)
                    propDrawn = True


        x_med = (propNode.pos().x() + domainNode.pos().x()) /2
        y_med = (propNode.pos().y() + domainNode.pos().y()) /2

        restrNode = DomainRestrictionNode(diagram=diagram)
        restrNode.setPos(x_med, y_med)

        self.session.undostack.push(CommandNodeAdd(diagram, restrNode))

        input1 = diagram.factory.create(Item.InputEdge, source=propNode, target=restrNode)
        propNode.addEdge(input1)
        restrNode.addEdge(input1)
        self.session.undostack.push(CommandEdgeAdd(diagram, input1))

        isa = diagram.factory.create(Item.InclusionEdge, source=restrNode, target=domainNode)
        domainNode.addEdge(isa)
        restrNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return restrNode

    def drawInverseObjProperties(self, first, second, diagram, x, y):

        firstDrawn = False
        secondDrawn = False

        if self.isAtomic(first):

            firstIRI = first.getIRI()
            firstNode = self.findNode(firstIRI, diagram)
            if firstNode != 'null':

                firstDrawn = True

        if self.isAtomic(second):

            secondIRI = second.getIRI()
            secondNode = self.findNode(secondIRI, diagram)

            if secondNode != 'null':
                secondDrawn = True

        if firstDrawn:

            if secondDrawn:

                pass

            else:

                if self.isAtomic(second):

                    x = firstNode.pos().x() + 300
                    y = firstNode.pos().y()
                    secondNode = self.createNode(second, diagram, x, y)
                    secondDrawn = True

                else:

                    x = firstNode.pos().x() + 300
                    y = firstNode.pos().y()

                    secondNode = self.draw(second, diagram, x, y)
                    secondDrawn = True

        else:

            if secondDrawn:

                if self.isAtomic(first):

                    x = secondNode.pos().x() - 300
                    y = secondNode.pos().y()
                    firstNode = self.createNode(first, diagram, x, y)
                    firstDrawn = True

                else:
                    x = secondNode.pos().x() - 300
                    y = secondNode.pos().y()
                    firstNode = self.draw(second, diagram, x, y)
                    firstDrawn = True

            else:

                if self.isAtomic(first):

                    x = x + 300
                    y = y + 300
                    firstNode = self.createNode(first, diagram, x, y)
                    firstDrawn = True

                else:

                    firstNode = self.draw(second, diagram, x+300, y+300)
                    firstDrawn = True

                if self.isAtomic(second):

                    x = firstNode.pos().x() + 300
                    y = firstNode.pos().y()
                    secondNode = self.createNode(second, diagram, x, y)
                    secondDrawn = True

                else:
                    x = firstNode.pos().x() + 300
                    y = firstNode.pos().y()
                    secondNode = self.draw(second, diagram, x, y)
                    secondDrawn = True

        inv = RoleInverseNode(diagram=diagram)
        x = (firstNode.pos().x() + secondNode.pos().x()) /2
        y = (firstNode.pos().y() + secondNode.pos().y()) /2
        inv.setPos(x, y)
        self.session.undostack.push(CommandNodeAdd(diagram, inv))

        input = diagram.factory.create(Item.InputEdge, source=secondNode, target=inv)
        secondNode.addEdge(input)
        inv.addEdge(input)
        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        equiv = diagram.factory.create(Item.EquivalenceEdge, source=inv, target=firstNode)
        inv.addEdge(equiv)
        firstNode.addEdge(equiv)
        self.session.undostack.push(CommandEdgeAdd(diagram, equiv))

        return inv

    def drawSubProperty(self, sub, sup, diagram, x, y):

        subDrawn = False
        supDrawn = False

        if self.isAtomic(sub):

            sub_iri = sub.getIRI()
            node0 = self.findNode(sub_iri, diagram)
            if node0 != 'null':
                subDrawn = True

        if self.isAtomic(sup):

            sup_iri = sup.getIRI()
            node1 = self.findNode(sup_iri, diagram)
            if node1 != 'null':
                supDrawn = True

        if subDrawn:

            if supDrawn:

                pass

            else:

                if self.isAtomic(sup):

                    x = node0.pos().x()
                    y = node0.pos().y() - 150
                    node1 = self.createNode(sup, diagram, x, y)
                    supDrawn = True

                else:
                    x = node0.pos().x()
                    y = node0.pos().y() - 150
                    node1 = self.draw(sup, diagram, x, y)
                    supDrawn = True

        else:

            if supDrawn:

                if self.isAtomic(sub):

                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.createNode(sub, diagram, x, y)
                    subDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.draw(sub, diagram, x, y)
                    subDrawn = True

            else:

                if self.isAtomic(sup):

                    x = x
                    y = y
                    node1 = self.createNode(sup, diagram, x, y)
                    supDrawn = True

                else:

                    node1 = self.draw(sup, diagram, x, y)
                    supDrawn = True

                if self.isAtomic(sub):

                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.createNode(sub, diagram, x, y)
                    subDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.draw(sub, diagram, x, y)
                    subDrawn = True

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=node1)
        node0.addEdge(isa)
        node1.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return isa

    def drawEquivalentClasses(self, expressions, diagram, x, y):

        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)

        if len(nodes) == 0:
            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x() - 150
            starting_y = nodes[0].pos().y() + 150

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(ex, diagram, x, y)
                nodes.append(n)

            else:

                if ex.isType(self.EntityType.CLASS):

                    iri = ex.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
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

        return equivalence

    def drawEquivalentProperties(self, expressions, diagram, x, y):

        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)

        if len(nodes) == 0:
            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().x()

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y
                n = self.draw(ex, diagram, x, y)
                nodes.append(n)

            else:

                if ex.isType(self.EntityType.DATA_PROPERTY) or ex.isType(self.EntityType.OBJECT_PROPERTY):

                    iri = ex.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
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

        return equivalence

    def drawClassAssertion(self, indiv, classs, diagram, x, y):

        classDrawn = False
        indivDrawn = False

        if self.isAtomic(classs):

            class_iri = classs.getIRI()
            if self.findNode(class_iri, diagram) != 'null':

                node1 = self.findNode(class_iri, diagram)
                classDrawn = True

        if self.isAtomic(indiv):

            indiv_iri = indiv.getIRI()
            if self.findNode(indiv_iri, diagram) != 'null':

                node0 = self.findNode(indiv_iri, diagram)
                indivDrawn = True

        if classDrawn:

            if indivDrawn:
                pass

            else:

                if self.isAtomic(indiv):

                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.createNode(indiv, diagram, x, y)
                    indivDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.draw(indiv, diagram, x, y)
                    indivDrawn = True

        else:

            if indivDrawn:

                if self.isAtomic(classs):

                    x = node0.pos().x()
                    y = node0.pos().y() - 150
                    node1 = self.createNode(classs, diagram, x, y)
                    classDrawn = True

                else:

                    x = node0.pos().x()
                    y = node0.pos().y() - 150
                    node1 = self.draw(classs, diagram, x, y)
                    classDrawn = True

            else:

                if self.isAtomic(classs):

                    x = x
                    y = y
                    node1 = self.createNode(classs, diagram, x, y)
                    classDrawn = True

                else:

                    node1 = self.draw(classs, diagram, x, y)
                    classDrawn = True

                if self.isAtomic(indiv):

                    x = node1.pos().x()
                    y = node1.pos().y() + 150
                    node0 = self.createNode(indiv, diagram, x, y)
                    indivDrawn = True

                else:
                    x = node1.pos().x()
                    y = node1.pos().y() + 150

                    node0 = self.draw(indiv, diagram, x, y)
                    indivDrawn = True

        isa = diagram.factory.create(Item.MembershipEdge, source=node0, target=node1)
        node0.addEdge(isa)
        node1.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        return isa

    def drawPropertyAssertion(self, prop, indiv, value, diagram, x, y):

        propDrawn = False
        indivDrawn = False
        valueDrawn = False


        if self.isAtomic(prop):
            propIri = prop.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':

                propDrawn = True

        if self.isAtomic(indiv):

            indvIri = indiv.getIRI()
            indivNode = self.findNode(indvIri, diagram)
            if indivNode != 'null':
                indivDrawn = True

        if self.isAtomic(value):

            if isinstance(value, self.OWLNamedIndividual):

                valueIri = value.getIRI()
                valueNode = self.findNode(valueIri, diagram)

                if valueNode != 'null':
                    valueDrawn = True

        if propDrawn:

            if indivDrawn:

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True
                    else:

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True
                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() - 150
                        y = propNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True


                    else:
                        x = propNode.pos().x() - 150
                        y = propNode.pos().y() - 150

                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x()
                        y = propNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:

                        x = propNode.pos().x()
                        y = propNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True
        else:

            if indivDrawn:

                if self.isAtomic(prop):

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    propNode = self.createNode(prop, diagram, x, y)
                    propDrawn = True

                else:

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    propNode = self.draw(prop, diagram, x, y)
                    propDrawn = True

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:
                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        propDrawn = True

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.draw(prop, diagram, x, y)

                else:

                    if self.isAtomic(value):

                        x = x
                        y = y
                        #print(value)
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:

                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        #print(indivNode)
                        indivDrawn = True

                    else:
                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150

                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        #print(propNode)
                        propDrawn = True

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.draw(prop, diagram, x, y)
                        propDrawn = True


        instanceNode = PropertyAssertionNode(diagram=diagram)
        x = (indivNode.pos().x() + propNode.pos().x()) / 2
        y = propNode.pos().x()
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

        return instanceNode

    def drawNegativePropertyAssertion(self, prop, indiv, value, diagram, x, y):

        propDrawn = False
        notDrawn = False
        indivDrawn = False
        valueDrawn = False

        if self.isAtomic(prop):

            propIri = prop.getIRI()
            propNode = self.findNode(propIri, diagram)
            if propNode != 'null':

                propDrawn = True

                edges = propNode.edges
                inputEdges = [e for e in edges if e.type() is Item.InputEdge]
                for e in inputEdges:
                    if e.target.type() is Item.ComplementNode:

                        notNode = e.target
                        notDrawn = True

        if self.isAtomic(indiv):

            indvIri = prop.getIRI()
            indivNode = self.findNode(indvIri, diagram)
            if indivNode != 'null':
                indivDrawn = True

        if self.isAtomic(value):
            if value.isType(self.EntityType.NAMED_INDIVIDUAL):

                valueIri = value.getIRI()
                valueNode = self.findNode(valueIri, diagram)

                if valueNode != 'null':
                    valueDrawn = True

        if propDrawn:

            if notDrawn:
                pass

            else:

                x = propNode.pos().x() + 50
                y = propNode.pos().y() + 50
                notNode = self.drawObjComplementOf(prop, diagram, x, y)
                notDrawn = True

            if indivDrawn:

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True
                    else:
                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.draw(value, diagram)
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True
                    else:

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True
                else:

                    if self.isAtomic(value):

                        x = propNode.pos().x() - 150
                        y = propNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = propNode.pos().x() - 150
                        y = propNode.pos().y() - 150
                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = propNode.pos().x()
                        y = propNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:

                        x = propNode.pos().x()
                        y = propNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True
        else:

            if indivDrawn:

                if self.isAtomic(prop):

                    x = indivNode.pos().x()
                    y = indivNode.pos().y() + 150
                    propNode = self.createNode(prop, diagram, x, y)
                    propDrawn = True

                    notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                    notDrawn = True

                else:
                    propNode = self.draw(prop, diagram, x, y)
                    propDrawn = True

                    notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                    notDrawn = True

                if valueDrawn:

                    pass

                else:

                    if self.isAtomic(value):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() - 150
                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

            else:

                if valueDrawn:

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150

                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        propDrawn = True

                        notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                        notDrawn = True

                    else:
                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.draw(prop, diagram, x, y)

                        notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                        notDrawn = True

                else:

                    if self.isAtomic(value):

                        x = x
                        y = y
                        valueNode = self.createNode(value, diagram, x, y)
                        valueDrawn = True

                    else:
                        x = x
                        y = y
                        valueNode = self.draw(value, diagram, x, y)
                        valueDrawn = True

                    if self.isAtomic(indiv):

                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.createNode(indiv, diagram, x, y)
                        indivDrawn = True

                    else:
                        x = valueNode.pos().x()
                        y = valueNode.pos().y() - 150
                        indivNode = self.draw(indiv, diagram, x, y)
                        indivDrawn = True

                    if self.isAtomic(prop):

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.createNode(prop, diagram, x, y)
                        propDrawn = True

                        notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                        notDrawn = True

                    else:

                        x = indivNode.pos().x()
                        y = indivNode.pos().y() + 150
                        propNode = self.draw(prop, diagram, x, y)
                        propDrawn = True

                        notNode = self.drawObjComplementOf(prop, diagram, x+50, y+50)
                        notDrawn = True

        instanceNode = PropertyAssertionNode(diagram=diagram)
        x = (indivNode.pos().x() + propNode.pos().x()) / 2
        y = propNode.pos().x()
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


        isa = diagram.factory.create(Item.MembershipEdge, source=instanceNode, target=notNode)
        instanceNode.addEdge(isa)
        notNode.addEdge(isa)
        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        input3 = diagram.factory.create(Item.InputEdge, source=propNode, target=notNode)
        propNode.addEdge(input3)
        notNode.addEdge(input3)
        self.session.undostack.push(CommandEdgeAdd(diagram, input3))

        return instanceNode

    def drawDiffIndiv(self, individuals, diagram, x, y):

        nodes = []
        for e in individuals:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)

        if len(nodes) == 0:
            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:
            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().y()

        for i in individuals:

            # if not i.isType(self.EntityType.NAMED_INDIVIDUAL):
            if not self.isAtomic(i):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(i, diagram, x, y)
                nodes.append(n)

            else:
                if i.isType(self.EntityType.NAMED_INDIVIDUAL):

                    iri = i.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':
                        x = starting_x + 150
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

        return different

    def drawSameIndiv(self, individuals, diagram, x, y):

        nodes = []

        for e in individuals:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)


        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = nodes[0].pos().x()
            starting_y = nodes[0].pos().y()

        for i in individuals:

            if not self.isAtomic(i):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(i, diagram, x, y)
                nodes.append(n)

            else:
                if i.isType(self.EntityType.NAMED_INDIVIDUAL):

                    iri = i.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
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

        return same

    def drawDisjointClasses(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(ex, diagram, x, y)
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:

                if ex.isType(self.EntityType.CLASS):

                    iri = ex.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

       # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX + minX) / 2
        # y_med = sum(y_positions) / len(y_positions)
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY + minY) / 2

        dis_node = ComplementNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        node0 = nodes[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
        node0.addEdge(isa)
        dis_node.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        node1 = nodes[1]

        input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
        node1.addEdge(input)
        dis_node.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return dis_node

    def drawDisjointUnion(self, classes, classs, diagram, x, y):

        nodes = []
        x_positions = []
        y_positions = []

        for e in classes:

            if self.isAtomic(e):

                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:


            starting_x = x - 150
            starting_y = y

            if self.isAtomic(classs):

                cIRI = classs.getIRI()
                cNode = self.findNode(cIRI, diagram)

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

                n = self.draw(c, diagram, x, y)
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if c.isType(self.EntityType.CLASS):

                    iri = c.getIRI()
                    node = self.findNode(iri, diagram)

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

            # x_med = sum(x_positions) / len(x_positions)
            maxX = max(x_positions)
            minX = min(x_positions)
            x_med = (maxX - minX) / 2
            # y_med = sum(y_positions) / len(y_positions) -100
            maxY = max(y_positions)
            minY = min(y_positions)
            y_med = (maxY - minY) / 2

        dis_node = DisjointUnionNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        for n in nodes:

            input = diagram.factory.create(Item.InputEdge, source=n, target=dis_node)
            n.addEdge(input)
            dis_node.addEdge(input)

            self.session.undostack.push(CommandEdgeAdd(diagram, input))

        if self.isAtomic(classs):

            cIri = classs.getIRI()
            cNode = self.findNode(cIri, diagram) if self.findNode(cIri, diagram) != 'null' else self.createNode(classs, diagram, x_med, y_med-100)

        else:

            cNode = self.draw(classs, diagram)
        equiv = diagram.factory.create(Item.EquivalenceEdge, source=cNode, target=dis_node)
        self.session.undostack.push(CommandEdgeAdd(diagram, equiv))

        return dis_node

    def drawDisjointDataProperties(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]

        for ex in expressions:

            if not self.isAtomic(ex):

                x = starting_x + 150
                y = starting_y

                starting_x = x
                starting_y = y

                n = self.draw(ex, diagram, x, y)
                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if ex.isType(self.EntityType.DATA_PROPERTY):
                    iri = ex.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
                        y = starting_y

                        starting_x = x
                        starting_y = y
                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)

        # x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX - minX) / 2
        # y_med = sum(y_positions) / len(y_positions)
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY - minY) / 2

        dis_node = ComplementNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        node0 = nodes[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
        node0.addEdge(isa)
        dis_node.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        node1 = nodes[1]

        input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
        node1.addEdge(input)
        dis_node.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return dis_node

    def drawDisjointObjectProperties(self, expressions, diagram, x, y):

        x_positions = []
        y_positions = []
        nodes = []

        for e in expressions:
            if self.isAtomic(e):
                iri = e.getIRI()
                node = self.findNode(iri, diagram)
                if node != 'null':
                    nodes.append(node)
                    x_positions.append(node.pos().x())
                    y_positions.append(node.pos().y())

        if len(nodes) == 0:

            starting_x = x - 150
            starting_y = y

        if len(nodes) > 0:

            starting_x = x_positions[0]
            starting_y = y_positions[0]


        for ex in expressions:

            if not self.isAtomic(ex):

                n = self.draw(ex, diagram, starting_x+150, starting_y)

                starting_x = starting_x+150

                nodes.append(n)

                xN = n.pos().x()
                x_positions.append(xN)

                yN = n.pos().y()
                y_positions.append(yN)

            else:
                if ex.isType(self.EntityType.OBJECT_PROPERTY):

                    iri = ex.getIRI()
                    node = self.findNode(iri, diagram)

                    if node == 'null':

                        x = starting_x + 150
                        y = starting_y

                        starting_x = x
                        starting_y = y

                        node = self.createNode(ex, diagram, x, y)
                        nodes.append(node)

                        x = node.pos().x()
                        x_positions.append(x)

                        y = node.pos().y()
                        y_positions.append(y)


        #x_med = sum(x_positions) / len(x_positions)
        maxX = max(x_positions)
        minX = min(x_positions)
        x_med = (maxX - minX) / 2
        #y_med = sum(y_positions) / len(y_positions)
        maxY = max(y_positions)
        minY = min(y_positions)
        y_med = (maxY - minY) / 2

        dis_node = ComplementNode(diagram=diagram)
        dis_node.setPos(x_med, y_med)
        self.session.undostack.push(CommandNodeAdd(diagram, dis_node))

        node0 = nodes[0]

        isa = diagram.factory.create(Item.InclusionEdge, source=node0, target=dis_node)
        node0.addEdge(isa)
        dis_node.addEdge(isa)

        self.session.undostack.push(CommandEdgeAdd(diagram, isa))

        node1 = nodes[1]

        input = diagram.factory.create(Item.InputEdge, source=node1, target=dis_node)
        node1.addEdge(input)
        dis_node.addEdge(input)

        self.session.undostack.push(CommandEdgeAdd(diagram, input))

        return dis_node

    # ATOMIC OPERATIONS #

    def createNode(self, ex, diagram, x, y):

        # create atomic node: Class, Attribute, Role, Individual, Literal, Datatype #

        starting_y = y
        while not self.isEmpty(x, y, diagram):

            y = y + 50
            if abs(starting_y - y) > 1000:

                y = starting_y
                break

        if isinstance(ex, self.OWLLiteral):

            lit = ex.getLiteral()
            DP = ex.getDatatype()

            iri = DP.getIRI()

            datatype = IRI(str(iri))

            d =[x.value for x in OWL2Datatype if str(x.value) == str(datatype)][0]

            literal = Literal(lit, d)

            literalNode = LiteralNode(literal=literal, diagram=diagram)
            literalNode.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, literalNode))

            literalNode.doUpdateNodeLabel()

            return literalNode

        if ex.isType(self.EntityType.CLASS):

            iri = IRI(str(ex.getIRI()))
            classs = ConceptNode(iri= iri, diagram=diagram)
            classs.iri = iri
            classs.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, classs))

            return classs

        if ex.isType(self.EntityType.NAMED_INDIVIDUAL):

            iri = IRI(str(ex.getIRI()))
            indiv = IndividualNode(iri=iri, diagram=diagram)
            indiv.iri = iri
            indiv.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, indiv))

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

            return objectProp

        if ex.isType(self.EntityType.DATATYPE):

            iri = IRI(str(ex.getIRI()))
            datatype = ValueDomainNode(iri=iri, diagram=diagram)
            datatype.iri = iri
            datatype.setPos(x, y)

            self.session.undostack.push(CommandNodeAdd(diagram, datatype))

            return datatype
        return

    def findNode(self, iri, diagram):

        ### FIND NODE BY IRI IN THE DIAGRAM ###
        for el in diagram.items():

            if el.isNode() and (el.type() == Item.ConceptNode or el.type() == Item.IndividualNode or el.type() == Item.RoleNode or el.type() == Item.AttributeNode) and str(iri) == str(el.iri):
                return el

        # IF NOT FOUND, RETURN 'NULL'
        return 'null'

    def isEmpty(self, x, y, diagram):
        # check if position x, y of diagram is empty #
        for el in diagram.items():

            if el.isNode() and el.pos().y() == y and abs(el.pos().x() - x) < 113.25:

                    return False
        return True

    def isAtomic(self, operand):
        # check if operand is atomic #
        if isinstance(operand, self.OWLClass) or isinstance(operand, self.OWLObjectProperty) or isinstance(operand, self.OWLDataProperty) or isinstance(operand, self.OWLDatatype) or isinstance(operand, self.OWLLiteral) or isinstance(operand, self.OWLNamedIndividual):

            return True

        else:

            return False

# WIDGET FORM to set Space between Items #
class AbstractItemSpaceForm(QtWidgets.QDialog):
    """
    Base class for diagram dialogs.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        """
        Initialize the dialog.
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)


        #################################
        # FORM AREA
        #################################

        self.spaceField = IntegerField(self)
        self.spaceField.setMinimumWidth(400)
        self.spaceField.setMaxLength(4)
        self.spaceField.setPlaceholderText('Space...')
        connect(self.spaceField.textChanged, self.onSpaceFieldChanged)

        self.warnLabel = QtWidgets.QLabel(self)
        self.warnLabel.setContentsMargins(0, 0, 0, 0)
        self.warnLabel.setProperty('class', 'invalid')
        self.warnLabel.setVisible(False)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self.spaceField)
        self.mainLayout.addWidget(self.warnLabel)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def onSpaceFieldChanged(self, space):
        """
        Executed when the content of the input field changes.
        :type space: int
        """
        enabled = False
        caption = ''

        if space != '':

            space = int(space.strip())
            if not space:
                caption = ''
                enabled = False
            else:
                if space < 130 or space > 500:
                    caption = "Space must be integer in range [130, 500]"
                    enabled = False
                else:
                    caption = ''
                    enabled = True

        self.warnLabel.setText(caption)
        self.warnLabel.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())

class SpaceForm(AbstractItemSpaceForm):

    def __init__(self, parent=None):
        """
        Initialize the new diagram dialog.
        :type project: Project
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.setWindowTitle('Set Space between ClassNodes')
