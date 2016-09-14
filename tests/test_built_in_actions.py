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


from tests import EddyTestCase

from eddy.core.functions.misc import first
from eddy.core.datatypes.graphol import Item


class BuiltInActionsTestCase(EddyTestCase):
    """
    Tests for built-in actions.
    """
    #############################################
    #   CUT / COPY / PASTE
    #################################

    def test_action_copy(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('copy')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()))
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertTrue(self.session.undostack.isClean())

    def test_action_copy_and_paste_single_node_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_copy = self.session.action('copy')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        # WHEN
        action_copy.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes + 1, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()))
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_copy_and_paste_single_node_with_hanging_edges_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_copy = self.session.action('copy')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        for edge in node.edges:
            edge.setSelected(True)
        # WHEN
        action_copy.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes + 1, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()))
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_copy_and_paste_multiple_nodes_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_copy = self.session.action('copy')
        action_paste = self.session.action('paste')
        node1 = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        node2 = first(self.project.predicates(Item.RoleNode, 'hasAncestor', diagram))
        node3 = first(self.project.predicates(Item.RoleNode, 'hasFather', diagram))
        node4 = first(self.project.predicates(Item.RoleNode, 'hasMother', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node1.setSelected(True)
        node2.setSelected(True)
        node3.setSelected(True)
        node4.setSelected(True)
        # WHEN
        action_copy.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes + 4, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()))
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 4)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_copy_and_paste_multiple_nodes_with_shared_edges_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_copy = self.session.action('copy')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        for edge in node.edges:
            edge.setSelected(True)
            edge.other(node).setSelected(True)
        # WHEN
        action_copy.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes + 4, len(diagram.nodes()))
        self.assertEqual(num_edges + 3, len(diagram.edges()))
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 7)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_cut(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('cut')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        # WHEN
        diagram.clearSelection()
        node.setSelected(True)
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()) + 1)
        self.assertEqual(num_edges, len(diagram.edges()) + 3)
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_cut_and_paste_single_node_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_cut = self.session.action('cut')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        # WHEN
        action_cut.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()) + 3)
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_cut_and_paste_single_node_with_hanging_edges_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_cut = self.session.action('cut')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        for edge in node.edges:
            edge.setSelected(True)
        # WHEN
        action_cut.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()) + 3)
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 1)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_cut_and_paste_multiple_nodes_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_cut = self.session.action('cut')
        action_paste = self.session.action('paste')
        node1 = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        node2 = first(self.project.predicates(Item.RoleNode, 'hasAncestor', diagram))
        node3 = first(self.project.predicates(Item.RoleNode, 'hasFather', diagram))
        node4 = first(self.project.predicates(Item.RoleNode, 'hasMother', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node1.setSelected(True)
        node2.setSelected(True)
        node3.setSelected(True)
        node4.setSelected(True)
        # WHEN
        action_cut.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()) + 7)
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 4)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_cut_and_paste_multiple_nodes_with_shared_edges_on_the_same_diagram(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action_cut = self.session.action('cut')
        action_paste = self.session.action('paste')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        for edge in node.edges:
            edge.setSelected(True)
            edge.other(node).setSelected(True)
        # WHEN
        action_cut.trigger()
        action_paste.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()) + 4)
        self.assertFalse(self.session.clipboard.empty())
        self.assertEqual(self.session.clipboard.size(), 7)
        self.assertFalse(self.session.undostack.isClean())

    #############################################
    #   DELETE / PURGE
    #################################

    def test_action_delete_single_node(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('delete')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()) + 1)
        self.assertEqual(num_edges, len(diagram.edges()) + 3)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_delete_multiple_nodes_with_shared_edges(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('delete')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        for edge in node.edges:
            edge.other(node).setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()) + 4)
        self.assertEqual(num_edges, len(diagram.edges()) + 7)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_delete_multiple_edges(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('delete')
        node = first(self.project.predicates(Item.RoleNode, 'hasParent', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        for edge in node.edges:
            edge.setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()))
        self.assertEqual(num_edges, len(diagram.edges()) + 3)
        self.assertFalse(self.session.undostack.isClean())

    def test_action_purge_role_node(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('purge')
        node = first(self.project.predicates(Item.RoleNode, 'hasAncestor', diagram))
        num_nodes = len(diagram.nodes())
        num_edges = len(diagram.edges())
        diagram.clearSelection()
        node.setSelected(True)
        # WHEN
        action.trigger()
        # THEN
        self.assertEqual(num_nodes, len(diagram.nodes()) + 3)
        self.assertEqual(num_edges, len(diagram.edges()) + 5)
        self.assertFalse(self.session.undostack.isClean())

    #############################################
    #   ITEM SELECTION
    #################################

    def test_action_select_all(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        action = self.session.action('select_all')
        # WHEN
        action.trigger()
        # THEN
        self.assertAll([x.isSelected() for x in diagram.nodes()])
        self.assertAll([x.isSelected() for x in diagram.edges()])