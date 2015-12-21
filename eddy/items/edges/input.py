# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
##########################################################################
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


from math import sin, cos, radians, pi as M_PI

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPen, QPolygonF, QColor, QPixmap, QPainterPath
from PyQt5.QtWidgets import QMenu

from eddy.datatypes import DiagramMode, Item, Identity, Restriction
from eddy.items.edges.common.base import AbstractEdge
from eddy.items.edges.common.label import Label


class InputEdge(AbstractEdge):
    """
    This class implements the Input edge.
    """
    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(252, 252, 252)
    headSize = 10
    item = Item.InputEdge
    name = 'input'
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    shapePen.setDashPattern([5, 5])
    xmlname = 'input'

    def __init__(self, functional=False, **kwargs):
        """
        Initialize the Input edge.
        :param functional: whether the edge is functional or not.
        """
        super().__init__(**kwargs)

        self._functional = functional

        self.label = Label('', centered=False, parent=self)
        self.tail = QLineF()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def functional(self):
        """
        Tells whether this edge is functional.
        :return: True if the edge is functional, False otherwise.
        :rtype: bool
        """
        return self._functional

    @functional.setter
    def functional(self, functional):
        """
        Set the functional attribute for this edge.
        :param functional: the complete value.
        """
        self._functional = bool(functional)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :param pos: the position where the context menu has been requested.
        :rtype: QMenu
        """
        menu = QMenu()
        scene = self.scene()
        breakpoint = self.breakpointAt(pos)
        if breakpoint is not None:
            action = scene.mainwindow.actionRemoveEdgeBreakpoint
            action.setData((self, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(scene.mainwindow.actionDelete)
            menu.addAction(scene.mainwindow.actionSwapEdge)
            menu.addSeparator()
            menu.addAction(scene.mainwindow.actionToggleEdgeFunctional)
            scene.mainwindow.actionSwapEdge.setVisible(self.isValid(self.target, self.source))
            scene.mainwindow.actionToggleEdgeFunctional.setChecked(self.functional)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current edge.
        :param scene: a reference to the scene where this item is being copied.
        """
        kwargs = {
            'scene': scene,
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'breakpoints': self.breakpoints[:],
            'functional': self.functional,
        }
        return self.__class__(**kwargs)

    def isValid(self, source, target):
        """
        Tells whether this edge is valid when being added between the given source and target nodes.
        :type source: Node.
        :type target: Node.
        :rtype: bool
        """
        if source is target:
            # Self connection is not valid.
            return False

        if not target.constructor:
            # Input edges can only target constructor nodes.
            return False

        ################################################################################################################
        #                                                                                                              #
        #   COMPLEMENT, DISJOINT UNION, INTERSECTION, UNION                                                            #
        #                                                                                                              #
        ################################################################################################################

        if target.isItem(Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode):

            if source.identity not in target.identities:
                # Source node identity is not supported by this node despite the currently set identity.
                print("identity is not among the ones available")
                return False

            if source.isItem(Item.ValueRestrictionNode):
                # Exclude unsupported nodes despite identity matching.
                print("unsupported node")
                return False

            if source.identity is not Identity.Neutral and \
                target.identity is not Identity.Neutral and \
                    source.identity is not target.identity:
                print("identity mismatch")
                # Identity mismatch.
                return False

            ############################################################################################################
            #                                                                                                          #
            #   COMPLEMENT                                                                                             #
            #                                                                                                          #
            ############################################################################################################

            if target.isItem(Item.ComplementNode):

                if len([e for e in target.edges \
                    if e.isItem(Item.InputEdge) and \
                        e.target is target and e is not self]) > 0:
                    # The Complement operator may have at most one node connected to it.
                    print("too many inputs")
                    return False

                if source.isItem(Item.RoleNode, Item.RoleInverseNode) and \
                    len([e for e in target.edges \
                        if e.isItem(Item.InputEdge) and \
                            e.source is target]) > 0:
                    # If the source of the node is a Role (ObjectPropertyExpression => chain is not included)
                    # check for the node not to have any outgoing Input edge: the only supported expression
                    # is `R1 ISA NOT R2` (this prevents the connection of Role expressions to Complement nodes
                    # that are given as inputs to Enumeration, Union and Disjoint Union operatore nodes.
                    return False

        ################################################################################################################
        #                                                                                                              #
        #   ENUMERATION                                                                                                #
        #                                                                                                              #
        ################################################################################################################

        if target.isItem(Item.EnumerationNode):

            if not source.isItem(Item.IndividualNode):
                # Enumeration operator (oneOf) takes as inputs individuals or literals, both represented by the
                # Individual node, and has the job of composing a set if individuals (either Concept or DataRange,
                # but not both together).
                return False

            if target.identity is Identity.Unknown:
                # Target node has an unkown identity: we do not allow the connection => the user MUST fix the
                # error first and then try to create again the connection (this should never happen actually).
                return False

            if target.identity is not Identity.Neutral:
                # Target node identity has been computed already so check for identity mismatch
                if source.identity is Identity.Individual and target.identity is Identity.DataRange or \
                    source.identity is Identity.Literal and target.identity is Identity.Concept:
                    # Identity mismatch.
                    return False

        ################################################################################################################
        #                                                                                                              #
        #   ROLE INVERSE                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.RoleInverseNode):

            # OWL 2 syntax: http://www.w3.org/TR/owl2-syntax/#Inverse_Object_Properties

            if not source.isItem(Item.RoleNode):
                # The Role Inverse operator takes as input a role and constructs its inverse by switching
                # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                return False

            if len([e for e in target.edges \
                if e.isItem(Item.InputEdge) and \
                     e.target is target and e is not self]) > 0:
                # The Role Inverse operator may have at most one Role node connected to it: if we need to
                # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                return False

        ################################################################################################################
        #                                                                                                              #
        #   ROLE CHAIN                                                                                                 #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.RoleChainNode):

            # OWL 2 syntax: http://www.w3.org/TR/owl2-syntax/#Object_Subproperties

            if not source.isItem(Item.RoleNode, Item.RoleInverseNode):
                # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                # of chains, despite the identity matches Role in both expressions).
                return False

        ################################################################################################################
        #                                                                                                              #
        #   DATATYPE RESTRICTION                                                                                       #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.DatatypeRestrictionNode):

            if not source.isItem(Item.ValueDomainNode, Item.ValueRestrictionNode):
                # The DatatypeRestriction node is used to compose complex datatypes and
                # accepts as inputs a Value-Domain node together with N Value-Restriction
                # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                return False

            if source.isItem(Item.ValueDomainNode):
                if len([e.source for e in target.edges \
                        if e.isItem(Item.InputEdge) and \
                        e.target is target and e is not self and \
                            e.source.isItem(Item.ValueDomainNode)]) > 0:
                    # The Value-Domain has already been attached to the DatatypeRestriction.
                    return False

        ################################################################################################################
        #                                                                                                              #
        #   PROPERTY ASSERTION                                                                                         #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.PropertyAssertionNode):

            # OWL 2 syntax: http://www.w3.org/TR/owl2-syntax/#Anonymous_Individuals

            if not source.isItem(Item.IndividualNode):
                # Property Assertion operators accepts only Individual nodes as input: they are
                # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                return False

            if len([e for e in target.edges \
                if e.isItem(Item.InputEdge) and \
                    e.target is target and e is not self]) >= 2:
                # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                # the individuals are identified by M.Draghi and "Mario".
                return False

            if source.identity is Identity.Literal and \
                    len([n for n in [e.other(target) \
                        for e in target.edges \
                            if e.isItem(Item.InputEdge) and \
                                e.target is target and e is not self] if n.identity is Identity.Literal]) > 0:
                # At most one Literal can be given as input (2 Individuals | 1 Individual + 1 Literal)
                return False

            # See if the source we are connecting to the Link is consistent with the instanceOf expression
            # if there is such expression (else we do not care since we check this in the instanceOf edge.
            node = next(iter(e.other(target) for e in target.edges \
                         if e.isItem(Item.InstanceOfEdge) and \
                            e.source is target), None)

            if node:

                if node.isItem(Item.RoleNode, Item.RoleInverseNode):
                    if source.identity is Identity.Literal:
                        # We are constructing an ObjectPropertyAssertion expression so we can't connect a Literal.
                        return False

                if node.isItem(Item.AttributeNode):
                    if source.identity is Identity.Individual and \
                        len([n for n in [e.other(target) \
                            for e in target.edges \
                                if e.isItem(Item.InputEdge) and \
                                    e.target is target and e is not self] if n.identity is Identity.Individual]) > 0:
                        # We are constructing a DataPropertyAssertion and so we can't have more than 1 Individual.
                        return False

        ################################################################################################################
        #                                                                                                              #
        #   DOMAIN RESTRICTION                                                                                         #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.DomainRestrictionNode):

            if len([e for e in target.edges \
                if e.isItem(Item.InputEdge) and \
                    e.target is target and e is not self]) >= 2:
                # Domain Restriction node can have at most 2 inputs.
                return False

            if source.identity not in {Identity.Neutral, Identity.Concept, Identity.Attribute, Identity.Role}:
                # Domain Restriction node takes as input:
                #  - Role => OWL 2 ObjectPropertyExpression
                #  - Attribute => OWL 2 DataPropertyExpression
                #  - Concept => Qualified Existential/Universal Restriction i.e: A ISA EXISTS R.C || A ISA FORALL R.C
                return False

            if source.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode):
                # Exclude incompatible sources: not that while RoleChain has a correct identity
                # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                return False

            # SOURCE => CONCEPT EXPRESSION || NEUTRAL

            if source.identity in {Identity.Concept, Identity.Neutral}:

                if target.restriction not in {Restriction.exists, Restriction.forall}:
                    # Not a Qualified Existential/Universal Restriction.
                    return False

                # We can connect a Concept in input only if there
                # is no other input or if the other input is a Role.
                node = next(iter(e.other(target) for e in target.edges \
                         if e.isItem(Item.InputEdge) and \
                            e.target is target and e is not self), None)

                if node:

                    if node.identity is not Identity.Role:
                        # We found another input on this node which is not a Role
                        # so we can't construct a Qualified Existential Restriction.
                        return False

            # SOURCE => ROLE EXPRESSION

            elif source.identity is Identity.Role:

                # We can connect a Role in input only if there is no other input or if the
                # other input is a Concept and the node specify an Existential Restriction.
                node = next(iter(e.other(target) for e in target.edges \
                         if e.isItem(Item.InputEdge) and \
                            e.target is target and e is not self), None)

                if node:

                    if node.identity is not Identity.Concept or target.restriction is not Restriction.exists:
                        # Not a Qualified Existential Restriction.
                        return False

            # SOURCE => ATTRIBUTE NODE

            elif source.identity is Identity.Attribute:

                if len([e.other(target) for e in target.edges \
                         if e.isItem(Item.InputEdge) and \
                            e.target is target and e is not self]) > 0:
                    # We can connect an Attribute in input only if there is no other input.
                    return False
        ################################################################################################################
        #                                                                                                              #
        #   RANGE RESTRICTION                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        elif target.isItem(Item.RangeRestrictionNode):

            if source.identity not in {Identity.Neutral, Identity.Attribute, Identity.Role}:
                # Range Restriction node takes as input:
                #  - Role => OWL 2 ObjectPropertyExpression
                #  - Attribute => OWL 2 DataPropertyExpression.
                return False

            if source.isItem(Item.RoleChainNode):
                # Role Chain is excluded since it doesn't match OWL 2 ObjectPropertyExpression
                return False

            if target.identity is not Identity.Neutral:
                # Identity mismatch: check particular case for this node since there is no identity inheritance
                if target.identity is Identity.Concept and source.isItem(Item.AttributeNode) or \
                    target.identity is Identity.DataRange and source.isItem(Item.RoleNode, Item.RoleChainNode):
                    # Identity mismatch.
                    return False

        return True

    def updateLabel(self, points):
        """
        Update the edge label (both text and position).
        :param points: a list of points defining the edge of this label.
        """
        if self.target and self.target.isItem(Item.PropertyAssertionNode, Item.RoleChainNode):
            self.label.setVisible(True)
            self.label.setText(str(self.target.inputs.index(self.id) + 1))
            self.label.updatePos(points)
        else:
            self.label.setVisible(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :param scene: the scene where the element will be inserted.
        :param E: the Graphol document element entry.
        :rtype: AbstractEdge
        """
        points = []

        # extract all the breakpoints from the edge children
        children = E.elementsByTagName('line:point')
        for i in range(0, children.count()):
            P = children.at(i).toElement()
            point = QPointF(int(P.attribute('x')), int(P.attribute('y')))
            points.append(point)

        kwargs = {
            'scene': scene,
            'id': E.attribute('id'),
            'source': scene.node(E.attribute('source')),
            'target': scene.node(E.attribute('target')),
            'breakpoints': points[1:-1],
            'functional': bool(int(E.attribute('functional', '0'))),
        }

        edge = cls(**kwargs)

        # set the anchor points only if they are inside the endpoint shape: users can modify the .graphol file manually,
        # changing anchor points coordinates, which will result in an edge floating in the scene without being bounded
        # by endpoint shapes. Not setting the anchor point will make the edge use the default one (node center point)

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        # map the edge over the source and target nodes
        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        edge.updateEdge()
        return edge

    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        ## ROOT ELEMENT
        edge = document.createElement('edge')
        edge.setAttribute('source', self.source.id)
        edge.setAttribute('target', self.target.id)
        edge.setAttribute('id', self.id)
        edge.setAttribute('type', self.xmlname)
        edge.setAttribute('functional', int(self.functional))

        ## LINE GEOMETRY
        source = self.source.anchor(self)
        target = self.target.anchor(self)

        for p in [source] + self.breakpoints + [target]:
            point = document.createElement('line:point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            edge.appendChild(point)

        return edge

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        for shape in self.handles.values():
            path.addEllipse(shape)
        for shape in self.anchors.values():
            path.addEllipse(shape)

        return path.controlPointRect()

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.path)
        path.addPolygon(self.head)

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
            for shape in self.anchors.values():
                path.addEllipse(shape)

        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY UPDATE                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :param target: the endpoint of this edge.
        """
        boxSize = self.selectionSize
        headSize = self.headSize
        sourceNode = self.source
        targetNode = self.target
        sourcePos = self.source.anchor(self)
        targetPos = target or self.target.anchor(self)

        self.updateAnchors()
        self.updateHandles()

        ################################################################################################################
        #                                                                                                              #
        #   UPDATE EDGE PATH, SELECTION BOX, HEAD AND TAIL                                                             #
        #                                                                                                              #
        ################################################################################################################

        # get the list of visible subpaths for this edge
        collection = self.computePath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])

        def createSelectionBox(pos1, pos2, angle, size):
            """
            Constructs the selection polygon between pos1 and pos2 according to the given angle.
            :param pos1: the start point.
            :param pos2: the end point:
            :param angle: the angle of the line connecting pos1 and pos2.
            :param size: the size of the selection polygon.
            :rtype: QPolygonF
            """
            rad = radians(angle)
            x = size / 2 * sin(rad)
            y = size / 2 * cos(rad)
            a = QPointF(+x, +y)
            b = QPointF(-x, -y)
            return QPolygonF([pos1 + a, pos1 + b, pos2 + b, pos2 + a])

        def createHead(pos1, angle, size):
            """
            Create the head polygon.
            :param pos1: the head point of the polygon.
            :param angle: the angle of the line connecting pos1 to the previous breakpoint.
            :param size: the size of the tail of the polygon.
            :rtype: QPolygonF
            """
            rad = radians(angle)
            pos2 = pos1 - QPointF(sin(rad + M_PI / 4.0) * size, cos(rad + M_PI / 4.0) * size)
            pos3 = pos2 - QPointF(sin(rad + 3.0 / 4.0 * M_PI) * size, cos(rad + 3.0 / 4.0 * M_PI) * size)
            pos4 = pos3 - QPointF(sin(rad - 3.0 / 4.0 * M_PI) * size, cos(rad - 3.0 / 4.0 * M_PI) * size)
            return QPolygonF([pos1, pos2, pos3, pos4])

        def createTail(pos1, angle, size):
            """
            Create the tail line.
            :param pos1: the intersection point between the edge and the souce shape.
            :param angle: the angle of the line connecting pos1 to the next breakpoint.
            :param size: the size of the tail of the polygon.
            :rtype: QLineF
            """
            rad = radians(angle)
            pos2 = pos1 + QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
            pos3 = pos1 + QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
            return QLineF(pos2, pos3)

        self.path = QPainterPath()
        self.selection = QPainterPath()

        points = [] # will store all the points defining the edge not to recompute the path to update the label
        append = points.append  # keep this shortcut and the one below since it saves a lot of computation
        extend = points.extend  # more: http://blog.cdleary.com/2010/04/efficiency-of-list-comprehensions/

        if len(collection) == 0:

            self.head = QPolygonF()
            self.tail = QLineF()

        elif len(collection) == 1:

            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                self.path.moveTo(p1)
                self.path.lineTo(p2)
                self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))
                self.head = createHead(p2, subpath.angle(), headSize)
                if self.functional:
                    self.tail = createTail(p1, subpath.angle(), headSize)
                extend((p1, p2))

        elif len(collection) > 1:

            subpath1 = collection[0]
            subpathN = collection[-1]
            p11 = sourceNode.intersection(subpath1)
            p22 = targetNode.intersection(subpathN)

            if p11 and p22:

                p12 = subpath1.p2()
                p21 = subpathN.p1()

                self.path.moveTo(p11)
                self.path.lineTo(p12)
                self.selection.addPolygon(createSelectionBox(p11, p12, subpath1.angle(), boxSize))
                extend((p11, p12))

                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    self.path.moveTo(p1)
                    self.path.lineTo(p2)
                    self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))
                    append(p2)

                self.path.moveTo(p21)
                self.path.lineTo(p22)
                self.selection.addPolygon(createSelectionBox(p21, p22, subpathN.angle(), boxSize))
                append(p22)

                self.head = createHead(p22, subpathN.angle(), headSize)
                if self.functional:
                    self.tail = createTail(p11, subpath1.angle(), headSize)

        self.updateZValue()
        self.updateLabel(points)
        self.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        lineWidth = 54
        headSize = 8  # length of the head side
        headSpan = 4  # offset between line end and head end (this is needed
                      # to prevent artifacts to be visible on low res screens)

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the line
        line_p1 = QPointF(((kwargs['w'] - lineWidth) / 2), kwargs['h'] / 2)
        line_p2 = QPointF(((kwargs['w'] - lineWidth) / 2) + lineWidth - (headSpan / 2), kwargs['h'] / 2)
        line = QLineF(line_p1, line_p2)

        angle = radians(line.angle())

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (headSpan / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 4.0) * headSize, cos(angle + M_PI / 4.0) * headSize)
        p3 = p2 - QPointF(sin(angle + 3.0 / 4.0 * M_PI) * headSize, cos(angle + 3.0 / 4.0 * M_PI) * headSize)
        p4 = p3 - QPointF(sin(angle - 3.0 / 4.0 * M_PI) * headSize, cos(angle - 3.0 / 4.0 * M_PI) * headSize)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3, p4])

        # Initialize dashed pen for the line
        linePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
        linePen.setDashPattern([3, 3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(linePen)
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.drawPolygon(head)

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        if self.canDraw():

            scene = self.scene()

            # Draw the selection path if needed
            if scene.mode in (DiagramMode.Idle, DiagramMode.NodeMove) and self.isSelected():
                painter.setRenderHint(QPainter.Antialiasing)
                painter.fillPath(self.selection, self.selectionBrush)

            # Draw the edge path
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.shapePen)
            painter.drawPath(self.path)

            # Draw the head polygon
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.headPen)
            painter.setBrush(self.headBrush)
            painter.drawPolygon(self.head)

            # Draw the tail line
            if self.functional:
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.headPen)
                painter.drawLine(self.tail)

            if self.isSelected():

                # Draw breakpoint handles
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.handlePen)
                painter.setBrush(self.handleBrush)
                for rect in self.handles.values():
                    painter.drawEllipse(rect)

                # Draw anchor points
                if self.target:
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setPen(self.handlePen)
                    painter.setBrush(self.handleBrush)
                    for rect in self.anchors.values():
                        painter.drawEllipse(rect)