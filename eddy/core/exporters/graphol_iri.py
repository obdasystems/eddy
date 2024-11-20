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

from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.fsystem import mkdir, fwrite, fexists, isdir
from eddy.core.functions.misc import postfix
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.output import getLogger
from eddy.ui.dialogs import DiagramSelectionDialog

LOGGER = getLogger()


class GrapholIRIProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export the structure of a Graphol project.
    A Graphol project is stored in a directory, whose structure is the following:
     -----------------------
     - projectname/
     -   projectname.graphol     # contains information on the ontology
     -   ...
    """

    def __init__(self, project, session=None, exportPath=None, selectDiagrams=False):
        """
        Initialize the project exporter.
        :type project: Project
        :type session: Session
        """
        super().__init__(project, session, exportPath, selectDiagrams)

        self.document = None
        self.selectedDiagrams = None

        self.itemToXml = {
            Item.AttributeNode: 'attribute',
            Item.ComplementNode: 'complement',
            Item.ConceptNode: 'concept',
            Item.DatatypeRestrictionNode: 'datatype-restriction',
            Item.DisjointUnionNode: 'disjoint-union',
            Item.DomainRestrictionNode: 'domain-restriction',
            Item.EnumerationNode: 'enumeration',
            Item.FacetNode: 'facet',
            Item.IndividualNode: 'individual',
            Item.LiteralNode: 'literal',
            Item.IntersectionNode: 'intersection',
            Item.PropertyAssertionNode: 'property-assertion',
            Item.RangeRestrictionNode: 'range-restriction',
            Item.RoleNode: 'role',
            Item.RoleChainNode: 'role-chain',
            Item.RoleInverseNode: 'role-inverse',
            Item.UnionNode: 'union',
            Item.ValueDomainNode: 'value-domain',
            Item.InclusionEdge: 'inclusion',
            Item.EquivalenceEdge: 'equivalence',
            Item.InputEdge: 'input',
            Item.MembershipEdge: 'membership',
            Item.SameEdge: 'same',
            Item.DifferentEdge: 'different',
            Item.HasKeyNode: 'has-key'
        }

        self.exportFuncForItem = {
            Item.AttributeNode: self.exportAttributeNode,
            Item.ComplementNode: self.exportComplementNode,
            Item.ConceptNode: self.exportConceptNode,
            Item.DatatypeRestrictionNode: self.exportDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.exportDisjointUnionNode,
            Item.DomainRestrictionNode: self.exportDomainRestrictionNode,
            Item.EnumerationNode: self.exportEnumerationNode,
            Item.FacetNode: self.exportFacetNode,
            Item.IndividualNode: self.exportIndividualNode,
            Item.LiteralNode: self.exportLiteralNode,
            Item.IntersectionNode: self.exportIntersectionNode,
            Item.PropertyAssertionNode: self.exportPropertyAssertionNode,
            Item.RangeRestrictionNode: self.exportRangeRestrictionNode,
            Item.RoleNode: self.exportRoleNode,
            Item.RoleChainNode: self.exportRoleChainNode,
            Item.RoleInverseNode: self.exportRoleInverseNode,
            Item.UnionNode: self.exportUnionNode,
            Item.ValueDomainNode: self.exportValueDomainNode,
            Item.InclusionEdge: self.exportInclusionEdge,
            Item.EquivalenceEdge: self.exportEquivalenceEdge,
            Item.InputEdge: self.exportInputEdge,
            Item.MembershipEdge: self.exportMembershipEdge,
            Item.SameEdge: self.exportSameEdge,
            Item.DifferentEdge: self.exportDifferentEdge,
            Item.HasKeyNode: self.exportHasKeyNode
        }

    #############################################
    #   MAIN EXPORT
    #################################

    def createDomDocument(self):
        """
        Create the QDomDocument where to store project information.
        """
        self.document = QtXml.QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.document.appendChild(instruction)
        graphol = self.getDomElement('graphol')
        graphol.setAttribute('version', '3')
        self.document.appendChild(graphol)

        project = self.getDomElement('project')
        project.setAttribute('name', self.project.name)
        project.setAttribute('version', self.project.version)
        graphol.appendChild(project)

        ontologyEl = self.getOntologyDomElement()
        project.appendChild(ontologyEl)

        diagramsEl = self.getDiagramsDomElement()
        project.appendChild(diagramsEl)

    def getOntologyDomElement(self):
        """
        Create the 'ontology' element in the QDomDocument.
        """
        ontologyEl = self.getDomElement('ontology')
        ontologyEl.setAttribute('iri',str(self.project.ontologyIRI))
        if self.project.ontologyPrefix:
            ontologyEl.setAttribute('prefix', str(self.project.ontologyPrefix))
        labelBoolean = '0'
        if self.project.addLabelFromSimpleName:
            labelBoolean = '1'
        ontologyEl.setAttribute('addLabelFromSimpleName', labelBoolean)

        labelBoolean = '0'
        if self.project.addLabelFromUserInput:
            labelBoolean = '1'
        ontologyEl.setAttribute('addLabelFromUserInput', labelBoolean)

        ontologyEl.setAttribute('lang', str(self.project.defaultLanguage))

        importsEl = self.getDomElement('imports')
        ontologyEl.appendChild(importsEl)
        for impOnt in sorted(self.project.importedOntologies,key=str):
            importEl = self.getOntologyImportDomElement(impOnt)
            importsEl.appendChild(importEl)


        prefixesEl = self.getDomElement('prefixes')
        ontologyEl.appendChild(prefixesEl)
        #for prefix,ns in self.project.prefixDictItems():
        for prefix in sorted(self.project.getManagedPrefixes(), key=str):
            ns = self.project.getPrefixResolution(prefix)
            valueEl = self.getDomElement('value')
            valueEl.appendChild(self.getDomTextNode(prefix))
            namespaceEl = self.getDomElement('namespace')
            namespaceEl.appendChild(self.getDomTextNode(ns))
            prefixEl = self.getDomElement('prefix')
            prefixEl.appendChild(valueEl)
            prefixEl.appendChild(namespaceEl)
            prefixesEl.appendChild(prefixEl)

        datatypesEl = self.getDomElement('datatypes')
        ontologyEl.appendChild(datatypesEl)
        for dtIri in sorted(self.project.getDatatypeIRIs(),key=str):
            datatypeEl = self.getDomElement('datatype')
            datatypeEl.appendChild(self.getDomTextNode(str(dtIri)))
            datatypesEl.appendChild(datatypeEl)

        languagesEl = self.getDomElement('languages')
        ontologyEl.appendChild(languagesEl)
        for lang in sorted(self.project.getLanguages(),key=str):
            langEl = self.getDomElement('language')
            langEl.appendChild(self.getDomTextNode(lang))
            languagesEl.appendChild(langEl)

        facetsEl = self.getDomElement('facets')
        ontologyEl.appendChild(facetsEl)
        for facetIri in sorted(self.project.constrainingFacets,key=str):
            facetEl = self.getDomElement('facet')
            facetEl.appendChild(self.getDomTextNode(str(facetIri)))
            facetsEl.appendChild(facetEl)

        annotationPropertiesEl = self.getDomElement('annotationProperties')
        ontologyEl.appendChild(annotationPropertiesEl)
        for annIri in sorted(self.project.getAnnotationPropertyIRIs(),key=str):
            annotationPropertyEl = self.getDomElement('annotationProperty')
            annotationPropertyEl.appendChild(self.getDomTextNode(str(annIri)))
            annotationPropertiesEl.appendChild(annotationPropertyEl)

        irisEl = self.getDomElement('iris')
        ontologyEl.appendChild(irisEl)
        for iri in sorted(self.project.iris, key=str):
            iriEl = self.getIriDomElement(iri)
            irisEl.appendChild(iriEl)
        return ontologyEl

    def getOntologyImportDomElement(self, impOnt):
        impEl = self.getDomElement('import')
        impEl.setAttribute('iri',  impOnt.ontologyIRI)
        impEl.setAttribute('version', impOnt.versionIRI)
        impEl.setAttribute('location', impOnt.docLocation)
        localBoolean = 0
        if impOnt.isLocalDocument:
            localBoolean = 1
        impEl.setAttribute('isLocal', localBoolean)
        return impEl

    def getIriDomElement(self,iri):
        iriEl = self.getDomElement('iri')

        valueEl = self.getDomElement('value')
        valueEl.appendChild(self.getDomTextNode(str(iri)))
        iriEl.appendChild(valueEl)

        functionalEl = self.getDomElement('functional')
        if iri.functional:
            iriEl.appendChild(functionalEl)

        inverseFunctionalEl = self.getDomElement('inverseFunctional')
        if iri.inverseFunctional:
            iriEl.appendChild(inverseFunctionalEl)

        symmetricEl = self.getDomElement('symmetric')
        if iri.symmetric:
            iriEl.appendChild(symmetricEl)

        asymmetricEl = self.getDomElement('asymmetric')
        if iri.asymmetric:
            iriEl.appendChild(asymmetricEl)

        reflexiveEl = self.getDomElement('reflexive')
        if iri.reflexive:
            iriEl.appendChild(reflexiveEl)

        irreflexiveEl = self.getDomElement('irreflexive')
        if iri.irreflexive:
            iriEl.appendChild(irreflexiveEl)

        transitiveEl = self.getDomElement('transitive')
        if iri.transitive:
            iriEl.appendChild(transitiveEl)

        if iri.annotationAssertions:
            annotationsEl = self.getDomElement('annotations')
            iriEl.appendChild(annotationsEl)
            for annotation in iri.annotationAssertions:
                annotationEl = self.getAnnotationAssertionDomElement(annotation)
                annotationsEl.appendChild(annotationEl)

        return iriEl

    def getAnnotationAssertionDomElement(self, annotation):
        annotationEl = self.getDomElement('annotation')

        subjectEl = self.getDomElement('subject')
        subjectEl.appendChild(self.getDomTextNode(str(annotation.subject)))
        annotationEl.appendChild(subjectEl)

        propertyEl = self.getDomElement('property')
        propertyEl.appendChild(self.getDomTextNode(str(annotation.assertionProperty)))
        annotationEl.appendChild(propertyEl)

        objectEl = self.getDomElement('object')
        if annotation.isIRIValued():
            objecIriEl = self.getDomElement('iri')
            objecIriEl.appendChild(self.getDomTextNode(str(annotation.value)))
            objectEl.appendChild(objecIriEl)
        else:
            lexicalFormEl = self.getDomElement('lexicalForm')
            lexicalFormEl.appendChild(self.getDomTextNode(str(annotation.value)))
            objectEl.appendChild(lexicalFormEl)

            datatypeEl = self.getDomElement('datatype')
            if annotation.datatype:
                datatypeEl.appendChild(self.getDomTextNode(str(annotation.datatype)))
            objectEl.appendChild(datatypeEl)

            languageEl = self.getDomElement('language')
            if annotation.language:
                languageEl.appendChild(self.getDomTextNode(str(annotation.language)))
            objectEl.appendChild(languageEl)
        annotationEl.appendChild(objectEl)

        return annotationEl

    def getAnnotationDomElement(self, annotation):
        annotationEl = self.getDomElement('annotation')

        propertyEl = self.getDomElement('property')
        propertyEl.appendChild(self.getDomTextNode(str(annotation.assertionProperty)))
        annotationEl.appendChild(propertyEl)

        objectEl = self.getDomElement('object')
        if annotation.isIRIValued():
            objecIriEl = self.getDomElement('iri')
            objecIriEl.appendChild(self.getDomTextNode(str(annotation.value)))
        else:
            lexicalFormEl = self.getDomElement('lexicalForm')
            lexicalFormEl.appendChild(self.getDomTextNode(str(annotation.value)))
            objectEl.appendChild(lexicalFormEl)

            datatypeEl = self.getDomElement('datatype')
            if annotation.datatype:
                datatypeEl.appendChild(self.getDomTextNode(str(annotation.datatype)))
            objectEl.appendChild(datatypeEl)

            languageEl = self.getDomElement('language')
            if annotation.language:
                languageEl.appendChild(self.getDomTextNode(str(annotation.language)))
            objectEl.appendChild(languageEl)
        annotationEl.appendChild(objectEl)

        return annotationEl

    def getLiteralDomElement(self, literal):
        literalEl = self.getDomElement('literal')

        lexicalFormEl = self.getDomElement('lexicalForm')
        lexicalFormEl.appendChild(self.getDomTextNode(str(literal.lexicalForm)))
        literalEl.appendChild(lexicalFormEl)

        datatypeEl = self.getDomElement('datatype')
        if literal.datatype:
            datatypeEl.appendChild(self.getDomTextNode(str(literal.datatype)))
        literalEl.appendChild(datatypeEl)

        languageEl = self.getDomElement('language')
        if literal.language:
            languageEl.appendChild(self.getDomTextNode(str(literal.language)))
        literalEl.appendChild(languageEl)

        return literalEl

    def getFacetDomElement(self, facetNode):
        facetEl = self.getDomElement('facet')
        constrainingFacetEl = self.getDomElement('constrainingFacet')
        constrainingFacetEl.appendChild(self.getDomTextNode(str(facetNode.facet.constrainingFacet)))
        facetEl.appendChild(constrainingFacetEl)
        facetEl.appendChild(self.getLiteralDomElement(facetNode.facet.literal))
        return facetEl

    def getDiagramsDomElement(self):
        diagramsEl = self.getDomElement('diagrams')
        if self.selectedDiagrams:
            currSet = self.selectedDiagrams
        else:
            currSet = self.project.diagrams()
        for diagram in sorted(currSet,key=str):
            diagramsEl.appendChild(self.getDiagramDomElement(diagram))
        return diagramsEl

    def getDiagramDomElement(self,diagram):
        diagramEl = self.getDomElement('diagram')
        diagramEl.setAttribute('name', diagram.name)
        diagramEl.setAttribute('width', int(diagram.width()))
        diagramEl.setAttribute('height', int(diagram.height()))
        for node in sorted(diagram.nodes(), key=lambda n:n.id):
            func = self.exportFuncForItem[node.type()]
            diagramEl.appendChild(func(node))
        for edge in sorted(diagram.edges(), key=lambda n:n.id):
            func = self.exportFuncForItem[edge.type()]
            diagramEl.appendChild(func(edge))
        return diagramEl

    #############################################
    #   ONTOLOGY DIAGRAMS EXPORT : NODES
    #################################

    def exportAttributeNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AttributeNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        iriEl = self.getDomElement('iri')
        iriEl.appendChild(self.getDomTextNode(str(node.iri)))
        nodeEl.appendChild(iriEl)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportComplementNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ComplementNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportConceptNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ConceptNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        iriEl = self.getDomElement('iri')
        iriEl.appendChild(self.getDomTextNode(str(node.iri)))
        nodeEl.appendChild(iriEl)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportDatatypeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DatatypeRestrictionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportDisjointUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DisjointUnionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        #labelEl = self.getLabelDomElement(node)
        #nodeEl.appendChild(labelEl)
        return nodeEl

    def exportDomainRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DomainRestrictionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node, labelText=True)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportEnumerationNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: EnumerationNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportFacetNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: FacetNode
        :rtype: QDomElement
        """
        #TODO
        nodeEl = self.getNodeDomElement(node)

        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', int(node.labelA.height()))
        label.setAttribute('width', int(node.labelA.width() + node.labelB.width()))
        label.setAttribute('x', int(position.x()))
        label.setAttribute('y', int(position.y()))
        label.appendChild(self.document.createTextNode(node.text()))
        nodeEl.appendChild(label)
        element = self.getFacetDomElement(node)
        nodeEl.appendChild(element)
        return nodeEl

    def exportIndividualNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IndividualNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        iriEl = self.getDomElement('iri')
        iriEl.appendChild(self.getDomTextNode(str(node.iri)))
        nodeEl.appendChild(iriEl)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportLiteralNode(self,node):
        """
        Export the given node into a QDomElement.
         :type node: LiteralNode
         :rtype: QDomElement
         """
        nodeEl = self.getNodeDomElement(node)
        nodeEl.appendChild(self.getLiteralDomElement(node.literal))
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportIntersectionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IntersectionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportPropertyAssertionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: PropertyAssertionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        nodeEl.setAttribute('inputs', ','.join(node.inputs))
        return nodeEl

    def exportRangeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RangeRestrictionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node, labelText=True)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportRoleNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        iriEl = self.getDomElement('iri')
        iriEl.appendChild(self.getDomTextNode(str(node.iri)))
        nodeEl.appendChild(iriEl)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportRoleChainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleChainNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        nodeEl.setAttribute('inputs', ','.join(node.inputs))
        return nodeEl

    def exportRoleInverseNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleInverseNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportValueDomainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ValueDomainNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        iriEl = self.getDomElement('iri')
        iriEl.appendChild(self.getDomTextNode(str(node.iri)))
        nodeEl.appendChild(iriEl)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: UnionNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        return nodeEl

    def exportHasKeyNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: HasKeyNode
        :rtype: QDomElement
        """
        nodeEl = self.getNodeDomElement(node)
        labelEl = self.getLabelDomElement(node)
        nodeEl.appendChild(labelEl)
        nodeEl.setAttribute('inputs', ','.join(node.inputs))
        return nodeEl


    #############################################
    #   ONTOLOGY DIAGRAMS EXPORT : EDGES
    #################################

    def exportInclusionEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InclusionEdge
        :rtype: QDomElement
        """
        return self.exportAxiomEdge(edge)

    def exportEquivalenceEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: EquivalenceEdge
        :rtype: QDomElement
        """
        return self.exportAxiomEdge(edge)

    def exportInputEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InputEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    def exportMembershipEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: MembershipEdge
        :rtype: QDomElement
        """
        return self.exportAxiomEdge(edge)

    def exportSameEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: SameEdge
        :rtype: QDomElement
        """
        return self.exportAxiomEdge(edge)

    def exportDifferentEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: DifferentEdge
        :rtype: QDomElement
        """
        return self.exportAxiomEdge(edge)

    #############################################
    #   ONTOLOGY DIAGRAMS EXPORT : GENERICS
    #################################

    def getLabelDomElement(self, node, labelText=False):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', int(node.label.height()))
        label.setAttribute('width', int(node.label.width()))
        label.setAttribute('x', int(position.x()))
        label.setAttribute('y', int(position.y()))
        label.setAttribute('customSize', 1 if node.label.customFont else 0)
        label.setAttribute('size', node.label.font().pixelSize())
        if labelText:
            label.appendChild(self.getDomTextNode(node.text()))
        return label

    def exportGenericEdge(self, edge):
        """
        Export the given node into a QDomElement.
        :type edge: AbstractEdge
        :rtype: QDomElement
        """
        element = self.document.createElement('edge')
        element.setAttribute('source', edge.source.id)
        element.setAttribute('target', edge.target.id)
        element.setAttribute('id', edge.id)
        element.setAttribute('type', self.itemToXml[edge.type()])

        for p in [edge.source.anchor(edge)] + edge.breakpoints + [edge.target.anchor(edge)]:
            point = self.document.createElement('point')
            point.setAttribute('x', int(p.x()))
            point.setAttribute('y', int(p.y()))
            element.appendChild(point)
        return element

    def exportAxiomEdge(self, edge):
        """
        Export the given node into a QDomElement.
        :type edge: AxiomEdge
        :rtype: QDomElement
        """
        element = self.exportGenericEdge(edge)
        if edge.annotations:
            annSetEl = self.document.createElement('annotations')
            element.appendChild(annSetEl)
            for annotation in edge.annotations:
                annotationEl = self.getAnnotationDomElement(annotation)
                annSetEl.appendChild(annotationEl)
        return element

    def getNodeDomElement(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        element = self.document.createElement('node')
        element.setAttribute('id', node.id)
        element.setAttribute('type', self.itemToXml[node.type()])
        element.setAttribute('color', node.brush().color().name())
        geometry = self.document.createElement('geometry')
        geometry.setAttribute('height', int(node.height()))
        geometry.setAttribute('width', int(node.width()))
        geometry.setAttribute('x', int(node.pos().x()))
        geometry.setAttribute('y', int(node.pos().y()))
        element.appendChild(geometry)
        return element

    #############################################
    #   INTERFACE
    #################################

    def createProjectFile(self):
        """
        Serialize a previously created QDomDocument to disk.
        """
        try:
            currPath = self.exportPath if self.exportPath else self.project.path
            if not fexists(currPath):
                folderPath = os.path.dirname(currPath)
                if not isdir(folderPath):
                    mkdir(folderPath)
                fd = os.open(currPath,os.O_CREAT)
                os.close(fd)
            #TODO filename = postfix(self.project.name, File.Graphol.extension)
            #TODO filepath = os.path.join(self.project.path, filename)
            #TODO fwrite(self.document.toString(2), filepath)
            fwrite(self.document.toString(2), currPath)
        except Exception as e:
            raise e
        else:
            LOGGER.info('Saved project %s to %s', self.project.name, currPath)

    def getDomElement(self,elName):
        return self.document.createElement(elName)

    def getDomTextNode(self, text):
        return self.document.createTextNode(text)

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Graphol

    def run(self, *args, **kwargs):
        """
        Perform Project export to disk.
        """
        # DIAGRAM SELECTION
        if self.selectDiagrams:
            dialog = DiagramSelectionDialog(self.session)
            if not dialog.exec_():
                return
            self.selectedDiagrams = dialog.selectedDiagrams()
            if not self.selectedDiagrams:
                return

        self.createDomDocument()
        #self.createOntology()
        #self.createDiagrams()
        self.createProjectFile()
