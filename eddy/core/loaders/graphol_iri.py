
import os
import textwrap
from time import time

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtXml

from eddy import APPNAME
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.project import CommandProjectAddPrefix, CommandProjectAddAnnotationProperty, \
    CommandProjectAddOntologyImport
from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Namespace
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.diagram import DiagramNotFoundError
from eddy.core.diagram import DiagramNotValidError
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.exporters.graphol_iri import GrapholIRIProjectExporter
from eddy.core.functions.fsystem import fread, fexists, isdir, rmdir, make_archive
from eddy.core.functions.misc import rstrip, postfix, rtfStripFontAttributes
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.nodes.common.base import OntologyEntityResizableNode
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.loaders.graphol import GrapholProjectLoader_v1
from eddy.core.loaders.owl2 import OwlOntologyImportSetWorker, OwlOntologyImportWorker
from eddy.core.output import getLogger
from eddy.core.owl import Literal, Facet, AnnotationAssertion, ImportedOntology, AnnotationAssertionProperty, \
    OWL2Datatype
from eddy.core.project import Project, K_DESCRIPTION, ProjectStopImportingError
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectVersionError
from eddy.core.project import ProjectStopLoadingError
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_ASYMMETRIC, K_IRREFLEXIVE, K_REFLEXIVE
from eddy.core.project import K_SYMMETRIC, K_TRANSITIVE
from eddy.ui.dialogs import DiagramSelectionDialog

LOGGER = getLogger()

    ####################
    #                  #
    #   VERSION 2      #
    #                  #
    ####################

class GrapholProjectIRILoaderMixin_2(object):
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
            path=self.path,
            version=parse(tag='version', default='1.0'),
            profile=self.session.createProfile('OWL 2'),
            prefixMap=self.getPrefixesDict(section),
            ontologyIRI=self.getOntologyIRI(section),
            datatypes=None,
            constrFacets=None,
            languages=None,
            annotationProperties=None,
            ontologyPrefix=self.getOntologyPrefix(section),
            defaultLanguage='en',
            addLabelFromSimpleName=False,
            addLabelFromUserInput=False,
            ontologies=set(),
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

    def getOntologyPrefix(self, ontologySection):
        result = ''
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        sube = e.firstChildElement('iri')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
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
                            prefix_value = None
                            sube_prefixes = sube.firstChildElement('prefixes')
                            sube_prefix = sube_prefixes.firstChildElement('prefix')
                            if not sube_prefix.isNull():
                                prefix_value = sube_prefix.attribute('prefix_value')
                            else:
                                prefix_value =''
                            return prefix_value
                    finally:
                        sube_property = sube_property.nextSiblingElement('property')
            except Exception:
                iriValue = sube.attribute('iri_value')
                LOGGER.exception('Failed to fetch namespace  %s', iriValue if iriValue else '"unknown"')
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

                '''
                ### Needed to fix the namespace of standard vocabularies which up to
                ### version 1.1.2 where stored without the fragment separator (#).
                ### See: https://github.com/obdasystems/eddy/issues/20
                for ns in Namespace:
                    if postfix(namespace, '#') == ns.value:
                        # Append the missing fragment separator
                        namespace += '#'
                        break
                '''

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
                    resolvedPrefix = self.nproject.getPrefixResolution(prefix)
                    if not resolvedPrefix:
                        resolvedPrefix = ''
                    namespace = iriElList[1]
                    iriString = '{}{}'.format(resolvedPrefix, namespace)
                elif len(iriElList) == 1:
                    iriString = iriElList[0]
                else:
                    iriString = prefixedIriString
                predicateIRI = self.nproject.getIRI(iriString)

                value = rtfStripFontAttributes(predicateElement.firstChildElement(K_DESCRIPTION).text())
                if value:
                    commentIRI = self.nproject.getIRI('http://www.w3.org/2000/01/rdf-schema#comment')
                    annAss = AnnotationAssertion(predicateIRI,commentIRI,value,OWL2Datatype.PlainLiteral.value, 'it')
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
    def getIriFromLabelText(self,labelText, itemType, addRdfsLabel=False, lang=None):
        if itemType==Item.ValueDomainIRINode:
            print()

        iriString = ''
        if labelText == 'TOP':
            addRdfsLabel = False
            if itemType is Item.AttributeIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#topDataProperty'
            if itemType is Item.RoleIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#topObjectProperty'
            if itemType is Item.ConceptIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#Thing'
        elif labelText == 'BOTTOM':
            addRdfsLabel = False
            if itemType is Item.AttributeIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomDataProperty'
            if itemType is Item.RoleIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomObjectProperty'
            if itemType is Item.ConceptIRINode:
                iriString = 'http://www.w3.org/2002/07/owl#Nothing'
        labelTextForIRI = labelText.replace('\n','')
        iriElList = labelTextForIRI.split(':')
        if len(iriElList) > 1:
            prefix = iriElList[0]
            resolvedPrefix = self.nproject.getPrefixResolution(prefix)
            if not resolvedPrefix:
                resolvedPrefix = ''
            simpleName = iriElList[1]
            iriString = '{}{}'.format(resolvedPrefix, simpleName)
        elif len(iriElList) == 1:
            iriString = iriElList[0]
        else:
            iriString = labelTextForIRI
        iri = self.nproject.getIRI(iriString)
        if addRdfsLabel:
            annAss = iri.getAnnotationAssertion(AnnotationAssertionProperty.Label.value, lang=lang)
            if not annAss:
                rdfsLabelValue = labelText
                labelElList = labelText.split(':')
                if len(labelElList)>1:
                    rdfsLabelValue = labelElList[1]
                annAss = AnnotationAssertion(iri, AnnotationAssertionProperty.Label.value, rdfsLabelValue,OWL2Datatype.PlainLiteral.value, lang)
                iri.addAnnotationAssertion(annAss)
        return iri

    def getIriPredicateNode(self, diagram, nodeElement, itemType):
        addRdfsLabel = False if itemType is Item.ValueDomainIRINode else True
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        iri = self.getIriFromLabelText(labelText,itemType,addRdfsLabel=addRdfsLabel, lang='it')
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(itemType, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'iri': iri
        })
        node.setBrush(QtGui.QBrush(QtGui.QColor(nodeElement.attribute('color', '#fcfcfc'))))
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

class GrapholOntologyIRILoader_v2(AbstractOntologyLoader, GrapholProjectIRILoaderMixin_2):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from Graphol file format.
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(expandPath(path), project, session)

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        pass

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
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()

        self.createPredicatesMeta()

        self.projectRender()
        self.projectMerge()

class GrapholIRIProjectLoader_v2(AbstractProjectLoader, GrapholProjectIRILoaderMixin_2):
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
        #path = os.path.join(path, os.path.basename(path))
        #path = postfix(path, File.Graphol.extension)
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
    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v2).
        """
        worker = GrapholProjectLoader_v1(os.path.dirname(self.path), self.session)
        worker.run()
        worker = GrapholProjectExporter(self.session.project)
        worker.run()
        print()
        #self.session.project = None


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
        version_1 = False
        try:
            self.createDomDocument()
        except (ProjectNotFoundError, ProjectVersionError):
            self.createLegacyProject()
            version_1 = True
        finally:
            if not version_1:
                #############################################
                # LEGACY LOADING CHECK
                #################################

                msgbox = QtWidgets.QMessageBox()
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Legacy mode')
                msgbox.setText(textwrap.dedent("""
                                    You have selected an {EDDY} version <b>2</b> project.<br/>
                                    If you continue with the loading procedure the project will be automatically
                                    converted to the most recent project version.<br/><br/>
                                    Do you want to continue?
                                    """.format(EDDY=APPNAME)))
                msgbox.exec_()

                if msgbox.result() == QtWidgets.QMessageBox.No:
                    raise ProjectStopLoadingError
            else:
                self.createDomDocument()
            self.createProject()
            self.createDiagrams()
            self.createPredicatesMeta()
            self.projectRender()
            self.projectLoaded()


    ####################
    #                  #
    #   VERSION 3      #
    #                  #
    ####################


    ####################
    #                  #
    #   VERSION 2      #
    #                  #
    ####################

class GrapholProjectIRILoaderMixin_3(object):
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
            'literal': Item.LiteralNode,
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
            'has-key': Item.HasKeyNode
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
            Item.LiteralNode: self.importLiteralNode,
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
            Item.HasKeyNode:self.importHasKeyNode
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
        version = int(e.attribute('version', '3'))
        if version != 3:
            raise ProjectVersionError('project version mismatch: %s != 3' % version)

    #############################################
    #   PROJECT (Prefixes,OntologyIRI)
    #################################
    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        projectEl = self.document.documentElement().firstChildElement('project')
        projectVersion = projectEl.attribute('version')
        projectName = projectEl.attribute('name')
        ontologyEl = projectEl.firstChildElement('ontology')
        ontologyIri = ontologyEl.attribute('iri')
        ontologyPrefix = ontologyEl.attribute('prefix',None)
        labelBoolean = False
        if ontologyEl.attribute('addLabelFromSimpleName'):
            labelBoolean = bool(int(ontologyEl.attribute('addLabelFromSimpleName')))
        labelUserInputBoolean = False
        if ontologyEl.attribute('addLabelFromUserInput'):
            labelUserInputBoolean = bool(int(ontologyEl.attribute('addLabelFromUserInput')))

        ontologyLang = ontologyEl.attribute('lang')
        prefixMap = self.getPrefixMap(ontologyEl)
        datatypes = self.getDatatypes(ontologyEl)
        facets = self.getFacets(ontologyEl)
        annotationProperties = self.getAnnotationproperties(ontologyEl)
        languages = self.getLanguages(ontologyEl)
        imports = self.getImports(ontologyEl)
        self.nproject = Project(
            name=projectName,
            # TODO path=os.path.dirname(self.path),
            path=self.path,
            version=projectVersion,
            profile=self.session.createProfile('OWL 2'),
            prefixMap=prefixMap,
            ontologyIRI=ontologyIri,
            datatypes=datatypes,
            constrFacets=facets,
            languages=languages,
            annotationProperties=annotationProperties,
            session=self.session,
            ontologyPrefix=ontologyPrefix,
            defaultLanguage=ontologyLang,
            addLabelFromSimpleName=labelBoolean,
            addLabelFromUserInput=labelUserInputBoolean,
            ontologies=imports
        )
        LOGGER.info('Loaded ontology: %s...', self.nproject.name)

        irisEl = ontologyEl.firstChildElement('iris')
        iriEl = irisEl.firstChildElement('iri')
        while not iriEl.isNull():
            try:
                self.getIri(iriEl, datatypes,facets,annotationProperties)
            except Exception as e:
                LOGGER.exception('Failed to import iri element [{}]'.format(e))
            finally:
                iriEl = iriEl.nextSiblingElement('iri')



    def getIri(self,iriEl,datatypes,facets,annotationProperties):
        iriString = iriEl.firstChildElement('value').text()
        if not (iriString in datatypes or iriString in facets or iriString in annotationProperties):
            result = self.nproject.getIRI(iriString)
            if not iriEl.firstChildElement('functional').isNull():
                result.functional = True
            if not iriEl.firstChildElement('inverseFunctional').isNull():
                result.inverseFunctional = True
            if not iriEl.firstChildElement('symmetric').isNull():
                result.symmetric = True
            if not iriEl.firstChildElement('asymmetric').isNull():
                result.asymmetric = True
            if not iriEl.firstChildElement('reflexive').isNull():
                result.reflexive = True
            if not iriEl.firstChildElement('irreflexive').isNull():
                result.irreflexive = True
            if not iriEl.firstChildElement('transitive').isNull():
                result.transitive = True
            '''
            result.functional = bool(int(iriEl.firstChildElement('functional').text()))
            result.inverseFunctional = bool(int(iriEl.firstChildElement('inverseFunctional').text()))
            result.symmetric = bool(int(iriEl.firstChildElement('symmetric').text()))
            result.asymmetric = bool(int(iriEl.firstChildElement('asymmetric').text()))
            result.reflexive = bool(int(iriEl.firstChildElement('reflexive').text()))
            result.irreflexive = bool(int(iriEl.firstChildElement('irreflexive').text()))
            result.transitive = bool(int(iriEl.firstChildElement('transitive').text()))
            '''
            annotationsEl = iriEl.firstChildElement('annotations')
            if not annotationsEl.isNull():
                annotationEl = annotationsEl.firstChildElement('annotation')
                while not annotationEl.isNull():
                    try:
                        result.addAnnotationAssertion(self.getAnnotationAssertion(annotationEl))
                    except Exception as e:
                        LOGGER.exception('Failed to import annotation element for iri {} [{}]'.format(iriString,e))
                    finally:
                        annotationEl = annotationEl.nextSiblingElement('annotation')
                return result

    def getAnnotationAssertion(self,annotationEl):
        subjectEl = annotationEl.firstChildElement('subject')
        subject = self.nproject.getIRI(subjectEl.text())
        propertyEl = annotationEl.firstChildElement('property')
        property = self.nproject.getIRI(propertyEl.text())
        value = None
        type = None
        language = None
        objectEl = annotationEl.firstChildElement('object')
        iriObjEl = objectEl.firstChildElement('iri')
        if not iriObjEl.isNull():
            value = self.nproject.getIRI(iriObjEl.text())
        else:
            value = objectEl.firstChildElement('lexicalForm').text()
            datatypeEl = objectEl.firstChildElement('datatype')
            if datatypeEl.text():
                type = self.nproject.getIRI(datatypeEl.text())
            languageEl = objectEl.firstChildElement('language')
            if languageEl.text():
                language = languageEl.text()
        return AnnotationAssertion(subject,property,value,type,language)

    def getPrefixMap(self, ontologyEl):
        prefixMap = dict()
        prefixesEl = ontologyEl.firstChildElement('prefixes')
        prefixEl = prefixesEl.firstChildElement('prefix')
        while not prefixEl.isNull():
            try:
                value = prefixEl.firstChildElement('value').text()
                ns = prefixEl.firstChildElement('namespace').text()
                prefixMap[value] = ns
            except Exception as e:
                LOGGER.exception('Failed to import prefix element ')
            finally:
                prefixEl = prefixEl.nextSiblingElement('prefix')
        return prefixMap

    def getAnnotationproperties(self, ontologyEl):
        result = set()
        annotationPropertiesEl = ontologyEl.firstChildElement('annotationProperties')
        annotationPropertyEl = annotationPropertiesEl.firstChildElement('annotationProperty')
        while not annotationPropertyEl.isNull():
            try:
                iriStr = annotationPropertyEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import annotationProperty element ')
            finally:
                annotationPropertyEl = annotationPropertyEl.nextSiblingElement('annotationProperty')
        return result

    def getDatatypes(self, ontologyEl):
        result = set()
        datatypesEl = ontologyEl.firstChildElement('datatypes')
        datatypeEl = datatypesEl.firstChildElement('datatype')
        while not datatypeEl.isNull():
            try:
                iriStr = datatypeEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import datatype element ')
            finally:
                datatypeEl = datatypeEl.nextSiblingElement('datatype')
        return result

    def getFacets(self, ontologyEl):
        result = set()
        facetsEls = ontologyEl.firstChildElement('facets')
        facetEl = facetsEls.firstChildElement('facet')
        while not facetEl.isNull():
            try:
                iriStr = facetEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import facet element ')
            finally:
                facetEl = facetEl.nextSiblingElement('facet')
        return result

    def getLanguages(self, ontologyEl):
        result = set()
        languagesEl = ontologyEl.firstChildElement('languages')
        languageEl = languagesEl.firstChildElement('language')
        while not languageEl.isNull():
            try:
                lang = languageEl.text()
                result.add(lang)
            except Exception as e:
                LOGGER.exception('Failed to import language element ')
            finally:
                languageEl = languageEl.nextSiblingElement('language')
        return result

    def getImports(self, ontologyEl):
        result = set()
        importsEl = ontologyEl.firstChildElement('imports')
        importEl = importsEl.firstChildElement('import')
        while not importEl.isNull():
            try:
                ontIri = importEl.attribute('iri')
                versionIri = importEl.attribute('version')
                location = importEl.attribute('location')
                isLocal = False
                if importEl.attribute('isLocal'):
                    isLocal = bool(int(importEl.attribute('isLocal')))
                ontImp = ImportedOntology(ontIri, location, versionIri, isLocal, self.nproject)
                result.add(ontImp)
            except Exception as e:
                LOGGER.exception('Failed to import import element. {}'.format(str(e)))
            finally:
                importEl = importEl.nextSiblingElement('import')
        return result

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
        section = self.document.documentElement().firstChildElement('project').firstChildElement('diagrams')
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
                node = func(diagram, nodeElement)
            except Exception as e:
                LOGGER.exception('Failed to create node {}. [{}]'.format(nodeElement.attribute('id'), e))
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
                LOGGER.exception('Failed to create edge {}. [{}]'.format(edgeElement.attribute('id'), e))
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
    #   NODES
    #################################


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

    def getIriPredicateNode(self, diagram, nodeElement, itemType):
        labelElement = nodeElement.firstChildElement('label')
        iriEl = nodeElement.firstChildElement('iri')
        iri = self.nproject.getIRI(iriEl.text())
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(itemType, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'iri': None
        })
        node.iri = iri
        node.setBrush(QtGui.QBrush(QtGui.QColor(nodeElement.attribute('color', '#fcfcfc'))))
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))

        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))

        #node.doUpdateNodeLabel()
        return node

    def importLiteralNode(self, diagram, nodeElement):
        literalEl = nodeElement.firstChildElement('literal')
        lexicalFormEl = literalEl.firstChildElement('lexicalForm')
        lexicalForm = lexicalFormEl.text()
        datatype = None
        datatypeEl = literalEl.firstChildElement('datatype')
        if datatypeEl.text():
            datatype = self.nproject.getIRI(datatypeEl.text())
        language = None
        languageEl = literalEl.firstChildElement('language')
        if languageEl.text():
            language = self.nproject.getIRI(languageEl.text())
        literal = Literal(lexicalForm, datatype,language)

        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.LiteralNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'literal': None
        })
        node.literal = literal
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        labelElement = nodeElement.firstChildElement('label')
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))

        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))

        #node.doUpdateNodeLabel()
        return node

    def importFacetNode(self, diagram, nodeElement):
        facetEl = nodeElement.firstChildElement('facet')
        constrFacetEl = facetEl.firstChildElement('constrainingFacet')
        constrFacetIRI = self.nproject.getIRI(constrFacetEl.text())
        literalEl = facetEl.firstChildElement('literal')
        lexForm = literalEl.firstChildElement('lexicalForm').text()



        datatypeStr = literalEl.firstChildElement('datatype').text()
        if datatypeStr:
            datatypeIRI = self.nproject.getIRI(datatypeStr)
        else:
            datatypeIRI = OWL2Datatype.PlainLiteral.value

        literal = Literal(lexForm,datatypeIRI)
        facet = Facet(constrFacetIRI, literal)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.FacetIRINode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'facet': facet
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        labelElement = nodeElement.firstChildElement('label')
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

    def importHasKeyNode(self, diagram, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: HasKeyNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.HasKeyNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

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
        labelElement = e.firstChildElement('label')
        geometry = self.getGeometryFromElement(e)
        node = diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))
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

class GrapholOntologyIRILoader_v3(AbstractOntologyLoader, GrapholProjectIRILoaderMixin_3):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from Graphol file format and merge them with current project
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(expandPath(path), project, session)
        self._owlOntologyImportErrors = set()

    @property
    def owlOntologyImportErrors(self):
        return self._owlOntologyImportErrors

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        worker = ProjectIRIMergeWorker_v3(self.project, self.nproject, self.session)
        connect(worker.sgnErrorManagingOWLOntologyImport, self.onImportError)
        worker.run()
        disconnect(worker.sgnErrorManagingOWLOntologyImport, self.onImportError)

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        self._owlOntologyImportErrors.update([(location,str(exc))])
        print()

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
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()
        self.projectRender()
        self.projectMerge()

class GrapholIRIProjectLoader_v3(AbstractProjectLoader, GrapholProjectIRILoaderMixin_3):
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
        #path = os.path.join(path, os.path.basename(path))
        #path = postfix(path, File.Graphol.extension)
        super().__init__(path, session)

    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v2).
        """
        #worker = GrapholIRIProjectLoader_v2(os.path.dirname(self.path), self.session)
        worker = GrapholIRIProjectLoader_v2(self.path, self.session)
        worker.run()
        worker = GrapholIRIProjectExporter(self.session.project)
        worker.run()

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
            LOGGER.info("Try to load legacy project (graphol version=2)")
            self.createLegacyProject()
        else:
            self.createProject()
            self.createDiagrams()
            self.projectRender()
            self.projectLoaded()

class ProjectIRIMergeWorker_v3(QtCore.QObject):
    """
    Extends QObject with facilities to merge the content of 2 distinct projects.
    """

    sgnErrorManagingOWLOntologyImport = QtCore.pyqtSignal(str, Exception)

    def __init__(self, project, other, session):
        """
        Initialize the project merge worker.
        :type project: Project
        :type other: Project
        :type session: Session
        """
        super().__init__(session)
        self.commands = list()
        self.project = project
        self.other = other

        self.selected_diagrams = None
        self.all_names_in_selected_diagrams = []

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for ProjectMergeWorker.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################
    def run(self):
        """
        Perform the merge of the 2 projects.
        """
        try:
            LOGGER.info('Performing project import: %s <- %s...', self.project.name, self.other.name)
            self.mergeDiagrams()
            self.importPrefixesTypesAndAnnotations()
            self.importImportedOntologies()
        except ProjectStopImportingError as e:
            LOGGER.exception('Fatal error during project merge: {}'.format(str(e)))
        else:
            self.mergeFinished()

    def importPrefixesTypesAndAnnotations(self):
        for prefix,ns in self.other.prefixDictItems():
            if not prefix in self.project.getManagedPrefixes():
                self.commands.append(CommandProjectAddPrefix(self.project,prefix,ns))
                #self.project.setPrefix(prefix, ns)
        '''
        for datatypeIRI in self.other.getDatatypeIRIs():
            self.project.addDatatype(str(datatypeIRI))
        '''

        for annPropIRI in self.other.getAnnotationPropertyIRIs():
            self.commands.append(CommandProjectAddAnnotationProperty(self.project, str(annPropIRI)))
            #self.project.addAnnotationProperty(str(annPropIRI))

    def importImportedOntologies(self):
        alreadyLoadedOntIRIs = [str(x.ontologyIRI) for x in self.project.importedOntologies]
        for otherImpOnt in self.other.importedOntologies:
            if not str(otherImpOnt.ontologyIRI) in alreadyLoadedOntIRIs:
                self.currImpOnt = ImportedOntology(otherImpOnt.ontologyIRI, otherImpOnt.docLocation, otherImpOnt.versionIRI, otherImpOnt.isLocalDocument, self.project)
                self.worker = OwlOntologyImportWorker(self.currImpOnt.docLocation, self.session, isLocalImport=self.currImpOnt.isLocalDocument)
                connect(self.worker.sgnCompleted, self.onImportCompleted)
                connect(self.worker.sgnErrored, self.onImportError)
                connect(self.worker.sgnClassFetched, self.onClassFetched)
                connect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
                connect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
                connect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
                self.worker.run()

    @QtCore.pyqtSlot(str)
    def onClassFetched(self, iri):
        self.currImpOnt.addClass(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onObjectPropertyFetched(self, iri):
        self.currImpOnt.addObjectProperty(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onDataPropertyFetched(self, iri):
        self.currImpOnt.addDataProperty(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onIndividualFetched(self, iri):
        self.currImpOnt.addIndividual(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot()
    def onImportCompleted(self):
        command = CommandProjectAddOntologyImport(self.project, self.currImpOnt)
        self.commands.append(command)
        disconnect(self.worker.sgnCompleted, self.onImportCompleted)
        disconnect(self.worker.sgnErrored, self.onImportError)
        disconnect(self.worker.sgnClassFetched, self.onClassFetched)
        disconnect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
        disconnect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
        disconnect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
        self.currImpOnt = None
        self.worker = None

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        LOGGER.exception('OWL 2 import located in {} could not be completed during merge. Error: {}'.format(location,str(exc)))
        command = CommandProjectAddOntologyImport(self.project, self.currImpOnt)
        self.commands.append(command)
        self.currImpOnt = None
        disconnect(self.worker.sgnCompleted, self.onImportCompleted)
        disconnect(self.worker.sgnErrored, self.onImportError)
        disconnect(self.worker.sgnClassFetched, self.onClassFetched)
        disconnect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
        disconnect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
        disconnect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
        self.sgnErrorManagingOWLOntologyImport.emit(location, exc)

    def mergeDiagrams(self):
        """
        Perform the merge of the diagrams by importing all the diagrams in the 'other' project in the loaded one.
        """
        try:
            diagrams_selection_dialog = DiagramSelectionDialog(self.session, project=self.other)
            diagrams_selection_dialog.exec_()
            self.selected_diagrams = diagrams_selection_dialog.selectedDiagrams()
        except Exception as e:
            print(e)

        alreadyAdded = set()
        alreadyAddedDiagram = set()
        for diagram in self.selected_diagrams:
            self.replaceIRIs(diagram,alreadyAdded)
            # We may be in the situation in which we are importing a diagram with name 'X'
            # even though we already have a diagram 'X' in our project. Because we do not
            # want to overwrite diagrams, we perform a rename of the diagram being imported,
            # to be sure to have a unique diagram name, in the current project namespace.
            occurrence = 1
            name = diagram.name
            while self.project.diagram(diagram.name) or diagram.name in alreadyAddedDiagram:
                diagram.name = '{0}_{1}'.format(name, occurrence)
                occurrence += 1
            ## SWITCH SIGNAL SLOTS
            disconnect(diagram.sgnItemAdded, self.other.doAddItem)
            disconnect(diagram.sgnItemRemoved, self.other.doRemoveItem)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            ## MERGE THE DIAGRAM IN THE CURRENT PROJECT
            self.commands.append(CommandDiagramAdd(diagram, self.project))
            alreadyAddedDiagram.add(diagram.name)

    def replaceIRIs(self,diagram,alreadyAdded):
        for node in diagram.nodes():
            if isinstance(node,OntologyEntityResizableNode) or isinstance(node, OntologyEntityResizableNode):
                otherIRI = node.iri
                projIRI = None
                if not str(otherIRI) in alreadyAdded and self.project.existIRI(str(otherIRI)):
                    LOGGER.warning('The IRI <{}> occurs in both projects...'.format(str(otherIRI)))
                    #TODO Gestisci possibili incongruenze: funct, asymm, annotation assertions, etc, etc,...
                    projIRI = self.project.getIRI(str(otherIRI))
                elif str(otherIRI) in alreadyAdded:
                    projIRI = self.project.getIRI(str(otherIRI))
                else:
                    projIRI = self.project.getIRI(str(otherIRI))
                    projIRI.functional = otherIRI.functional
                    projIRI.inverseFunctional = otherIRI.inverseFunctional
                    projIRI.asymmetric = otherIRI.asymmetric
                    projIRI.symmetric = otherIRI.symmetric
                    projIRI.reflexive = otherIRI.reflexive
                    projIRI.irreflexive = otherIRI.irreflexive
                    projIRI.transitive = otherIRI.transitive
                    for annAss in otherIRI.annotationAssertions:
                        newAss = AnnotationAssertion(projIRI,annAss.assertionProperty, annAss.value, annAss.datatype, annAss.language)
                        projIRI.addAnnotationAssertion(newAss)
                    alreadyAdded.add(str(otherIRI))
                node.iri = projIRI

    def mergeFinished(self):
        """
        Completes the merge by executing the commands in the buffer on the undostack.
        """
        if self.commands:
            self.session.undostack.beginMacro(
                'import project "{0}" into "{1}"'.format(self.other.name, self.project.name))
            for command in self.commands:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()



