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
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.ui.iri import IriBuilderDialog
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

        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))

        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))

        # THEN
        def on_timeout_single_concept_node():
            num_nodes_in_diagram = len(diagram.nodes())
            num_items_in_project = len(project.items())
            num_nodes_in_project = len(project.nodes())
            dialog = None
            for child in session.children():
                if isinstance(child, IriBuilderDialog):
                    dialog = child
                    break
            if dialog:
                newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
                newIri = project.getIRI(newStr)
                dialog.widget('full_iri_field').setValue(newStr)
                dialog.accept()
            assert not dialog is None
            assert num_nodes_in_diagram == len(diagram.nodes()) - 1
            assert num_items_in_project == len(project.items()) - 1
            assert num_nodes_in_project == len(project.nodes()) - 1
            assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
            assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 1
        # WHEN
        QtCore.QTimer.singleShot(100, on_timeout_single_concept_node)
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, position)

    def test_insert_single_concept_node_with_control_modifier(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))

        position = view.mapFromScene(node.pos() - QtCore.QPointF(-200, 0))

        # THEN
        def on_timeout_single_concept_node_with_control_modifier():
            num_nodes_in_diagram = len(diagram.nodes())
            num_items_in_project = len(project.items())
            num_nodes_in_project = len(project.nodes())
            dialog = None
            for child in session.children():
                if isinstance(child, IriBuilderDialog):
                    dialog = child
                    break
            if dialog:
                newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
                newIri = project.getIRI(newStr)
                dialog.widget('full_iri_field').setValue(newStr)
                dialog.accept()
            assert not dialog is None
            assert num_nodes_in_diagram == len(diagram.nodes()) - 1
            assert num_items_in_project == len(project.items()) - 1
            assert num_nodes_in_project == len(project.nodes()) - 1
            assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
            assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 1

        # WHEN
        QtCore.QTimer.singleShot(100, on_timeout_single_concept_node_with_control_modifier)
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, position)

    def test_insert_multiple_concept_nodes_with_control_modifier(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        init_num_nodes_in_diagram = len(diagram.nodes())
        init_num_items_in_project = len(project.items())
        init_num_nodes_in_project = len(project.nodes())

        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))

        positions = [view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200)]
        alreadyAddedIDs = []

        newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
        newIri = project.getIRI(newStr)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[0])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                dialog = child
                break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
            alreadyAddedIDs.append(dialog.node.id)
        assert not dialog is None
        assert not diagram.mode == DiagramMode.NodeAdd
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[1])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                if not child.node.id in alreadyAddedIDs:
                    dialog = child
                    break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
            alreadyAddedIDs.append(dialog.node.id)
        assert not dialog is None
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[2])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                if not child.node.id in alreadyAddedIDs:
                    dialog = child
                    break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
        assert not dialog is None
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1

        # FINALLY
        assert init_num_nodes_in_diagram == len(diagram.nodes()) - 3
        assert init_num_items_in_project == len(project.items()) - 3
        assert init_num_nodes_in_project == len(project.nodes()) - 3
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 3

    def test_insert_multiple_concept_nodes_with_control_modifier_released_after_insertion(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        init_num_nodes_in_diagram = len(diagram.nodes())
        init_num_items_in_project = len(project.items())
        init_num_nodes_in_project = len(project.nodes())

        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))

        positions = [view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200)]
        alreadyAddedIDs = []

        newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
        newIri = project.getIRI(newStr)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[0])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                dialog = child
                break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
            alreadyAddedIDs.append(dialog.node.id)
        assert not dialog is None
        assert not diagram.mode == DiagramMode.NodeAdd
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[1])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                if not child.node.id in alreadyAddedIDs:
                    dialog = child
                    break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
            alreadyAddedIDs.append(dialog.node.id)
        assert not dialog is None
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[2])
        num_nodes_in_diagram = len(diagram.nodes())
        num_items_in_project = len(project.items())
        num_nodes_in_project = len(project.nodes())
        dialog = None
        for child in session.children():
            if isinstance(child, IriBuilderDialog):
                if not child.node.id in alreadyAddedIDs:
                    dialog = child
                    break
        if dialog:
            newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
            dialog.widget('full_iri_field').setValue(newStr)
            dialog.accept()
        assert not dialog is None
        assert num_nodes_in_diagram == len(diagram.nodes()) - 1
        assert num_items_in_project == len(project.items()) - 1
        assert num_nodes_in_project == len(project.nodes()) - 1
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri)) - 1

        # FINALLY
        qtbot.keyRelease(session, QtCore.Qt.Key_Control)
        assert init_num_nodes_in_diagram == len(diagram.nodes()) - 3
        assert init_num_items_in_project == len(project.items()) - 3
        assert init_num_nodes_in_project == len(project.nodes()) - 3
        assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
        assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 3

    '''
    def test_insert_multiple_concept_nodes_with_control_modifier(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)

        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))

        positions = [view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200)]

        # THEN
        def on_timeout_multiple_concept_nodes_with_control_modifier(iteration, alreadyAddedIDs=[]):
            num_nodes_in_diagram = len(diagram.nodes())
            num_items_in_project = len(project.items())
            num_nodes_in_project = len(project.nodes())
            dialog = None
            dialogCount = 0
            for child in session.children():
                if isinstance(child, IriBuilderDialog):
                    dialogCount +=1
                    if not child.node.id in alreadyAddedIDs:
                        dialog = child
                        break
            if dialog:
                newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
                newIri = project.getIRI(newStr)
                newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))
                dialog.widget('full_iri_field').setValue(newStr)
                dialog.accept()
                alreadyAddedIDs.append(dialog.node.id)
            assert not dialog is None
            assert num_nodes_in_diagram == len(diagram.nodes()) - 1
            assert num_items_in_project == len(project.items()) - 1
            assert num_nodes_in_project == len(project.nodes()) - 1
            assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
            assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri))-1


            nextIteration = iteration+1
            if nextIteration<3:
                callback = functools.partial(on_timeout_multiple_concept_nodes_with_control_modifier, iteration=nextIteration, alreadyAddedIDs=alreadyAddedIDs)
                QtCore.QTimer.singleShot(100, callback)
                qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[nextIteration])
        # WHEN
        callback = functools.partial(on_timeout_multiple_concept_nodes_with_control_modifier, iteration=0)
        QtCore.QTimer.singleShot(100, callback)
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[0])

    def test_insert_multiple_concept_nodes_with_control_modifier_released_after_insertion(self, session, qtbot):
        # GIVEN
        project = session.project
        view = session.mdi.activeView()
        diagram = session.mdi.activeDiagram()
        diagram.setMode(DiagramMode.NodeAdd, Item.ConceptNode)
        init_num_nodes_in_diagram = len(diagram.nodes())
        init_num_items_in_project = len(project.items())
        init_num_nodes_in_project = len(project.nodes())
        iri = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node = first(project.iriOccurrences(Item.ConceptNode, iri, diagram))
        positions = [view.mapFromScene(node.pos() - QtCore.QPointF(-300, x)) for x in (0, +200, -200)]
        newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
        newIri = project.getIRI(newStr)

        # THEN
        def on_timeout_multiple_concept_nodes_with_control_modifier_released_after_insertion(iteration):
            num_nodes_in_diagram = len(diagram.nodes())
            num_items_in_project = len(project.items())
            num_nodes_in_project = len(project.nodes())
            dialog = None
            try:
                for child in session.children():
                    if isinstance(child, IriBuilderDialog):
                        dialog = child
                        break
                if dialog:
                    newStr = 'http://www.dis.uniroma1.it/~graphol/test_project/NewClass'
                    newIri = project.getIRI(newStr)
                    newCount = len(project.iriOccurrences(Item.ConceptNode, newIri))

                    dialog.widget('full_iri_field').setValue(newStr)
                    dialog.accept()
                assert not dialog is None
                assert num_nodes_in_diagram == len(diagram.nodes()) - 1
                assert num_items_in_project == len(project.items()) - 1
                assert num_nodes_in_project == len(project.nodes()) - 1
                assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
                assert newCount == len(project.iriOccurrences(Item.ConceptNode, newIri))-1
            except Exception as e:
                pass
            nextIteration = iteration + 1
            if(nextIteration<3):
                callback = functools.partial(on_timeout_multiple_concept_nodes_with_control_modifier_released_after_insertion, iteration=nextIteration)
                QtCore.QTimer.singleShot(100, callback)
                qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[nextIteration])

        # THEN FINALLY
        def on_final_timeout_multiple_concept_nodes_with_control_modifier_released_after_insertion(num_nodes_in_diagram, num_items_in_project, num_nodes_in_project):
            assert num_nodes_in_diagram == len(diagram.nodes()) - 3
            assert num_items_in_project == len(project.items()) - 3
            assert num_nodes_in_project == len(project.nodes()) - 3
            assert len(project.iriOccurrences(Item.ConceptNode, iri)) == 1
            assert len(project.iriOccurrences(Item.ConceptNode, newIri)) == 3

        finalCallback = functools.partial(on_final_timeout_multiple_concept_nodes_with_control_modifier_released_after_insertion, num_nodes_in_diagram=init_num_nodes_in_diagram, num_items_in_project=init_num_items_in_project, num_nodes_in_project=init_num_nodes_in_project)

        # WHEN
        callback = functools.partial(on_timeout_multiple_concept_nodes_with_control_modifier_released_after_insertion, iteration=0)
        QtCore.QTimer.singleShot(100, callback)
        qtbot.mousePress(view.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier, positions[0])
        # FINALLY
        qtbot.keyRelease(session, QtCore.Qt.Key_Control)
        #QtCore.QTimer.singleShot(2000, finalCallback)

    '''
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

        iri1 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Male')
        node1 = first(project.iriOccurrences(Item.ConceptNode, iri1, diagram))

        iri2 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node2 = first(project.iriOccurrences(Item.ConceptNode, iri2, diagram))

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

        iri1 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Male')
        node1 = first(project.iriOccurrences(Item.ConceptNode, iri1, diagram))

        iri2 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node2 = first(project.iriOccurrences(Item.ConceptNode, iri2, diagram))

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

    def test_change_diagram_font(self, session):
        # GIVEN
        project = session.project
        diagram = session.mdi.activeDiagram()

        iri1 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Male')
        node1 = first(project.iriOccurrences(Item.ConceptNode, iri1, diagram))

        iri2 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/Person')
        node2 = first(project.iriOccurrences(Item.ConceptNode, iri2, diagram))

        iri3 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/hasMother')
        node3 = first(project.iriOccurrences(Item.RoleNode, iri3, diagram))

        iri4 = project.getIRI('http://www.dis.uniroma1.it/~graphol/test_project/hasFather')
        node4 = first(project.iriOccurrences(Item.RoleNode, iri4, diagram))

        pos1 = node1.textPos()
        pos2 = node2.textPos()
        pos3 = node3.textPos()
        pos4 = node4.textPos()
        font = diagram.font()
        # WHEN
        diagram.setFont(Font(font=font, pixelSize=font.pixelSize() * 2))
        # THEN
        assert pos1 == node1.textPos()
        assert pos2 == node2.textPos()
        assert pos3 == node3.textPos()
        assert pos4 == node4.textPos()
        # WHEN
        diagram.setFont(font)
        # THEN
        assert pos1 == node1.textPos()
        assert pos2 == node2.textPos()
        assert pos3 == node3.textPos()
        assert pos4 == node4.textPos()

