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


from PyQt5 import QtCore
from PyQt5 import QtTest

from tests import EddyTestCase

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath


class DiagramTestCase(EddyTestCase):
    """
    Tests for eddy's diagram operations.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        super(DiagramTestCase, self).setUp()
        self.init('test_project_1')
        self.session.sgnFocusDiagram.emit(self.project.diagram(expandPath('@tests/.tests/test_project_1/diagram.graphol')))

    #############################################
    #   NODE INSERTION
    #################################

    def test_insert_single_concept_node(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(self.project.items())
        num_nodes_in_project = len(self.project.nodes())
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, position)
        # THEN
        self.assertEqual(num_nodes_in_diagram, len(diagram.nodes()) - 1)
        self.assertEqual(num_items_in_project, len(self.project.items()) - 1)
        self.assertEqual(num_nodes_in_project, len(self.project.nodes()) - 1)
        self.assertLen(1, self.project.predicates(Item.ConceptNode, 'concept'))

    def test_insert_single_concept_node_with_control_modifier(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(self.project.items())
        num_nodes_in_project = len(self.project.nodes())
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        self.assertEqual(num_nodes_in_diagram, len(diagram.nodes()) - 1)
        self.assertEqual(num_items_in_project, len(self.project.items()) - 1)
        self.assertEqual(num_nodes_in_project, len(self.project.nodes()) - 1)
        self.assertLen(1, self.project.predicates(Item.ConceptNode, 'concept'))

    def test_insert_multiple_concept_nodes_with_control_modifier(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(self.project.items())
        num_nodes_in_project = len(self.project.nodes())
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
        # WHEN
        for position in positions:
            QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        self.assertEqual(num_nodes_in_diagram, len(diagram.nodes()) - 3)
        self.assertEqual(num_items_in_project, len(self.project.items()) - 3)
        self.assertEqual(num_nodes_in_project, len(self.project.nodes()) - 3)
        self.assertLen(3, self.project.predicates(Item.ConceptNode, 'concept'))

    def test_insert_multiple_concept_nodes_with_control_modifier_released_after_insertion(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(self.project.items())
        num_nodes_in_project = len(self.project.nodes())
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
        # WHEN
        for position in positions:
            QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        QtTest.QTest.keyRelease(self.session, QtCore.Qt.Key_Control)
        # THEN
        self.assertEqual(num_nodes_in_diagram, len(diagram.nodes()) - 3)
        self.assertEqual(num_items_in_project, len(self.project.items()) - 3)
        self.assertEqual(num_nodes_in_project, len(self.project.nodes()) - 3)
        self.assertLen(3, self.project.predicates(Item.ConceptNode, 'concept'))

    #############################################
    #   EDGE INSERTION
    #################################

    def test_insert_edge(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.EdgeAdd, Item.InclusionEdge)
        num_edges_in_diagram = len(diagram.edges())
        num_items_in_project = len(self.project.items())
        num_edges_in_project = len(self.project.edges())
        node1 = first(self.project.predicates(Item.ConceptNode, 'Male', diagram))
        node2 = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        num_edges_in_node1 = len(node1.edges)
        num_edges_in_node2 = len(node2.edges)
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos())
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
        QtTest.QTest.mouseMove(view.viewport(), pos2)
        # THEN
        self.assertTrue(diagram.isEdgeAdd())
        # WHEN
        QtTest.QTest.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
        # THEN
        self.assertFalse(diagram.isEdgeAdd())
        self.assertEqual(num_edges_in_diagram, len(diagram.edges()) - 1)
        self.assertEqual(num_items_in_project, len(self.project.items()) - 1)
        self.assertEqual(num_edges_in_project, len(self.project.edges()) - 1)
        self.assertEqual(num_edges_in_node1, len(node1.edges) - 1)
        self.assertEqual(num_edges_in_node2, len(node2.edges) - 1)

    def test_insert_edge_with_missing_endpoint(self):
        # GIVEN
        view = self.session.mdi.activeView()
        diagram = self.session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.EdgeAdd, Item.InclusionEdge)
        num_edges_in_diagram = len(diagram.edges())
        num_items_in_project = len(self.project.items())
        num_edges_in_project = len(self.project.edges())
        node1 = first(self.project.predicates(Item.ConceptNode, 'Male', diagram))
        node2 = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
        QtTest.QTest.mouseMove(view.viewport(), pos2)
        # THEN
        self.assertTrue(diagram.isEdgeAdd())
        # WHEN
        QtTest.QTest.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
        # THEN
        self.assertFalse(diagram.isEdgeAdd())
        self.assertEqual(num_edges_in_diagram, len(diagram.edges()))
        self.assertEqual(num_items_in_project, len(self.project.items()))
        self.assertEqual(num_edges_in_project, len(self.project.edges()))
