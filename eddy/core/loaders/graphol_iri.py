
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
from eddy.core.project import Project
from eddy.core.project import ProjectMergeWorker
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectVersionError
from eddy.core.project import ProjectStopLoadingError
from eddy.core.project import K_DESCRIPTION, K_DESCRIPTION_STATUS
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_ASYMMETRIC, K_IRREFLEXIVE, K_REFLEXIVE
from eddy.core.project import K_SYMMETRIC, K_TRANSITIVE

LOGGER = getLogger()

class GrapholLoaderMixin_v2(object):
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
            Item.ConceptIRINode: self.importPredicateMeta,
            Item.IndividualIRINode: self.importPredicateMeta,
            Item.RoleIRINode: self.importRoleMeta,
        }


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
                        sube_property = sube_property.nextSibling('property')
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
                for namespace in Namespace:
                    if postfix(namespace, '#') == namespace.value:
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
                        sube_prefix = sube_prefix.nextSibling('prefix')
            except Exception:
                LOGGER.exception('Failed to fetch namespace  %s', namespace)
            finally:
                sube = sube.nextSiblingElement('iri')
        return dictionary_to_return

    #############################################
    #   DIAGRAM
    #################################

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
        ## LOAD DIAGRAM NODES
        sube = diagramElement.firstChildElement('node')


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
        if not iriString:
            iriString = self.getIriFromLabelText(labelText)
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

    def getIriPredicateNode(self, nodeElement, itemType):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        iri = self.nproject.getIRI(labelText,itemType)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = self.diagram.factory.create(itemType, **{
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

    def importAttributeNode(self, nodeElement):
        self.getIriPredicateNode(nodeElement, Item.AttributeIRINode)

    def importRoleNode(self, nodeElement):
        self.getIriPredicateNode(nodeElement, Item.RoleIRINode)

    def importConceptNode(self, nodeElement):
        self.getIriPredicateNode(nodeElement, Item.ConceptIRINode)

    def importIndividualNode(self, nodeElement):
        self.getIriPredicateNode(nodeElement, Item.IndividualIRINode)

    def importValueDomainNode(self, nodeElement):
        self.getIriPredicateNode(nodeElement, Item.ValueDomainIRINode)

    def importLiteralNode(self, nodeElement):
        #TODO Implementa
        pass

    def importFacetNode(self, nodeElement):
        #TODO Implementa
        pass

    def importComplementNode(self, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(Item.ComplementNode, e)

    def importDatatypeRestrictionNode(self, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(Item.EnumerationNode, e)

    def importIntersectionNode(self, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(Item.RoleInverseNode, e)

    def importUnionNode(self, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(Item.UnionNode, e)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(Item.EquivalenceEdge, e)

    def importInclusionEdge(self, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        if self.getEdgeEquivalenceFromElement(e):
            return self.importEquivalenceEdge(e)
        return self.importGenericEdge(Item.InclusionEdge, e)

    def importInputEdge(self, e):
        """
        Build an Input edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(Item.InputEdge, e)

    def importMembershipEdge(self, e):
        """
        Build a Membership edge using the given QDomElement.
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(Item.MembershipEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importGenericEdge(self, item, e):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = self.getPointInsideElement(e)
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = self.getPointBesideElement(point)

        source = self.nodes[e.attribute('source')]
        target = self.nodes[e.attribute('target')]
        edge = self.diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1] \
                            if not (source.painterPath().contains(p) or target.painterPath().contains(p))]
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

    def importGenericNode(self, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(e)
        node = self.diagram.factory.create(item, **{
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
