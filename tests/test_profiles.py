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

from mock import Mock

from PyQt5 import QtCore
from PyQt5 import QtTest

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath

from tests import EddyTestCase


class ProfilesTestCase(EddyTestCase):
    """
    Tests for Eddy profiles.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        super(ProfilesTestCase, self).setUp()
        self.init('test_project_2')
        self.session.project.profile.reset = Mock()

    #############################################
    #   UTILITY METHODS
    #################################

    def __give_focus_to_diagram(self, path):
        """
        Gives focus to the given diagram.
        :type path: str
        """
        self.session.sgnDiagramFocus.emit(self.project.diagram(expandPath(path)))

    def __insert_edge_between(self, item, source, target):
        """
        Insert the given edge between the source and the target node.
        :type item: Item
        :type source: T <= tuple|AbstractNode
        :type target: T <= tuple|AbstractNode
        """
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.EdgeAdd, item)
        view = self.session.mdi.activeView()
        if isinstance(source, tuple):
            source = first(self.project.predicates(source[0], source[1], diagram))
        if isinstance(target, tuple):
            target = first(self.project.predicates(target[0], target[1], diagram))
        sourcePos = view.mapFromScene(source.pos())
        targetPos = view.mapFromScene(target.pos())
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, sourcePos)
        QtTest.QTest.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, targetPos)

    #############################################
    #   INCLUSION
    #################################

    def test_inclusion_no_graphol_expression(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.IndividualNode, 'I1'), (Item.IndividualNode, 'I2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion must involve two graphol expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Role and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Role and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Attribute and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('@tests/.tests/test_project_2/diagram1.graphol')
        num_edges_in_project = len(self.project.edges())
        node = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), node)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())
