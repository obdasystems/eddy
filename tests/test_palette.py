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
Tests for the palette plugin.
"""

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
        session = Session(qapp, expandPath('@tests/test_project_3/test_project_3_1.graphol'))
        session.show()
    qtbot.addWidget(session)
    qtbot.waitExposed(session, timeout=3000)
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(session.project.diagram('diagram'))
    yield session


#############################################
#   TEST NODE INSERTION
#################################

def test_insert_single_node(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    view = session.mdi.activeView()
    plugin = session.plugin('palette')
    palette = plugin.widget('palette')
    button = palette.button(Item.ConceptNode)
    iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
    node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))
    position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
    # WHEN
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.NodeAdd
    assert diagram.modeParam is Item.ConceptNode
    # WHEN

    def on_timeout_insert_single_node():
        from eddy.ui.iri import IriBuilderDialog
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
        newIri = project.getIRI(newStr)
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                dialog = child
                break
        if dialog:
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
        assert not dialog is None
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 1
    QtCore.QTimer.singleShot(100, on_timeout_insert_single_node)
    qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, position)
    qtbot.wait(500)
    # THEN
    assert not button.isChecked()
    assert diagram.mode is DiagramMode.Idle
    assert diagram.modeParam is None


@pytest.mark.skip('node insert with control modifier is not supported anymore')
def test_insert_single_node_with_control_modifier(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    view = session.mdi.activeView()
    plugin = session.plugin('palette')
    palette = plugin.widget('palette')
    button = palette.button(Item.ConceptNode)
    iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
    node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))
    position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))
    # WHEN
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.NodeAdd
    assert diagram.modeParam is Item.ConceptNode
    # WHEN
    qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
    # THEN
    assert not button.isChecked()
    assert diagram.mode is not DiagramMode.NodeAdd
    assert diagram.modeParam is not Item.ConceptNode


@pytest.mark.skip('node insert with control modifier is not supported anymore')
def test_insert_multiple_nodes_with_control_modifier(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    view = session.mdi.activeView()
    plugin = session.plugin('palette')
    palette = plugin.widget('palette')
    button = palette.button(Item.RoleNode)
    iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
    node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))
    positions = (view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200))
    # WHEN
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.NodeAdd
    assert diagram.modeParam is Item.RoleNode
    # WHEN
    for position in positions:
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)
    # THEN
    assert not button.isChecked()
    assert diagram.mode is not DiagramMode.NodeAdd
    assert diagram.modeParam is not Item.RoleNode


#############################################
#   TEST EDGE INSERTION
#################################

def test_insert_edge(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    view = session.mdi.activeView()
    plugin = session.plugin('palette')
    palette = plugin.widget('palette')
    button = palette.button(Item.InclusionEdge)

    iri1 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Male')
    node1 = first(project.iriOccurrences(Item.ConceptNode, iri1, diagram))

    iri2 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
    node2 = first(project.iriOccurrences(Item.ConceptNode, iri2, diagram))

    pos1 = view.mapFromScene(node1.pos())
    pos2 = view.mapFromScene(node2.pos())
    # WHEN
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.EdgeAdd
    assert diagram.modeParam is Item.InclusionEdge
    # WHEN
    qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos1)
    qtbot.mouseMove(view.viewport(), pos2)
    # THEN
    assert button.isChecked()
    # WHEN
    qtbot.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos2)
    # THEN
    assert not button.isChecked()
    assert diagram.mode is DiagramMode.Idle
    assert diagram.modeParam is None


def test_insert_edge_with_control_modifier(session, qtbot):
    # GIVEN
    project = session.project
    diagram = session.mdi.activeDiagram()
    view = session.mdi.activeView()
    plugin = session.plugin('palette')
    palette = plugin.widget('palette')
    button = palette.button(Item.InclusionEdge)

    iri1 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Male')
    node1 = first(project.iriOccurrences(Item.ConceptNode, iri1, diagram))

    iri2 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
    node2 = first(project.iriOccurrences(Item.ConceptNode, iri2, diagram))

    pos1 = view.mapFromScene(node1.pos())
    pos2 = view.mapFromScene(node2.pos())
    # WHEN
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.EdgeAdd
    assert diagram.modeParam is Item.InclusionEdge
    # WHEN
    qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, pos1)
    qtbot.mouseMove(view.viewport(), pos2)
    # THEN
    assert button.isChecked()
    # WHEN
    qtbot.mouseRelease(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, pos2)
    # THEN
    assert button.isChecked()
    assert diagram.mode is DiagramMode.EdgeAdd
    assert diagram.modeParam is Item.InclusionEdge

