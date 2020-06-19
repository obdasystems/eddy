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
import os

import pytest
from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.fsystem import cpdir, fcopy, fexists, mkdir
from eddy.core.functions.path import expandPath
from eddy.core.loaders.graphml import GraphMLOntologyLoader
from eddy.core.loaders.graphol import GrapholProjectLoader_v1
from eddy.core.loaders.graphol import GrapholProjectLoader_v2
from eddy.core.loaders.graphol_iri import GrapholIRIProjectLoader_v2, GrapholIRIProjectLoader_v3
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


@pytest.fixture(autouse=True)
def no_message_box(monkeypatch):
    """
    Patch QtWidgets.QMessageBox methods exec_() and show()
    """
    monkeypatch.setattr(QtWidgets.QMessageBox, 'exec_', lambda *args: True)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'show', lambda *args: True)


#############################################
#   GRAPHOL IMPORT
#################################
#No more supported
'''
def test_load_project_from_graphol_v1(session, qtbot, tmpdir):
    # GIVEN
    graphol = tmpdir.join('LUBM')
    cpdir(expandPath('@tests/test_resources/loaders/graphol/v1/LUBM'), str(graphol))
    project = session.project
    diagram = 'LUBM'
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    loader = GrapholProjectLoader_v1(str(graphol), session)
    loader.run()
    # THEN
    assert diagram in map(lambda d: d.name, loader.project.diagrams())
    assert len(loader.project.diagram(diagram).nodes()) == 71
    assert len(loader.project.diagram(diagram).edges()) == 80
    assert len(list(filter(lambda n: n.type() == Item.ConceptNode, loader.project.diagram(diagram).nodes()))) == 18
    assert len(list(filter(lambda n: n.type() == Item.RoleNode, loader.project.diagram(diagram).nodes()))) == 9
    assert len(list(filter(lambda n: n.type() == Item.AttributeNode, loader.project.diagram(diagram).nodes()))) == 5
    assert len(list(filter(lambda n: n.type() == Item.IndividualNode, loader.project.diagram(diagram).nodes()))) == 0
'''

#No more supported
'''
def test_load_project_from_graphol_v2(session, qtbot, tmpdir):
    # GIVEN
    graphol = tmpdir.join('LUBM')
    cpdir(expandPath('@tests/test_resources/loaders/graphol/v2/LUBM'), str(graphol))
    project = session.project
    diagram = 'LUBM'
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    loader = GrapholProjectLoader_v2(str(graphol), session)
    loader.run()
    # THEN
    assert diagram in map(lambda d: d.name, loader.nproject.diagrams())
    assert len(loader.nproject.diagram(diagram).nodes()) == 71
    assert len(loader.nproject.diagram(diagram).edges()) == 80
    assert len(list(filter(lambda n: n.type() == Item.ConceptNode, loader.nproject.diagram(diagram).nodes()))) == 18
    assert len(list(filter(lambda n: n.type() == Item.RoleNode, loader.nproject.diagram(diagram).nodes()))) == 9
    assert len(list(filter(lambda n: n.type() == Item.AttributeNode, loader.nproject.diagram(diagram).nodes()))) == 5
    assert len(list(filter(lambda n: n.type() == Item.IndividualNode, loader.nproject.diagram(diagram).nodes()))) == 0
'''

def test_load_project_from_graphol_v2(session, qtbot, tmpdir):
    # GIVEN
    graphol = tmpdir.join('MovieOntology/MovieOntology_v2.graphol')
    grapholDir = tmpdir.join('MovieOntology')
    mkdir(str(grapholDir))
    os.open(str(graphol), os.O_CREAT)
    fcopy(expandPath('@tests/test_resources/loaders/graphol/v2/MovieOntology/MovieOntology_v2.graphol'), str(graphol))

    project = session.project
    diagram1 = 'movie'
    diagram2 = 'territory'
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    loader = GrapholIRIProjectLoader_v3(str(graphol), session)
    loader.run()
    # THEN
    assert diagram1 in map(lambda d: d.name, loader.session.project.diagrams())
    assert len(loader.session.project.diagram(diagram1).nodes()) == 347
    assert len(loader.session.project.diagram(diagram1).edges()) == 433
    assert len(list(filter(lambda n: n.type() == Item.ConceptIRINode, loader.session.project.diagram(diagram1).nodes()))) == 65
    assert len(list(filter(lambda n: n.type() == Item.RoleIRINode, loader.session.project.diagram(diagram1).nodes()))) == 60
    assert len(list(filter(lambda n: n.type() == Item.AttributeIRINode, loader.session.project.diagram(diagram1).nodes()))) == 27
    assert len(list(filter(lambda n: n.type() == Item.IndividualIRINode, loader.session.project.diagram(diagram1).nodes()))) == 0
    assert diagram2 in map(lambda d: d.name, loader.session.project.diagrams())
    assert len(loader.session.project.diagram(diagram2).nodes()) == 8
    assert len(loader.session.project.diagram(diagram2).edges()) == 8
    assert len(list(filter(lambda n: n.type() == Item.ConceptIRINode, loader.session.project.diagram(diagram2).nodes()))) == 2
    assert len(list(filter(lambda n: n.type() == Item.RoleIRINode, loader.session.project.diagram(diagram2).nodes()))) == 2
    assert len(list(filter(lambda n: n.type() == Item.AttributeIRINode, loader.session.project.diagram(diagram2).nodes()))) == 0
    assert len(list(filter(lambda n: n.type() == Item.IndividualIRINode, loader.session.project.diagram(diagram2).nodes()))) == 0


def test_load_project_from_graphol_v3(session, qtbot, tmpdir):
    # GIVEN
    graphol = tmpdir.join('MovieOntology/MovieOntology_v3.graphol')
    grapholDir = tmpdir.join('MovieOntology')
    mkdir(str(grapholDir))
    os.open(str(graphol), os.O_CREAT)
    fcopy(expandPath('@tests/test_resources/loaders/graphol/v3/MovieOntology/MovieOntology_v3.graphol'), str(graphol))

    project = session.project
    diagram1 = 'movie'
    diagram2 = 'territory'
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    loader = GrapholIRIProjectLoader_v3(str(graphol), session)
    loader.run()
    # THEN
    assert diagram1 in map(lambda d: d.name, loader.session.project.diagrams())
    assert len(loader.session.project.diagram(diagram1).nodes()) == 347
    assert len(loader.session.project.diagram(diagram1).edges()) == 433
    assert len(list(filter(lambda n: n.type() == Item.ConceptIRINode, loader.session.project.diagram(diagram1).nodes()))) == 65
    assert len(list(filter(lambda n: n.type() == Item.RoleIRINode, loader.session.project.diagram(diagram1).nodes()))) == 60
    assert len(list(filter(lambda n: n.type() == Item.AttributeIRINode, loader.session.project.diagram(diagram1).nodes()))) == 27
    assert len(list(filter(lambda n: n.type() == Item.IndividualIRINode, loader.session.project.diagram(diagram1).nodes()))) == 0
    assert diagram2 in map(lambda d: d.name, loader.session.project.diagrams())
    assert len(loader.session.project.diagram(diagram2).nodes()) == 8
    assert len(loader.session.project.diagram(diagram2).edges()) == 8
    assert len(list(filter(lambda n: n.type() == Item.ConceptIRINode, loader.session.project.diagram(diagram2).nodes()))) == 2
    assert len(list(filter(lambda n: n.type() == Item.RoleIRINode, loader.session.project.diagram(diagram2).nodes()))) == 2
    assert len(list(filter(lambda n: n.type() == Item.AttributeIRINode, loader.session.project.diagram(diagram2).nodes()))) == 0
    assert len(list(filter(lambda n: n.type() == Item.IndividualIRINode, loader.session.project.diagram(diagram2).nodes()))) == 0


