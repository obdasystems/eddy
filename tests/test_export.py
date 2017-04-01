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


from mock import patch

from tests import EddyTestCase

from eddy.core.datatypes.owl import OWLSyntax, OWLAxiom
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.exporters.pdf import PdfDiagramExporter
from eddy.core.functions.fsystem import fread
from eddy.core.functions.path import expandPath


class ExportTestCase(EddyTestCase):
    """
    Tests for eddy's export facilities.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        super().setUp()
        self.init('test_project_1')

    #############################################
    #   GRAPHML EXPORT
    #################################

    def test_export_diagram_to_graphml(self):
        # GIVEN
        self.session.sgnFocusDiagram.emit(self.project.diagram('diagram'))
        # WHEN
        worker = GraphMLDiagramExporter(self.session.mdi.activeDiagram(), self.session)
        worker.run('@tests/.tests/diagram.graphml')
        # THEN
        self.assertFileExists('@tests/.tests/diagram.graphml')

    #############################################
    #   PDF EXPORT
    #################################

    @patch('eddy.core.exporters.pdf.openPath')
    def test_export_diagram_to_pdf(self, _):
        # GIVEN
        self.session.sgnFocusDiagram.emit(self.project.diagram('diagram'))
        # WHEN
        worker = PdfDiagramExporter(self.session.mdi.activeDiagram(), self.session)
        worker.run(expandPath('@tests/.tests/diagram.pdf'))
        # THEN
        self.assertFileExists('@tests/.tests/diagram.pdf')

    #############################################
    #   OWL EXPORT
    #################################

    def test_export_project_to_owl_without_normalization(self):
        # WHEN
        worker = OWLOntologyExporterWorker(self.project, '@tests/.tests/test_project_1.owl',
           axioms={x for x in OWLAxiom}, normalize=False, syntax=OWLSyntax.Functional)
        worker.run()
        # THEN
        self.assertFileExists('@tests/.tests/test_project_1.owl')
        # WHEN
        content = list(filter(None, fread('@tests/.tests/test_project_1.owl').split('\n')))
        # THEN
        self.assertIn('Prefix(:=<http://www.dis.uniroma1.it/~graphol/test_project#>)', content)
        self.assertIn('Prefix(owl:=<http://www.w3.org/2002/07/owl#>)', content)
        self.assertIn('Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)', content)
        self.assertIn('Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)', content)
        self.assertIn('Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)', content)
        self.assertIn('Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)', content)
        self.assertIn('Prefix(test:=<http://www.dis.uniroma1.it/~graphol/test_project#>)', content)
        self.assertIn('Ontology(<http://www.dis.uniroma1.it/~graphol/test_project>', content)
        self.assertIn('Declaration(Class(test:Vegetable))', content)
        self.assertIn('Declaration(Class(test:Person))', content)
        self.assertIn('Declaration(Class(test:Male))', content)
        self.assertIn('Declaration(Class(test:Female))', content)
        self.assertIn('Declaration(Class(test:Mother))', content)
        self.assertIn('Declaration(Class(test:Father))', content)
        self.assertIn('Declaration(Class(test:Underage))', content)
        self.assertIn('Declaration(Class(test:Adult))', content)
        self.assertIn('Declaration(Class(test:Vehicle))', content)
        self.assertIn('Declaration(Class(test:Less_than_50_cc))', content)
        self.assertIn('Declaration(Class(test:Over_50_cc))', content)
        self.assertIn('Declaration(NamedIndividual(test:Bob))', content)
        self.assertIn('Declaration(NamedIndividual(test:Alice))', content)
        self.assertIn('Declaration(NamedIndividual(test:Trudy))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasAncestor))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasParent))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasFather))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasMother))', content)
        self.assertIn('Declaration(ObjectProperty(test:isAncestorOf))', content)
        self.assertIn('Declaration(ObjectProperty(test:drives))', content)
        self.assertIn('Declaration(DataProperty(test:name))', content)
        self.assertIn('Declaration(Datatype(xsd:string))', content)
        self.assertIn('Declaration(AnnotationProperty(<rdfs:comment>))', content)
        self.assertIn('AnnotationAssertion(<rdfs:comment> test:Person "A human being"^^xsd:string)', content)
        self.assertIn('SubClassOf(test:Person ObjectSomeValuesFrom(test:hasAncestor owl:Thing))', content)
        self.assertIn('SubClassOf(test:Father test:Male)', content)
        self.assertIn('SubClassOf(test:Mother test:Female)', content)
        self.assertIn('SubClassOf(test:Underage ObjectAllValuesFrom(test:drives test:Less_than_50_cc))', content)
        self.assertIn('SubObjectPropertyOf(test:hasParent test:hasAncestor)', content)
        self.assertIn('SubObjectPropertyOf(test:hasFather test:hasParent)', content)
        self.assertIn('SubObjectPropertyOf(test:hasMother test:hasParent)', content)
        self.assertIn('FunctionalObjectProperty(test:hasFather)', content)
        self.assertIn('FunctionalObjectProperty(test:hasMother)', content)
        self.assertIn('DataPropertyRange(test:name xsd:string)', content)
        self.assertIn('DataPropertyDomain(test:name test:Person)', content)
        self.assertIn('InverseObjectProperties(test:hasAncestor test:isAncestorOf)', content)
        self.assertIn('ObjectPropertyAssertion(test:isAncestorOf test:Bob test:Alice)', content)
        self.assertIn('ObjectPropertyRange(test:hasAncestor test:Person)', content)
        self.assertIn('ObjectPropertyRange(test:hasFather test:Father)', content)
        self.assertIn('ObjectPropertyRange(test:hasMother test:Mother)', content)
        self.assertIn('ObjectPropertyRange(test:drives test:Vehicle)', content)
        self.assertIn('NegativeObjectPropertyAssertion(test:isAncestorOf test:Bob test:Trudy)', content)
        self.assertIn(')', content)
        # AND
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasAncestor) owl:Thing) test:Person)', content)
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasMother) owl:Thing) test:Mother)', content)
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasFather) owl:Thing) test:Father)', content)
        # AND
        self.assertAnyIn(['EquivalentClasses(test:Person ObjectUnionOf(test:Underage test:Adult))',
                          'EquivalentClasses(test:Person ObjectUnionOf(test:Adult test:Underage))',
                          'EquivalentClasses(ObjectUnionOf(test:Underage test:Adult) test:Person)',
                          'EquivalentClasses(ObjectUnionOf(test:Adult test:Person) test:Person)'], content)
        self.assertAnyIn(['EquivalentClasses(test:Person DataSomeValuesFrom(test:name rdfs:Literal))',
                          'EquivalentClasses(DataSomeValuesFrom(test:name rdfs:Literal) test:Person)'], content)
        self.assertAnyIn(['EquivalentClasses(test:Person ObjectUnionOf(test:Female test:Male))',
                          'EquivalentClasses(test:Person ObjectUnionOf(test:Male test:Female))',
                          'EquivalentClasses(ObjectUnionOf(test:Female test:Male) test:Person)',
                          'EquivalentClasses(ObjectUnionOf(test:Male test:Female) test:Person)'], content)
        self.assertAnyIn(['EquivalentClasses(test:Vehicle ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc))',
                          'EquivalentClasses(test:Vehicle ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc))',
                          'EquivalentClasses(ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc) test:Vehicle)',
                          'EquivalentClasses(ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc) test:Vehicle)'], content)
        self.assertAnyIn(['EquivalentClasses(test:Person ObjectAllValuesFrom(test:drives owl:Thing))',
                          'EquivalentClasses(ObjectAllValuesFrom(test:drives owl:Thing) test:Person)',], content)
        self.assertAnyIn(['DisjointClasses(test:Female test:Male)',
                          'DisjointClasses(test:Male test:Female)'], content)
        self.assertAnyIn(['DisjointClasses(test:Person test:Vegetable)',
                          'DisjointClasses(test:Vegetable test:Person)'], content)
        self.assertAnyIn(['DisjointClasses(test:Underage test:Adult)',
                          'DisjointClasses(test:Adult test:Underage)'], content)
        self.assertAnyIn(['DisjointClasses(test:Less_than_50_cc test:Over_50_cc)',
                          'DisjointClasses(test:Over_50_cc test:Less_than_50_cc)'], content)
        # AND
        self.assertLen(61, content)

    def test_export_project_to_owl_with_normalization(self):
        # WHEN
        worker = OWLOntologyExporterWorker(self.project, '@tests/.tests/test_project_1.owl',
           axioms={x for x in OWLAxiom}, normalize=True, syntax=OWLSyntax.Functional)
        worker.run()
        # THEN
        self.assertFileExists('@tests/.tests/test_project_1.owl')
        # WHEN
        content = list(filter(None, fread('@tests/.tests/test_project_1.owl').split('\n')))
        # THEN
        self.assertIn('Prefix(:=<http://www.dis.uniroma1.it/~graphol/test_project#>)', content)
        self.assertIn('Prefix(owl:=<http://www.w3.org/2002/07/owl#>)', content)
        self.assertIn('Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)', content)
        self.assertIn('Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)', content)
        self.assertIn('Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)', content)
        self.assertIn('Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)', content)
        self.assertIn('Prefix(test:=<http://www.dis.uniroma1.it/~graphol/test_project#>)', content)
        self.assertIn('Ontology(<http://www.dis.uniroma1.it/~graphol/test_project>', content)
        self.assertIn('Declaration(Class(test:Vegetable))', content)
        self.assertIn('Declaration(Class(test:Person))', content)
        self.assertIn('Declaration(Class(test:Male))', content)
        self.assertIn('Declaration(Class(test:Female))', content)
        self.assertIn('Declaration(Class(test:Mother))', content)
        self.assertIn('Declaration(Class(test:Father))', content)
        self.assertIn('Declaration(Class(test:Underage))', content)
        self.assertIn('Declaration(Class(test:Adult))', content)
        self.assertIn('Declaration(Class(test:Vehicle))', content)
        self.assertIn('Declaration(Class(test:Less_than_50_cc))', content)
        self.assertIn('Declaration(Class(test:Over_50_cc))', content)
        self.assertIn('Declaration(NamedIndividual(test:Bob))', content)
        self.assertIn('Declaration(NamedIndividual(test:Alice))', content)
        self.assertIn('Declaration(NamedIndividual(test:Trudy))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasAncestor))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasParent))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasFather))', content)
        self.assertIn('Declaration(ObjectProperty(test:hasMother))', content)
        self.assertIn('Declaration(ObjectProperty(test:isAncestorOf))', content)
        self.assertIn('Declaration(ObjectProperty(test:drives))', content)
        self.assertIn('Declaration(DataProperty(test:name))', content)
        self.assertIn('Declaration(Datatype(xsd:string))', content)
        self.assertIn('Declaration(AnnotationProperty(<rdfs:comment>))', content)
        self.assertIn('AnnotationAssertion(<rdfs:comment> test:Person "A human being"^^xsd:string)', content)
        self.assertIn('SubClassOf(test:Person ObjectSomeValuesFrom(test:hasAncestor owl:Thing))', content)
        self.assertIn('SubClassOf(test:Father test:Male)', content)
        self.assertIn('SubClassOf(test:Mother test:Female)', content)
        self.assertIn('SubClassOf(test:Person DataSomeValuesFrom(test:name rdfs:Literal))', content)
        self.assertIn('SubClassOf(test:Female test:Person)', content)
        self.assertIn('SubClassOf(test:Male test:Person)', content)
        self.assertIn('SubClassOf(test:Underage test:Person)', content)
        self.assertIn('SubClassOf(test:Adult test:Person)', content)
        self.assertIn('SubClassOf(test:Less_than_50_cc test:Vehicle)', content)
        self.assertIn('SubClassOf(test:Over_50_cc test:Vehicle)', content)
        self.assertIn('SubClassOf(test:Underage ObjectAllValuesFrom(test:drives test:Less_than_50_cc))', content)
        self.assertIn('SubClassOf(test:Person ObjectAllValuesFrom(test:drives owl:Thing))', content)
        self.assertIn('SubClassOf(ObjectAllValuesFrom(test:drives owl:Thing) test:Person)', content)
        self.assertIn('SubObjectPropertyOf(test:hasParent test:hasAncestor)', content)
        self.assertIn('SubObjectPropertyOf(test:hasFather test:hasParent)', content)
        self.assertIn('SubObjectPropertyOf(test:hasMother test:hasParent)', content)
        self.assertIn('FunctionalObjectProperty(test:hasFather)', content)
        self.assertIn('FunctionalObjectProperty(test:hasMother)', content)
        self.assertIn('DataPropertyRange(test:name xsd:string)', content)
        self.assertIn('DataPropertyDomain(test:name test:Person)', content)
        self.assertIn('InverseObjectProperties(test:hasAncestor test:isAncestorOf)', content)
        self.assertIn('ObjectPropertyAssertion(test:isAncestorOf test:Bob test:Alice)', content)
        self.assertIn('ObjectPropertyRange(test:hasAncestor test:Person)', content)
        self.assertIn('ObjectPropertyRange(test:hasFather test:Father)', content)
        self.assertIn('ObjectPropertyRange(test:hasMother test:Mother)', content)
        self.assertIn('ObjectPropertyRange(test:drives test:Vehicle)', content)
        self.assertIn('NegativeObjectPropertyAssertion(test:isAncestorOf test:Bob test:Trudy)', content)
        self.assertIn(')', content)
        # AND
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasAncestor) owl:Thing) test:Person)', content)
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasMother) owl:Thing) test:Mother)', content)
        self.assertNotIn('SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasFather) owl:Thing) test:Father)', content)
        self.assertNotIn('SubClassOf(DataSomeValuesFrom(test:name rdfs:Literal) test:Person)', content)
        # AND
        self.assertAnyIn(['SubClassOf(test:Person ObjectUnionOf(test:Underage test:Adult))',
                          'SubClassOf(test:Person ObjectUnionOf(test:Adult test:Underage))'], content)
        self.assertAnyIn(['SubClassOf(test:Person ObjectUnionOf(test:Female test:Male))',
                          'SubClassOf(ObjectUnionOf(test:Female test:Male) test:Person)'], content)
        self.assertAnyIn(['SubClassOf(test:Vehicle ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc))',
                          'SubClassOf(test:Vehicle ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc))'], content)
        self.assertAnyIn(['DisjointClasses(test:Female test:Male)',
                          'DisjointClasses(test:Male test:Female)'], content)
        self.assertAnyIn(['DisjointClasses(test:Person test:Vegetable)',
                          'DisjointClasses(test:Vegetable test:Person)'], content)
        self.assertAnyIn(['DisjointClasses(test:Underage test:Adult)',
                          'DisjointClasses(test:Adult test:Underage)'], content)
        self.assertAnyIn(['DisjointClasses(test:Less_than_50_cc test:Over_50_cc)',
                          'DisjointClasses(test:Over_50_cc test:Less_than_50_cc)'], content)
        # AND
        self.assertLen(68, content)