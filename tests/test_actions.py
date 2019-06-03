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


"""
Tests for built-in actions.
"""

import pytest
from pytestqt.qtbot import QtBot

from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item
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


#############################################
#   CUT / COPY / PASTE
#################################

def test_action_copy(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('copy')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    # WHEN
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges())
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert session.undostack.isClean()


def test_action_copy_and_paste_single_predicate_node_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_copy = session.action('copy')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    # WHEN
    action_copy.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram + 1 == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges())
    assert num_items_in_project + 1 == len(project.items())
    assert num_nodes_in_project + 1 == len(project.nodes())
    assert num_edges_in_project == len(project.edges())
    assert num_items_in_project + 1 == len(project.items(diagram))
    assert num_nodes_in_project + 1 == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram))
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 2
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert not session.undostack.isClean()


def test_action_copy_and_paste_single_predicate_node_with_hanging_edges_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_copy = session.action('copy')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    for edge in node.edges:
        edge.setSelected(True)
    # WHEN
    action_copy.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram + 1 == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges())
    assert num_items_in_project + 1 == len(project.items())
    assert num_nodes_in_project + 1 == len(project.nodes())
    assert num_edges_in_project == len(project.edges())
    assert num_items_in_project + 1 == len(project.items(diagram))
    assert num_nodes_in_project + 1 == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram))
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 2
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert not session.undostack.isClean()


def test_action_copy_and_paste_multiple_predicate_nodes_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_copy = session.action('copy')
    action_paste = session.action('paste')
    node1 = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    node2 = first(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram))
    node3 = first(project.predicates(Item.RoleNode, 'test:hasFather', diagram))
    node4 = first(project.predicates(Item.RoleNode, 'test:hasMother', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node1.setSelected(True)
    node2.setSelected(True)
    node3.setSelected(True)
    node4.setSelected(True)
    # WHEN
    action_copy.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram + 4 == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges())
    assert num_items_in_project + 4 == len(project.items())
    assert num_nodes_in_project + 4 == len(project.nodes())
    assert num_edges_in_project == len(project.edges())
    assert num_items_in_project + 4 == len(project.items(diagram))
    assert num_nodes_in_project + 4 == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram))
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasFather', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasFather')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasMother', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasMother')) == 2
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 4
    assert not session.undostack.isClean()


def test_action_copy_and_paste_multiple_predicate_nodes_with_shared_edges_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_copy = session.action('copy')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    for edge in node.edges:
        edge.setSelected(True)
        edge.other(node).setSelected(True)
    # WHEN
    action_copy.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram + 4 == len(diagram.nodes())
    assert num_edges_in_diagram + 3 == len(diagram.edges())
    assert num_items_in_project + 7 == len(project.items())
    assert num_nodes_in_project + 4 == len(project.nodes())
    assert num_edges_in_project + 3 == len(project.edges())
    assert num_items_in_project + 7 == len(project.items(diagram))
    assert num_nodes_in_project + 4 == len(project.nodes(diagram))
    assert num_edges_in_project + 3 == len(project.edges(diagram))
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasFather', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasFather')) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasMother', diagram)) == 2
    assert len(project.predicates(Item.RoleNode, 'test:hasMother')) == 2
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 7
    assert not session.undostack.isClean()


def test_action_cut(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('cut')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    # WHEN
    diagram.clearSelection()
    node.setSelected(True)
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes()) + 1
    assert num_edges_in_diagram == len(diagram.edges()) + 3
    assert num_items_in_project == len(project.items()) + 4
    assert num_nodes_in_project == len(project.nodes()) + 1
    assert num_edges_in_project == len(project.edges()) + 3
    assert num_items_in_project == len(project.items(diagram)) + 4
    assert num_nodes_in_project == len(project.nodes(diagram)) + 1
    assert num_edges_in_project == len(project.edges(diagram)) + 3
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 0
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert not session.undostack.isClean()


def test_action_cut_and_paste_single_predicate_node_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_cut = session.action('cut')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    # WHEN
    action_cut.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges()) + 3
    assert num_items_in_project == len(project.items()) + 3
    assert num_nodes_in_project == len(project.nodes())
    assert num_edges_in_project == len(project.edges()) + 3
    assert num_items_in_project == len(project.items(diagram)) + 3
    assert num_nodes_in_project == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram)) + 3
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 1
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert not session.undostack.isClean()


def test_action_cut_and_paste_single_predicate_node_with_hanging_edges_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_cut = session.action('cut')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    diagram.clearSelection()
    node.setSelected(True)
    for edge in node.edges:
        edge.setSelected(True)
    # WHEN
    action_cut.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges()) + 3
    assert num_items_in_project == len(project.items()) + 3
    assert num_nodes_in_project == len(project.nodes())
    assert num_edges_in_project == len(project.edges()) + 3
    assert num_items_in_project == len(project.items(diagram)) + 3
    assert num_nodes_in_project == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram)) + 3
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 1
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 1
    assert not session.undostack.isClean()


def test_action_cut_and_paste_multiple_predicate_nodes_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_cut = session.action('cut')
    action_paste = session.action('paste')
    node1 = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    node2 = first(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram))
    node3 = first(project.predicates(Item.RoleNode, 'test:hasFather', diagram))
    node4 = first(project.predicates(Item.RoleNode, 'test:hasMother', diagram))
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    diagram.clearSelection()
    node1.setSelected(True)
    node2.setSelected(True)
    node3.setSelected(True)
    node4.setSelected(True)
    # WHEN
    action_cut.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges()) + 8
    assert num_items_in_project == len(project.items()) + 8
    assert num_nodes_in_project == len(project.nodes())
    assert num_edges_in_project == len(project.edges()) + 8
    assert num_items_in_project == len(project.items(diagram)) + 8
    assert num_nodes_in_project == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram)) + 8
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasFather', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasFather')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasMother', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasMother')) == 1
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 4
    assert not session.undostack.isClean()


def test_action_cut_and_paste_multiple_predicate_nodes_with_shared_edges_on_the_same_diagram(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action_cut = session.action('cut')
    action_paste = session.action('paste')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    diagram.clearSelection()
    node.setSelected(True)
    for edge in node.edges:
        edge.setSelected(True)
        edge.other(node).setSelected(True)
    # WHEN
    action_cut.trigger()
    action_paste.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges()) + 5
    assert num_items_in_project == len(project.items()) + 5
    assert num_nodes_in_project == len(project.nodes())
    assert num_edges_in_project == len(project.edges()) + 5
    assert num_items_in_project == len(project.items(diagram)) + 5
    assert num_nodes_in_project == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram)) + 5
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasFather', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasFather')) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasMother', diagram)) == 1
    assert len(project.predicates(Item.RoleNode, 'test:hasMother')) == 1
    assert not session.clipboard.empty()
    assert session.clipboard.size() == 7
    assert not session.undostack.isClean()


#############################################
#   DELETE / PURGE
#################################

def test_action_delete_single_predicate_node(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('delete')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    # WHEN
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes()) + 1
    assert num_edges_in_diagram == len(diagram.edges()) + 3
    assert num_items_in_project == len(project.items()) + 4
    assert num_nodes_in_project == len(project.nodes()) + 1
    assert num_edges_in_project == len(project.edges()) + 3
    assert num_items_in_project == len(project.items(diagram)) + 4
    assert num_nodes_in_project == len(project.nodes(diagram)) + 1
    assert num_edges_in_project == len(project.edges(diagram)) + 3
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 0
    assert not session.undostack.isClean()


def test_action_delete_multiple_predicate_nodes_with_shared_edges(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('delete')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    for edge in node.edges:
        edge.other(node).setSelected(True)
    # WHEN
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes()) + 4
    assert num_edges_in_diagram == len(diagram.edges()) + 8
    assert num_items_in_project == len(project.items()) + 12
    assert num_nodes_in_project == len(project.nodes()) + 4
    assert num_edges_in_project == len(project.edges()) + 8
    assert num_items_in_project == len(project.items(diagram)) + 12
    assert num_nodes_in_project == len(project.nodes(diagram)) + 4
    assert num_edges_in_project == len(project.edges(diagram)) + 8
    assert len(project.predicates(Item.RoleNode, 'test:hasParent', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasParent')) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasFather', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasFather')) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasMother', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasMother')) == 0
    assert not session.undostack.isClean()


def test_action_delete_multiple_edges(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('delete')
    node = first(project.predicates(Item.RoleNode, 'test:hasParent', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    for edge in node.edges:
        edge.setSelected(True)
    # WHEN
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes())
    assert num_edges_in_diagram == len(diagram.edges()) + 3
    assert num_items_in_project == len(project.items()) + 3
    assert num_nodes_in_project == len(project.nodes())
    assert num_edges_in_project == len(project.edges()) + 3
    assert num_items_in_project == len(project.items(diagram)) + 3
    assert num_nodes_in_project == len(project.nodes(diagram))
    assert num_edges_in_project == len(project.edges(diagram)) + 3
    assert not session.undostack.isClean()


def test_action_purge_role_node(session):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('purge')
    node = first(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram))
    num_items_in_project = len(project.items())
    num_nodes_in_project = len(project.nodes())
    num_edges_in_project = len(project.edges())
    num_nodes_in_diagram = len(diagram.nodes())
    num_edges_in_diagram = len(diagram.edges())
    diagram.clearSelection()
    node.setSelected(True)
    # WHEN
    action.trigger()
    # THEN
    assert num_nodes_in_diagram == len(diagram.nodes()) + 3
    assert num_edges_in_diagram == len(diagram.edges()) + 6
    assert num_items_in_project == len(project.items()) + 9
    assert num_nodes_in_project == len(project.nodes()) + 3
    assert num_edges_in_project == len(project.edges()) + 6
    assert num_items_in_project == len(project.items(diagram)) + 9
    assert num_nodes_in_project == len(project.nodes(diagram)) + 3
    assert num_edges_in_project == len(project.edges(diagram)) + 6
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor', diagram)) == 0
    assert len(project.predicates(Item.RoleNode, 'test:hasAncestor')) == 0
    assert not session.undostack.isClean()


#############################################
#   ITEM SELECTION
#################################

def test_action_select_all(session):
    # GIVEN
    diagram = session.mdi.activeDiagram()
    action = session.action('select_all')
    # WHEN
    action.trigger()
    # THEN
    assert all([x.isSelected() for x in diagram.nodes()])
    assert all([x.isSelected() for x in diagram.edges()])


#############################################
#   PROPERTIES DIALOG
#################################

def test_action_open_properties_dialog(session, qtbot: QtBot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('node_properties')
    diagram.clearSelection()
    for node in project.nodes(diagram):
        node.setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        assert node.isSelected()
        attempts = 0
        while not QtWidgets.QApplication.activeModalWidget():
            if attempts >= 20:
                pytest.fail('Timeout exceeded waiting for dialog to activate')
            qtbot.wait(250)
            attempts += 1
        QtWidgets.QApplication.activeModalWidget().close()
        node.setSelected(False)


#############################################
#   DESCRIPTION DIALOG
#################################

def test_action_open_description_dialog(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    action = session.action('node_description')
    diagram.clearSelection()
    for node in project.nodes(diagram):
        if node.type() in {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.IndividualNode}:
            node.setSelected(True)
            # WHEN
            action.trigger()
            # THEN
            assert node.isSelected()
            attempts = 0
            while not QtWidgets.QApplication.activeModalWidget():
                if attempts >= 20:
                    pytest.fail('Timeout exceeded waiting for dialog to activate')
                qtbot.wait(250)
                attempts += 1
            QtWidgets.QApplication.activeModalWidget().close()
            node.setSelected(False)

