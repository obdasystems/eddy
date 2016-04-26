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

from PyQt5.QtCore import pyqtSlot, pyqtSignal

from eddy.core.datatypes.graphol import Item, Identity, Special, Restriction
from eddy.core.datatypes.owl import OWLSyntax
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.exporters.common import AbstractExporter
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.owl import OWLText, OWLAnnotationText


class OWLExporter(AbstractExporter):
    """
    This class can be used to export Graphol diagrams into OWL ontologies.
    Due to the deep usage of Java OWL api the worker method of this class should be run in a separate thread.
    It has not been implemented as a QThread so it's possible to change Thread affinity at runtime.
    For more information see: http://doc.qt.io/qt-5/qobject.html#moveToThread
    """
    completed = pyqtSignal()  # emitted when the translation completes successfully
    errored = pyqtSignal(Exception)  # emitted when the translation cannot be completed
    finished = pyqtSignal()  # emitted upon worker termination
    progress = pyqtSignal(int, int)  # emitted meanwhile the translation is in progress
    started = pyqtSignal()  # emitted upon worker startup

    def __init__(self, scene, ontoIRI, ontoPrefix):
        """
        Initialize the OWL translator: this class does not specify any parent otherwise
        we won't be able to move the execution of the worker method to a different thread.
        :type scene: DiagramScene
        :type ontoIRI: str
        :type ontoPrefix: str
        """
        super().__init__(scene)

        self.ontoIRI = ontoIRI
        self.ontoPrefix = ontoPrefix

        self.count = 0
        self.total = len(scene.nodes()) + len(scene.edges())

        self.AddAxiom = jnius.autoclass('org.semanticweb.owlapi.model.AddAxiom')
        self.ByteArrayOutputStream = jnius.autoclass('java.io.ByteArrayOutputStream')
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
        self.OutputStream = jnius.autoclass('java.io.OutputStream')
        self.RDFXMLDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.RDFXMLDocumentFormat')
        self.Set = jnius.autoclass('java.util.Set')
        self.TurtleDocumentFormat = jnius.autoclass('org.semanticweb.owlapi.formats.TurtleDocumentFormat')

        self.axioms = set()
        self.converted = dict()
        self.man = self.OWLManager.createOWLOntologyManager()
        self.factory = self.man.getOWLDataFactory()
        self.ontology = None

    ####################################################################################################################
    #                                                                                                                  #
    #   NODES PRE-PROCESSING                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def buildAttribute(self, node):
        """
        Build and returns a OWL attribute using the given Graphol node.
        :type node: AttributeNode
        :rtype: OWLDataProperty
        """
        if node not in self.converted:
            if not node.special:
                self.converted[node] = self.factory.getOWLDataProperty(self.IRI.create(self.ontoIRI, OWLText(node.text())))
            elif node.special is Special.Top:
                self.converted[node] = self.factory.getOWLTopDataProperty()
            elif node.special is Special.Bottom:
                self.converted[node] = self.factory.getOWLBottomDataProperty()
        return self.converted[node]

    def buildComplement(self, node):
        """
        Build and returns a OWL complement using the given Graphol node
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node not in self.converted:

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain, Identity.Role}

            collection = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)

            if not collection:
                raise MalformedDiagramError(node, 'missing operand')

            if len(collection) > 1:
                raise MalformedDiagramError(node, 'too many operands')

            operand = collection[0]

            if operand.identity is Identity.Concept:

                if operand.item is Item.ConceptNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildConcept(operand))
                elif operand.item is Item.ComplementNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildComplement(operand))
                elif operand.item is Item.EnumerationNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildEnumeration(operand))
                elif operand.item is Item.IntersectionNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildIntersection(operand))
                elif operand.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildUnion(operand))
                elif operand.item is Item.DomainRestrictionNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildDomainRestriction(operand))
                elif operand.item is Item.RangeRestrictionNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(operand))

            elif operand.identity is Identity.ValueDomain:

                if operand.item is Item.ValueDomainNode:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildValueDomain(operand))
                elif operand.item is Item.ComplementNode:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildComplement(operand))
                elif operand.item is Item.EnumerationNode:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildEnumeration(operand))
                elif operand.item is Item.IntersectionNode:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildIntersection(operand))
                elif operand.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildUnion(operand))
                elif operand.item is Item.DatatypeRestrictionNode:
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildDatatypeRestriction(operand))
                elif operand.item is Item.RangeRestrictionNode:
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(operand))

            elif operand.identity is Identity.Role:

                # If we have a Role in input to this Complement node, create a mapping using
                # the OWL representation of the Role/Inv itself so that we can generate the role
                # disjoint axiom later by calling self.factory.getOWLDisjointObjectPropertiesAxiom
                if operand.item is Item.RoleNode:
                    self.converted[node] = self.buildRole(operand)
                elif operand.item is Item.RoleInverseNode:
                    self.converted[node] = self.buildRoleInverse(operand)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(operand))

        return self.converted[node]

    def buildConcept(self, node):
        """
        Build and returns a OWL concept using the given Graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        if node not in self.converted:
            if not node.special:
                self.converted[node] = self.factory.getOWLClass(self.IRI.create(self.ontoIRI, OWLText(node.text())))
            elif node.special is Special.Top:
                self.converted[node] = self.factory.getOWLThing()
            elif node.special is Special.Bottom:
                self.converted[node] = self.factory.getOWLNothing()
        return self.converted[node]

    def buildDatatypeRestriction(self, node):
        """
        Build and returns a OWL datatype restriction using the given Graphol node.
        :type node: DatatypeRestrictionNode
        :rtype: OWLDatatypeRestriction
        """
        if node not in self.converted:

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.item is Item.ValueDomainNode
            f3 = lambda x: x.item is Item.ValueRestrictionNode

            o1 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not o1:
                raise MalformedDiagramError(node, 'missing value domain node')

            datatypeEx = self.buildValueDomain(o1)

            collection = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)
            if not collection:
                raise MalformedDiagramError(node, 'missing value restriction node(s)')

            restrictions = self.HashSet()
            for i in collection:
                restrictions.doAddNode(self.buildValueRestriction(i))

            restrictions = jnius.cast(self.Set, restrictions)
            self.converted[node] = self.factory.getOWLDatatypeRestriction(datatypeEx, restrictions)

        return self.converted[node]

    def buildDomainRestriction(self, node):
        """
        Build and returns a OWL domain restriction using the given Graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        if node not in self.converted:

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))

            if not o1:
                raise MalformedDiagramError(node, 'missing operand(s)')

            if o1.identity is Identity.Attribute:

                f3 = lambda x: x.identity is Identity.ValueDomain
                o2 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))

                dataPropEx = self.buildAttribute(o1)

                if not o2:
                    dataRangeEx = self.factory.getTopDatatype()
                elif o2.item is Item.ValueDomainNode:
                    dataRangeEx = self.buildValueDomain(o2)
                elif o2.item is Item.ComplementNode:
                    dataRangeEx = self.buildComplement(o2)
                elif o2.item is Item.EnumerationNode:
                    dataRangeEx = self.buildEnumeration(o2)
                elif o2.item is Item.IntersectionNode:
                    dataRangeEx = self.buildIntersection(o2)
                elif o2.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    dataRangeEx = self.buildComplement(o2)
                elif o2.item is Item.DatatypeRestrictionNode:
                    dataRangeEx = self.buildDatatypeRestriction(o2)
                elif o2.item is Item.RangeRestrictionNode:
                    dataRangeEx = self.buildRangeRestriction(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.Self:
                    raise MalformedDiagramError(node, 'unsupported restriction')
                elif node.restriction is Restriction.Exists:
                    self.converted[node] = self.factory.getOWLDataSomeValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Forall:
                    self.converted[node] = self.factory.getOWLDataAllValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Cardinality:
                    collection = self.HashSet()
                    cmin = node.cardinality['min']
                    cmax = node.cardinality['max']
                    if cmin is not None:
                        collection.doAddNode(self.factory.getOWLDataMinCardinality(cmin, dataPropEx, dataRangeEx))
                    if cmax is not None:
                        collection.doAddNode(self.factory.getOWLDataMinCardinality(cmax, dataPropEx, dataRangeEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif collection.size() >= 1:
                        collection = jnius.cast(self.Set, collection)
                        self.converted[node] = self.factory.getOWLDataIntersectionOf(collection)
                    else:
                        self.converted[node] = collection.iterator().next()

            elif o1.identity is Identity.Role:

                if o1.item is Item.RoleNode:
                    objectPropertyEx = self.buildRole(o1)
                elif o1.item is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(o1)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o1))

                f3 = lambda x: x.identity is Identity.Concept
                o2 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))

                if not o2:
                    classEx = self.factory.getOWLThing()
                elif o2.item is Item.ConceptNode:
                    classEx = self.buildConcept(o2)
                elif o2.item is Item.ComplementNode:
                    classEx = self.buildComplement(o2)
                elif o2.item is Item.EnumerationNode:
                    classEx = self.buildEnumeration(o2)
                elif o2.item is Item.IntersectionNode:
                    classEx = self.buildIntersection(o2)
                elif o2.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(o2)
                elif o2.item is Item.DomainRestrictionNode:
                    classEx = self.buildDomainRestriction(o2)
                elif o2.item is Item.RangeRestrictionNode:
                    classEx = self.buildRangeRestriction(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.Self:
                    self.converted[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.converted[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.converted[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    collection = self.HashSet()
                    cmin = node.cardinality['min']
                    cmax = node.cardinality['max']
                    if node.cardinality['min'] is not None:
                        collection.doAddNode(self.factory.getOWLObjectMinCardinality(cmin, objectPropertyEx, classEx))
                    if node.cardinality['max'] is not None:
                        collection.doAddNode(self.factory.getOWLObjectMaxCardinality(cmax, objectPropertyEx, classEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif collection.size() >= 1:
                        collection = jnius.cast(self.Set, collection)
                        self.converted[node] = self.factory.getOWLObjectIntersectionOf(collection)
                    else:
                        self.converted[node] = collection.iterator().next()

        return self.converted[node]

    def buildEnumeration(self, node):
        """
        Build and returns a OWL enumeration using the given Graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node not in self.converted:
            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.item is Item.IndividualNode
            collection = self.HashSet()
            for i in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                collection.doAddNode(self.buildIndividual(i))
            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')
            collection = jnius.cast(self.Set, collection)
            self.converted[node] = self.factory.getOWLObjectOneOf(collection)
        return self.converted[node]

    def buildIndividual(self, node):
        """
        Build and returns a OWL individual using the given Graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        if node not in self.converted:
            if node.identity is Identity.Instance:
                IRI = self.IRI.create(self.ontoIRI, OWLText(node.text()))
                self.converted[node] = self.factory.getOWLNamedIndividual(IRI)
            elif node.identity is Identity.Value:
                datatype = self.OWL2Datatype.valueOf(node.datatype.owlapi)
                self.converted[node] = self.factory.getOWLLiteral(node.value, datatype)
        return self.converted[node]

    def buildIntersection(self, node):
        """
        Build and returns a OWL intersection using the given Graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf | OWLDataIntersectionOf
        """
        if node not in self.converted:

            collection = self.HashSet()

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if item.item is Item.ConceptNode:
                    collection.doAddNode(self.buildConcept(item))
                elif item.item is Item.ValueDomainNode:
                    collection.doAddNode(self.buildValueDomain(item))
                elif item.item is Item.ComplementNode:
                    collection.doAddNode(self.buildComplement(item))
                elif item.item is Item.EnumerationNode:
                    collection.doAddNode(self.buildEnumeration(item))
                elif item.item is Item.IntersectionNode:
                    collection.doAddNode(self.buildIntersection(item))
                elif item.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.doAddNode(self.buildUnion(item))
                elif item.item is Item.DomainRestrictionNode:
                    collection.doAddNode(self.buildDomainRestriction(item))
                elif item.item is Item.RangeRestrictionNode:
                    collection.doAddNode(self.buildRangeRestriction(item))
                elif item.item is Item.DatatypeRestrictionNode:
                    collection.doAddNode(self.buildDatatypeRestriction(item))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(item))

            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')

            collection = jnius.cast(self.Set, collection)

            if node.identity is Identity.Concept:
                self.converted[node] = self.factory.getOWLObjectIntersectionOf(collection)
            elif node.identity is Identity.ValueDomain:
                self.converted[node] = self.factory.getOWLDataIntersectionOf(collection)

        return self.converted[node]

    def buildPropertyAssertion(self, node):
        """
        Build and returns a collection of individuals that can be used to build property assertions.
        :type node: PropertyAssertionNode
        :rtype: tuple
        """
        if node not in self.converted:

            if len(node.inputs) < 2:
                raise MalformedDiagramError(node, 'missing operand(s)')
            elif len(node.inputs) > 2:
                raise MalformedDiagramError(node, 'too many operands')

            collection = []
            for x in [self.scene.edge(i).other(node) for i in node.inputs]:
                if x.item is not Item.IndividualNode:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(x))
                collection.append(self.buildIndividual(x))

            self.converted[node] = collection

        return self.converted[node]

    def buildRangeRestriction(self, node):
        """
        Build and returns a OWL range restriction using the given Graphol node.
        :type node: DomainRestrictionNode
        :rtype: T <= OWLClassExpression | OWLDataProperty
        """
        if node not in self.converted:

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))

            if not o1:
                raise MalformedDiagramError(node, 'missing operand')

            if o1.identity is Identity.Attribute:

                # In this case we just create a mapping using the OWLDataPropertyExpression which
                # is needed later when we create the ISA between this node and the ValueDomain.
                self.converted[node] = self.buildAttribute(o1)

            elif o1.identity is Identity.Role:

                if o1.item is Item.RoleNode:
                    objectPropertyEx = self.buildRole(o1).getInverseProperty()
                elif o1.item is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(o1).getInverseProperty()
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o1))

                f3 = lambda x: x.identity is Identity.Concept
                o2 = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))

                if not o2:
                    classEx = self.factory.getOWLThing()
                elif o2.item is Item.ConceptNode:
                    classEx = self.buildConcept(o2)
                elif o2.item is Item.ComplementNode:
                    classEx = self.buildComplement(o2)
                elif o2.item is Item.EnumerationNode:
                    classEx = self.buildEnumeration(o2)
                elif o2.item is Item.IntersectionNode:
                    classEx = self.buildIntersection(o2)
                elif o2.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.Self:
                    self.converted[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.converted[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.converted[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    collection = self.HashSet()
                    cmin = node.cardinality['min']
                    cmax = node.cardinality['max']
                    if cmin is not None:
                        collection.doAddNode(self.factory.getOWLObjectMinCardinality(cmin, objectPropertyEx, classEx))
                    if cmax is not None:
                        collection.doAddNode(self.factory.getOWLObjectMaxCardinality(cmax, objectPropertyEx, classEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    if collection.size() >= 1:
                        collection = jnius.cast(self.Set, collection)
                        self.converted[node] = self.factory.getOWLObjectIntersectionOf(collection)
                    else:
                        self.converted[node] = collection.iterator().next()

        return self.converted[node]

    def buildRole(self, node):
        """
        Build and returns a OWL role using the given Graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node not in self.converted:
            if not node.special:
                self.converted[node] = self.factory.getOWLObjectProperty(self.IRI.create(self.ontoIRI, OWLText(node.text())))
            elif node.special is Special.Top:
                self.converted[node] = self.factory.getOWLTopObjectProperty()
            elif node.special is Special.Bottom:
                self.converted[node] = self.factory.getOWLBottomObjectProperty()
        return self.converted[node]

    def buildRoleChain(self, node):
        """
        Constructs and returns a chain of OWLObjectExpression (OPE => Role & RoleInverse).
        :type node: RoleChainNode
        :rtype: list
        """
        if node not in self.converted:
            if not node.inputs:
                raise MalformedDiagramError(node, 'missing operand(s)')
            collection = self.LinkedList()
            for x in [self.scene.edge(i).other(node) for i in node.inputs]:
                if x.item not in {Item.RoleNode, Item.RoleInverseNode}:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(x))
                elif x.item is Item.RoleNode:
                    collection.doAddNode(self.buildRole(x))
                elif x.item is Item.RoleInverseNode:
                    collection.doAddNode(self.buildRoleInverse(x))
            collection = jnius.cast(self.List, collection)
            self.converted[node] = collection
        return self.converted[node]

    def buildRoleInverse(self, node):
        """
        Build and returns a OWL role inverse using the given Graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        if node not in self.converted:
            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.item is Item.RoleNode
            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, 'missing operand')
            self.converted[node] = self.buildRole(operand).getInverseProperty()
        return self.converted[node]

    def buildUnion(self, node):
        """
        Build and returns a OWL union using the given Graphol node.
        :type node: UnionNode
        :rtype: T <= OWLObjectUnionOf | OWLDataUnionOf
        """
        if node not in self.converted:

            collection = self.HashSet()

            f1 = lambda x: x.item is Item.InputEdge
            f2 = lambda x: x.identity in {Identity.Concept, Identity.ValueDomain}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if item.item is Item.ConceptNode:
                    collection.doAddNode(self.buildConcept(item))
                elif item.item is Item.ValueDomainNode:
                    collection.doAddNode(self.buildValueDomain(item))
                elif item.item is Item.ComplementNode:
                    collection.doAddNode(self.buildComplement(item))
                elif item.item is Item.EnumerationNode:
                    collection.doAddNode(self.buildEnumeration(item))
                elif item.item is Item.IntersectionNode:
                    collection.doAddNode(self.buildIntersection(item))
                elif item.item in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.doAddNode(self.buildUnion(item))
                elif item.item is Item.DomainRestrictionNode:
                    collection.doAddNode(self.buildDomainRestriction(item))
                elif item.item is Item.RangeRestrictionNode:
                    collection.doAddNode(self.buildRangeRestriction(item))
                elif item.item is Item.DatatypeRestrictionNode:
                    collection.doAddNode(self.buildDatatypeRestriction(item))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(item))

            if not collection.size():
                raise MalformedDiagramError(node, 'missing operand(s)')

            collection = jnius.cast(self.Set, collection)

            if node.identity is Identity.Concept:
                self.converted[node] = self.factory.getOWLObjectUnionOf(collection)
            elif node.identity is Identity.ValueDomain:
                self.converted[node] = self.factory.getOWLDataUnionOf(collection)

        return self.converted[node]

    def buildValueDomain(self, node):
        """
        Build and returns a OWL datatype using the given Graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        if node not in self.converted:
            self.converted[node] = self.factory.getOWLDatatype(self.OWL2Datatype.valueOf(node.datatype.owlapi).getIRI())
        return self.converted[node]

    def buildValueRestriction(self, node):
        """
        Build and returns a OWL value restriction using the given Graphol node.
        :type node: ValueRestrictionNode
        :rtype: OWLFacetRestriction
        """
        if node not in self.converted:
            facetEx = self.OWLFacet.valueOf(node.facet.owlapi)
            literalEx = self.factory.getOWLLiteral(node.value, self.OWL2Datatype.valueOf(node.datatype.owlapi))
            self.converted[node] = self.factory.getOWLFacetRestriction(facetEx, literalEx)
        return self.converted[node]

    ####################################################################################################################
    #                                                                                                                  #
    #   AXIOMS GENERATION                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def axiomAnnotation(self, node):
        """
        Generate a OWL annotation axiom.
        :type node: AbstractNode
        """
        meta = self.scene.meta.metaFor(node.item, node.text())
        if meta and not isEmpty(meta.description):
            annotationP = self.factory.getOWLAnnotationProperty(self.IRI.create("Description"))
            annotationV = self.factory.getOWLLiteral(OWLAnnotationText(meta.description))
            annotationV = jnius.cast(self.OWLAnnotationValue, annotationV)
            annotation = self.factory.getOWLAnnotation(annotationP, annotationV)
            self.axioms.add(self.factory.getOWLAnnotationAssertionAxiom(self.converted[node].getIRI(), annotation))
    
    def axiomDataProperty(self, node):
        """
        Generate OWL Data Property specific axioms.
        :type node: AttributeNode
        """
        meta = self.scene.meta.metaFor(node.item, node.text())
        if meta:
            if meta.functionality:
                self.axioms.add(self.factory.getOWLFunctionalDataPropertyAxiom(self.converted[node]))

    def axiomClassAssertion(self, edge):
        """
        Generate a OWL ClassAssertion axiom.
        :type edge: InstanceOf
        """
        self.axioms.add(self.factory.getOWLClassAssertionAxiom(self.converted[edge.target], self.converted[edge.source]))

    def axiomDataPropertyAssertion(self, edge):
        """
        Generate a OWL DataPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        op1 = self.converted[edge.source][0]
        op2 = self.converted[edge.source][1]
        self.axioms.add(self.factory.getOWLDataPropertyAssertionAxiom(self.converted[edge.target], op1, op2))

    def axiomDataPropertyRange(self, edge):
        """
        Generate a OWL DataPropertyRange axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLDataPropertyRangeAxiom(self.converted[edge.source], self.converted[edge.target]))

    def axiomDeclaration(self, node):
        """
        Generate a OWL Declaration axiom.
        :type node: AbstractNode
        """
        self.axioms.add(self.factory.getOWLDeclarationAxiom(self.converted[node]))

    def axiomDisjointClasses(self, node):
        """
        Generate a OWL DisjointClasses axiom.
        :type node: DisjointUnionNode
        """
        collection = self.HashSet()
        for j in node.incomingNodes(lambda x: x.item is Item.InputEdge):
            collection.doAddNode(self.converted[j])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointClassesAxiom(collection))

    def axiomDisjointDataProperties(self, edge):
        """
        Generate a OWL DisjointDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.doAddNode(self.converted[edge.source])
        collection.doAddNode(self.converted[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointDataPropertiesAxiom(collection))

    def axiomDisjointObjectProperties(self, edge):
        """
        Generate a OWL DisjointObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.doAddNode(self.converted[edge.source])
        collection.doAddNode(self.converted[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLDisjointObjectPropertiesAxiom(collection))

    def axiomEquivalentClasses(self, edge):
        """
        Generate a OWL EquivalentClasses axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.doAddNode(self.converted[edge.source])
        collection.doAddNode(self.converted[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentClassesAxiom(collection))

    def axiomEquivalentDataProperties(self, edge):
        """
        Generate a OWL EquivalentDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.doAddNode(self.converted[edge.source])
        collection.doAddNode(self.converted[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentDataPropertiesAxiom(collection))

    def axiomEquivalentObjectProperties(self, edge):
        """
        Generate a OWL EquivalentObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.doAddNode(self.converted[edge.source])
        collection.doAddNode(self.converted[edge.target])
        collection = jnius.cast(self.Set, collection)
        self.axioms.add(self.factory.getOWLEquivalentObjectPropertiesAxiom(collection))

    def axiomObjectProperty(self, node):
        """
        Generate OWL ObjectProperty specific axioms.
        :type node: RoleNode
        """
        meta = self.scene.meta.metaFor(node.item, node.text())
        if meta:
            if meta.functionality:
                self.axioms.add(self.factory.getOWLFunctionalObjectPropertyAxiom(self.converted[node]))
            if meta.inverseFunctionality:
                self.axioms.add(self.factory.getOWLInverseFunctionalObjectPropertyAxiom(self.converted[node]))
            if meta.asymmetry:
                self.axioms.add(self.factory.getOWLAsymmetricObjectPropertyAxiom(self.converted[node]))
            if meta.irreflexivity:
                self.axioms.add(self.factory.getOWLIrreflexiveObjectPropertyAxiom(self.converted[node]))
            if meta.reflexivity:
                self.axioms.add(self.factory.getOWLReflexiveObjectPropertyAxiom(self.converted[node]))
            if meta.symmetry:
                self.axioms.add(self.factory.getOWLSymmetricObjectPropertyAxiom(self.converted[node]))
            if meta.transitivity:
                self.axioms.add(self.factory.getOWLTransitiveObjectPropertyAxiom(self.converted[node]))

    def axiomObjectPropertyAssertion(self, edge):
        """
        Generate a OWL ObjectPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        op1 = self.converted[edge.source][0]
        op2 = self.converted[edge.source][1]
        self.axioms.add(self.factory.getOWLObjectPropertyAssertionAxiom(self.converted[edge.target], op1, op2))

    def axiomSubclassOf(self, edge):
        """
        Generate a OWL SubclassOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubClassOfAxiom(self.converted[edge.source], self.converted[edge.target]))

    def axiomSubDataPropertyOfAxiom(self, edge):
        """
        Generate a OWL SubDataPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubDataPropertyOfAxiom(self.converted[edge.source], self.converted[edge.target]))

    def axiomSubObjectPropertyOf(self, edge):
        """
        Generate a OWL SubObjectPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubObjectPropertyOfAxiom(self.converted[edge.source], self.converted[edge.target]))

    def axiomSubPropertyChainOf(self, edge):
        """
        Generate a OWL SubPropertyChainOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.factory.getOWLSubPropertyChainOfAxiom(self.converted[edge.source], self.converted[edge.target]))

    ####################################################################################################################
    #                                                                                                                  #
    #   ONTOLOGY EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def export(self, syntax=OWLSyntax.Functional):
        """
        Export the coverted ontology using the provided syntax.
        :type syntax: OWLSyntax
        :rtype: str
        """
        if syntax is OWLSyntax.Functional:
            ontoFormat = self.FunctionalSyntaxDocumentFormat()
        elif syntax is OWLSyntax.Manchester:
            ontoFormat = self.ManchesterSyntaxDocumentFormat()
        elif syntax is OWLSyntax.RDF:
            ontoFormat = self.RDFXMLDocumentFormat()
        elif syntax is OWLSyntax.Turtle:
            ontoFormat = self.TurtleDocumentFormat()
        else:
            raise TypeError('unsupported syntax ({})'.format(syntax))

        ontoFormat.setPrefix(self.ontoPrefix, self.ontoIRI)

        stream = self.ByteArrayOutputStream()
        stream = jnius.cast(self.OutputStream, stream)

        self.man.setOntologyFormat(self.ontology, ontoFormat)
        self.man.saveOntology(self.ontology, stream)

        stream = jnius.cast(self.ByteArrayOutputStream, stream)
        return stream.toString("UTF-8")

    ####################################################################################################################
    #                                                                                                                  #
    #   ONTOLOGY GENERATION                                                                                            #
    #                                                                                                                  #
    ####################################################################################################################

    def run(self):
        """
        Perform OWL ontology generation.
        """
        self.axioms = set()
        self.converted = dict()

        # 1) NODES CONVERSION
        for n in self.scene.nodes():

            if n.item is Item.ConceptNode:                                                      # CONCEPT
                self.buildConcept(n)
            elif n.item is Item.AttributeNode:                                                  # ATTRIBUTE
                self.buildAttribute(n)
            elif n.item is Item.RoleNode:                                                       # ROLE
                self.buildRole(n)
            elif n.item is Item.ValueDomainNode:                                                # VALUE-DOMAIN
                self.buildValueDomain(n)
            elif n.item is Item.ValueRestrictionNode:                                           # VALUE-RESTRICTION
                self.buildValueRestriction(n)
            elif n.item is Item.IndividualNode:                                                 # INDIVIDUAL
                self.buildIndividual(n)
            elif n.item is Item.RoleInverseNode:                                                # ROLE INVERSE
                self.buildRoleInverse(n)
            elif n.item is Item.RoleChainNode:                                                  # ROLE CHAIN
                self.buildRoleChain(n)
            elif n.item is Item.ComplementNode:                                                 # COMPLEMENT
                self.buildComplement(n)
            elif n.item is Item.EnumerationNode:                                                # ENUMERATION
                self.buildEnumeration(n)
            elif n.item is Item.IntersectionNode:                                               # INTERSECTION
                self.buildIntersection(n)
            elif n.item in {Item.UnionNode, Item.DisjointUnionNode}:                            # UNION / DISJOINT UNION
                self.buildUnion(n)
            elif n.item is Item.DatatypeRestrictionNode:                                        # DATATYPE RESTRICTION
                self.buildDatatypeRestriction(n)
            elif n.item is Item.PropertyAssertionNode:                                          # PROPERTY ASSERTION
                self.buildPropertyAssertion(n)
            elif n.item is Item.DomainRestrictionNode:                                          # DOMAIN RESTRICTION
                self.buildDomainRestriction(n)
            elif n.item is Item.RangeRestrictionNode:                                           # RANGE RESTRICTION
                self.buildRangeRestriction(n)

            self.step(+1)

        # 2) GENERATE AXIOMS FROM NODES
        for n in self.scene.nodes():

            if n.item in {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode}:
                self.axiomDeclaration(n)
                if n.item is Item.AttributeNode:
                    self.axiomDataProperty(n)
                elif n.item is Item.RoleNode:
                    self.axiomObjectProperty(n)
            elif n.item is Item.DisjointUnionNode:
                self.axiomDisjointClasses(n)

            if n.predicate:
                self.axiomAnnotation(n)

        # 3) GENERATE AXIOMS FROM EDGES
        for e in self.scene.edges():

            if e.item is Item.InclusionEdge:

                if not e.complete:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axiomSubclassOf(e)
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        if e.source.item is Item.RoleChainNode:
                            self.axiomSubPropertyChainOf(e)
                        elif e.source.item is Item.ComplementNode ^ e.target.item is Item.ComplementNode:
                            self.axiomDisjointObjectProperties(e)
                        elif e.source.item in {Item.RoleNode, Item.RoleInverseNode} and e.target.item in {Item.RoleNode, Item.RoleInverseNode}:
                            self.axiomSubObjectPropertyOf(e)
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        if e.source.item is Item.ComplementNode ^ e.target.item is Item.ComplementNode:
                            self.axiomDisjointDataProperties(e)
                        else:
                            self.axiomSubDataPropertyOfAxiom(e)
                    elif e.source.item is Item.RangeRestrictionNode and e.target.identity is Identity.ValueDomain:
                        self.axiomDataPropertyRange(e)
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in inclusion')

                else:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axiomEquivalentClasses(e)
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        self.axiomEquivalentObjectProperties(e)
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        self.axiomEquivalentDataProperties(e)
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in equivalence')

            elif e.item is Item.MembershipEdge:

                if e.source.identity is Identity.Instance and e.target.identity is Identity.Concept:
                    self.axiomClassAssertion(e)
                elif e.source.identity is Identity.RoleInstance:
                    self.axiomObjectPropertyAssertion(e)
                elif e.source.identity is Identity.AttributeInstance:
                    self.axiomDataPropertyAssertion(e)
                else:
                    raise MalformedDiagramError(e, 'type mismatch in instanceOf')

            self.step(+1)

        # 4) GENERATE THE ONTOLOGY
        self.ontology = self.man.createOntology(self.IRI.create(self.ontoIRI))

        # 5) ITERATIVELY APPLY AXIOMS
        for axiom in self.axioms:
            self.man.applyChange(self.AddAxiom(self.ontology, axiom))

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARTY METHODS                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def step(self, count, increase=0):
        """
        Increments the progress by the given step and emits the progress signal.
        :type count: int
        :type increase: int
        """
        self.total += increase
        self.count += count
        self.count = clamp(self.count, minval=0, maxval=self.total)
        self.progress.emit(self.count, self.total)

    ####################################################################################################################
    #                                                                                                                  #
    #   MAIN WORKER                                                                                                    #
    #                                                                                                                  #
    ####################################################################################################################

    # noinspection PyArgumentList
    @pyqtSlot()
    def work(self):
        """
        Main worker: will trigger the execution of the run() method and catch any exception raised.
        Will trigger the following signals:

            - started: when the translation starts.
            - errored: if the translation can't be completed.
            - completed: if the translation completed.
            - finished: when the translation terminates (even if it errored).

        The errored signal will carry the instance of the Exception that caused the error.
        """
        try:
            self.started.emit()
            self.run()
        except Exception as e:
            self.errored.emit(e)
        else:
            self.completed.emit()
        finally:
            jnius.detach()
            self.finished.emit()