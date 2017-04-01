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


from mock import Mock

from PyQt5 import QtCore
from PyQt5 import QtTest

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import first

from tests import EddyTestCase


class OWL2ProfileTestCase(EddyTestCase):
    """
    Tests for Eddy profiles.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        super().setUp()
        self.init('test_project_2')
        self.session.project.profile.reset = Mock()

    #############################################
    #   UTILITY METHODS
    #################################

    def __give_focus_to_diagram(self, name):
        """
        Gives focus to the given diagram.
        :type name: str
        """
        self.session.sgnFocusDiagram.emit(self.project.diagram(name))

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
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.IndividualNode, 'I1'), (Item.IndividualNode, 'I2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion must involve two graphol expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_concept_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ConceptNode, 'C1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Concept and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Role and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Role and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between Attribute and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_disjoint_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DisjointUnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and disjoint union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and intersection node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_disjoint_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DisjointUnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and disjoint union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and intersection node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_value_domain_expressions(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between value-domain expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_complement_node_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, source, (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid source for Role inclusion: complement node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_complement_node_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, source, (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid source for Attribute inclusion: complement node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_chain_node_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleChainNode and x is not source, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Inclusion between role chain node and role chain node is forbidden')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Role chain nodes cannot be target of a Role inclusion')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_role_and_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram49')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.RoleNode, 'R9'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Detected unsupported operator sequence on intersection node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_inclusion_between_attribute_and_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram50')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InclusionEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Detected unsupported operator sequence on intersection node')
        self.assertFalse(self.project.profile.pvr().isValid())

    #############################################
    #   EQUIVALENCE
    #################################

    def test_equivalence_no_graphol_expression(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.IndividualNode, 'I1'), (Item.IndividualNode, 'I2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(),'Type mismatch: equivalence must involve two graphol expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_concept_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.ConceptNode, 'C1'), (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Concept and Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_concept_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.ConceptNode, 'C1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Concept and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_concept_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.ConceptNode, 'C1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Concept and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Role and Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Role and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_attribute_and_value_domain(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.AttributeNode, 'A1'), (Item.ValueDomainNode, 'xsd:string'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between Attribute and Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_disjoint_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DisjointUnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and disjoint union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: role node and intersection node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_attribute_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_attribute_and_disjoint_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DisjointUnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and disjoint union node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_attribute_and_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.AttributeNode, 'A1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: attribute node and intersection node are not compatible')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_value_domain_expressions(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: equivalence between value-domain expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_complement_node_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, source, (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Equivalence is forbidden when expressing Role disjointness')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_complement_node_and_attribute(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, source, (Item.AttributeNode, 'A1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Equivalence is forbidden when expressing Attribute disjointness')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_chain_node_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleChainNode and x is not source, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Equivalence is forbidden in presence of a role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_equivalence_between_role_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.EquivalenceEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Equivalence is forbidden in presence of a role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    #############################################
    #   INPUT
    #################################

    def test_input_between_concept_node_and_concept_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C1'), (Item.ConceptNode, 'C2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Input edges can only target constructor nodes')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_node_and_role_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.RoleNode, 'R1'), (Item.RoleNode, 'R2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Input edges can only target constructor nodes')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to complement node: Individual')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to union node: Individual')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram1')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to intersection node: Individual')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_chain_of_inclusion_connected_neutral_operators(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram18')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: inclusion between value-domain expressions')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_complement_node_with_already_an_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram15')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C2'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many inputs to complement node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_node_and_complement_node_with_outgoing_edge(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram19')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.RoleNode, 'R1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid negative Role expression')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_non_neutral_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram16')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: union between Value Domain and Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_non_neutral_disjoint_union_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram17')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DisjointUnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: disjoint union between Value Domain and Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_non_neutral_intersection_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram2')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.IntersectionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: intersection between Value Domain and Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_range_restriction_node_and_union_of_value_domain_nodes(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram23')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.UnionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to union node: range restriction node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_enumeration_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram24')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.EnumerationNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C5'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to enumeration node: Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_node_and_enumeration_node_with_individuals(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram4')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.EnumerationNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, '"32"^^xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to enumeration node: Value')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_chain_node_and_role_inverse_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram20')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleInverseNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to role inverse node: role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_inverse_node_and_role_inverse_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram21')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleInverseNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleInverseNode and x is not source, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to role inverse node: role inverse node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_chain_node_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram22')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleChainNode and x is not source, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to role chain node: role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_datatype_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram25')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C6'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to datatype restriction node: concept node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_datatype_restriction_node_with_datatype_connected(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram26')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:integer'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many value-domain nodes in input to datatype restriction node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_datatype_restriction_node_with_incompatible_facet_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram6')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: datatype xsd:string is not compatible by facet xsd:maxExclusive')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_facet_node_and_datatype_restriction_node_with_incompatible_datatype(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram29')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.FacetNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.DatatypeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Type mismatch: facet xsd:maxExclusive is not compatible by datatype xsd:string')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_property_assertion_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram27')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to property assertion node: concept node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_property_assertion_node_with_already_two_inputs(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram7')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I3'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many inputs to property assertion node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_node_and_property_assertion_node_set_as_role_instance(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram28')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, '"12"^^xsd:integer'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to Role Instance: Value')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_property_assertion_node_set_as_attribute_instance(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram31')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I2'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many individuals in input to Attribute Instance')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_node_and_property_assertion_node_set_as_attribute_instance(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram32')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, '"32"^^xsd:integer'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many values in input to Attribute Instance')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_domain_restriction_node_with_filler(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram11')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C2'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many inputs to domain restriction node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_domain_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram33')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I4'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to domain restriction node: Individual')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_chain_node_and_domain_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram10')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to domain restriction node: role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_property_assertion_node_and_domain_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram5')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to domain restriction node: property assertion node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_domain_restriction_node_with_self_restriction(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram12')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C1'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid restriction type for qualified domain restriction: self')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_domain_restriction_node_with_attribute_in_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram3')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C7'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid qualified domain restriction: Concept + Attribute')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_node_and_domain_restriction_node_with_value_domain_in_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram14')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.RoleNode, 'R5'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid qualified domain restriction: Role + Value Domain')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_attribute_node_and_domain_restriction_node_with_self_restriction(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram30')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.AttributeNode, 'A4'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Attributes do not have self')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_attribute_node_and_domain_restriction_node_with_concept_in_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram9')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.AttributeNode, 'A4'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid qualified domain restriction: Attribute + Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_domain_restriction_node_with_self_restriction(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram8')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid restriction type for qualified domain restriction: self')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_domain_restriction_node_with_role_in_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram13')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.DomainRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid qualified domain restriction: Value Domain + Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_concept_node_and_range_restriction_node_with_filler(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram34')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ConceptNode, 'C2'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many inputs to range restriction node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_range_restriction_node_with_attribute_as_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram35')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Too many inputs to attribute range restriction')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_individual_node_and_range_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram36')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.IndividualNode, 'I4'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to range restriction node: Individual')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_chain_node_and_range_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram37')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to range restriction node: role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_property_assertion_node_and_range_restriction_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram38')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid input to range restriction node: property assertion node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_role_node_and_range_restriction_node_with_role_node_in_input(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram39')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.RoleNode, 'R5'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid qualified range restriction: Role + Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_attribute_node_and_range_restriction_node_with_self_restriction(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram40')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.RangeRestrictionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.AttributeNode, 'A4'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Attributes do not have self')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_input_between_value_domain_node_and_facet_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram41')
        num_edges_in_project = len(self.project.edges())
        target = first(filter(lambda x: x.type() is Item.FacetNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.InputEdge, (Item.ValueDomainNode, 'xsd:string'), target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Facet node cannot be target of any input')
        self.assertFalse(self.project.profile.pvr().isValid())

    #############################################
    #   MEMBERSHIP
    #################################

    def test_membership_between_concept_and_concept(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram42')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, (Item.ConceptNode, 'C1'), (Item.ConceptNode, 'C2'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid source for membership edge: Concept')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_individual_and_role(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram44')
        num_edges_in_project = len(self.project.edges())
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, (Item.IndividualNode, 'I1'), (Item.RoleNode, 'R4'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid target for Concept assertion: Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_role_instance_and_role_chain_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram43')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.RoleChainNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid target for Role assertion: role chain node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_role_instance_and_neutral_chained_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram46')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Detected unsupported operator sequence on intersection node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_attribute_instance_and_role_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram45')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, source, (Item.RoleNode, 'R1'))
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Invalid target for Attribute assertion: Role')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_attribute_instance_and_neutral_chained_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram47')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Detected unsupported operator sequence on intersection node')
        self.assertFalse(self.project.profile.pvr().isValid())

    def test_membership_between_neutral_property_assertion_node_and_neutral_chained_complement_node(self):
        # GIVEN
        self.__give_focus_to_diagram('diagram48')
        num_edges_in_project = len(self.project.edges())
        source = first(filter(lambda x: x.type() is Item.PropertyAssertionNode, self.project.nodes(self.session.mdi.activeDiagram())))
        target = first(filter(lambda x: x.type() is Item.ComplementNode, self.project.nodes(self.session.mdi.activeDiagram())))
        # WHEN
        self.__insert_edge_between(Item.MembershipEdge, source, target)
        # THEN
        self.assertEqual(len(self.project.edges()), num_edges_in_project)
        self.assertEqual(self.project.profile.pvr().message(), 'Detected unsupported operator sequence on intersection node')
        self.assertFalse(self.project.profile.pvr().isValid())