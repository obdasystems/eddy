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


from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPolygonF
from PyQt5.QtWidgets import QUndoCommand

from eddy.core.datatypes import Restriction, DistinctList, Item
from eddy.core.functions import identify


class CommandNodeAdd(QUndoCommand):
    """
    This command is used to add nodes to the scene.
    """
    def __init__(self, scene, node):
        """
        Initialize the command.
        """
        super().__init__('add {}'.format(node.name))
        self.scene = scene
        self.node = node

    def redo(self):
        """redo the command"""
        self.scene.addItem(self.node)
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.scene.removeItem(self.node)
        self.scene.updated.emit()


class CommandNodeSetZValue(QUndoCommand):
    """
    This command is used to change the Z value of scene nodes.
    """
    def __init__(self, scene, node, zValue):
        """
        Initialize the command.
        """
        super().__init__('change {} Z value'.format(node.name))
        self.node = node
        self.scene = scene
        self.zValue = {'redo': zValue, 'undo': node.zValue()}

    def redo(self):
        """redo the command"""
        self.node.setZValue(self.zValue['redo'])
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.setZValue(self.zValue['undo'])
        self.node.updateEdges()
        self.scene.updated.emit()


class CommandNodeRezize(QUndoCommand):
    """
    This command is used to resize nodes.
    """
    def __init__(self, scene, node):
        """
        Initialize the command.
        """
        super().__init__('resize {}'.format(node.name))
        self.node = node
        self.scene = scene
        self.data = {
            'undo': {
                'polygon': QRectF(node.polygon) if isinstance(node.polygon, QRectF) else QPolygonF(node.polygon),
                'anchors': {edge: pos for edge, pos in node.anchors.items()},
                'label': {'moved': node.label.moved}
            }
        }

    def end(self):
        """
        End the command collecting new data.
        """
        node = self.node
        self.data['redo'] = {
            'polygon': QRectF(node.polygon) if isinstance(node.polygon, QRectF) else QPolygonF(node.polygon),
            'anchors': {edge: pos for edge, pos in node.anchors.items()},
            'label': {'moved': node.label.moved}
        }

    def redo(self):
        """redo the command"""
        if 'redo' in self.data:
            self.node.polygon = self.data['redo']['polygon']
            for edge, pos in self.data['redo']['anchors'].items():
                self.node.setAnchor(edge, pos)
            self.node.updateHandlesPos()
            self.node.updateLabelPos(moved=self.data['redo']['label']['moved'])
            self.node.updateEdges()
            self.node.update()
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.polygon = self.data['undo']['polygon']
        for edge, pos in self.data['undo']['anchors'].items():
            self.node.setAnchor(edge, pos)
        self.node.updateHandlesPos()
        self.node.updateLabelPos(moved=self.data['undo']['label']['moved'])
        self.node.updateEdges()
        self.node.update()
        self.scene.updated.emit()


class CommandNodeMove(QUndoCommand):
    """
    This command is used to move nodes (1 or more).
    """
    def __init__(self, scene, pos1, pos2):
        """
        Initialize the command.
        """
        self.scene = scene
        self.pos = {'redo': pos2, 'undo': pos1}

        if len(pos1['nodes']) != 1:
            params = 'move {} nodes'.format(len(pos1['nodes']))
        else:
            params = 'move {}'.format(next(iter(pos1['nodes'].keys())).name)

        super().__init__(params)

    def redo(self):
        """redo the command"""
        # update edges breakpoints
        for edge, breakpoints in self.pos['redo']['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # update nodes positions
        for node, data in self.pos['redo']['nodes'].items():
            node.setPos(data['pos'])
            # update edge anchors
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # update edges
        for edge in set(self.pos['redo']['edges'].keys()) | set(x for n in self.pos['redo']['nodes'].keys() for x in n.edges):
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # update edges breakpoints
        for edge, breakpoints in self.pos['undo']['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # update nodes positions
        for node, data in self.pos['undo']['nodes'].items():
            node.setPos(data['pos'])
            # update edge anchors
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # update edges
        for edge in set(self.pos['undo']['edges'].keys()) | set(x for n in self.pos['undo']['nodes'].keys() for x in n.edges):
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()


class CommandNodeLabelMove(QUndoCommand):
    """
    This command is used to move nodes labels.
    """
    def __init__(self, scene, node, label):
        """
        Initialize the command.
        """
        super().__init__('move {} label'.format(node.name))
        self.scene = scene
        self.label = label
        self.pos = {'undo': label.pos()}

    def end(self, pos):
        """
        End the command collecting new data.
        :type pos: QPointF
        """
        self.pos['redo'] = pos

    def redo(self):
        """redo the command"""
        if 'redo' in self.pos:
            self.label.setPos(self.pos['redo'])
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.label.setPos(self.pos['undo'])
        self.scene.updated.emit()


class CommandNodeLabelEdit(QUndoCommand):
    """
    This command is used to edit nodes labels.
    """
    def __init__(self, scene, node):
        """
        Initialize the command.
        """
        super().__init__('edit {} label'.format(node.name))
        self.node = node
        self.scene = scene
        self.text = {'undo': node.label.text().strip()}

    def end(self, text):
        """
        End the command collecting new data.
        :type text: str
        """
        self.text['redo'] = text.strip()

    def isTextChanged(self, text):
        """
        Checks whether the given text is different from the old value.
        :type text: str
        """
        return self.text['undo'] != text.strip()

    def redo(self):
        """redo the command"""
        if 'redo' in self.text:

            # remove the item from the old index
            if self.text['undo'] in self.scene.nodesByLabel:
                self.scene.nodesByLabel[self.text['undo']].remove(self.node)
                if not self.scene.nodesByLabel[self.text['undo']]:
                    del self.scene.nodesByLabel[self.text['undo']]

            # update the label text
            self.node.label.setText(self.text['redo'])

            # map the item over the new index
            if not self.text['redo'] in self.scene.nodesByLabel:
                self.scene.nodesByLabel[self.text['redo']] = DistinctList()
            self.scene.nodesByLabel[self.text['redo']].append(self.node)

            # if the label belongs to an individual identify all the connected enumeration nodes
            if self.node.isItem(Item.IndividualNode):
                f1 = lambda x: x.isItem(Item.InputEdge) and x.source is self.node
                f2 = lambda x: x.isItem(Item.EnumerationNode)
                for node in {n for n in [e.other(self.node) for e in self.node.edges if f1(e)] if f2(n)}:
                    identify(node)

            # emit update signal
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove the item from the old index
        if self.text['redo'] in self.scene.nodesByLabel:
            self.scene.nodesByLabel[self.text['redo']].remove(self.node)
            if not self.scene.nodesByLabel[self.text['redo']]:
                del self.scene.nodesByLabel[self.text['redo']]

        # update the label text
        self.node.label.setText(self.text['undo'])

        # map the item over the new index
        if not self.text['undo'] in self.scene.nodesByLabel:
            self.scene.nodesByLabel[self.text['undo']] = DistinctList()
        self.scene.nodesByLabel[self.text['undo']].append(self.node)

        # if the label belongs to an individual identify all the connected enumeration nodes
        if self.node.isItem(Item.IndividualNode):
            f1 = lambda x: x.isItem(Item.InputEdge) and x.source is self.node
            f2 = lambda x: x.isItem(Item.EnumerationNode)
            for node in {n for n in [e.other(self.node) for e in self.node.edges if f1(e)] if f2(n)}:
                identify(node)

        # emit update signal
        self.scene.updated.emit()


class CommandNodeValueDomainSelectDatatype(QUndoCommand):
    """
    This command is used to change the datatype of a value-domain node.
    """
    def __init__(self, scene, node, datatype):
        """
        Initialize the command.
        """
        super().__init__('change {} datatype'.format(node.name))
        self.scene = scene
        self.node = node
        self.data = {'redo': datatype, 'undo': node.datatype}

    def redo(self):
        """redo the command"""
        self.node.datatype = self.data['redo']
        self.node.label.setText(self.node.datatype.value)
        self.node.updateRect()
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.datatype = self.data['undo']
        self.node.label.setText(self.node.datatype.value)
        self.node.updateRect()
        self.node.updateEdges()
        self.scene.updated.emit()


class CommandNodeHexagonSwitchTo(QUndoCommand):
    """
    This command is used to change the class of hexagon based constructor nodes.
    """
    def __init__(self, scene, node1, node2):
        """
        Initialize the command.
        """
        super().__init__('switch {} to {}'.format(node1.name, node2.name))
        self.scene = scene
        self.node = {'redo': node2, 'undo': node1}

    def redo(self):
        """redo the command"""
        # add the new node to the scene
        self.scene.addItem(self.node['redo'])

        # move the anchor points
        for edge, point in self.node['undo'].anchors.items():
            self.node['redo'].setAnchor(edge, point)

        # move the edges
        for edge in self.node['undo'].edges:
            if edge.source is self.node['undo']:
                edge.source = self.node['redo']
            if edge.target is self.node['undo']:
                edge.target = self.node['redo']

            self.node['redo'].addEdge(edge)
            # IMPORTANT: clear anchors dict in the edge or we will have also the
            # reference of the previous node since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()

        # clear edge and anchor references from node1
        self.node['undo'].anchors.clear()
        self.node['undo'].edges.clear()

        # remove the old node from the scene
        self.scene.removeItem(self.node['undo'])

        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # add back to the scene the old node
        self.scene.addItem(self.node['undo'])

        # move the anchor points back
        for edge, point in self.node['redo'].anchors.items():
            self.node['undo'].setAnchor(edge, point)

        # move the edges
        for edge in self.node['redo'].edges:
            if edge.source is self.node['redo']:
                edge.source = self.node['undo']
            if edge.target is self.node['redo']:
                edge.target = self.node['undo']

            self.node['undo'].addEdge(edge)
            # IMPORTANT: clear anchors dict in the edge or we will have also the
            # reference of the previous node since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()

        # clear edge and anchor references from node2
        self.node['redo'].anchors.clear()
        self.node['redo'].edges.clear()

        # remove the new node from the scene
        self.scene.removeItem(self.node['redo'])

        # emit updated signal
        self.scene.updated.emit()


class CommandNodeSquareChangeRestriction(QUndoCommand):
    """
    This command is used to change the restriction of square based constructor nodes.
    """
    def __init__(self, scene, node, restriction, cardinality=None):
        """
        Initialize the command.
        """
        self.node = node
        self.scene = scene
        self.restriction = {'redo': restriction, 'undo': self.node.restriction}
        self.cardinality = {'redo': dict(min=None, max=None) if not cardinality else cardinality, 'undo': self.node.cardinality}
        value = restriction.label
        if restriction is Restriction.Cardinality:
            value = value.format(min=self.s(cardinality['min']), max=self.s(cardinality['max']))
        super().__init__('change {} restriction to {}'.format(node.name, value))

    @staticmethod
    def s(x):
        """
        Return a valid string representation for the cardinality value.
        :type x: str | int | None
        """
        return str(x) if x is not None else '-'

    def redo(self):
        """redo the command"""
        if self.restriction['redo'] is Restriction.Cardinality:
            self.node.restriction = self.restriction['redo']
            self.node.cardinality = self.cardinality['redo']
            self.node.label.setText(self.node.restriction.label.format(min=self.s(self.node.cardinality['min']),
                                                                       max=self.s(self.node.cardinality['max'])))
        else:
            self.node.restriction = self.restriction['redo']
            self.node.cardinality = dict(min=None, max=None)
            self.node.label.setText(self.node.restriction.label)

        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        if self.restriction['undo'] is Restriction.Cardinality:
            self.node.restriction = self.restriction['undo']
            self.node.cardinality = self.cardinality['undo']
            self.node.label.setText(self.node.restriction.label.format(min=self.s(self.node.cardinality['min']),
                                                                       max=self.s(self.node.cardinality['max'])))
        else:
            self.node.restriction = self.restriction['undo']
            self.node.cardinality = dict(min=None, max=None)
            self.node.label.setText(self.node.restriction.label)

        # emit updated signal
        self.scene.updated.emit()


class CommandNodeSetURL(QUndoCommand):
    """
    This command is used to change the url attached to a node.
    """
    def __init__(self, node, url):
        """
        Initialize the command.
        """
        super().__init__('change {} URL'.format(node.name))
        self.url = {'redo': url, 'undo': node.url}
        self.node = node

    def redo(self):
        """redo the command"""
        self.node.url = self.url['redo']

    def undo(self):
        """undo the command"""
        self.node.url = self.url['undo']


class CommandNodeSetDescription(QUndoCommand):
    """
    This command is used to change the description attached to a node.
    """
    def __init__(self, node, description):
        """
        Initialize the command.
        """
        super().__init__('change {} description'.format(node.name))
        self.description = {'redo': description, 'undo': node.description}
        self.node = node

    def redo(self):
        """redo the command"""
        self.node.description = self.description['redo']

    def undo(self):
        """undo the command"""
        self.node.description = self.description['undo']


class CommandNodeSetSpecial(QUndoCommand):
    """
    This command is used to change the special attribute of nodes.
    """
    def __init__(self, scene, node, special):
        """
        Initilize the command.
        """
        self.node = node
        self.scene = scene

        if not special:
            # remove special: TOP|BOTTOM -> None
            super().__init__('remove {} from {}'.format(node.special.value, node.name))
            self.data = {
                'undo': {'special': node.special, 'text': node.special.value, 'pos': node.label.defaultPos()},
                'redo': {'special': None, 'text': node.label.defaultText, 'pos': node.label.defaultPos()}
            }
        else:
            if node.special:
                # change special TOP <-> BOTTOM
                super().__init__('change {} from {} to {}'.format(node.name, node.special.value, special.value))
                self.data = {
                    'undo': {'special': node.special, 'text': node.special.value, 'pos': node.label.defaultPos()},
                    'redo': {'special': special, 'text': special.value, 'pos': node.label.defaultPos()}
                }
            else:
                # set as special: None -> TOP|BOTTOM
                super().__init__('set {} as {}'.format(node.name, special.value))
                self.data = {
                    'undo': {'special': None, 'text': node.label.text(), 'pos': node.label.pos()},
                    'redo': {'special': special, 'text': special.value, 'pos': node.label.defaultPos()}
                }

    def redo(self):
        """redo the command"""
        self.node.special = self.data['redo']['special']
        self.node.setLabelText(self.data['redo']['text'])
        self.node.setLabelPos(self.data['redo']['pos'])
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        self.node.special = self.data['undo']['special']
        self.node.setLabelText(self.data['undo']['text'])
        self.node.setLabelPos(self.data['undo']['pos'])
        self.scene.updated.emit()


class CommandNodeChangeInputOrder(QUndoCommand):
    """
    This command is used to change the order of Role chain and Property assertion inputs.
    """
    def __init__(self, scene, node, inputs):
        """
        Initilize the command.
        """
        self.node = node
        self.scene = scene
        self.inputs = {'redo': inputs, 'undo': node.inputs}
        super().__init__('change {} inputs order'.format(node.name))

    def redo(self):
        """redo the command"""
        self.node.inputs = self.inputs['redo']
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        self.node.inputs = self.inputs['undo']
        self.node.updateEdges()
        self.scene.updated.emit()


class CommandNodeChangeBrush(QUndoCommand):
    """
    This command is used to change the brush of predicate nodes.
    """
    def __init__(self, scene, nodes, brush):
        """
        Initilize the command.
        """
        self.scene = scene
        self.nodes = nodes
        self.brush = {x: {'undo': x.brush, 'redo': brush} for x in nodes}
        if len(nodes) != 1:
            super().__init__('change color of {} nodes'.format(len(nodes)))
        else:
            super().__init__('change {} color'.format(next(iter(nodes)).name))

    def redo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['redo']
            node.update()
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['undo']
            node.update()
        self.scene.updated.emit()