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

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath

from tests import EddyTestCase


class PaletteTestCase(EddyTestCase):
    """
    Tests for the palette plugin.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        super(PaletteTestCase, self).setUp()
        self.init('test_project_1')
        self.session.sgnFocusDiagram.emit(
            self.project.diagram(expandPath('@tests/.tests/test_project_1/diagram.graphol')))

    #############################################
    #   TEST NODE INSERTION
    #################################

    def test_insert_single_node(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        view = self.session.mdi.activeView()
        plugin = self.session.plugin('palette')
        palette = plugin.widget('palette')
        button = palette.button(Item.ConceptNode)
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        QtTest.QTest.mouseClick(button, QtCore.Qt.LeftButton)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.NodeAdd)
        self.assertIs(diagram.modeParam, Item.ConceptNode)
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, position)
        # THEN
        self.assertFalse(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.Idle)
        self.assertIsNone(diagram.modeParam)

    def test_insert_single_node_with_control_modifier(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        view = self.session.mdi.activeView()
        plugin = self.session.plugin('palette')
        palette = plugin.widget('palette')
        button = palette.button(Item.ConceptNode)
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
        # WHEN
        QtTest.QTest.mouseClick(button, QtCore.Qt.LeftButton)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.NodeAdd)
        self.assertIs(diagram.modeParam, Item.ConceptNode)
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.NodeAdd)
        self.assertIs(diagram.modeParam, Item.ConceptNode)

    def test_insert_multiple_nodes_with_control_modifier(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        view = self.session.mdi.activeView()
        plugin = self.session.plugin('palette')
        palette = plugin.widget('palette')
        button = palette.button(Item.RoleNode)
        node = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
        # WHEN
        QtTest.QTest.mouseClick(button, QtCore.Qt.LeftButton)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.NodeAdd)
        self.assertIs(diagram.modeParam, Item.RoleNode)
        # WHEN
        for position in positions:
            QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.NodeAdd)
        self.assertIs(diagram.modeParam, Item.RoleNode)

    #############################################
    #   TEST EDGE INSERTION
    #################################

    def test_insert_edge(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        view = self.session.mdi.activeView()
        plugin = self.session.plugin('palette')
        palette = plugin.widget('palette')
        button = palette.button(Item.InclusionEdge)
        node1 = first(self.project.predicates(Item.ConceptNode, 'Male', diagram))
        node2 = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos())
        # WHEN
        QtTest.QTest.mouseClick(button, QtCore.Qt.LeftButton)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.EdgeAdd)
        self.assertIs(diagram.modeParam, Item.InclusionEdge)
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
        QtTest.QTest.mouseMove(view.viewport(), pos2)
        # THEN
        self.assertTrue(button.isChecked())
        # WHEN
        QtTest.QTest.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
        # THEN
        self.assertFalse(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.Idle)
        self.assertIsNone(diagram.modeParam)

    def test_insert_edge_with_control_modifier(self):
        # GIVEN
        diagram = self.session.mdi.activeDiagram()
        view = self.session.mdi.activeView()
        plugin = self.session.plugin('palette')
        palette = plugin.widget('palette')
        button = palette.button(Item.InclusionEdge)
        node1 = first(self.project.predicates(Item.ConceptNode, 'Male', diagram))
        node2 = first(self.project.predicates(Item.ConceptNode, 'Person', diagram))
        pos1 = view.mapFromScene(node1.pos())
        pos2 = view.mapFromScene(node2.pos())
        # WHEN
        QtTest.QTest.mouseClick(button, QtCore.Qt.LeftButton)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.EdgeAdd)
        self.assertIs(diagram.modeParam, Item.InclusionEdge)
        # WHEN
        QtTest.QTest.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, pos1)
        QtTest.QTest.mouseMove(view.viewport(), pos2)
        # THEN
        self.assertTrue(button.isChecked())
        # WHEN
        QtTest.QTest.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, pos2)
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(diagram.mode, DiagramMode.EdgeAdd)
        self.assertIs(diagram.modeParam, Item.InclusionEdge)