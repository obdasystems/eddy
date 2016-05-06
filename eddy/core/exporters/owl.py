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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import jnius

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject

from eddy.core.datatypes.graphol import Item, Identity, Special, Restriction
from eddy.core.datatypes.owl import OWLSyntax
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.functions.fsystem import fwrite
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.owl import OWLShortIRI, OWLAnnotationText
from eddy.core.functions.signals import emit

from eddy.lang import gettext as _


class OWLExporter(QObject):
    """
    This class can be used to export Graphol projects into OWL ontologies.
    Due to the deep usage of Java OWL api the worker method of this class should be run in a separate thread.
    It has not been implemented as a QThread so it's possible to change Thread affinity at runtime.
    For more information see: http://doc.qt.io/qt-5/qobject.html#moveToThread
    """
    sgnCompleted = pyqtSignal()
    sgnErrored = pyqtSignal(Exception)
    sgnFinished = pyqtSignal()
    sgnProgress = pyqtSignal(int, int)
    sgnStarted = pyqtSignal()

    def __init__(self, project, path, syntax):
        """
        Initialize the OWL translator: this class does not specify any parent otherwise
        we won't be able to move the execution of the worker method to a different thread.
        :type project: Project
        :type path: str
        :type syntax: OWLSyntax
        """
        super().__init__()

        self.path = path
        self.syntax = syntax
        self.project = project
        self.ontoIRI = self.project.iri
        self.ontoPrefix = self.project.prefix

        self.axioms = set()
        self.conv = dict()
        self.factory = None
        self.num = 0
        self.man = None
        self.max = len(self.project.nodes()) + len(self.project.edges())
        self.ontology = None
        self.pm = None

        self.AddAxiom = jnius.autoclass('org.semanticweb.owlapi.model.AddAxiom')
        self.DefaultPrefixManager = jnius.autoclass('org.semanticweb.owlapi.util.DefaultPrefixManager')
        self.FunctionalSyntaxDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.FunctionalSyntaxDocumentFormat')
        self.HashSet = jnius.autoclass('java.util.HashSet')
        self.IRI = jnius.autoclass('org.semanticweb.owlapi.model.IRI')
        self.LinkedList = jnius.autoclass('java.util.LinkedList')
        self.List = jnius.autoclass('java.util.List')
        self.ManchesterSyntaxDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.ManchesterSyntaxDocumentFormat')
        self.OWLAnnotationValue = jnius.autoclass('org.semanticweb.owlapi.model.OWLAnnotationValue')
        self.OWLFacet = jnius.autoclass('org.semanticweb.owlapi.vocab.OWLFacet')
        self.OWL2Datatype = jnius.autoclass('org.semanticweb.owlapi.vocab.OWL2Datatype')
        self.OWLManager = jnius.autoclass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.OWLOntologyDocumentTarget = jnius.autoclass('org.semanticweb.owlapi.io.OWLOntologyDocumentTarget')
        self.RDFXMLDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.RDFXMLDocumentFormat')
        self.PrefixManager = jnius.autoclass('org.semanticweb.owlapi.model.PrefixManager')
        self.Set = jnius.autoclass('java.util.Set')
        self.StringDocumentTarget = jnius.autoclass('org.semanticweb.owlapi.io.StringDocumentTarget')
        self.TurtleDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.TurtleDocumentFormat')

    #############################################
    #   NODES PRE-PROCESSING
    #################################

    def buildAttribute(self, node):
        """
        Build and returns a OWL attribute using the given graphol node.
        :type node: AttributeNode
        :rtype: OWLDataProperty
        """
        if node not in self.conv:
            if node.special is Special.Top:
                self.conv[node] = self.factory.getOWLTopDataProperty()
            elif node.special is Special.Bottom:
                self.conv[node] = self.factory.getOWLBottomDataProperty()
            else:
                self.conv[node] = self.factory.getOWLDataProperty(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildComplement(self, node):
        """
        Build and returns a OWL complement using the given graphol node.
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain, Identity.Role}

            incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            if not incoming:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))
            if len(incoming) > 1:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_TOO_MANY_OPERANDS'))

            operand = first(incoming)

            if operand.identity is Identity.Concept:

                if operand.type() is Item.ConceptNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildConcept(operand))
                elif operand.type() is Item.ComplementNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildUnion(operand))
                elif operand.type() is Item.DomainRestrictionNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildDomainRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

            elif operand.identity is Identity.ValueDomain:

                if operand.type() is Item.ValueDomainNode:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildValueDomain(operand))
                elif operand.type() is Item.ComplementNode:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildUnion(operand))
                elif operand.type() is Item.DatatypeRestrictionNode:
                    self.conv[node] = self.factory.getOWLDataComplementOf(self.buildDatatypeRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    self.conv[node] = self.factory.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

            elif operand.identity is Identity.Role:

                # If we have a Role in input to this Complement node, we store
                # the OWL representation of the Role (or the inverse of it) so
                # that we can generate the role disjoint axiom later by calling
                # self.factory.getOWLDisjointObjectPropertiesAxiom.
                if operand.type() is Item.RoleNode:
                    self.conv[node] = self.buildRole(operand)
                elif operand.type() is Item.RoleInverseNode:
                    self.conv[node] = self.buildRoleInverse(operand)
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

        return self.conv[node]

    def buildConcept(self, node):
        """
        Build and returns a OWL concept using the given graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        if node not in self.conv:
            if node.special is Special.Top:
                self.conv[node] = self.factory.getOWLThing()
            elif node.special is Special.Bottom:
                self.conv[node] = self.factory.getOWLNothing()
            else:
                self.conv[node] = self.factory.getOWLClass(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildDatatypeRestriction(self, node):
        """
        Build and returns a OWL datatype restriction using the given graphol node.
        :type node: DatatypeRestrictionNode
        :rtype: OWLDatatypeRestriction
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.ValueDomainNode
            f3 = lambda x: x.type() is Item.FacetNode

            #############################################
            # BUILD DATATYPE
            #################################

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_VALUE_DOMAIN'))

            datatypeEx = self.buildValueDomain(operand)

            #############################################
            # BUILD FACETS
            #################################

            incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)
            if not incoming:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_FACET'))

            collection = self.HashSet()
            for i in incoming:
                collection.add(self.buildFacet(i))

            #############################################
            # BUILD DATATYPE RESTRICTION
            #################################

            collection = jnius.cast(self.Set, collection)
            self.conv[node] = self.factory.getOWLDatatypeRestriction(datatypeEx, collection)

        return self.conv[node]

    def buildDomainRestriction(self, node):
        """
        Build and returns a OWL domain restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            f3 = lambda x: x.identity is Identity.ValueDomain
            f4 = lambda x: x.identity is Identity.Concept

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))

            if operand.identity is Identity.Attribute:

                #############################################
                # BUILD OPERAND
                #################################

                dataPropEx = self.buildAttribute(operand)

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                if not filler:
                    dataRangeEx = self.factory.getTopDatatype()
                elif filler.type() is Item.ValueDomainNode:
                    dataRangeEx = self.buildValueDomain(filler)
                elif filler.type() is Item.ComplementNode:
                    dataRangeEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    dataRangeEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    dataRangeEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    dataRangeEx = self.buildUnion(filler)
                elif filler.type() is Item.DatatypeRestrictionNode:
                    dataRangeEx = self.buildDatatypeRestriction(filler)
                elif filler.type() is Item.RangeRestrictionNode:
                    dataRangeEx = self.buildRangeRestriction(filler)
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', filler))

                if node.restriction is Restriction.Exists:
                    self.conv[node] = self.factory.getOWLDataSomeValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.factory.getOWLDataAllValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.factory.getOWLDataMinCardinality(min_c, dataPropEx, dataRangeEx))
                    if max_c is not None:
                        cardinalities.add(self.factory.getOWLDataMinCardinality(max_c, dataPropEx, dataRangeEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_CARDINALITY'))
                    elif cardinalities.size() >= 1:
                        cardinalities = jnius.cast(self.Set, cardinalities)
                        self.conv[node] = self.factory.getOWLDataIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_RESTRICTION'))

            elif operand.identity is Identity.Role:

                #############################################
                # BUILD OPERAND
                #################################

                if operand.type() is Item.RoleNode:
                    objectPropertyEx = self.buildRole(operand)
                elif operand.type() is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(operand)
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f4))
                if not filler:
                    classEx = self.factory.getOWLThing()
                elif filler.type() is Item.ConceptNode:
                    classEx = self.buildConcept(filler)
                elif filler.type() is Item.ComplementNode:
                    classEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    classEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    classEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(filler)
                elif filler.type() is Item.DomainRestrictionNode:
                    classEx = self.buildDomainRestriction(filler)
                elif filler.type() is Item.RangeRestrictionNode:
                    classEx = self.buildRangeRestriction(filler)
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', filler))

                if node.restriction is Restriction.Self:
                    self.conv[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.conv[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.factory.getOWLObjectMinCardinality(min_c, objectPropertyEx, classEx))
                    if max_c is not None:
                        cardinalities.add(self.factory.getOWLObjectMaxCardinality(max_c, objectPropertyEx, classEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_CARDINALITY'))
                    elif cardinalities.size() >= 1:
                        cardinalities = jnius.cast(self.Set, cardinalities)
                        self.conv[node] = self.factory.getOWLObjectIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()

        return self.conv[node]

    def buildEnumeration(self, node):
        """
        Build and returns a OWL enumeration using the given graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node not in self.conv:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.IndividualNode
            individuals = self.HashSet()
            for i in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                individuals.add(self.buildIndividual(i))
            if individuals.isEmpty():
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))
            individuals = jnius.cast(self.Set, individuals)
            self.conv[node] = self.factory.getOWLObjectOneOf(individuals)
        return self.conv[node]

    def buildFacet(self, node):
        """
        Build and returns a OWL facet restriction using the given graphol node.
        :type node: FacetNode
        :rtype: OWLFacetRestriction
        """
        if node not in self.conv:
            datatype = node.datatype
            if not datatype:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_DISCONNECTED_FACET'))
            literalEx = self.factory.getOWLLiteral(node.value, self.OWL2Datatype.valueOf(datatype.owlapi))
            facetEx = self.OWLFacet.valueOf(node.facet.owlapi)
            self.conv[node] = self.factory.getOWLFacetRestriction(facetEx, literalEx)
        return self.conv[node]

    def buildIndividual(self, node):
        """
        Build and returns a OWL individual using the given graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        if node not in self.conv:
            if node.identity is Identity.Instance:
                self.conv[node] = self.factory.getOWLNamedIndividual(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
            elif node.identity is Identity.Value:
                self.conv[node] = self.factory.getOWLLiteral(node.value, self.OWL2Datatype.valueOf(node.datatype.owlapi))
        return self.conv[node]

    def buildIntersection(self, node):
        """
        Build and returns a OWL intersection using the given graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf | OWLDataIntersectionOf
        """
        if node not in self.conv:

            collection = self.HashSet()

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain}

            for operand in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if operand.type() is Item.ConceptNode:
                    collection.add(self.buildConcept(operand))
                elif operand.type() is Item.ValueDomainNode:
                    collection.add(self.buildValueDomain(operand))
                elif operand.type() is Item.ComplementNode:
                    collection.add(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    collection.add(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    collection.add(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.add(self.buildUnion(operand))
                elif operand.type() is Item.DomainRestrictionNode:
                    collection.add(self.buildDomainRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    collection.add(self.buildRangeRestriction(operand))
                elif operand.type() is Item.DatatypeRestrictionNode:
                    collection.add(self.buildDatatypeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

            if collection.isEmpty():
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))

            collection = jnius.cast(self.Set, collection)

            if node.identity is Identity.Concept:
                self.conv[node] = self.factory.getOWLObjectIntersectionOf(collection)
            elif node.identity is Identity.ValueDomain:
                self.conv[node] = self.factory.getOWLDataIntersectionOf(collection)

        return self.conv[node]

    def buildPropertyAssertion(self, node):
        """
        Build and returns a collection of individuals that can be used to build property assertions.
        :type node: PropertyAssertionNode
        :rtype: tuple
        """
        if node not in self.conv:

            if len(node.inputs) < 2:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))
            elif len(node.inputs) > 2:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_TOO_MANY_OPERANDS'))

            collection = []
            for n in [node.diagram.edge(i).other(node) for i in node.inputs]:
                if n.type() is not Item.IndividualNode:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', n))
                collection.append(self.buildIndividual(n))

            self.conv[node] = collection

        return self.conv[node]

    def buildRangeRestriction(self, node):
        """
        Build and returns a OWL range restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: T <= OWLClassExpression | OWLDataProperty
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            f3 = lambda x: x.identity is Identity.Concept

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))

            if operand.identity is Identity.Attribute:

                #############################################
                # BUILD OPERAND
                #################################

                # In this case we just create a mapping using
                # OWLDataPropertyExpression which is needed later
                # when we create the DataPropertyRange using this
                # very node and a Value-Domain expression.
                self.conv[node] = self.buildAttribute(operand)

            elif operand.identity is Identity.Role:

                #############################################
                # BUILD OPERAND
                #################################

                if operand.type() is Item.RoleNode:
                    objectPropertyEx = self.buildRole(operand).getInverseProperty()
                elif operand.type() is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(operand).getInverseProperty()
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', operand))

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                if not filler:
                    classEx = self.factory.getOWLThing()
                elif filler.type() is Item.ConceptNode:
                    classEx = self.buildConcept(filler)
                elif filler.type() is Item.ComplementNode:
                    classEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    classEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    classEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(filler)
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', filler))

                if node.restriction is Restriction.Self:
                    self.conv[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.conv[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.factory.getOWLObjectMinCardinality(min_c, objectPropertyEx, classEx))
                    if max_c is not None:
                        cardinalities.add(self.factory.getOWLObjectMaxCardinality(max_c, objectPropertyEx, classEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_CARDINALITY'))
                    if cardinalities.size() >= 1:
                        cardinalities = jnius.cast(self.Set, cardinalities)
                        self.conv[node] = self.factory.getOWLObjectIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()

        return self.conv[node]

    def buildRole(self, node):
        """
        Build and returns a OWL role using the given graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node not in self.conv:
            if node.special is Special.Top:
                self.conv[node] = self.factory.getOWLTopObjectProperty()
            elif node.special is Special.Bottom:
                self.conv[node] = self.factory.getOWLBottomObjectProperty()
            else:
                self.conv[node] = self.factory.getOWLObjectProperty(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildRoleChain(self, node):
        """
        Constructs and returns a chain of OWLObjectExpression (OPE => Role & RoleInverse).
        :type node: RoleChainNode
        :rtype: list
        """
        if node not in self.conv:
            if not node.inputs:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))
            collection = self.LinkedList()
            for n in [node.diagram.edge(i).other(node) for i in node.inputs]:
                if n.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', n))
                elif n.type() is Item.RoleNode:
                    collection.add(self.buildRole(n))
                elif n.type() is Item.RoleInverseNode:
                    collection.add(self.buildRoleInverse(n))
            collection = jnius.cast(self.List, collection)
            self.conv[node] = collection
        return self.conv[node]

    def buildRoleInverse(self, node):
        """
        Build and returns a OWL role inverse using the given graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        if node not in self.conv:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.RoleNode
            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))
            self.conv[node] = self.buildRole(operand).getInverseProperty()
        return self.conv[node]

    def buildUnion(self, node):
        """
        Build and returns a OWL union using the given graphol node.
        :type node: UnionNode
        :rtype: T <= OWLObjectUnionOf | OWLDataUnionOf
        """
        if node not in self.conv:

            collection = self.HashSet()

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if item.type() is Item.ConceptNode:
                    collection.add(self.buildConcept(item))
                elif item.type() is Item.ValueDomainNode:
                    collection.add(self.buildValueDomain(item))
                elif item.type() is Item.ComplementNode:
                    collection.add(self.buildComplement(item))
                elif item.type() is Item.EnumerationNode:
                    collection.add(self.buildEnumeration(item))
                elif item.type() is Item.IntersectionNode:
                    collection.add(self.buildIntersection(item))
                elif item.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.add(self.buildUnion(item))
                elif item.type() is Item.DomainRestrictionNode:
                    collection.add(self.buildDomainRestriction(item))
                elif item.type() is Item.RangeRestrictionNode:
                    collection.add(self.buildRangeRestriction(item))
                elif item.type() is Item.DatatypeRestrictionNode:
                    collection.add(self.buildDatatypeRestriction(item))
                else:
                    raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND', item))

            if not collection.size():
                raise MalformedDiagramError(node, _('PROJECT_EXPORT_OWL_MISSING_OPERAND'))

            collection = jnius.cast(self.Set, collection)

            if node.identity is Identity.Concept:
                self.conv[node] = self.factory.getOWLObjectUnionOf(collection)
            elif node.identity is Identity.ValueDomain:
                self.conv[node] = self.factory.getOWLDataUnionOf(collection)

        return self.conv[node]

    def buildValueDomain(self, node):
        """
        Build and returns a OWL datatype using the given graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        if node not in self.conv:
            self.conv[node] = self.factory.getOWLDatatype(self.OWL2Datatype.valueOf(node.datatype.owlapi).getIRI())
        return self.conv[node]

    #############################################
    #   AXIOMS GENERATION
    #################################

    def axiomAnnotation(self, node):
        """
        Generate a OWL annotation axiom.
        :type node: AbstractNode
        """
        meta = self.project.meta(node.type(), node.text())
        if meta and not isEmpty(meta.description):
            prop = self.factory.getOWLAnnotationProperty(self.IRI.create("Description"))
            value = self.factory.getOWLLiteral(OWLAnnotationText(meta.description))
            value = jnius.cast(self.OWLAnnotationValue, value)
            annotation = self.factory.getOWLAnnotation(prop, value)
            self.axioms.add(self.factory.getOWLAnnotationAssertionAxiom(self.conv[node].getIRI(), annotation))

    def axiomDataProperty(self, node):
        """
        Generate OWL Data Property specific axioms.
        :type node: AttributeNode
        """
        meta = self.project.meta(node.type(), node.text())
        if meta:
            if meta.functional:
                self.axioms.add(self.factory.getOWLFunctionalDataPropertyAxiom(self.conv[node]))

    def axiomClassAssertion(self, edge):
        """
        Generate a OWL ClassAssertion axiom.
        :type edge: InstanceOf
        """
        self.axioms.add(self.factory.getOWLClassAssertionAxiom(self.conv[edge.target], self.conv[edge.source]))

    def axiomDataPropertyAssertion(self, edge):
        """
        Generate a OWL DataPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        operand1 = self.conv[edge.source][0]
        operand2 = self.conv[edge.source][1]
        self.axioms.add(self.factory.getOWLDataPropertyAssertionAxiom(self.conv[edge.target], operand1, operand2))

    def axiomDataPropertyRange(self, edge):
        """
        Generate a OWL DataPropertyRange axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLDataPropertyRangeAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomDeclaration(self, node):
        """
        Generate a OWL Declaration axiom.
        :type node: AbstractNode
        """
        self.axioms.add(self.factory.getOWLDeclarationAxiom(self.conv[node]))

    def axiomDisjointClasses(self, node):
        """
        Generate a OWL DisjointClasses axiom.
        :type node: DisjointUnionNode
        """
        collection = self.HashSet()
        for j in node.incomingNodes(lambda x: x.type() is Item.InputEdge):
            collection.add(self.conv[j])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointClassesAxiom(collection))

    def axiomDisjointDataProperties(self, edge):
        """
        Generate a OWL DisjointDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointDataPropertiesAxiom(collection))

    def axiomDisjointObjectProperties(self, edge):
        """
        Generate a OWL DisjointObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointObjectPropertiesAxiom(collection))

    def axiomEquivalentClasses(self, edge):
        """
        Generate a OWL EquivalentClasses axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentClassesAxiom(collection))

    def axiomEquivalentDataProperties(self, edge):
        """
        Generate a OWL EquivalentDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentDataPropertiesAxiom(collection))

    def axiomEquivalentObjectProperties(self, edge):
        """
        Generate a OWL EquivalentObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentObjectPropertiesAxiom(collection))

    def axiomObjectProperty(self, node):
        """
        Generate OWL ObjectProperty specific axioms.
        :type node: RoleNode
        """
        meta = self.project.meta(node.type(), node.text())
        if meta:
            if meta.functional:
                self.axioms.add(self.factory.getOWLFunctionalObjectPropertyAxiom(self.conv[node]))
            if meta.inverseFunctional:
                self.axioms.add(self.factory.getOWLInverseFunctionalObjectPropertyAxiom(self.conv[node]))
            if meta.asymmetric:
                self.axioms.add(self.factory.getOWLAsymmetricObjectPropertyAxiom(self.conv[node]))
            if meta.irreflexive:
                self.axioms.add(self.factory.getOWLIrreflexiveObjectPropertyAxiom(self.conv[node]))
            if meta.reflexive:
                self.axioms.add(self.factory.getOWLReflexiveObjectPropertyAxiom(self.conv[node]))
            if meta.symmetric:
                self.axioms.add(self.factory.getOWLSymmetricObjectPropertyAxiom(self.conv[node]))
            if meta.transitive:
                self.axioms.add(self.factory.getOWLTransitiveObjectPropertyAxiom(self.conv[node]))

    def axiomObjectPropertyAssertion(self, edge):
        """
        Generate a OWL ObjectPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        operand1 = self.conv[edge.source][0]
        operand2 = self.conv[edge.source][1]
        self.axioms.add(self.factory.getOWLObjectPropertyAssertionAxiom(self.conv[edge.target], operand1, operand2))

    def axiomSubclassOf(self, edge):
        """
        Generate a OWL SubclassOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubClassOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubDataPropertyOfAxiom(self, edge):
        """
        Generate a OWL SubDataPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubDataPropertyOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubObjectPropertyOf(self, edge):
        """
        Generate a OWL SubObjectPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubObjectPropertyOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubPropertyChainOf(self, edge):
        """
        Generate a OWL SubPropertyChainOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubPropertyChainOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    #############################################
    #   ONTOLOGY GENERATION
    #################################

    def export(self):
        """
        Perform OWL ontology generation.
        """
        #############################################
        # INITIALIZE ONTOLOGY
        #################################

        self.man = self.OWLManager.createOWLOntologyManager()
        self.factory = self.man.getOWLDataFactory()
        self.ontology = self.man.createOntology(self.IRI.create(self.project.iri))
        self.pm = self.DefaultPrefixManager()
        self.pm.setPrefix(self.project.prefix, self.project.iri)

        jnius.cast(self.PrefixManager, self.pm)

        #############################################
        # NODES CONVERSION
        #################################

        for n in self.project.nodes():

            if n.type() is Item.ConceptNode:                            # CONCEPT
                self.buildConcept(n)
            elif n.type() is Item.AttributeNode:                        # ATTRIBUTE
                self.buildAttribute(n)
            elif n.type() is Item.RoleNode:                             # ROLE
                self.buildRole(n)
            elif n.type() is Item.ValueDomainNode:                      # VALUE-DOMAIN
                self.buildValueDomain(n)
            elif n.type() is Item.IndividualNode:                       # INDIVIDUAL
                self.buildIndividual(n)
            elif n.type() is Item.FacetNode:                            # FACET
                self.buildFacet(n)
            elif n.type() is Item.RoleInverseNode:                      # ROLE INVERSE
                self.buildRoleInverse(n)
            elif n.type() is Item.RoleChainNode:                        # ROLE CHAIN
                self.buildRoleChain(n)
            elif n.type() is Item.ComplementNode:                       # COMPLEMENT
                self.buildComplement(n)
            elif n.type() is Item.EnumerationNode:                      # ENUMERATION
                self.buildEnumeration(n)
            elif n.type() is Item.IntersectionNode:                     # INTERSECTION
                self.buildIntersection(n)
            elif n.type() in {Item.UnionNode, Item.DisjointUnionNode}:  # UNION / DISJOINT UNION
                self.buildUnion(n)
            elif n.type() is Item.DatatypeRestrictionNode:              # DATATYPE RESTRICTION
                self.buildDatatypeRestriction(n)
            elif n.type() is Item.PropertyAssertionNode:                # PROPERTY ASSERTION
                self.buildPropertyAssertion(n)
            elif n.type() is Item.DomainRestrictionNode:                # DOMAIN RESTRICTION
                self.buildDomainRestriction(n)
            elif n.type() is Item.RangeRestrictionNode:                 # RANGE RESTRICTION
                self.buildRangeRestriction(n)

            self.step(+1)

        #############################################
        # AXIOMS FROM NODES
        #################################

        for n in self.project.nodes():

            if n.type() in {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode}:
                self.axiomDeclaration(n)
                if n.type() is Item.AttributeNode:
                    self.axiomDataProperty(n)
                elif n.type() is Item.RoleNode:
                    self.axiomObjectProperty(n)
            elif n.type() is Item.DisjointUnionNode:
                self.axiomDisjointClasses(n)

            if n.isPredicate():
                self.axiomAnnotation(n)

        #############################################
        # AXIOMS FROM EDGES
        #################################

        for e in self.project.edges():

            if e.type() is Item.InclusionEdge:

                if not e.complete:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axiomSubclassOf(e)
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        if e.source.type() is Item.RoleChainNode:
                            self.axiomSubPropertyChainOf(e)
                        elif e.source.type() is Item.ComplementNode ^ e.target.type() is Item.ComplementNode:
                            self.axiomDisjointObjectProperties(e)
                        elif e.source.type() in {Item.RoleNode, Item.RoleInverseNode} and \
                                e.target.type() in {Item.RoleNode, Item.RoleInverseNode}:
                            self.axiomSubObjectPropertyOf(e)
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        if e.source.type() is Item.ComplementNode ^ e.target.type() is Item.ComplementNode:
                            self.axiomDisjointDataProperties(e)
                        else:
                            self.axiomSubDataPropertyOfAxiom(e)
                    elif e.source.type() is Item.RangeRestrictionNode and e.target.identity is Identity.ValueDomain:
                        self.axiomDataPropertyRange(e)
                    else:
                        raise MalformedDiagramError(e, _('PROJECT_EXPORT_OWL_MISMATCH_INCLUSION'))

                else:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axiomEquivalentClasses(e)
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        self.axiomEquivalentObjectProperties(e)
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        self.axiomEquivalentDataProperties(e)
                    else:
                        raise MalformedDiagramError(e, _('PROJECT_EXPORT_OWL_MISMATCH_EQUIVALENCE'))

            elif e.type() is Item.MembershipEdge:

                if e.source.identity is Identity.Instance and e.target.identity is Identity.Concept:
                    self.axiomClassAssertion(e)
                elif e.source.identity is Identity.RoleInstance:
                    self.axiomObjectPropertyAssertion(e)
                elif e.source.identity is Identity.AttributeInstance:
                    self.axiomDataPropertyAssertion(e)
                else:
                    raise MalformedDiagramError(e, _('PROJECT_EXPORT_OWL_MISMATCH_MEMBERSHIP'))

            self.step(+1)

        #############################################
        # APPLY GENERATED AXIOMS
        #################################

        for axiom in self.axioms:
            self.man.applyChange(self.AddAxiom(self.ontology, axiom))

        #############################################
        # SERIALIZE THE ONTOLOGY
        #################################

        if self.syntax is OWLSyntax.Functional:
            DocumentFormat = self.FunctionalSyntaxDocumentFormat
        elif self.syntax is OWLSyntax.Manchester:
            DocumentFormat = self.ManchesterSyntaxDocumentFormat
        elif self.syntax is OWLSyntax.RDF:
            DocumentFormat = self.RDFXMLDocumentFormat
        elif self.syntax is OWLSyntax.Turtle:
            DocumentFormat = self.TurtleDocumentFormat
        else:
            raise TypeError(_('PROJECT_EXPORT_OWL_UNSUPPORTED_SYNTAX', self.syntax))

        # COPY PREFIXES
        ontoFormat = DocumentFormat()
        ontoFormat.copyPrefixesFrom(self.pm)
        # CREARE TARGET STREAM
        stream = self.StringDocumentTarget()
        stream = jnius.cast(self.OWLOntologyDocumentTarget, stream)
        # SAVE THE ONTOLOGY TO DISK
        self.man.setOntologyFormat(self.ontology, ontoFormat)
        self.man.saveOntology(self.ontology, stream)
        stream = jnius.cast(self.StringDocumentTarget, stream)
        fwrite(stream.toString(), self.path)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def step(self, num, increase=0):
        """
        Increments the progress by the given step and emits the progress signal.
        :type num: int
        :type increase: int
        """
        self.max += increase
        self.num += num
        self.num = clamp(self.num, minval=0, maxval=self.max)
        emit(self.sgnProgress, self.num, self.max)

    #############################################
    #   MAIN WORKER
    #################################

    @pyqtSlot()
    def run(self):
        """
        Main worker: will trigger the execution of the export() method and catch any exception raised.
        """
        try:
            emit(self.sgnStarted)
            self.export()
        except Exception as e:
            emit(self.sgnErrored, e)
        else:
            emit(self.sgnCompleted)
        finally:
            jnius.detach()
            emit(self.sgnFinished)