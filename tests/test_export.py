# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from eddy.core.datatypes import OWLSyntax
from eddy.core.exporters import OWLExporter, GrapholExporter
from eddy.core.functions import expandPath, isEmpty

from tests import EddyTestCase


class Test_Export(EddyTestCase):

    def setUp(self):
        """
        Setup Translation specific test environment.
        """
        super().setUp()

    def init(self, path=None):
        """
        Additional specific test case initialiation tasks.
        :type path: str
        """
        if path:
            self.scene = self.mainwindow.createSceneFromGrapholFile(expandPath(path))
        else:
            self.scene = self.mainwindow.createScene(5000, 5000)

        self.mainview = self.mainwindow.createView(self.scene)
        self.subwindow = self.mainwindow.createSubWindow(self.mainview)
        self.subwindow.show()
        self.mainwindow.mdi.setActiveSubWindow(self.subwindow)
        self.mainwindow.mdi.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   EXAMPLE FILES -> OWL                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def test_animals_graphol_to_owl(self):
        # GIVEN
        self.init('@examples/Animals.graphol')
        # WHEN
        exporter = OWLExporter(scene=self.scene, ontoIRI='IRI', ontoPrefix='PREFIX')
        exporter.work()
        # THEN
        translation = exporter.export(OWLSyntax.Functional)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_family_graphol_to_owl(self):
        # GIVEN
        self.init('@examples/Family.graphol')
        # WHEN
        exporter = OWLExporter(scene=self.scene, ontoIRI='IRI', ontoPrefix='PREFIX')
        exporter.work()
        # THEN
        translation = exporter.export(OWLSyntax.Functional)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_pizza_graphol_to_owl(self):
        # GIVEN
        self.init('@examples/Pizza.graphol')
        # WHEN
        exporter = OWLExporter(scene=self.scene, ontoIRI='IRI', ontoPrefix='PREFIX')
        exporter.work()
        # THEN
        translation = exporter.export(OWLSyntax.Functional)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_diet_graphol_to_owl(self):
        # GIVEN
        self.init('@examples/Diet.graphol')
        # WHEN
        exporter = OWLExporter(scene=self.scene, ontoIRI='IRI', ontoPrefix='PREFIX')
        exporter.work()
        # THEN
        translation = exporter.export(OWLSyntax.Functional)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_lubm_graphol_to_owl(self):
        # GIVEN
        self.init('@examples/LUBM.graphol')
        # WHEN
        exporter = OWLExporter(scene=self.scene, ontoIRI='IRI', ontoPrefix='PREFIX')
        exporter.work()
        # THEN
        translation = exporter.export(OWLSyntax.Functional)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    ####################################################################################################################
    #                                                                                                                  #
    #   EXAMPLE FILES -> GRAPHOL                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def test_animals_graphol_to_graphol(self):
        # GIVEN
        self.init('@examples/Animals.graphol')
        # WHEN
        exporter = GrapholExporter(scene=self.scene)
        exporter.run()
        # THEN
        translation = exporter.export(indent=2)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_family_graphol_to_graphol(self):
        # GIVEN
        self.init('@examples/Family.graphol')
        # WHEN
        exporter = GrapholExporter(scene=self.scene)
        exporter.run()
        # THEN
        translation = exporter.export(indent=2)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_pizza_graphol_to_graphol(self):
        # GIVEN
        self.init('@examples/Pizza.graphol')
        # WHEN
        exporter = GrapholExporter(scene=self.scene)
        exporter.run()
        # THEN
        translation = exporter.export(indent=2)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_diet_graphol_to_graphol(self):
        # GIVEN
        self.init('@examples/Diet.graphol')
        # WHEN
        exporter = GrapholExporter(scene=self.scene)
        exporter.run()
        # THEN
        translation = exporter.export(indent=2)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))

    def test_lubm_graphol_to_graphol(self):
        # GIVEN
        self.init('@examples/LUBM.graphol')
        # WHEN
        exporter = GrapholExporter(scene=self.scene)
        exporter.run()
        # THEN
        translation = exporter.export(indent=2)
        self.assertIsInstance(translation, str)
        self.assertFalse(isEmpty(translation))