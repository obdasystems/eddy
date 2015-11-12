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


from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from grapholed.datatypes import ItemType, DiagramMode
from grapholed.items import InclusionEdge
from tests import GrapholEdTestCase


class Test_DiagramScene(GrapholEdTestCase):

    def setUp(self):
        super().setUp()
        self.scene = self.mainwindow.getScene(5000, 5000)
        self.mainview = self.mainwindow.getMainView(self.scene)
        self.subwindow = self.mainwindow.getMDISubWindow(self.mainview)
        self.subwindow.showMaximized() # MUST KEEP OR WE CAN'T PROCESS EVENTS
        self.mainwindow.mdiArea.setActiveSubWindow(self.subwindow)
        self.mainwindow.mdiArea.update()

    def test_insert_node_single(self):
        # GIVEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
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
        self.assertEqual(1, self.scene.undoStack.count())
        self.assertTrue(self.scene.nodesById['n0'].isSelected())
        self.assertEquals(self.scene.nodesById['n0'].pos(), self.mainview.mapToScene(QPoint(100, 100)))

    def test_insert_node_multi(self):
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
        self.assertEqual(2, self.scene.undoStack.count())
        self.assertEquals(self.scene.node('n0').pos(), self.mainview.mapToScene(QPoint(0, 100)))
        self.assertEquals(self.scene.node('n1').pos(), self.mainview.mapToScene(QPoint(400, 100)))
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())

    def test_insert_edge_single_with_endpoint_release(self):
        # GIVEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 0))
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(400, 0))
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 0))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(5, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(400, 0))
        # THEN
        self.assertLen(5, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertDictHasKey('n1', self.scene.nodesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertEqual(3, self.scene.undoStack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_edge_single_with_no_endpoint_release(self):
        # GIVEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 0))
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(400, 0))
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 0))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(5, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(2000, 0))
        # THEN
        self.assertLen(4, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertDictHasKey('n1', self.scene.nodesById)
        self.assertEqual(2, self.scene.undoStack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_edge_multi_with_endpoint_release(self):
        # GIVEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 0))
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(400, 0))
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(0, 400))
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 0))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(400, 0))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 0))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 400))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(400, 0))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 400))
        # THEN
        self.assertLen(9, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertDictHasKey('n1', self.scene.nodesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertDictHasKey('e1', self.scene.edgesById)
        self.assertDictHasKey('e2', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertIs(self.scene.edge('e1').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e1').target, self.scene.node('n2'))
        self.assertEqual(6, self.scene.undoStack.count())
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())