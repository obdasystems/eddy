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


import re

from jpype import JClass

from eddy.core.datatypes import Special, Item, Identity, Restriction
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.regex import RE_OWL_INVALID_CHAR


def OWLText(text):
    """
    Transform the given text returning OWL compatible text.
    :type text: T <= bytes | unicode
    :rtype: str
    """
    return re.sub(RE_OWL_INVALID_CHAR, '_', str(text))


def OWLTranslate(scene, ontoIRI, ontoPrefix):
    """
    Translate the given DiagramScene into OWL functional syntax.
    :type scene: DiagramScene
    :type ontoIRI: T <= bytes | unicode
    :type ontoPrefix: T <= bytes | unicode
    """
    AddAxiom = JClass('org.semanticweb.owlapi.model.AddAxiom')
    ByteArrayOutputStream = JClass('java.io.ByteArrayOutputStream')
    HashSet = JClass('java.util.HashSet')
    IRI = JClass('org.semanticweb.owlapi.model.IRI')
    LinkedList = JClass('java.util.LinkedList')
    OWLFunctionalSyntaxOntologyFormat = JClass('org.semanticweb.owlapi.io.OWLFunctionalSyntaxOntologyFormat')
    OWL2Datatype = JClass('org.semanticweb.owlapi.vocab.OWL2Datatype')
    OWLManager = JClass('org.semanticweb.owlapi.apibinding.OWLManager')
    
    axioms = set()
    converted = dict()
    man = OWLManager.createOWLOntologyManager()
    factory = man.getOWLDataFactory()
    
    ####################################################################################################################
    #                                                                                                                  #
    #   NODES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def OWLAttribute(node):
        """
        Build and returns a OWL attribute using the given Graphol node.
        :type node: AttributeNode
        :rtype: OWLDataProperty
        """
        if node not in converted:
            if not node.special:
                converted[node] = factory.getOWLDataProperty(IRI.create(ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                converted[node] = factory.getOWLTopDataProperty()
            elif node.special is Special.BOTTOM:
                converted[node] = factory.getOWLBottomDataProperty()
        return converted[node]

    def OWLComplement(node):
        """
        Build and returns a OWL complement using the given Graphol node
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node not in converted:

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
                    converted[node] = factory.getOWLObjectComplementOf(OWLConcept(operand))
                elif operand.isItem(Item.ComplementNode):
                    converted[node] = factory.getOWLObjectComplementOf(OWLComplement(operand))
                elif operand.isItem(Item.EnumerationNode):
                    converted[node] = factory.getOWLObjectComplementOf(OWLEnumeration(operand))
                elif operand.isItem(Item.IntersectionNode):
                    converted[node] = factory.getOWLObjectComplementOf(OWLIntersection(operand))
                elif operand.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    converted[node] = factory.getOWLObjectComplementOf(OWLUnion(operand))
                elif operand.isItem(Item.DomainRestrictionNode):
                    converted[node] = factory.getOWLObjectComplementOf(OWLDomainRestriction(operand))

            elif operand.identity is Identity.DataRange:

                # TODO: support DatatypeRestriction
                if operand.isItem(Item.ValueDomainNode):
                    converted[node] = factory.getOWLDataComplementOf(OWLValueDomain(operand))
                elif operand.isItem(Item.ComplementNode):
                    converted[node] = factory.getOWLDataComplementOf(OWLComplement(operand))
                elif operand.isItem(Item.EnumerationNode):
                    converted[node] = factory.getOWLDataComplementOf(OWLEnumeration(operand))
                elif operand.isItem(Item.IntersectionNode):
                    converted[node] = factory.getOWLDataComplementOf(OWLIntersection(operand))
                elif operand.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    converted[node] = factory.getOWLDataComplementOf(OWLUnion(operand))

            elif operand.identity is Identity.Role:

                # If we have a Role in input to this Complement node, create a mapping using
                # the OWL representation of the Role/Inv itself so that we can generate the role
                # disjoint axiom later by calling factory.getOWLDisjointObjectPropertiesAxiom.
                if operand.isItem(Item.RoleNode):
                    converted[node] = OWLRole(operand)
                elif operand.isItem(Item.RoleInverseNode):
                    converted[node] = OWLRoleInverse(operand)

        return converted[node]

    def OWLConcept(node):
        """
        Build and returns a OWL concept using the given Graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        if node not in converted:
            if not node.special:
                converted[node] = factory.getOWLClass(IRI.create(ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                converted[node] = factory.getOWLThing()
            elif node.special is Special.BOTTOM:
                converted[node] = factory.getOWLNothing()
        return converted[node]
    
    def OWLDomainRestriction(node):
        """
        Build and returns a OWL domain restriction using the given Graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        if node not in converted:

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

            if not o1:
                raise MalformedDiagramError(node, 'missing operand(s)')

            if o1.identity is Identity.Attribute:

                f3 = lambda x: x.identity is Identity.DataRange
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                dataPropEx = OWLAttribute(o1)

                # TODO: support DatatypeRestriction
                if not o2:
                    dataRangeEx = factory.getTopDatatype()
                elif o2.isItem(Item.ValueDomainNode):
                    dataRangeEx = OWLValueDomain(o2)
                elif o2.isItem(Item.ComplementNode):
                    dataRangeEx = OWLComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    dataRangeEx = OWLEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    dataRangeEx = OWLIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    dataRangeEx = OWLComplement(o2)
                else:
                    raise MalformedDiagramError(o2, 'unsupported operand')

                if node.restriction is Restriction.self:
                    raise MalformedDiagramError(node, 'unsupported restriction')
                elif node.restriction is Restriction.exists:
                    converted[node] = factory.getOWLDataSomeValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.forall:
                    converted[node] = factory.getOWLDataAllValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.cardinality:
                    collection = HashSet()
                    if node.cardinality['min'] is not None:
                        collection.add(factory.getOWLDataMinCardinality(node.cardinality['min'], dataPropEx, dataRangeEx))
                    if node.cardinality['max'] is not None:
                        collection.add(factory.getOWLDataMinCardinality(node.cardinality['max'], dataPropEx, dataRangeEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif collection.size() >= 1:
                        converted[node] = factory.getOWLDataIntersectionOf(collection)
                    else:
                        converted[node] = collection.iterator().next()

            elif o1.identity is Identity.Role:

                if o1.isItem(Item.RoleNode):
                    objectPropertyEx = OWLRole(o1)
                elif o1.isItem(Item.RoleInverseNode):
                    objectPropertyEx = OWLRoleInverse(o1)
                else:
                    raise MalformedDiagramError(o1, 'unsupported operand')

                f3 = lambda x: x.identity is Identity.Concept
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                if not o2:
                    classEx = factory.getOWLThing()
                elif o2.isItem(Item.ConceptNode):
                    classEx = OWLConcept(o2)
                elif o2.isItem(Item.ComplementNode):
                    classEx = OWLComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    classEx = OWLEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    classEx = OWLIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    classEx = OWLUnion(o2)
                elif o2.isItem(Item.DomainRestrictionNode):
                    classEx = OWLDomainRestriction(o2)
                else:
                    raise MalformedDiagramError(o2, 'unsupported operand')

                if node.restriction is Restriction.self:
                    converted[node] = factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.exists:
                    converted[node] = factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.forall:
                    converted[node] = factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.cardinality:
                    collection = HashSet()
                    if node.cardinality['min'] is not None:
                        collection.add(factory.getOWLObjectMinCardinality(node.cardinality['min'], objectPropertyEx, classEx))
                    if node.cardinality['max'] is not None:
                        collection.add(factory.getOWLObjectMaxCardinality(node.cardinality['max'], objectPropertyEx, classEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif collection.size() >= 1:
                        converted[node] = factory.getOWLObjectIntersectionOf(collection)
                    else:
                        converted[node] = collection.iterator().next()

        return converted[node]

    def OWLEnumeration(node):
        """
        Build and returns a OWL enumeration using the given Graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node not in converted:
            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.isItem(Item.IndividualNode)
            collection = HashSet()
            for i in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                collection.add(OWLIndividual(i))
            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')
            converted[node] = factory.getOWLObjectOneOf(collection)
        return converted[node]
    
    def OWLIndividual(node):
        """
        Build and returns a OWL individual using the given Graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        # FIXME: what about Individual/Literals?
        if node not in converted:
            converted[node] = factory.getOWLNamedIndividual(IRI.create(ontoIRI, OWLText(node.labelText())))
        return converted[node]
    
    def OWLIntersection(node):
        """
        Build and returns a OWL intersection using the given Graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf | OWLDataIntersectionOf
        """
        if node not in converted:

            collection = HashSet()

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Concept, Identity.DataRange}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                # TODO: support DatatypeRestriction
                if item.isItem(Item.ConceptNode):
                    collection.add(OWLConcept(item))
                if item.isItem(Item.ValueDomainNode):
                    collection.add(OWLValueDomain(item))
                elif item.isItem(Item.ComplementNode):
                    collection.add(OWLComplement(item))
                elif item.isItem(Item.EnumerationNode):
                    collection.add(OWLEnumeration(item))
                elif item.isItem(Item.IntersectionNode):
                    collection.add(OWLIntersection(item))
                elif item.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    collection.add(OWLUnion(item))
                elif item.isItem(Item.DomainRestrictionNode):
                    collection.add(OWLDomainRestriction(item))

            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')

            if node.identity is Identity.Concept:
                converted[node] = factory.getOWLObjectIntersectionOf(collection)
            elif node.identity is Identity.DataRange:
                converted[node] = factory.getOWLDataIntersectionOf(collection)

        return converted[node]

    def OWLRangeRestriction(node):
        """
        Build and returns a OWL range restriction using the given Graphol node.
        :type node: DomainRestrictionNode
        :rtype: T <= OWLClassExpression | OWLDataProperty
        """
        if node not in converted:

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Role, Identity.Attribute}
            o1 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

            if not o1:
                raise MalformedDiagramError(node, 'missing operand')

            if o1.identity is Identity.Attribute:

                # In this case we just create a mapping using the OWLDataPropertyExpression which
                # is needed later when we create the ISA between this node and the DataRange.
                # FIXME: what about exists/cardinality/forall/self??????
                converted[node] = OWLAttribute(o1)

            elif o1.identity is Identity.Role:

                if o1.isItem(Item.RoleNode):
                    objectPropertyEx = OWLRole(o1).getInverseProperty()
                elif o1.isItem(Item.RoleInverseNode):
                    objectPropertyEx = OWLRoleInverse(o1).getInverseProperty()
                else:
                    raise MalformedDiagramError(o1, 'unsupported operand')

                f3 = lambda x: x.identity is Identity.Concept
                o2 = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)), None)

                if not o2:
                    classEx = factory.getOWLThing()
                elif o2.isItem(Item.ConceptNode):
                    classEx = OWLConcept(o2)
                elif o2.isItem(Item.ComplementNode):
                    classEx = OWLComplement(o2)
                elif o2.isItem(Item.EnumerationNode):
                    classEx = OWLEnumeration(o2)
                elif o2.isItem(Item.IntersectionNode):
                    classEx = OWLIntersection(o2)
                elif o2.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    classEx = OWLUnion(o2)
                else:
                    raise MalformedDiagramError(o2, 'unsupported operand')

                if node.restriction is Restriction.self:
                    converted[node] = factory.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.exists:
                    converted[node] = factory.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.forall:
                    converted[node] = factory.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.cardinality:
                    collection = HashSet()
                    if node.cardinality['min'] is not None:
                        collection.add(factory.getOWLObjectMinCardinality(node.cardinality['min'], objectPropertyEx, classEx))
                    if node.cardinality['max'] is not None:
                        collection.add(factory.getOWLObjectMaxCardinality(node.cardinality['max'], objectPropertyEx, classEx))
                    if collection.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    if collection.size() >= 1:
                        converted[node] = factory.getOWLObjectIntersectionOf(collection)
                    else:
                        converted[node] = collection.iterator().next()

        return converted[node]

    def OWLRole(node):
        """
        Build and returns a OWL role using the given Graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node not in converted:
            if not node.special:
                converted[node] = factory.getOWLObjectProperty(IRI.create(ontoIRI, OWLText(node.labelText())))
            elif node.special is Special.TOP:
                converted[node] = factory.getOWLTopObjectProperty()
            elif node.special is Special.BOTTOM:
                converted[node] = factory.getOWLBottomObjectProperty()
        return converted[node]
    
    def OWLRoleChain(node):
        """
        Constructs and returns a chain of OWLObjectExpression (OPE => Role & RoleInverse).
        :type node: RoleChainNode
        :rtype: list
        """
        if node not in converted:
            if not node.inputs:
                raise MalformedDiagramError(node, 'missing operand(s)')
            collection = LinkedList()
            for x in [scene.edge(i).other(node) for i in node.inputs]:
                if not x.isItem(Item.RoleNode, Item.RoleInverseNode):
                    raise MalformedDiagramError(node, 'invalid operand ({})'.format(x))
                elif x.isItem(Item.RoleNode):
                    collection.add(OWLRole(x))
                elif x.isItem(Item.RoleInverseNode):
                    collection.add(OWLRoleInverse(x))
            converted[node] = collection
        return converted[node]
    
    def OWLRoleInverse(node):
        """
        Build and returns a OWL role inverse using the given Graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        if node not in converted:
            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.isItem(Item.RoleNode)
            operand = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)
            if not operand:
                raise MalformedDiagramError(node, 'missing operand')
            converted[node] = OWLRole(operand).getInverseProperty()
        return converted[node]

    def OWLUnion(node):
        """
        Build and returns a OWL union using the given Graphol node.
        :type node: UnionNode
        :rtype: T <= OWLObjectUnionOf | OWLDataUnionOf
        """
        if node not in converted:

            collection = HashSet()

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.identity in {Identity.Concept, Identity.DataRange}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                # TODO: support DatatypeRestriction
                if item.isItem(Item.ConceptNode):
                    collection.add(OWLConcept(item))
                if item.isItem(Item.ValueDomainNode):
                    collection.add(OWLValueDomain(item))
                elif item.isItem(Item.ComplementNode):
                    collection.add(OWLComplement(item))
                elif item.isItem(Item.EnumerationNode):
                    collection.add(OWLEnumeration(item))
                elif item.isItem(Item.IntersectionNode):
                    collection.add(OWLIntersection(item))
                elif item.isItem(Item.UnionNode, Item.DisjointUnionNode):
                    collection.add(OWLUnion(item))
                elif item.isItem(Item.DomainRestrictionNode):
                    collection.add(OWLDomainRestriction(item))

            if not collection.size():
                raise MalformedDiagramError(node, 'missing operand(s)')

            if node.identity is Identity.Concept:
                converted[node] = factory.getOWLObjectUnionOf(collection)
            elif node.identity is Identity.DataRange:
                converted[node] = factory.getOWLDataUnionOf(collection)

        return converted[node]

    def OWLValueDomain(node):
        """
        Build and returns a OWL datatype using the given Graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        if node not in converted:
            # FIXME: what about Special.BOTTOM
            if not node.special:
                converted[node] = factory.getOWLDatatype(OWL2Datatype.valueOf(node.datatype.owlEnum).getIRI())
            elif node.special is Special.TOP:
                converted[node] = factory.getTopDatatype()
        return converted[node]
    
    ####################################################################################################################
    #                                                                                                                  #
    #   EDGES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def OWLFunctionalInput(edge):
        """
        Build and returns an OWL functional input axiom using the given Graphol node.
        :type edge: InputEdge
        :rtype: OWLAxiom
        """
        pass

    def OWLInclusion(edge):
        """
        Build and returns an OWL ISA using the given Graphol node.
        :type edge: InclusioneEdge
        :rtype: OWLAxiom
        """
        if edge not in converted:

            if not edge.complete:

                if edge.source.identity is Identity.Concept and edge.target.identity is Identity.Concept:
                    converted[edge] = factory.getOWLSubClassOfAxiom(converted[edge.source], converted[edge.target])
                elif edge.source.identity is Identity.Role and edge.target.identity is Identity.Role:
                    if edge.source.isItem(Item.RoleChainNode):
                        converted[edge] = factory.getOWLSubPropertyChainOfAxiom(converted[edge.source], converted[edge.target])
                    elif edge.source.isItem(Item.ComplementNode) ^ edge.target.isItem(Item.ComplementNode):
                        converted[edge] = factory.getOWLDisjointObjectPropertiesAxiom(converted[edge.source], converted[edge.target])
                    elif edge.source.isItem(Item.RoleNode, Item.RoleInverseNode) and edge.target.isItem(Item.RoleNode, Item.RoleInverseNode):
                        converted[edge] = factory.getOWLSubObjectPropertyOfAxiom(converted[edge.source], converted[edge.target])
                elif edge.source.identity is Identity.Attribute and edge.target.identity is Identity.Attribute:
                    # FIXME: what about getOWLDisjointDataPropertiesAxiom???
                    converted[edge] = factory.getOWLSubDataPropertyOfAxiom(converted[edge.source], converted[edge.target])
                elif edge.source.isItem(Item.RangeRestrictionNode) and edge.target.identity is Identity.DataRange:
                    converted[edge] = factory.getOWLDataPropertyRangeAxiom(converted[edge.source], converted[edge.target])
                else:
                    raise MalformedDiagramError(edge, 'type mismatch in ISA')

            else:

                if edge.source.identity is Identity.Concept and edge.target.identity is Identity.Concept:
                    converted[edge] = factory.getOWLEquivalentClassesAxiom(converted[edge.source], converted[edge.target])
                elif edge.source.identity is Identity.Role and edge.target.identity is Identity.Role:
                    converted[edge] = factory.getOWLEquivalentObjectPropertiesAxiom(converted[edge.source], converted[edge.target])
                elif edge.source.identity is Identity.Attribute and edge.target.identity is Identity.Attribute:
                    converted[edge] = factory.getOWLEquivalentDataPropertiesAxiom(converted[edge.source], converted[edge.target])
                else:
                    raise MalformedDiagramError(edge, 'type mismatch in equivalence')

        return converted[edge]

    def OWLInstanceOf(edge):
        """
        Build and returns an OWL instance of axiom using the given Graphol node.
        :type edge: InputEdge
        :rtype: OWLAxiom
        """
        if edge not in converted:

            if edge.source.identity is Identity.Individual and edge.target.identity is Identity.Concept:
                converted[edge] = factory.getOWLClassAssertionAxiom(converted[edge.target], converted[edge.source])
            else:
                # FIXME: what about: if(source instanceof OWLClass && target instanceof OWLClassExpression)
                raise MalformedDiagramError(edge, 'type mismatch in instanceOf')

        return converted[edge]

    ####################################################################################################################
    #                                                                                                                  #
    #   ONTOLOGY GENERATION                                                                                            #
    #                                                                                                                  #
    ####################################################################################################################

    # TODO: support DatatypeRestriction, ValueRestriction and PropertyAssertion

    # 1) NODES CONVERSION
    for n in scene.nodes():

        if n.isItem(Item.ConceptNode):                                                      # CONCEPT
            OWLConcept(n)
        elif n.isItem(Item.AttributeNode):                                                  # ATTRIBUTE
            OWLAttribute(n)
        elif n.isItem(Item.RoleNode):                                                       # ROLE
            OWLRole(n)
        elif n.isItem(Item.ValueDomainNode):                                                # VALUE-DOMAIN
            OWLValueDomain(n)
        elif n.isItem(Item.IndividualNode):                                                 # INDIVIDUAL
            OWLIndividual(n)
        elif n.isItem(Item.RoleInverseNode):                                                # ROLE INVERSE
            OWLRoleInverse(n)
        elif n.isItem(Item.RoleChainNode):                                                  # ROLE CHAIN
            OWLRoleChain(n)
        elif n.isItem(Item.ComplementNode):                                                 # COMPLEMENT
            OWLComplement(n)
        elif n.isItem(Item.EnumerationNode):                                                # ENUMERATION
            OWLEnumeration(n)
        elif n.isItem(Item.IntersectionNode):                                               # INTERSECTION
            OWLIntersection(n)
        elif n.isItem(Item.UnionNode, Item.DisjointUnionNode):                              # UNION / DISJOINT UNION
            OWLUnion(n)
        elif n.isItem(Item.DomainRestrictionNode):                                          # DOMAIN RESTRICTION
            OWLDomainRestriction(n)
        elif n.isItem(Item.RangeRestrictionNode):                                           # RANGE RESTRICTION
            OWLRangeRestriction(n)

    # 2) GENERATE AXIOMS FROM NODES
    for n in scene.nodes():

        if n.isItem(Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode):
            axioms.add(factory.getOWLDeclarationAxiom(converted[n]))
        elif n.isItem(Item.DisjointUnionNode):
            operands = HashSet()
            for j in n.incomingNodes(lambda x: x.isItem(Item.InputEdge)):
                operands.add(converted[j])
            axioms.add(factory.getOWLDisjointClassesAxiom(operands))

    # 3) GENERATE AXIOMS FROM EDGES
    for e in scene.edges():

        if e.isItem(Item.InclusionEdge):                                                    # INCLUSION
            axioms.add(OWLInclusion(e))
        #elif e.isItem(Item.InputEdge):                                                     # FUNCTIONAL INPUT
        #    if e.functional:
        #        axioms.add(OWLFunctionalInput(e))
        elif e.isItem(Item.InstanceOfEdge):
            axioms.add(OWLInstanceOf(e))

    ontology = man.createOntology(IRI.create(ontoIRI))

    for axiom in axioms:
        man.applyChange(AddAxiom(ontology, axiom))

    ####################################################################################################################
    #                                                                                                                  #
    #   ONTOLOGY EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    stream = ByteArrayOutputStream()
    syntax = OWLFunctionalSyntaxOntologyFormat()
    syntax.setPrefix(ontoPrefix, ontoIRI)
    man.setOntologyFormat(ontology, syntax)
    man.saveOntology(ontology, stream)

    return stream.toString("UTF-8")