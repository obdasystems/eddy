
import os
import textwrap
from time import time

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtXml

from eddy import APPNAME
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Namespace
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.diagram import DiagramNotFoundError
from eddy.core.diagram import DiagramNotValidError
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.functions.fsystem import fread, fexists, isdir, rmdir, make_archive
from eddy.core.functions.misc import rstrip, postfix, rtfStripFontAttributes
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.output import getLogger
from eddy.core.owl import Literal, Facet, AnnotationAssertion
from eddy.core.project import Project
from eddy.core.project import ProjectMergeWorker
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectVersionError
from eddy.core.project import ProjectStopLoadingError
from eddy.core.project import K_DESCRIPTION
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_ASYMMETRIC, K_IRREFLEXIVE, K_REFLEXIVE
from eddy.core.project import K_SYMMETRIC, K_TRANSITIVE

LOGGER = getLogger()

class GrapholIRILoaderMixin_2(object):
    """
    Mixin which adds the ability to create a project out of a Graphol file.
    """

    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)

        self.buffer = dict()
        self.document = None
        self.nproject = None

        self.itemFromXml = {
            'attribute': Item.AttributeIRINode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptIRINode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetIRINode,
            'individual': Item.IndividualIRINode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleIRINode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainIRINode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'membership': Item.MembershipEdge,
            'same': Item.SameEdge,
            'different': Item.DifferentEdge,
        }

        self.importFuncForItem = {
            Item.AttributeIRINode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptIRINode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetIRINode: self.importFacetNode,
            Item.IndividualIRINode: self.importIndividualNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleIRINode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainIRINode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
            Item.SameEdge: self.importSameEdge,
            Item.DifferentEdge: self.importDifferentEdge,
        }

        self.importMetaFuncForItem = {
            Item.AttributeIRINode: self.importAttributeMeta,
            Item.ConceptIRINode: self.importConceptMeta,
            Item.IndividualIRINode: self.importIndividualMeta,
            Item.RoleIRINode: self.importRoleMeta,
        }

    #############################################
    #   DOCUMENT (Prefixes,OntologyIRI)
    #################################
    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse Project information.
        """
        if not fexists(self.path):
            raise ProjectNotFoundError('missing project ontology: %s' % self.path)
        self.document = QtXml.QDomDocument()
        if File.forPath(self.path) is not File.Graphol or not self.document.setContent(fread(self.path)):
            raise ProjectNotValidError('invalid project ontology supplied: %s' % self.path)
        e = self.document.documentElement()
        version = int(e.attribute('version', '2'))
        if version != 2:
            raise ProjectVersionError('project version mismatch: %s != 2' % version)

    #############################################
    #   PROJECT (Prefixes,OntologyIRI)
    #################################
    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('ontology')

        def parse(tag, default='NULL'):
            """
            Read an element from the given tag.
            :type tag: str
            :type default: str
            :rtype: str
            """
            QtWidgets.QApplication.processEvents()
            subelement = section.firstChildElement(tag)
            if subelement.isNull():
                LOGGER.warning('Missing tag <%s> in ontology section, using default: %s', tag, default)
                return default
            content = subelement.text()
            if (not content):
                LOGGER.warning('Empty tag <%s> in ontology section, using default: %s', tag, default)
                return default
            LOGGER.debug('Loaded ontology %s: %s', tag, content)
            return content

        self.nproject = Project(
            name=parse(tag='name', default=rstrip(os.path.basename(self.path), File.Graphol.extension)),
            path=os.path.dirname(self.path),
            version=parse(tag='version', default='1.0'),
            profile=self.session.createProfile(parse('profile', 'OWL 2')),
            prefixMap=self.getPrefixesDict(section),
            ontologyIRI=self.getOntologyIRI(section),
            session=self.session)
        LOGGER.info('Loaded ontology: %s...', self.nproject.name)

    def getOntologyIRI(self, ontologySection):
        result = ''
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        sube = e.firstChildElement('iri')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                namespace = sube.attribute('iri_value')
                sube_properties = sube.firstChildElement('properties')
                sube_property = sube_properties.firstChildElement('property')
                while not sube_property.isNull():
                    try:
                        QtWidgets.QApplication.processEvents()
                        property_value = sube_property.attribute('property_value')
                    except Exception:
                        LOGGER.exception('Failed to fetch property %s', property_value)
                    else:
                        if property_value == 'Project_IRI':
                            return namespace
                    finally:
                        sube_property = sube_property.nextSiblingElement('property')
            except Exception:
                LOGGER.exception('Failed to fetch namespace  %s', namespace)
            finally:
                sube = sube.nextSiblingElement('iri')
        return result

    def getPrefixesDict(self, ontologySection):
        dictionary_to_return = dict()
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        sube = e.firstChildElement('iri')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                namespace = sube.attribute('iri_value')

                ### Needed to fix the namespace of standard vocabularies which up to
                ### version 1.1.2 where stored without the fragment separator (#).
                ### See: https://github.com/obdasystems/eddy/issues/20
                for ns in Namespace:
                    if postfix(namespace, '#') == ns.value:
                        # Append the missing fragment separator
                        namespace += '#'
                        break

                sube_prefixes = sube.firstChildElement('prefixes')

                #PREFIX MAP
                sube_prefix = sube_prefixes.firstChildElement('prefix')
                while not sube_prefix.isNull():
                    try:
                        QtWidgets.QApplication.processEvents()
                        prefix_value = sube_prefix.attribute('prefix_value')
                    except Exception:
                        LOGGER.exception('Failed to fetch prefixes %s', prefix_value)
                    else:
                        dictionary_to_return[prefix_value]=namespace
                    finally:
                        sube_prefix = sube_prefix.nextSiblingElement('prefix')
            except Exception:
                LOGGER.exception('Failed to fetch namespace  %s', namespace)
            finally:
                sube = sube.nextSiblingElement('iri')
        return dictionary_to_return

    def projectRender(self):
        """
        Render all the elements in the Project ontology.
        """
        for item in self.nproject.items():
            QtWidgets.QApplication.processEvents()
            item.updateEdgeOrNode()

    #############################################
    #   DIAGRAM
    #################################
    def createDiagrams(self):
        """
        Create ontology diagrams by parsing the 'diagrams' section of the QDomDocument.
        """
        counter = 1
        section = self.document.documentElement().firstChildElement('diagrams')
        element = section.firstChildElement('diagram')
        while not element.isNull():
            self.nproject.addDiagram(self.importDiagram(element, counter))
            element = element.nextSiblingElement('diagram')
            counter += 1

    def importDiagram(self, diagramElement, i):
        """
        Create a diagram from the given QDomElement.
        :type e: QDomElement
        :type i: int
        :rtype: Diagram
        """
        QtWidgets.QApplication.processEvents()
        ## PARSE DIAGRAM INFORMATION
        name = diagramElement.attribute('name', 'diagram_{0}'.format(i))
        size = max(int(diagramElement.attribute('width', '10000')), int(diagramElement.attribute('height', '10000')))
        ## CREATE NEW DIAGRAM
        LOGGER.info('Loading diagram: %s', name)
        diagram = Diagram.create(name, size, self.nproject)
        self.buffer[diagram.name] = dict()
        ## LOAD DIAGRAM NODES
        nodeElement = diagramElement.firstChildElement('node')
        while not nodeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(nodeElement)
                func = self.importFuncForItem[item]
                node = func(diagram,nodeElement)
            except Exception as e:
                LOGGER.exception('Failed to create node {}. [{}]'.format(nodeElement.attribute('id'),e))
            else:
                diagram.addItem(node)
                diagram.guid.update(node.id)
                self.buffer[diagram.name][node.id] = node
            finally:
                nodeElement = nodeElement.nextSiblingElement('node')
        
        ## LOAD DIAGRAM EDGES
        edgeElement = diagramElement.firstChildElement('edge')
        while not edgeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(edgeElement)
                func = self.importFuncForItem[item]
                edge = func(diagram, edgeElement)
            except Exception as e:
                LOGGER.exception('Failed to create edge {}. [{}]'.format(edgeElement.attribute('id'),e))
            else:
                diagram.addItem(edge)
                diagram.guid.update(edge.id)
                self.buffer[diagram.name][edge.id] = edge
            finally:
                edgeElement = edgeElement.nextSiblingElement('edge')
        ## IDENTIFY NEUTRAL NODES
        nodes = [x for x in diagram.items(edges=False) if Identity.Neutral in x.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                diagram.sgnNodeIdentification.emit(node)
        ## CONFIGURE DIAGRAM SIGNALS
        connect(diagram.sgnItemAdded, self.nproject.doAddItem)
        connect(diagram.sgnItemRemoved, self.nproject.doRemoveItem)
        connect(diagram.selectionChanged, self.session.doUpdateState)
        ## RETURN GENERATED DIAGRAM
        return diagram

    #############################################
    #   IRI META
    #################################
    def createPredicatesMeta(self):
        """
        Create ontology predicate metadata by parsing the 'predicates' section of the QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('predicates')
        predicateElement = section.firstChildElement('predicate')
        while not predicateElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()

                prefixedIriString = predicateElement.attribute('name')
                iriElList = prefixedIriString.split(':')
                if len(iriElList) > 1:
                    prefix = iriElList[0]
                    namespace = iriElList[1]
                    iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), namespace)
                elif len(iriElList) == 1:
                    iriString = iriElList[0]
                else:
                    iriString = prefixedIriString
                predicateIRI = self.nproject.getIRI(iriString)

                value = rtfStripFontAttributes(predicateElement.firstChildElement(K_DESCRIPTION).text())
                if value:
                    commentIRI = self.nproject.getIRI('http://www.w3.org/2000/01/rdf-schema#comment')
                    annAss = AnnotationAssertion(predicateIRI,commentIRI,value)
                    predicateIRI.addAnnotationAssertion(annAss)

                item = self.itemFromXml[predicateElement.attribute('type')]
                func = self.importMetaFuncForItem[item]
                func(predicateElement,predicateIRI)
            except Exception as e:
                LOGGER.exception('Failed to import meta for predicate {}. [{}]'.format(predicateElement.attribute('name'),e))
            finally:
                predicateElement = predicateElement.nextSiblingElement('predicate')

    def importAttributeMeta(self, predicateElement, iri):
        boolValue = bool(int(predicateElement.firstChildElement(K_FUNCTIONAL).text()))
        iri.functional = boolValue

    def importConceptMeta(self, predicateElement, iri):
        pass

    def importIndividualMeta(self, predicateElement, iri):
        pass

    def importRoleMeta(self, predicateElement, iri):
        boolValue = bool(int(predicateElement.firstChildElement(K_FUNCTIONAL).text()))
        iri.functional = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_INVERSE_FUNCTIONAL).text()))
        iri.inverseFunctional = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_ASYMMETRIC).text()))
        iri.asymmetric = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_IRREFLEXIVE).text()))
        iri.irreflexive = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_REFLEXIVE).text()))
        iri.reflexive = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_SYMMETRIC).text()))
        iri.symmetric = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_TRANSITIVE).text()))
        iri.transitive = boolValue

    #############################################
    #   NODES
    #################################
    def getIriFromLabelText(self,labelText, itemType):
        iriString = ''
        if labelText == 'TOP':
            if itemType is Item.AttributeIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#topDataProperty'
            if itemType is Item.RoleIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#topObjectProperty'
            if itemType is Item.ConceptIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#Thing'
        elif labelText == 'BOTTOM':
            if itemType is Item.AttributeIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomDataProperty'
            if itemType is Item.RoleIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomObjectProperty'
            if itemType is Item.ConceptIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#Nothing'
        iriElList = labelText.split(':')
        if len(iriElList) > 1:
            prefix = iriElList[0]
            namespace = iriElList[1]
            iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), namespace)
        elif len(iriElList) == 1:
            iriString = iriElList[0]
        else:
            iriString = labelText
        iri = self.nproject.getIRI(iriString)
        return iri

    def getIriPredicateNode(self, diagram, nodeElement, itemType):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        iri = self.getIriFromLabelText(labelText,itemType)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(itemType, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'iri': iri
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importAttributeNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.AttributeIRINode)

    def importRoleNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.RoleIRINode)

    def importConceptNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ConceptIRINode)

    def importIndividualNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        doubleQuote = '"'
        if doubleQuote in labelText:
            return self.importLiteralNode(diagram, nodeElement)
        return self.getIriPredicateNode(diagram, nodeElement, Item.IndividualIRINode)

    def importValueDomainNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ValueDomainIRINode)

    def importLiteralNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        firstQuote = labelText.find('"')
        secondQuote = labelText.rfind('"')
        lexForm = labelText[firstQuote+1:secondQuote]
        typeIndex = labelText.rfind('^')
        prefixedType = labelText[typeIndex+1:]
        colonIndex = prefixedType.find(':')
        prefix = prefixedType[:colonIndex]
        ns = prefixedType[colonIndex+1:]
        iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), ns)
        dtIRI = self.nproject.getIRI(iriString)
        literal = Literal(lexForm,dtIRI)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.LiteralNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'literal': literal
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importFacetNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        firstQuote = labelText.find('"')
        secondQuote = labelText.rfind('"')
        lexForm = labelText[firstQuote + 1:secondQuote]
        literal = Literal(lexForm)
        typeIndex = labelText.find('^')
        prefixedType = labelText[:typeIndex]
        colonIndex = prefixedType.find(':')
        prefix = prefixedType[:colonIndex]
        ns = prefixedType[colonIndex + 1:]
        iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), ns)
        conFacetIRI = self.nproject.getIRI(iriString)
        facet = Facet(conFacetIRI,literal)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.FacetIRINode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'facet': facet
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importComplementNode(self, diagram, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(diagram, Item.ComplementNode, e)

    def importDatatypeRestrictionNode(self, diagram, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(diagram, Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, diagram, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(diagram, Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, diagram, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, diagram, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(diagram, Item.EnumerationNode, e)

    def importIntersectionNode(self, diagram, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(diagram, Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, diagram, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, diagram, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, diagram, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, diagram, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(diagram, Item.RoleInverseNode, e)

    def importUnionNode(self, diagram, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(diagram, Item.UnionNode, e)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, d, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(d, Item.EquivalenceEdge, e)

    def importInclusionEdge(self, d, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        return self.importGenericEdge(d, Item.InclusionEdge, e)

    def importInputEdge(self, d, e):
        """
        Build an Input edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(d, Item.InputEdge, e)

    def importMembershipEdge(self, d, e):
        """
        Build a Membership edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(d, Item.MembershipEdge, e)

    def importSameEdge(self, d, e):
        """
        Build a Same edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: SameEdge
        """
        return self.importGenericEdge(d, Item.SameEdge, e)

    def importDifferentEdge(self, d, e):
        """
        Build a Different edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DifferentEdge
        """
        return self.importGenericEdge(d, Item.DifferentEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def itemFromXmlNode(self, e):
        """
        Returns the item matching the given Graphol XML node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    def importGenericEdge(self, d, i, e):
        """
        Build an edge using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = e.firstChildElement('point')
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = point.nextSiblingElement('point')

        source = self.buffer[d.name][e.attribute('source')]
        target = self.buffer[d.name][e.attribute('target')]
        edge = d.factory.create(i, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1]
                            if not (source.painterPath().contains(source.mapFromScene(p)) or
                                    target.painterPath().contains(target.mapFromScene(p)))]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    def importGenericNode(self, diagram, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(e)
        node = diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(e):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type e: QDomElement
        :rtype: bool
        """
        if e.hasAttribute('equivalence'):
            return bool(int(e.attribute('equivalence', '0')))
        return bool(int(e.attribute('complete', '0')))

    @staticmethod
    def getGeometryFromElement(e):
        """
        Returns the geometry element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('geometry')
        if search.isNull():
            search = e.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(e):
        """
        Returns the label element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('label')
        if search.isNull():
            search = e.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(e):
        """
        Returns the point element beside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.nextSiblingElement('point')
        if search.isNull():
            search = e.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(e):
        """
        Returns the point element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('point')
        if search.isNull():
            search = e.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, e):
        """
        Returns the item matching the given graphol node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None


class GrapholIRIProjectLoader_v2(AbstractProjectLoader, GrapholIRILoaderMixin_2):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    """

    def __init__(self, path, session):
        """
        Initialize the Project loader.
        :type path: str
        :type session: Session
        """
        path = expandPath(path)
        path = os.path.join(path, os.path.basename(path))
        path = postfix(path, File.Graphol.extension)
        super().__init__(path, session)

    '''
    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v1).
        """
        worker = GrapholProjectLoader_v1(os.path.dirname(self.path), self.session)
        worker.run()
        worker = GrapholProjectExporter(self.session.project)
        worker.run()
    '''

    def projectLoaded(self):
        """
        Initialize the Session Project to be the loaded one.
        """
        self.session.project = self.nproject

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import.
        """
        try:
            self.createDomDocument()
        except (ProjectNotFoundError, ProjectVersionError):
            #self.createLegacyProject()
            LOGGER.exception("PROBLEMI NEL CARICAMENTO....")
        else:
            self.createProject()
            self.createDiagrams()
            self.createPredicatesMeta()
            self.projectRender()
            self.projectLoaded()
