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


from PyQt5 import QtCore
from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.functions.fsystem import fwrite
from eddy.core.functions.misc import isEmpty
from eddy.core.output import getLogger


LOGGER = getLogger()


class GraphMLDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams in GraphML format.
    """
    KeyNode = 'd0'
    KeyEdge = 'd1'
    KeyPrefix = 'd2'
    KeyIri = 'd3'
    KeyDescription = 'd4'

    def __init__(self, diagram, session):
        """
        Initialize the GraphML exporter.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(diagram, session)

        self.document = None
        self.missing = {Item.FacetNode, Item.PropertyAssertionNode}

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
        }

    #############################################
    #   NODES
    #################################

    def exportAttributeNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AttributeNode
        :rtype: QDomElement
        """
        element = self.exportGenericNode(node, 'com.yworks.entityRelationship.attribute')
        element.setAttribute('remaining_characters', node.remaining_characters)

        return element

    def exportComplementNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ComplementNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportConceptNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ConceptNode
        :rtype: QDomElement
        """
        element = self.exportGenericNode(node, 'com.yworks.entityRelationship.small_entity')
        element.setAttribute('remaining_characters', node.remaining_characters)

        return element

    def exportDatatypeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DatatypeRestrictionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportDisjointUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DisjointUnionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportDomainRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DomainRestrictionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'rectangle')

    def exportEnumerationNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: EnumerationNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportFacetNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: FacetNode
        :rtype: QDomElement
        """
        # NO SUCH NODE IN THE GRAPHOL PALETTE FOR YED
        return None

    def exportIndividualNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IndividualNode
        :rtype: QDomElement
        """
        element = self.exportShapeNode(node, 'octagon')
        element.setAttribute('remaining_characters', node.remaining_characters)

        return element

    def exportIntersectionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IntersectionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportPropertyAssertionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: PropertyAssertionNode
        :rtype: QDomElement
        """
        # NO SUCH NODE IN THE GRAPHOL PALETTE FOR YED
        return None

    def exportRangeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RangeRestrictionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'rectangle')

    def exportRoleNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleNode
        :rtype: QDomElement
        """
        element = self.exportGenericNode(node, 'com.yworks.entityRelationship.relationship')
        element.setAttribute('remaining_characters', node.remaining_characters)

        return element

    def exportRoleChainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleChainNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportRoleInverseNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleInverseNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    def exportValueDomainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ValueDomainNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'roundrectangle')

    def exportUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: UnionNode
        :rtype: QDomElement
        """
        return self.exportShapeNode(node, 'hexagon')

    #############################################
    #   EDGES
    #################################

    def exportInclusionEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InclusionEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge, 'line', 'standard', '')

    def exportEquivalenceEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: EquivalenceEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge, 'line', 'standard', 'standard')

    def exportInputEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InputEdge
        :rtype: QDomElement
        """
        source = ''
        if edge.source.type() is Item.RoleNode:
            if edge.target.type() is Item.DomainRestrictionNode and edge.source.isFunctional():
                source = 't_shape'
            if edge.target.type() is Item.RangeRestrictionNode and edge.source.isInverseFunctional():
                source = 't_shape'
        if edge.source.type() is Item.AttributeNode:
            if edge.target.type() is Item.DomainRestrictionNode and edge.source.isFunctional():
                source = 't_shape'
        return self.exportGenericEdge(edge, 'dashed', 'white_diamond', source)

    def exportMembershipEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: MembershipEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge, 'line', 'standard', '', 'instanceOf')

    def exportSameEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: SameEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge, 'line', 'none', '', 'same')

    def exportDifferentEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: DifferentEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge, 'line', 'none', '', 'different')

    #############################################
    #   AUXILIARY METHODS
    #################################

    def exportGenericNode(self, node, configuration):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :type configuration: str
        :rtype: QDomElement
        """
        #############################################
        # NODE GEOMETRY
        #################################

        nodePos = self.translatePos(node)
        geometry = self.document.createElement('y:Geometry')
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', nodePos.x())
        geometry.setAttribute('y', nodePos.y())

        #############################################
        # NODE FILL
        #################################

        fill = self.document.createElement('y:Fill')
        fill.setAttribute('color', node.brush().color().name())
        fill.setAttribute('transparent', 'false')

        #############################################
        # BORDER STYLE
        #################################

        border = self.document.createElement('y:BorderStyle')
        border.setAttribute('color', '#000000')
        border.setAttribute('type', 'line')
        border.setAttribute('width', '1.0')

        #############################################
        # NODE LABEL
        #################################

        labelPos = self.translateLabelPos(node)
        label = self.document.createElement('y:NodeLabel')
        label.setAttribute('alignment', 'center')
        label.setAttribute('autoSizePolicy', 'content')
        label.setAttribute('fontFamily', 'Arial')
        label.setAttribute('fontSize', '12')
        label.setAttribute('fontStyle', 'plain')
        label.setAttribute('hasBackgroundColor', 'false')
        label.setAttribute('hasLineColor', 'false')
        label.setAttribute('height', node.label.height())
        label.setAttribute('modelName', 'free')
        label.setAttribute('modelPosition', 'anywhere')
        label.setAttribute('textColor', '#000000')
        label.setAttribute('visible', 'true')
        label.setAttribute('width', node.label.width())
        label.setAttribute('x', labelPos.x())
        label.setAttribute('y', labelPos.y())
        label.appendChild(self.document.createTextNode(node.text()))

        #############################################
        # STYLE PROPERTIES
        #################################

        prop = self.document.createElement('y:Property')
        prop.setAttribute('class', 'java.lang.Boolean')
        prop.setAttribute('name', 'y.view.ShadowNodePainter.SHADOW_PAINTING')
        prop.setAttribute('value', 'false')
        style = self.document.createElement('y:StyleProperties')
        style.appendChild(prop)

        #############################################
        # GENERIC NODE
        #################################

        genericNode = self.document.createElement('y:GenericNode')
        genericNode.setAttribute('configuration', configuration)
        genericNode.appendChild(geometry)
        genericNode.appendChild(fill)
        genericNode.appendChild(border)
        genericNode.appendChild(label)
        genericNode.appendChild(style)

        #############################################
        # DATA [NODE]
        #################################

        dataNode = self.document.createElement('data')
        dataNode.setAttribute('key', GraphMLDiagramExporter.KeyNode)
        dataNode.appendChild(genericNode)

        #############################################
        # DATA [IRI/PREFIX]
        #################################

        meta = self.diagram.project.meta(node.type(), node.text())

        """
        wikiPREFIX = '../wiki/{0}'.format(node.text())

        if not isEmpty(meta.get(K_PREFIX, '')):
            wikiPREFIX = meta.get(K_PREFIX, '')

        dataPREFIX = self.document.createElement('data')
        dataPREFIX.setAttribute('key', GraphMLDiagramExporter.KeyPrefix)
        dataPREFIX.appendChild(self.document.createTextNode(wikiPREFIX))

        wikiIRI = '../wiki/{0}'.format(node.text())

        if not isEmpty(meta.get(K_IRI, '')):
            wikiIRI = meta.get(K_IRI, '')

        dataIRI = self.document.createElement('data')
        dataIRI.setAttribute('key', GraphMLDiagramExporter.KeyIri)
        dataIRI.appendChild(self.document.createTextNode(wikiIRI))
        """
        #############################################
        # DATA [DESCRIPTION]
        #################################

        dataWIKI = self.document.createElement('data')
        dataWIKI.setAttribute('key', GraphMLDiagramExporter.KeyDescription)

        #############################################
        # NODE
        #################################

        elem = self.document.createElement('node')
        elem.setAttribute('id', node.id)
        elem.appendChild(dataNode)
        #elem.appendChild(dataPREFIX)
        #elem.appendChild(dataIRI)
        elem.appendChild(dataWIKI)

        return elem

    def exportShapeNode(self, node, shapeType):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :type shapeType: str
        :rtype: QDomElement
        """
        #############################################
        # NODE GEOMETRY
        #################################

        pos = self.translatePos(node)
        geometry = self.document.createElement('y:Geometry')
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', pos.x())
        geometry.setAttribute('y', pos.y())

        #############################################
        # NODE FILL
        #################################

        fill = self.document.createElement('y:Fill')
        fill.setAttribute('color', node.brush().color().name())
        fill.setAttribute('transparent', 'false')

        #############################################
        # BORDER STYLE
        #################################

        border = self.document.createElement('y:BorderStyle')
        border.setAttribute('color', '#000000')
        border.setAttribute('type', 'line')
        border.setAttribute('width', '1.0')

        #############################################
        # NODE LABEL
        #################################

        label = self.document.createElement('y:NodeLabel')
        label.setAttribute('alignment', 'center')
        label.setAttribute('autoSizePolicy', 'content')
        label.setAttribute('fontFamily', 'Arial')
        label.setAttribute('fontSize', '12')
        label.setAttribute('fontStyle', 'plain')
        label.setAttribute('hasBackgroundColor', 'false')
        label.setAttribute('hasLineColor', 'false')

        # Exclude the nodes that have no label.
        # Note that we include an empty NodeLabel XML tag in the .graphml file.
        if node.type() not in {Item.PropertyAssertionNode, Item.DisjointUnionNode}:
            labelPos = self.translateLabelPos(node)
            label.setAttribute('height', node.label.height())
            label.setAttribute('modelName', 'free')
            label.setAttribute('modelPosition', 'anywhere')
            label.setAttribute('textColor', '#000000')
            label.setAttribute('visible', 'true')
            label.setAttribute('width', node.label.width())
            label.setAttribute('x', labelPos.x())
            label.setAttribute('y', labelPos.y())
            smartNodeLabelModel = self.document.createElement('y:SmartNodeLabelModel')
            smartNodeLabelModel.setAttribute('distance', '4.0')
            labelModel = self.document.createElement('y:LabelModel')
            labelModel.appendChild(smartNodeLabelModel)
            smartNodeLabelModelParameter = self.document.createElement('y:SmartNodeLabelModelParameter')
            smartNodeLabelModelParameter.setAttribute('labelRatioX', '0.0')
            smartNodeLabelModelParameter.setAttribute('labelRatioY', '0.0')
            smartNodeLabelModelParameter.setAttribute('nodeRatioX', '0.0')
            smartNodeLabelModelParameter.setAttribute('nodeRatioY', '0.0')
            smartNodeLabelModelParameter.setAttribute('offsetX', '0.0')
            smartNodeLabelModelParameter.setAttribute('offsetY', '0.0')
            smartNodeLabelModelParameter.setAttribute('upX', '0.0')
            smartNodeLabelModelParameter.setAttribute('upY', '-1.0')
            modelParameter = self.document.createElement('y:ModelParameter')
            modelParameter.appendChild(smartNodeLabelModelParameter)
            label.appendChild(self.document.createTextNode(node.text()))
            label.appendChild(labelModel)
            label.appendChild(modelParameter)
        else:
            label.setAttribute('height', '4.0')
            label.setAttribute('hasText', 'false')
            label.setAttribute('width', '4.0')
            label.setAttribute('x', '0.0')
            label.setAttribute('y', '0.0')

        #############################################
        # SHAPE
        #################################

        shape = self.document.createElement('y:Shape')
        shape.setAttribute('type', shapeType)

        #############################################
        # SHAPE NODE
        #################################

        shapeNode = self.document.createElement('y:ShapeNode')
        shapeNode.appendChild(geometry)
        shapeNode.appendChild(fill)
        shapeNode.appendChild(border)
        shapeNode.appendChild(label)
        shapeNode.appendChild(shape)

        #############################################
        # DATA
        #################################

        data = self.document.createElement('data')
        data.setAttribute('key', GraphMLDiagramExporter.KeyNode)
        data.appendChild(shapeNode)

        #############################################
        # NODE
        #################################

        elem = self.document.createElement('node')
        elem.setAttribute('id', node.id)
        elem.appendChild(data)

        return elem

    def exportGenericEdge(self, edge, lineType, target, source='', label=''):
        """
        Export the given node into a QDomElement.
        :type edge: AbstractEdge
        :type lineType: str
        :type target: str
        :type source: str
        :type label: str
        :rtype: QDomElement
        """
        #############################################
        # PATH
        #################################

        sourcePos = self.translateAnchorPos(edge, edge.source)
        targetPos = self.translateAnchorPos(edge, edge.target)
        path = self.document.createElement('y:Path')
        path.setAttribute('sx', sourcePos.x())
        path.setAttribute('sy', sourcePos.y())
        path.setAttribute('tx', targetPos.x())
        path.setAttribute('ty', targetPos.y())

        for p in edge.breakpoints:
            point = self.document.createElement('y:Point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            path.appendChild(point)

        #############################################
        # LINE STYLE
        #################################

        lineStyle = self.document.createElement('y:LineStyle')
        lineStyle.setAttribute('color', '#000000')
        lineStyle.setAttribute('type', lineType)
        lineStyle.setAttribute('width', '1.0')

        #############################################
        # ARROWS
        #################################

        arrows = self.document.createElement('y:Arrows')
        arrows.setAttribute('color', '#000000')
        arrows.setAttribute('source', source or 'none')
        arrows.setAttribute('target', target)

        #############################################
        # EDGE LABEL
        #################################

        if label:
            smartEdgeLabelModel = self.document.createElement('y:SmartEdgeLabelModel')
            smartEdgeLabelModel.setAttribute('autoRotationEnabled', 'false')
            smartEdgeLabelModel.setAttribute('defaultAngle', '0.0')
            smartEdgeLabelModel.setAttribute('defaultDistance', '10.0')
            labelModel = self.document.createElement('y:LabelModel')
            labelModel.appendChild(smartEdgeLabelModel)
            smartEdgeLabelModelParameter = self.document.createElement('y:SmartEdgeLabelModelParameter')
            smartEdgeLabelModelParameter.setAttribute('angle', '0.0')
            smartEdgeLabelModelParameter.setAttribute('distance', '30.0')
            smartEdgeLabelModelParameter.setAttribute('distanceToCenter', 'true')
            smartEdgeLabelModelParameter.setAttribute('position', 'left')
            smartEdgeLabelModelParameter.setAttribute('ratio', '0.0')
            smartEdgeLabelModelParameter.setAttribute('segment', '0')
            modelParameter = self.document.createElement('y:ModelParameter')
            modelParameter.appendChild(smartEdgeLabelModelParameter)
            preferredPlacementDescriptor = self.document.createElement('y:PreferredPlacementDescriptor')
            preferredPlacementDescriptor.setAttribute('angle', '0.0')
            preferredPlacementDescriptor.setAttribute('angleOffsetOnRightSide', '0')
            preferredPlacementDescriptor.setAttribute('angleReference', 'absolute')
            preferredPlacementDescriptor.setAttribute('angleRotationOnRightSide', 'co')
            preferredPlacementDescriptor.setAttribute('distance', '-1.0')
            preferredPlacementDescriptor.setAttribute('frozen', 'true')
            preferredPlacementDescriptor.setAttribute('placement', 'anywhere')
            preferredPlacementDescriptor.setAttribute('side', 'anywhere')
            preferredPlacementDescriptor.setAttribute('sideReference', 'relative_to_edge_flow')
            edgeLabel = self.document.createElement('y:EdgeLabel')
            edgeLabel.setAttribute('alignment', 'center')
            edgeLabel.setAttribute('configuration', 'AutoFlippingLabel')
            edgeLabel.setAttribute('distance', '2.0')
            edgeLabel.setAttribute('fontFamily', 'Arial')
            edgeLabel.setAttribute('fontSize', '12')
            edgeLabel.setAttribute('fontStyle', 'plain')
            edgeLabel.setAttribute('hasBackgroundColor', 'false')
            edgeLabel.setAttribute('hasLineColor', 'false')
            edgeLabel.setAttribute('height', edge.label.height())
            edgeLabel.setAttribute('ratio', '0.5')
            edgeLabel.setAttribute('textColor', '#000000')
            edgeLabel.setAttribute('visible', 'true')
            edgeLabel.setAttribute('width', edge.label.width())
            edgeLabel.setAttribute('x', edge.label.pos().x())
            edgeLabel.setAttribute('y', edge.label.pos().y())
            edgeLabel.appendChild(self.document.createTextNode(label))
            edgeLabel.appendChild(labelModel)
            edgeLabel.appendChild(modelParameter)
            edgeLabel.appendChild(preferredPlacementDescriptor)

        #############################################
        # BEND STYLE
        #################################

        bendStyle = self.document.createElement('y:BendStyle')
        bendStyle.setAttribute('smoothed', 'false')

        #############################################
        # POLYLINE EDGE
        #################################

        polyLineEdge = self.document.createElement('y:PolyLineEdge')
        polyLineEdge.appendChild(path)
        polyLineEdge.appendChild(lineStyle)
        polyLineEdge.appendChild(arrows)
        if label:
            #polyLineEdge.appendChild(label)
            polyLineEdge.appendChild(edgeLabel)
        polyLineEdge.appendChild(bendStyle)

        #############################################
        # DATA
        #################################

        data = self.document.createElement('data')
        data.setAttribute('key', GraphMLDiagramExporter.KeyEdge)
        data.appendChild(polyLineEdge)

        #############################################
        # EDGE
        #################################

        elem = self.document.createElement('edge')
        elem.setAttribute('id', edge.id)
        elem.setAttribute('source', edge.source.id)
        elem.setAttribute('target', edge.target.id)
        elem.appendChild(data)

        return elem

    @staticmethod
    def translateAnchorPos(edge, node):
        """
        Translate the the anchor point of the given edge in the given node in yEd coordinates.
        :type edge: AbstractEdge
        :type node: AbstractNode
        :rtype: QtCore.QPointF
        """
        return node.mapFromScene(node.anchor(edge))

    @staticmethod
    def translateLabelPos(node):
        """
        Translate the given label position in yEd coordinates.
        :type node: AbstractNode
        :rtype: QtCore.QPointF
        """
        return node.label.pos() + \
               QtCore.QPointF(node.width() / 2, node.height() / 2) - \
               QtCore.QPointF(node.label.width() / 2, node.label.height() / 2) + \
               QtCore.QPointF(2.0, 2.0)

    @staticmethod
    def translatePos(node):
        """
        Translate the given position in yEd coordinates.
        :type node: AbstractNode
        :rtype: QtCore.QPointF
        """
        # yEd uses the TOP-LEFT corner as (0,0) coordinate => we need to translate our
        # position (0,0), which is instead at the center of the shape, so that the TOP-LEFT
        # corner of the shape in yEd matches the TOP-LEFT corner of the shape in Eddy.
        return node.pos() - QtCore.QPointF(node.width() / 2, node.height() / 2)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.GraphML

    def run(self, path):
        """
        Perform GraphML document generation.
        :type path: str
        """
        LOGGER.info('Exporting diagram %s to %s', self.diagram.name, path)

        # 1) CREATE THE DOCUMENT
        self.document = QtXml.QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.document.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.document.createElement('graphml')
        root.setAttribute('xmlns', 'http://graphml.graphdrawing.org/xmlns')
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.setAttribute('xmlns:y', 'http://www.yworks.com/xml/graphml')
        root.setAttribute('xmlns:yed', 'http://www.yworks.com/xml/yed/3')
        root.setAttribute('xsi:schemaLocation', 'http://graphml.graphdrawing.org/xmlns '
                                                'http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd')

        # 3) CREATE ELEMENT KEYS
        key = self.document.createElement('key')
        key.setAttribute('for', 'node')
        key.setAttribute('id', GraphMLDiagramExporter.KeyNode)
        key.setAttribute('yfiles.type', 'nodegraphics')
        root.appendChild(key)

        key = self.document.createElement('key')
        key.setAttribute('for', 'edge')
        key.setAttribute('id', GraphMLDiagramExporter.KeyEdge)
        key.setAttribute('yfiles.type', 'edgegraphics')
        root.appendChild(key)

        """
        key = self.document.createElement('key')
        key.setAttribute('attr.name', K_PREFIX)
        key.setAttribute('attr.type', 'string')
        key.setAttribute('for', 'node')
        key.setAttribute('id', GraphMLDiagramExporter.KeyPrefix)
        root.appendChild(key)

        key = self.document.createElement('key')
        key.setAttribute('attr.name', K_IRI)
        key.setAttribute('attr.type', 'string')
        key.setAttribute('for', 'node')
        key.setAttribute('id', GraphMLDiagramExporter.KeyIri)
        root.appendChild(key)
        """
        key = self.document.createElement('key')
        key.setAttribute('attr.type', 'string')
        key.setAttribute('for', 'node')
        key.setAttribute('id', GraphMLDiagramExporter.KeyDescription)
        root.appendChild(key)

        # 4) CREATE THE GRAPH NODE
        graph = self.document.createElement('graph')
        graph.setAttribute('edgedefault', 'directed')
        graph.setAttribute('id', 'G')

        # 5) GENERATE NODES
        for node in self.diagram.nodes():
            if node.type() not in self.missing:
                func = self.exportFuncForItem[node.type()]
                graph.appendChild(func(node))

        # 6) GENERATE EDGES
        for edge in self.diagram.edges():
            if edge.source.type() not in self.missing and edge.target.type() not in self.missing:
                func = self.exportFuncForItem[edge.type()]
                graph.appendChild(func(edge))

        # 7) APPEND THE GRAPH TO THE DOCUMENT
        self.document.appendChild(root)
        root.appendChild(graph)

        # 8) GENERATE THE FILE
        fwrite(self.document.toString(2), path)
