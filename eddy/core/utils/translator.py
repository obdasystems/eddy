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


import jpype

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from eddy.core.datatypes import Special, Item, Identity, Restriction, OWLSyntax
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.functions import clamp, OWLText


class OWLTranslator(QObject):
    """
    This class can be used to translate Graphol diagrams into OWL ontologies.
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
        :type ontoIRI: T <= bytes | unicode
        :type ontoPrefix: T <= bytes | unicode
        """
        super().__init__()

        self.scene = scene
        self.ontoIRI = ontoIRI
        self.ontoPrefix = ontoPrefix

        self.count = 0
        self.total = len(scene.nodes()) + len(scene.edges())
        
        self.AddAxiom = jpype.JClass('org.semanticweb.owlapi.model.AddAxiom')
        self.ByteArrayOutputStream = jpype.JClass('java.io.ByteArrayOutputStream')
        self.FunctionalSyntaxDocumentFormat = jpype.JClass('org.semanticweb.owlapi.formats.FunctionalSyntaxDocumentFormat')
        self.HashSet = jpype.JClass('java.util.HashSet')
        self.IRI = jpype.JClass('org.semanticweb.owlapi.model.IRI')
        self.LinkedList = jpype.JClass('java.util.LinkedList')
        self.ManchesterSyntaxDocumentFormat = jpype.JClass('org.semanticweb.owlapi.formats.ManchesterSyntaxDocumentFormat')
        self.OWL2Datatype = jpype.JClass('org.semanticweb.owlapi.vocab.OWL2Datatype')
        self.OWLManager = jpype.JClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.RDFXMLDocumentFormat = jpype.JClass('org.semanticweb.owlapi.formats.RDFXMLDocumentFormat')
        self.TurtleDocumentFormat = jpype.JClass('org.semanticweb.owlapi.formats.TurtleDocumentFormat')

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
                self.converted[node] = self.factory.getOWLDataProperty(self.IRI.create(self.ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                self.converted[node] = self.factory.getOWLTopDataProperty()
            elif node.special is Special.BOTTOM:
                self.converted[node] = self.factory.getOWLBottomDataProperty()
        return self.converted[node]
    
    def buildComplement(self, node):
        """
        Build and returns a OWL complement using the given Graphol node
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node not in self.converted:

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Concept, Identity.DataRange, Identity.Role}

            collection = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)

            if not collection:
                raise MalformedDiagramError(node, 'missing operand')

            if len(collection) > 1:
                raise MalformedDiagramError(node, 'too many operands')

            operand = collection[0]

            if operand.identity is Identity.Concept:

                if operand.isItem(Item.ConceptNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildConcept(operand))
                elif operand.isItem(Item.ComplementNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildComplement(operand))
                elif operand.isItem(Item.EnumerationNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildEnumeration(operand))
                elif operand.isItem(Item.IntersectionNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildIntersection(operand))
                elif operand.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildUnion(operand))
                elif operand.isItem(Item.DomainRestrictionNode):
                    self.converted[node] = self.factory.getOWLObjectComplementOf(self.buildDomainRestriction(operand))

            elif operand.identity is Identity.DataRange:

                # TODO: support DatatypeRestriction
                if operand.isItem(Item.ValueDomainNode):
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildValueDomain(operand))
                elif operand.isItem(Item.ComplementNode):
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildComplement(operand))
                elif operand.isItem(Item.EnumerationNode):
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildEnumeration(operand))
                elif operand.isItem(Item.IntersectionNode):
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildIntersection(operand))
                elif operand.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    self.converted[node] = self.factory.getOWLDataComplementOf(self.buildUnion(operand))

            elif operand.identity is Identity.Role:

                # If we have a Role in input to this Complement node, create a mapping using
                # the OWL representation of the Role/Inv itself so that we can generate the role
                # disjoint axiom later by calling self.factory.getOWLDisjointObjectPropertiesAxiom
                if operand.isItem(Item.RoleNode):
                    self.converted[node] = self.buildRole(operand)
                elif operand.isItem(Item.RoleInverseNode):
                    self.converted[node] = self.buildRoleInverse(operand)

        return self.converted[node]
    
    def buildConcept(self, node):
        """
        Build and returns a OWL concept using the given Graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        if node not in self.converted:
            if not node.special:
                self.converted[node] = self.factory.getOWLClass(self.IRI.create(self.ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                self.converted[node] = self.factory.getOWLThing()
            elif node.special is Special.BOTTOM:
                self.converted[node] = self.factory.getOWLNothing()
        return self.converted[node]
    
    def buildDomainRestriction(self, node):
        """
        Build and returns a OWL domain restriction using the given Graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        if node not in self.converted:

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

            if not o1:
                raise MalformedDiagramError(node, 'missing operand(s)')

            if o1.identity is Identity.Attribute:

                f3 = lambda x: x.identity is Identity.DataRange
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                dataPropEx = self.buildAttribute(o1)

                # TODO: support DatatypeRestriction
                if not o2:
                    dataRangeEx = self.factory.getTopDatatype()
                elif o2.isItem(Item.ValueDomainNode):
                    dataRangeEx = self.buildValueDomain(o2)
                elif o2.isItem(Item.ComplementNode):
                    dataRangeEx = self.buildComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    dataRangeEx = self.buildEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    dataRangeEx = self.buildIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    dataRangeEx = self.buildComplement(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.self:
                    raise MalformedDiagramError(node, 'unsupported restriction')
                elif node.restriction is Restriction.exists:
                    self.converted[node] = self.factory.getOWLDataSomeValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.forall:
                    self.converted[node] = self.factory.getOWLDataAllValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.cardinality:
                    HS = self.HashSet()
                    if node.cardinality['min'] is not None:
                        HS.add(self.factory.getOWLDataMinCardinality(node.cardinality['min'], dataPropEx, dataRangeEx))
                    if node.cardinality['max'] is not None:
                        HS.add(self.factory.getOWLDataMinCardinality(node.cardinality['max'], dataPropEx, dataRangeEx))
                    if HS.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif HS.size() >= 1:
                        self.converted[node] = self.factory.getOWLDataIntersectionOf(HS)
                    else:
                        self.converted[node] = HS.iterator().next()

            elif o1.identity is Identity.Role:

                if o1.isItem(Item.RoleNode):
                    objectPropertyEx = self.buildRole(o1)
                elif o1.isItem(Item.RoleInverseNode):
                    objectPropertyEx = self.buildRoleInverse(o1)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o1))

                f3 = lambda x: x.identity is Identity.Concept
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                if not o2:
                    classEx = self.factory.getOWLThing()
                elif o2.isItem(Item.ConceptNode):
                    classEx = self.buildConcept(o2)
                elif o2.isItem(Item.ComplementNode):
                    classEx = self.buildComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    classEx = self.buildEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    classEx = self.buildIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    classEx = self.buildUnion(o2)
                elif o2.isItem(Item.DomainRestrictionNode):
                    classEx = self.buildDomainRestriction(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.self:
                    self.converted[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.exists:
                    self.converted[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.forall:
                    self.converted[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.cardinality:
                    HS = self.HashSet()
                    if node.cardinality['min'] is not None:
                        HS.add(self.factory.getOWLObjectMinCardinality(node.cardinality['min'], objectPropertyEx, classEx))
                    if node.cardinality['max'] is not None:
                        HS.add(self.factory.getOWLObjectMaxCardinality(node.cardinality['max'], objectPropertyEx, classEx))
                    if HS.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif HS.size() >= 1:
                        self.converted[node] = self.factory.getOWLObjectIntersectionOf(HS)
                    else:
                        self.converted[node] = HS.iterator().next()

        return self.converted[node]
    
    def buildEnumeration(self, node):
        """
        Build and returns a OWL enumeration using the given Graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node not in self.converted:
            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.isItem(Item.IndividualNode)
            collection = self.HashSet()
            for i in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                collection.add(self.buildIndividual(i))
            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')
            self.converted[node] = self.factory.getOWLObjectOneOf(collection)
        return self.converted[node]
    
    def buildIndividual(self, node):
        """
        Build and returns a OWL individual using the given Graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        # FIXME: what about Individual/Literals?
        if node not in self.converted:
            self.converted[node] = self.factory.getOWLNamedIndividual(self.IRI.create(self.ontoIRI, OWLText(node.labelText())))
        return self.converted[node]
    
    def buildIntersection(self, node):
        """
        Build and returns a OWL intersection using the given Graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf | OWLDataIntersectionOf
        """
        if node not in self.converted:

            collection = self.HashSet()

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Concept, Identity.DataRange}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                # TODO: support DatatypeRestriction
                if item.isItem(Item.ConceptNode):
                    collection.add(self.buildConcept(item))
                if item.isItem(Item.ValueDomainNode):
                    collection.add(self.buildValueDomain(item))
                elif item.isItem(Item.ComplementNode):
                    collection.add(self.buildComplement(item))
                elif item.isItem(Item.EnumerationNode):
                    collection.add(self.buildEnumeration(item))
                elif item.isItem(Item.IntersectionNode):
                    collection.add(self.buildIntersection(item))
                elif item.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    collection.add(self.buildUnion(item))
                elif item.isItem(Item.DomainRestrictionNode):
                    collection.add(self.buildDomainRestriction(item))

            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')

            if node.identity is Identity.Concept:
                self.converted[node] = self.factory.getOWLObjectIntersectionOf(collection)
            elif node.identity is Identity.DataRange:
                self.converted[node] = self.factory.getOWLDataIntersectionOf(collection)

        return self.converted[node]

    def buildPropertyAssertion(self, node):
        """
        Build and returns a collection of Individuals that can be used to build property assertions.
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
                if not x.isItem(Item.IndividualNode):
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

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

            if not o1:
                raise MalformedDiagramError(node, 'missing operand')

            if o1.identity is Identity.Attribute:

                # In this case we just create a mapping using the OWLDataPropertyExpression which
                # is needed later when we create the ISA between this node and the DataRange.
                # FIXME: what about exists/cardinality/forall/self??????
                self.converted[node] = self.buildAttribute(o1)

            elif o1.identity is Identity.Role:

                if o1.isItem(Item.RoleNode):
                    objectPropertyEx = self.buildRole(o1).getInverseProperty()
                elif o1.isItem(Item.RoleInverseNode):
                    objectPropertyEx = self.buildRoleInverse(o1).getInverseProperty()
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o1))

                f3 = lambda x: x.identity is Identity.Concept
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                if not o2:
                    classEx = self.factory.getOWLThing()
                elif o2.isItem(Item.ConceptNode):
                    classEx = self.buildConcept(o2)
                elif o2.isItem(Item.ComplementNode):
                    classEx = self.buildComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    classEx = self.buildEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    classEx = self.buildIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    classEx = self.buildUnion(o2)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(o2))

                if node.restriction is Restriction.self:
                    self.converted[node] = self.factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.exists:
                    self.converted[node] = self.factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.forall:
                    self.converted[node] = self.factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.cardinality:
                    HS = self.HashSet()
                    if node.cardinality['min'] is not None:
                        HS.add(self.factory.getOWLObjectMinCardinality(node.cardinality['min'], objectPropertyEx, classEx))
                    if node.cardinality['max'] is not None:
                        HS.add(self.factory.getOWLObjectMaxCardinality(node.cardinality['max'], objectPropertyEx, classEx))
                    if HS.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    if HS.size() >= 1:
                        self.converted[node] = self.factory.getOWLObjectIntersectionOf(HS)
                    else:
                        self.converted[node] = HS.iterator().next()

        return self.converted[node]

    def buildRole(self, node):
        """
        Build and returns a OWL role using the given Graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node not in self.converted:
            if not node.special:
                self.converted[node] = self.factory.getOWLObjectProperty(self.IRI.create(self.ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                self.converted[node] = self.factory.getOWLTopObjectProperty()
            elif node.special is Special.BOTTOM:
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
                if not x.isItem(Item.RoleNode, Item.RoleInverseNode):
                    raise MalformedDiagramError(node, 'unsupported operand ({})'.format(x))
                elif x.isItem(Item.RoleNode):
                    collection.add(self.buildRole(x))
                elif x.isItem(Item.RoleInverseNode):
                    collection.add(self.buildRoleInverse(x))
            self.converted[node] = collection
        return self.converted[node]
    
    def buildRoleInverse(self, node):
        """
        Build and returns a OWL role inverse using the given Graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        if node not in self.converted:
            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.isItem(Item.RoleNode)
            operand = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)
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

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Concept, Identity.DataRange}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                # TODO: support DatatypeRestriction
                if item.isItem(Item.ConceptNode):
                    collection.add(self.buildConcept(item))
                if item.isItem(Item.ValueDomainNode):
                    collection.add(self.buildValueDomain(item))
                elif item.isItem(Item.ComplementNode):
                    collection.add(self.buildComplement(item))
                elif item.isItem(Item.EnumerationNode):
                    collection.add(self.buildEnumeration(item))
                elif item.isItem(Item.IntersectionNode):
                    collection.add(self.buildIntersection(item))
                elif item.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    collection.add(self.buildUnion(item))
                elif item.isItem(Item.DomainRestrictionNode):
                    collection.add(self.buildDomainRestriction(item))

            if not collection.size():
                raise MalformedDiagramError(node, 'missing operand(s)')

            if node.identity is Identity.Concept:
                self.converted[node] = self.factory.getOWLObjectUnionOf(collection)
            elif node.identity is Identity.DataRange:
                self.converted[node] = self.factory.getOWLDataUnionOf(collection)

        return self.converted[node]

    def buildValueDomain(self, node):
        """
        Build and returns a OWL datatype using the given Graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        if node not in self.converted:
            # FIXME: what about Special.BOTTOM
            if not node.special:
                self.converted[node] = self.factory.getOWLDatatype(self.OWL2Datatype.valueOf(node.datatype.owlEnum).getIRI())
            elif node.special is Special.TOP:
                self.converted[node] = self.factory.getTopDatatype()
        return self.converted[node]

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
        stream = self.ByteArrayOutputStream()

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

        self.man.setOntologyFormat(self.ontology, ontoFormat)
        self.man.saveOntology(self.ontology, stream)

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

        # TODO: support DatatypeRestriction, ValueRestriction
        # 1) NODES CONVERSION
        for n in self.scene.nodes():

            if n.isItem(Item.ConceptNode):                                                      # CONCEPT
                self.buildConcept(n)
            elif n.isItem(Item.AttributeNode):                                                  # ATTRIBUTE
                self.buildAttribute(n)
            elif n.isItem(Item.RoleNode):                                                       # ROLE
                self.buildRole(n)
            elif n.isItem(Item.ValueDomainNode):                                                # VALUE-DOMAIN
                self.buildValueDomain(n)
            elif n.isItem(Item.IndividualNode):                                                 # INDIVIDUAL
                self.buildIndividual(n)
            elif n.isItem(Item.RoleInverseNode):                                                # ROLE INVERSE
                self.buildRoleInverse(n)
            elif n.isItem(Item.RoleChainNode):                                                  # ROLE CHAIN
                self.buildRoleChain(n)
            elif n.isItem(Item.ComplementNode):                                                 # COMPLEMENT
                self.buildComplement(n)
            elif n.isItem(Item.EnumerationNode):                                                # ENUMERATION
                self.buildEnumeration(n)
            elif n.isItem(Item.IntersectionNode):                                               # INTERSECTION
                self.buildIntersection(n)
            elif n.isItem(Item.UnionNode, Item.DisjointUnionNode):                              # UNION / DISJOINT UNION
                self.buildUnion(n)
            elif n.isItem(Item.PropertyAssertionNode):                                          # PROPERTY ASSERTION
                self.buildPropertyAssertion(n)
            elif n.isItem(Item.DomainRestrictionNode):                                          # DOMAIN RESTRICTION
                self.buildDomainRestriction(n)
            elif n.isItem(Item.RangeRestrictionNode):                                           # RANGE RESTRICTION
                self.buildRangeRestriction(n)

            self.step(+1)

        # 2) GENERATE AXIOMS FROM NODES
        for n in self.scene.nodes():

            if n.isItem(Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode):

                self.axioms.add(self.factory.getOWLDeclarationAxiom(self.converted[n]))

                if n.isItem(Item.RoleNode):
                    if n.symmetric:
                        self.axioms.add(self.factory.getOWLSymmetricObjectPropertyAxiom(self.converted[n]))
                    elif n.asymmetric:
                        self.axioms.add(self.factory.getOWLAsymmetricObjectPropertyAxiom(self.converted[n]))
                    if n.reflexive:
                        self.axioms.add(self.factory.getOWLReflexiveObjectPropertyAxiom(self.converted[n]))
                    elif n.irreflexive:
                        self.axioms.add(self.factory.getOWLIrreflexiveObjectPropertyAxiom(self.converted[n]))
                    if n.transitive:
                        self.axioms.add(self.factory.getOWLTransitiveObjectPropertyAxiom(self.converted[n]))

            elif n.isItem(Item.DisjointUnionNode):

                HS = self.HashSet()
                for j in n.incomingNodes(lambda x: x.isItem(Item.InputEdge)):
                    HS.add(self.converted[j])
                self.axioms.add(self.factory.getOWLDisjointClassesAxiom(HS))

        # 3) GENERATE AXIOMS FROM EDGES
        for e in self.scene.edges():

            if e.isItem(Item.InclusionEdge):

                if not e.complete:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axioms.add(self.factory.getOWLSubClassOfAxiom(self.converted[e.source], self.converted[e.target]))
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        if e.source.isItem(Item.RoleChainNode):
                            self.axioms.add(self.factory.getOWLSubPropertyChainOfAxiom(self.converted[e.source], self.converted[e.target]))
                        elif e.source.isItem(Item.ComplementNode) ^ e.target.isItem(Item.ComplementNode):
                            self.axioms.add(self.factory.getOWLDisjointObjectPropertiesAxiom(self.converted[e.source], self.converted[e.target]))
                        elif e.source.isItem(Item.RoleNode, Item.RoleInverseNode) and e.target.isItem(Item.RoleNode, Item.RoleInverseNode):
                            self.axioms.add(self.factory.getOWLSubObjectPropertyOfAxiom(self.converted[e.source], self.converted[e.target]))
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        # FIXME: what about getOWLDisjointDataPropertiesAxiom???
                        self.axioms.add(self.factory.getOWLSubDataPropertyOfAxiom(self.converted[e.source], self.converted[e.target]))
                    elif e.source.isItem(Item.RangeRestrictionNode) and e.target.identity is Identity.DataRange:
                        self.axioms.add(self.factory.getOWLDataPropertyRangeAxiom(self.converted[e.source], self.converted[e.target]))
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in ISA')

                else:

                    if e.source.identity is Identity.Concept and e.target.identity is Identity.Concept:
                        self.axioms.add(self.factory.getOWLEquivalentClassesAxiom(self.converted[e.source], self.converted[e.target]))
                    elif e.source.identity is Identity.Role and e.target.identity is Identity.Role:
                        self.axioms.add(self.factory.getOWLEquivalentObjectPropertiesAxiom(self.converted[e.source], self.converted[e.target]))
                    elif e.source.identity is Identity.Attribute and e.target.identity is Identity.Attribute:
                        self.axioms.add(self.factory.getOWLEquivalentDataPropertiesAxiom(self.converted[e.source], self.converted[e.target]))
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in equivalence')

            elif e.isItem(Item.InputEdge):

                if e.functional:

                    if e.source.identity is Identity.Role:
                        if e.target.isItem(Item.DomainRestrictionNode):
                            self.axioms.add(self.factory.getOWLFunctionalObjectPropertyAxiom(self.converted[e.source]))
                        elif e.target.isItem(Item.RangeRestrictionNode):
                            self.axioms.add(self.factory.getOWLInverseFunctionalObjectPropertyAxiom(self.converted[e.source]))
                    elif e.source.identity is Identity.Attribute:
                        if e.target.isItem(Item.DomainRestrictionNode):
                            self.axioms.add(self.factory.getOWLFunctionalDataPropertyAxiom(self.converted[e.source]))
                        else:
                            raise MalformedDiagramError(e, 'unsupported inverse functional edge')
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in functional edge')

            elif e.isItem(Item.InstanceOfEdge):

                if e.source.identity is Identity.Individual and e.target.identity is Identity.Concept:
                    self.axioms.add(self.factory.getOWLClassAssertionAxiom(self.converted[e.target], self.converted[e.source]))
                elif e.source.identity is Identity.Link and e.target.identity is Identity.Role:
                    self.axioms.add(self.factory.getOWLObjectPropertyAssertionAxiom(self.converted[e.target], self.converted[e.source][0], self.converted[e.source][1]))
                elif e.source.identity is Identity.Link and e.target.identity is Identity.Attribute:
                    self.axioms.add(self.factory.getOWLDataPropertyAssertionAxiom(self.converted[e.target], self.converted[e.source][0], self.converted[e.source][1]))
                else:
                    # FIXME: what about: if(source instanceof OWLClass && target instanceof OWLClassExpression)
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

    @pyqtSlot()
    def process(self):
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
            # This is needed so that JPype can move the JVM on the current thread whether
            # or not this method is executed on the main thread ot a new spawned thread. If
            # we don't attach the JVM to the thread running this worker we can run the translator
            # only in the UI thread which will cause the whole user interface to freeze during the work.
            jpype.attachThreadToJVM()
            self.started.emit()
            self.run()
        except Exception as e:
            self.errored.emit(e)
        else:
            self.completed.emit()
        finally:
            # Detaching is not really needed since the thread is going to be destroyed.
            jpype.detachThreadFromJVM()
            self.finished.emit()