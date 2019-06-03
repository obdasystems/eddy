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


import pytest

from PyQt5 import QtCore

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.ui.session import Session


@pytest.fixture
def session(qapp, qtbot, logging_disabled):
    """
    Provide an initialized Session instance.
    """
    with logging_disabled:
        session = Session(qapp, expandPath('@tests/test_project_1'))
        session.show()
    qtbot.addWidget(session)
    qtbot.waitExposed(session, timeout=3000)
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(session.project.diagram('diagram'))
    yield session


class TestDiagram:
    """
    Tests for eddy's diagram operations.
    """
    #############################################
    #   NODE INSERTION
    #################################

    def test_insert_single_concept_node(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        node = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, position)
        # THEN
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.predicates(Item.ConceptNode, 'test:concept')) == 1

    def test_insert_single_concept_node_with_control_modifier(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        node = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.predicates(Item.ConceptNode, 'test:concept')) == 1

    def test_insert_multiple_concept_nodes_with_control_modifier(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        node = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
        # WHEN
        for position in positions:
            qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        assert num_nodes_in_diagram == len(diagram.nodes()) - 3
        assert num_items_in_project == len(project.items()) - 3
        assert num_nodes_in_project == len(project.nodes()) - 3
        assert len(project.predicates(Item.ConceptNode, 'test:concept')) == 3

    def test_insert_multiple_concept_nodes_with_control_modifier_released_after_insertion(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        node = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
        # WHEN
        for position in positions:
            qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        qtbot.keyRelease(session, QtCore.Qt.Key_Control)
        # THEN
        assert num_nodes_in_diagram == len(diagram.nodes()) - 3
        assert num_items_in_project == len(project.items()) - 3
        assert num_nodes_in_project == len(project.nodes()) - 3
        assert len(project.predicates(Item.ConceptNode, 'test:concept')) == 3

    #############################################
    #   EDGE INSERTION
    #################################

    def test_insert_edge(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.EdgeAdd, Item.InclusionEdge)
        num_edges_in_diagram = len(diagram.edges())
        num_items_in_project = len(project.items())
        num_edges_in_project = len(project.edges())
        node1 = first(project.predicates(Item.ConceptNode, 'test:Male', diagram))
        node2 = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        num_edges_in_node1 = len(node1.edges)
        num_edges_in_node2 = len(node2.edges)
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos())
        # WHEN
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
        qtbot.mouseMove(view.viewport(), pos2)
        # THEN
        assert diagram.isEdgeAdd()
        # WHEN
        qtbot.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
        # THEN
        assert not diagram.isEdgeAdd()
        assert num_edges_in_diagram == len(diagram.edges()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_edges_in_project == len(project.edges()) - 1
        assert num_edges_in_node1 == len(node1.edges) - 1
        assert num_edges_in_node2 == len(node2.edges) - 1

    def test_insert_edge_with_missing_endpoint(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.EdgeAdd, Item.InclusionEdge)
        num_edges_in_diagram = len(diagram.edges())
        num_items_in_project = len(project.items())
        num_edges_in_project = len(project.edges())
        node1 = first(project.predicates(Item.ConceptNode, 'test:Male', diagram))
        node2 = first(project.predicates(Item.ConceptNode, 'test:Person', diagram))
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
        qtbot.mouseMove(view.viewport(), pos2)
        # THEN
        assert diagram.isEdgeAdd()
        # WHEN
        qtbot.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
        # THEN
        assert not diagram.isEdgeAdd()
        assert num_edges_in_diagram == len(diagram.edges())
        assert num_items_in_project == len(project.items())
        assert num_edges_in_project == len(project.edges())
