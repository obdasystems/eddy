# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from grapholed.datatypes import ItemType, DiagramMode
from grapholed.items import InclusionEdge
from mockito import when
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from tests import GrapholEdTestCase


class Test_DiagramScene(GrapholEdTestCase):

    def setUp(self):
        """
        Setup DiagramScene specific test environment.
        """
        super().setUp()

        self.scene = self.mainwindow.createScene(5000, 5000)
        self.mainview = self.mainwindow.createView(self.scene)
        self.subwindow = self.mainwindow.createSubWindow(self.mainview)
        self.subwindow.showMaximized()
        self.mainwindow.mdi.setActiveSubWindow(self.subwindow)
        self.mainwindow.mdi.update()

        when(self.scene.settings).value('scene/snap_to_grid', False, bool).thenReturn(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   NODE INSERTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_insert_single_node(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.ConceptNode)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertTrue(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.NodeInsert)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(100, 100))
        # THEN
        self.assertFalse(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(2, self.scene.items())
        self.assertEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').isSelected())
        self.assertEquals(self.scene.node('n0').pos(), self.mainview.mapToScene(QPoint(100, 100)))

    def test_insert_multiple_nodes(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.ConceptNode)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 100))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(400, 100))
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.NodeInsert)
        self.assertLen(4, self.scene.items())
        self.assertEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertDictHasKey('n1', self.scene.nodesById)
        self.assertEqual(2, self.scene.undostack.count())
        self.assertEquals(self.scene.node('n0').pos(), self.mainview.mapToScene(QPoint(0, 100)))
        self.assertEquals(self.scene.node('n1').pos(), self.mainview.mapToScene(QPoint(400, 100)))
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGE INSERTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_insert_single_edge_with_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(9, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(+200, -200)))
        # THEN
        self.assertLen(9, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_single_edge_with_no_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(9, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(2000, -200)))
        # THEN
        self.assertLen(8, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertEmpty(self.scene.edgesById)
        self.assertEqual(0, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_multiple_edges_with_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200)))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200)))
        # THEN
        self.assertLen(11, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertDictHasKey('e1', self.scene.edgesById)
        self.assertDictHasKey('e2', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertIs(self.scene.edge('e1').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e1').target, self.scene.node('n2'))
        self.assertIs(self.scene.edge('e2').source, self.scene.node('n2'))
        self.assertIs(self.scene.edge('e2').target, self.scene.node('n3'))
        self.assertEqual(3, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())

    ####################################################################################################################
    #                                                                                                                  #
    #   ITEM SELECTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_select_single_item(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(+200, -220)))
        # THEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(1, self.scene.selectedNodes())
        self.assertLen(1, self.scene.selectedItems())
        self.assertTrue(self.scene.node('n1').isSelected())

    def test_select_multiple_items(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +220)))
        # THEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(0, self.scene.selectedEdges())
        self.assertLen(3, self.scene.selectedNodes())
        self.assertLen(3, self.scene.selectedItems())
        self.assertTrue(self.scene.node('n0').isSelected())
        self.assertTrue(self.scene.node('n1').isSelected())
        self.assertTrue(self.scene.node('n3').isSelected())
        self.assertFalse(self.scene.node('n2').isSelected())

    def test_select_all_using_shortcut(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.keyClick(self.mainview.viewport(), 'a', Qt.ControlModifier)
        # THEN
        self.assertCountEqual(self.scene.nodes(), self.scene.selectedNodes())
        self.assertCountEqual(self.scene.edges(), self.scene.selectedEdges())

    ####################################################################################################################
    #                                                                                                                  #
    #   STUB DIAGRAM GENERATION                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def createStubDiagram1(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of 4 Concept nodes.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n2
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n3
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        self.scene.undostack.clear()

    def createStubDiagram2(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of 4 Concept nodes connected using 4 Inclusion edges and 1 Input edge.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n2
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n3
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.InclusionEdge), Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n0 -> n1
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n0 -> n2
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n2 -> n3
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n3 -> n1
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.InputEdge), Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n2 -> n1
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        self.scene.undostack.clear()