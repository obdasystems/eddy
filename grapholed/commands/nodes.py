 # -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPolygonF
from PyQt5.QtWidgets import QUndoCommand

from grapholed.datatypes import RestrictionType


class CommandNodeAdd(QUndoCommand):
    """
    This command is used to add nodes to the scene.
    """
    def __init__(self, scene, node):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node being added.
        """
        super().__init__('add {0} node'.format(node.name))
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
        :param scene: the scene where this command is being performed.
        :param node: the node whose zValue is changing.
        :param zValue: the new zValue.
        """
        super().__init__('change {0} node Z value'.format(node.name))
        self.scene = scene
        self.node = node
        self.zvalue1 = node.zValue()
        self.zvalue2 = zValue

    def redo(self):
        """redo the command"""
        self.node.setZValue(self.zvalue2)
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.setZValue(self.zvalue1)
        self.node.updateEdges()
        self.scene.updated.emit()


class CommandNodeRezize(QUndoCommand):
    """
    This command is used to resize nodes.
    """
    def __init__(self, scene, node):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose resizing operation we want to Undo.
        """
        super().__init__('resize {0} node'.format(node.name))
        self.node = node
        self.scene = scene
        self.data2 = None
        self.data1 = {
            'shape': QRectF(self.node.rect) if hasattr(self.node, 'rect') else QPolygonF(self.node.polygon),
            'anchors': {edge: pos for edge, pos in self.node.anchors.items()},
            'label': {'moved': self.node.label.moved}
        }

    def end(self):
        """
        End the command collecting new data.
        """
        self.data2 = {
            'shape': QRectF(self.node.rect) if hasattr(self.node, 'rect') else QPolygonF(self.node.polygon),
            'anchors': {edge: pos for edge, pos in self.node.anchors.items()},
            'label': {'moved': self.node.label.moved}
        }

    def redo(self):
        """redo the command"""
        if self.data2:
            if hasattr(self.node, 'rect'):
                self.node.rect = self.data2['shape']
            else:
                self.node.polygon = self.data2['shape']

            for edge, pos in self.data2['anchors'].items():
                self.node.setAnchor(edge, pos)

            self.node.updateHandlesPos()
            self.node.updateLabelPos(moved=self.data2['label']['moved'])
            self.node.updateEdges()
            self.node.update()

            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        if hasattr(self.node, 'rect'):
            self.node.rect = self.data1['shape']
        else:
            self.node.polygon = self.data1['shape']

        for edge, pos in self.data1['anchors'].items():
            self.node.setAnchor(edge, pos)

        self.node.updateHandlesPos()
        self.node.updateLabelPos(moved=self.data2['label']['moved'])
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
        :param scene: the scene where this command is being performed.
        :param pos1: a dictionary containing node old positions' data.
        :param pos2: a dictionary containing node new positions' data.
        """
        self.scene = scene
        self.pos1 = pos1
        self.pos2 = pos2

        if len(pos1['nodes']) != 1:
            params = 'move {0} nodes'.format(len(pos1['nodes']))
        else:
            params = 'move {0} node'.format(next(iter(pos1['nodes'].keys())).name)

        super().__init__(params)

    def redo(self):
        """redo the command"""
        # update edges breakpoints
        for edge, breakpoints in self.pos2['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # update nodes positions
        for node, data in self.pos2['nodes'].items():
            node.setPos(data['pos'])
            # update edge anchors
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # handle edge updates in a separate cycle: calling node.updateEdges() here seems
        # to be causing troubles, leaving the diagram scene with edges pointing nowhere
        for edge in set(self.pos2['edges'].keys()) | set(x for n in self.pos2['nodes'].keys() for x in n.edges):
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # update edges breakpoints
        for edge, breakpoints in self.pos1['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # update nodes positions
        for node, data in self.pos1['nodes'].items():
            node.setPos(data['pos'])
            # update edge anchors
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # handle edge updates in a separate cycle: calling node.updateEdges() here seems
        # to be causing troubles, leaving the diagram scene with edges pointing nowhere
        for edge in set(self.pos1['edges'].keys()) | set(x for n in self.pos1['nodes'].keys() for x in n.edges):
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
        :param scene: the scene where this command is being performed.
        :param node: the node whose label is being moved.
        :param label: the label that is being moved.
        """
        super().__init__('move {0} node label'.format(node.name))
        self.scene = scene
        self.label = label
        self.pos1 = label.pos()
        self.pos2 = None

    def end(self, pos):
        """
        End the command collecting new data.
        :param pos: the new position of the label.
        """
        self.pos2 = pos

    def redo(self):
        """redo the command"""
        if self.pos2 is not None:
            self.label.setPos(self.pos2)
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.label.setPos(self.pos1)
        self.scene.updated.emit()


class CommandNodeLabelEdit(QUndoCommand):
    """
    This command is used to edit nodes labels.
    """
    def __init__(self, scene, node, label, text):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose label is being edited.
        :param label: the label whose text is being edited.
        :param text: the text of the label before the edit.
        """
        super().__init__('edit {0} node label'.format(node.name))
        self.scene = scene
        self.label = label
        self.text1 = text
        self.text2 = None

    def end(self, text):
        """
        End the command collecting new data.
        :param text: the new label text.
        """
        self.text2 = text

    def isTextChanged(self, text):
        """
        Checks whether the given text is different from the old value.
        :param text: the text to compare with the old value.
        """
        return self.text1 != text

    def redo(self):
        """redo the command"""
        if self.text2:
            self.label.setText(self.text2)
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.label.setText(self.text1)
        self.scene.updated.emit()


class CommandNodeValueDomainSelectDatatype(QUndoCommand):
    """
    This command is used to change the datatype of a value-domain node.
    """
    def __init__(self, scene, node, datatype):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose datatype is being changed.
        :param datatype: the new datatype.
        """
        super().__init__('change {0} datatype'.format(node.name))
        self.scene = scene
        self.node = node
        self.data1 = node.datatype
        self.data2 = datatype

    def redo(self):
        """redo the command"""
        self.node.datatype = self.data2
        self.node.label.setText(self.node.datatype.value)
        self.node.updateRect()
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.datatype = self.data1
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
        :param scene: the scene where this command is being executed.
        :param node1: the node being replaced.
        :param node2: the replacement node.
        """
        super().__init__('switch {0} to {1}'.format(node1.name, node2.name))
        self.scene = scene
        self.node1 = node1
        self.node2 = node2

    def redo(self):
        """redo the command"""
        # add the new node to the scene
        self.scene.addItem(self.node2)

        # move the anchor points
        for edge, point in self.node1.anchors.items():
            self.node2.setAnchor(edge, point)

        # move the edges
        for edge in self.node1.edges:
            if edge.source is self.node1:
                edge.source = self.node2
            if edge.target is self.node1:
                edge.target = self.node2
            # IMPORTANT: clear anchors dict in the edge or we will have also the
            # reference  of the previous node since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()
            self.node2.addEdge(edge)

        # clear edge and anchor references from node1
        self.node1.anchors.clear()
        self.node1.edges.clear()

        # remove the old node from the scene
        self.scene.removeItem(self.node1)

        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # add back to the scene the old node
        self.scene.addItem(self.node1)

        # move the anchor points back
        for edge, point in self.node2.anchors.items():
            self.node1.setAnchor(edge, point)

        # move the edges
        for edge in self.node2.edges:
            if edge.source is self.node2:
                edge.source = self.node1
            if edge.target is self.node2:
                edge.target = self.node1
            # IMPORTANT: clear anchors dict in the edge or we will have also the
            # reference  of the previous node since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()
            self.node1.addEdge(edge)

        # clear edge and anchor references from node2
        self.node2.anchors.clear()
        self.node2.edges.clear()

        # remove the new node from the scene
        self.scene.removeItem(self.node2)

        # emit updated signal
        self.scene.updated.emit()


class CommandNodeSquareChangeRestriction(QUndoCommand):
    """
    This command is used to change the restriction of square based constructor nodes.
    """
    def __init__(self, scene, node, restriction, cardinality=None):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose restriction is being changed.
        :param restriction: the new restriction type.
        """
        self.node = node
        self.scene = scene
        self.restriction1 = self.node.restriction
        self.cardinality1 = self.node.cardinality
        self.restriction2 = restriction
        self.cardinality2 = dict(min=None, max=None) if not cardinality else cardinality

        value = restriction.label
        if restriction is RestrictionType.cardinality:
            value = value.format(min=self.s(cardinality['min']), max=self.s(cardinality['max']))

        super().__init__('change {0} to {1}'.format(node.name, value))

    @staticmethod
    def s(x):
        """
        Return a valid string representation for the cardinality value.
        :param x: the value to represent.
        """
        return str(x) if x is not None else '-'

    def redo(self):
        """redo the command"""
        if self.restriction2 is RestrictionType.cardinality:
            self.node.restriction = self.restriction2
            self.node.cardinality = self.cardinality2
            self.node.label.setText(self.node.restriction.label.format(min=self.s(self.node.cardinality['min']),
                                                                       max=self.s(self.node.cardinality['max'])))
        else:
            self.node.restriction = self.restriction2
            self.node.cardinality = dict(min=None, max=None)
            self.node.label.setText(self.node.restriction.label)

        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        if self.restriction1 is RestrictionType.cardinality:
            self.node.restriction = self.restriction1
            self.node.cardinality = self.cardinality1
            self.node.label.setText(self.node.restriction.label.format(min=self.s(self.node.cardinality['min']),
                                                                       max=self.s(self.node.cardinality['max'])))
        else:
            self.node.restriction = self.restriction1
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
        :param node: the node whose url is changing.
        :param url: the new url.
        """
        super().__init__('change {0} node URL'.format(node.name))
        self.node = node
        self.url1 = node.url
        self.url2 = url

    def redo(self):
        """redo the command"""
        self.node.url = self.url2

    def undo(self):
        """undo the command"""
        self.node.url = self.url1


class CommandNodeSetDescription(QUndoCommand):
    """
    This command is used to change the description attached to a node.
    """
    def __init__(self, node, description):
        """
        Initialize the command.
        :param node: the node whose description is changing.
        :param description: the new description.
        """
        super().__init__('change {0} node description'.format(node.name))
        self.node = node
        self.description1 = node.description
        self.description2 = description

    def redo(self):
        """redo the command"""
        self.node.description = self.description2

    def undo(self):
        """undo the command"""
        self.node.description = self.description1


class CommandConceptNodeSetSpecial(QUndoCommand):
    """
    This command is used to change the special attribute of Concept nodes.
    """
    def __init__(self, scene, node, special):
        """
        Initilize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose special attribute is changing.
        :param special: the special value.
        """
        self.node = node
        self.scene = scene

        if not special:
            # remove special: TOP|BOTTOM -> None
            self.data1 = {'special': node.special, 'text': node.special.value, 'pos': node.label.defaultPos()}
            self.data2 = {'special': None, 'text': node.label.defaultText, 'pos': node.label.defaultPos()}
            super().__init__('remove {0} from {1} node'.format(node.special.value, node.name))
        else:
            if node.special:
                # change special TOP <-> BOTTOM
                self.data1 = {'special': node.special, 'text': node.special.value, 'pos': node.label.defaultPos()}
                self.data2 = {'special': special, 'text': special.value, 'pos': node.label.defaultPos()}
                super().__init__('change {0} node from {1} to {2}'.format(node.name, node.special.value, special.value))
            else:
                # set as special: None -> TOP|BOTTOM
                self.data1 = {'special': None, 'text': node.label.text(), 'pos': node.label.pos()}
                self.data2 = {'special': special, 'text': special.value, 'pos': node.label.defaultPos()}
                super().__init__('set {0} node as {1}'.format(node.name, special.value))

    def redo(self):
        """redo the command"""
        self.node.special = self.data2['special']
        self.node.setLabelText(self.data2['text'])
        self.node.setLabelPos(self.data2['pos'])
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        self.node.special = self.data1['special']
        self.node.setLabelText(self.data1['text'])
        self.node.setLabelPos(self.data1['pos'])
        self.scene.updated.emit()


class CommandNodeChangeInputOrder(QUndoCommand):
    """
    This command is used to change the order of Role chain and Property assertion inputs.
    """
    def __init__(self, scene, node, inputs):
        """
        Initilize the command.
        :param scene: the scene where this command is being performed.
        :param node: the node whose special attribute is changing.
        :param inputs: the new inputs order.
        """
        self.node = node
        self.scene = scene
        self.inputs1 = node.inputs
        self.inputs2 = inputs
        super().__init__('change {0} node inputs order'.format(node.name))

    def redo(self):
        """redo the command"""
        self.node.inputs = self.inputs2
        self.node.updateEdges()
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        self.node.inputs = self.inputs1
        self.node.updateEdges()
        self.scene.updated.emit()


class CommandNodeChangeBrush(QUndoCommand):
    """
    This command is used to change the brush of predicate nodes.
    """
    def __init__(self, scene, nodes, brush):
        """
        Initilize the command.
        :param scene: the scene where this command is being performed.
        :param nodes: a set of nodes on which to change the brush.
        :param brush: the new brush value.
        """
        self.scene = scene
        self.nodes = nodes
        self.brush = {x: {'from': x.brush, 'to': brush} for x in nodes}
        if len(nodes) != 1:
            super().__init__('change color of {0} nodes'.format(len(nodes)))
        else:
            super().__init__('change {0} node color'.format(next(iter(nodes)).name))

    def redo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['to']
            node.update()
        self.scene.updated.emit()

    def undo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['from']
            node.update()
        self.scene.updated.emit()