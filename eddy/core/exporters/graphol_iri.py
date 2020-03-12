import os

from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.fsystem import mkdir, fwrite
from eddy.core.functions.misc import postfix
from eddy.core.output import getLogger

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

    def __init__(self, project, session=None):
        """
        Initialize the project exporter.
        :type project: Project
        :type session: Session
        """
        super().__init__(project, session)

        self.document = None

        self.itemToXml = {
            Item.AttributeIRINode: 'attribute',
            Item.ComplementNode: 'complement',
            Item.ConceptIRINode: 'concept',
            Item.DatatypeRestrictionNode: 'datatype-restriction',
            Item.DisjointUnionNode: 'disjoint-union',
            Item.DomainRestrictionNode: 'domain-restriction',
            Item.EnumerationNode: 'enumeration',
            Item.FacetIRINode: 'facet',
            Item.IndividualIRINode: 'individual',
            Item.LiteralNode: 'literal',
            Item.IntersectionNode: 'intersection',
            Item.PropertyAssertionNode: 'property-assertion',
            Item.RangeRestrictionNode: 'range-restriction',
            Item.RoleIRINode: 'role',
            Item.RoleChainNode: 'role-chain',
            Item.RoleInverseNode: 'role-inverse',
            Item.UnionNode: 'union',
            Item.ValueDomainIRINode: 'value-domain',
            Item.InclusionEdge: 'inclusion',
            Item.EquivalenceEdge: 'equivalence',
            Item.InputEdge: 'input',
            Item.MembershipEdge: 'membership',
            Item.SameEdge: 'same',
            Item.DifferentEdge: 'different',
        }

        self.exportFuncForItem = {
            Item.AttributeIRINode: self.exportAttributeNode,
            Item.ComplementNode: self.exportComplementNode,
            Item.ConceptIRINode: self.exportConceptNode,
            Item.DatatypeRestrictionNode: self.exportDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.exportDisjointUnionNode,
            Item.DomainRestrictionNode: self.exportDomainRestrictionNode,
            Item.EnumerationNode: self.exportEnumerationNode,
            Item.FacetIRINode: self.exportFacetNode,
            Item.IndividualIRINode: self.exportIndividualNode,
            Item.LiteralNode: self.exportLiteralNode,
            Item.IntersectionNode: self.exportIntersectionNode,
            Item.PropertyAssertionNode: self.exportPropertyAssertionNode,
            Item.RangeRestrictionNode: self.exportRangeRestrictionNode,
            Item.RoleIRINode: self.exportRoleNode,
            Item.RoleChainNode: self.exportRoleChainNode,
            Item.RoleInverseNode: self.exportRoleInverseNode,
            Item.UnionNode: self.exportUnionNode,
            Item.ValueDomainIRINode: self.exportValueDomainNode,
            Item.InclusionEdge: self.exportInclusionEdge,
            Item.EquivalenceEdge: self.exportEquivalenceEdge,
            Item.InputEdge: self.exportInputEdge,
            Item.MembershipEdge: self.exportMembershipEdge,
            Item.SameEdge: self.exportSameEdge,
            Item.DifferentEdge: self.exportDifferentEdge,
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

        prefixesEl = self.getDomElement('prefixes')
        ontologyEl.appendChild(prefixesEl)
        for prefix,ns in self.project.prefixDictItems():
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
        for dtIri in self.project.getDatatypeIRIs():
            datatypeEl = self.getDomElement('datatype')
            datatypeEl.appendChild(self.getDomTextNode(str(dtIri)))
            datatypesEl.appendChild(datatypeEl)

        languagesEl = self.getDomElement('languages')
        ontologyEl.appendChild(languagesEl)
        for lang in self.project.getLanguages():
            langEl = self.getDomElement('language')
            langEl.appendChild(self.getDomTextNode(lang))
            languagesEl.appendChild(langEl)

        facetsEl = self.getDomElement('facets')
        ontologyEl.appendChild(facetsEl)
        for facetIri in self.project.constrainingFacets:
            facetEl = self.getDomElement('facet')
            facetEl.appendChild(self.getDomTextNode(str(facetIri)))
            facetsEl.appendChild(facetEl)

        annotationPropertiesEl = self.getDomElement('annotationProperties')
        ontologyEl.appendChild(annotationPropertiesEl)
        for annIri in self.project.getAnnotationPropertyIRIs():
            annotationPropertyEl = self.getDomElement('annotationProperty')
            annotationPropertyEl.appendChild(self.getDomTextNode(str(annIri)))
            annotationPropertiesEl.appendChild(annotationPropertyEl)

        irisEl = self.getDomElement('iris')
        ontologyEl.appendChild(irisEl)
        for iri in self.project.iris:
            iriEl = self.getIriDomElement(iri)
            irisEl.appendChild(iriEl)

        return ontologyEl

    def getIriDomElement(self,iri):
        iriEl = self.getDomElement('iri')

        valueEl = self.getDomElement('value')
        valueEl.appendChild(self.getDomTextNode(str(iri)))
        iriEl.appendChild(valueEl)

        functionalEl = self.getDomElement('functional')
        if iri.functional:
            functionalEl.appendChild(self.getDomTextNode('1'))
        else:
            functionalEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(functionalEl)

        inverseFunctionalEl = self.getDomElement('inverseFunctional')
        if iri.inverseFunctional:
            inverseFunctionalEl.appendChild(self.getDomTextNode('1'))
        else:
            inverseFunctionalEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(inverseFunctionalEl)

        symmetricEl = self.getDomElement('symmetric')
        if iri.symmetric:
            symmetricEl.appendChild(self.getDomTextNode('1'))
        else:
            symmetricEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(symmetricEl)

        asymmetricEl = self.getDomElement('asymmetric')
        if iri.asymmetric:
            asymmetricEl.appendChild(self.getDomTextNode('1'))
        else:
            asymmetricEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(asymmetricEl)

        reflexiveEl = self.getDomElement('reflexive')
        if iri.reflexive:
            reflexiveEl.appendChild(self.getDomTextNode('1'))
        else:
            reflexiveEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(reflexiveEl)

        irreflexiveEl = self.getDomElement('irreflexive')
        if iri.irreflexive:
            irreflexiveEl.appendChild(self.getDomTextNode('1'))
        else:
            irreflexiveEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(irreflexiveEl)

        transitiveEl = self.getDomElement('transitive')
        if iri.transitive:
            transitiveEl.appendChild(self.getDomTextNode('1'))
        else:
            transitiveEl.appendChild(self.getDomTextNode('0'))
        iriEl.appendChild(transitiveEl)

        annotationsEl = self.getDomElement('annotations')
        iriEl.appendChild(annotationsEl)
        for annotation in iri.annotationAssertions:
            annotationEl = self.getAnnotationDomElement(annotation)
            annotationsEl.appendChild(annotationEl)

        return iriEl

    def getAnnotationDomElement(self, annotation):
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

    def getFacetDomElement(self, facet):
        facetEl = self.getDomElement('facet')
        constrainingFacetEl = self.getDomElement('constrainingFacet')
        constrainingFacetEl.appendChild(self.getDomTextNode(str(facet.constrainingFacet)))
        facetEl.appendChild(constrainingFacetEl)
        facetEl.appendChild(self.getLiteralDomElement(facet.literal))
        return facetEl

    def getDiagramsDomElement(self):
        diagramsEl = self.getDomElement('diagrams')
        for diagram in self.project.diagrams():
            diagramsEl.appendChild(self.getDiagramDomElement(diagram))
        return diagramsEl

    def getDiagramDomElement(self,diagram):
        diagramEl = self.getDomElement('diagram')
        diagramEl.setAttribute('name', diagram.name)
        diagramEl.setAttribute('width', diagram.width())
        diagramEl.setAttribute('height', diagram.height())
        for node in diagram.nodes():
            func = self.exportFuncForItem[node.type()]
            diagramEl.appendChild(func(node))
        for edge in diagram.edges():
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
        labelEl = self.getLabelDomElement(node)
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
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', node.labelA.height())
        label.setAttribute('width', node.labelA.width() + node.labelB.width())
        label.setAttribute('x', position.x())
        label.setAttribute('y', position.y())
        label.appendChild(self.document.createTextNode(node.text()))
        element = self.getFacetDomElement(node)
        element.appendChild(label)
        return element

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
        labelEl = self.getLabelDomElement(node)
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

    #############################################
    #   ONTOLOGY DIAGRAMS EXPORT : EDGES
    #################################

    def exportInclusionEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InclusionEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    def exportEquivalenceEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: EquivalenceEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

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
        return self.exportGenericEdge(edge)

    def exportSameEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: SameEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    def exportDifferentEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: DifferentEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    #############################################
    #   ONTOLOGY DIAGRAMS EXPORT : GENERICS
    #################################

    def getLabelDomElement(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', node.label.height())
        label.setAttribute('width', node.label.width())
        label.setAttribute('x', position.x())
        label.setAttribute('y', position.y())
        #label.appendChild(self.document.createTextNode(node.text()))
        #element = self.getNodeDomElement(node)
        #element.appendChild(label)
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
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            element.appendChild(point)

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
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', node.pos().x())
        geometry.setAttribute('y', node.pos().y())
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
            mkdir(self.project.path)
            filename = postfix(self.project.name, File.Graphol.extension)
            filepath = os.path.join(self.project.path, filename)
            fwrite(self.document.toString(2), filepath)
        except Exception as e:
            raise e
        else:
            LOGGER.info('Saved project %s to %s', self.project.name, self.project.path)

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
        self.createDomDocument()
        #self.createOntology()
        #self.createDiagrams()
        self.createProjectFile()