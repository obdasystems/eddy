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


import os
import sys

from enum import Enum, unique, IntEnum
from types import DynamicClassAttribute

from PyQt5.QtGui import QFont

from eddy.core.functions.fsystem import expandPath


@unique
class Color(Enum):
    """
    This class defines predicate nodes available colors.
    """
    __order__ = 'White Yellow Orange Red Purple Blue Teal Green Lime'

    White = '#fcfcfc'
    Yellow = '#f0e50c'
    Orange = '#f29210'
    Red = '#e41b20'
    Purple = '#724e9d'
    Blue = '#1760ab'
    Teal = '#16ccef'
    Green = '#2da735'
    Lime = '#86f42e'

    @classmethod
    def forValue(cls, value):
        """
        Returns the color matching the given HEX code.
        :type value: str
        :rtype: Color
        """
        for x in cls:
            if x.value == value.lower():
                return x
        return None


@unique
class DiagramMode(IntEnum):
    """
    This class defines the diagram scene operational modes.
    """
    Idle = 0 # idle mode
    NodeInsert = 1 # node insertion
    NodeMove = 2 # node movement
    NodeResize = 3 # node interactive resize
    EdgeInsert = 4 # edge insertion
    EdgeAnchorPointMove = 5 # edge anchor point movement
    EdgeBreakPointMove = 6 # edge breakpoint movement
    LabelMove = 7 # text label edit
    LabelEdit = 8 # text label movement
    RubberBandDrag = 9 # multi selection
    SceneDrag = 10 # scene being dragged by the mouse


class DistinctList(list):
    """
    Extends python default list making sure not to have duplicated elements.
    """
    def __init__(self, collection=None):
        """
        Initialize the DistinctList.
        :type collection: iterable
        """
        super(DistinctList, self).__init__()
        if collection:
            for item in collection:
                self.append(item)

    def append(self, p_object):
        """
        Append the given element at the end of the list.
        :type p_object: mixed
        """
        if p_object not in self:
            super(DistinctList, self).append(p_object)

    def extend(self, iterable):
        """
        Extends the current list by appending items of the given iterable (if they are not in the list already).
        :type iterable: iterable
        """
        for item in iterable:
            self.append(item)

    def insert(self, index, p_object):
        """
        Insert the given element in the given index.
        :type index: int
        :type p_object: mixed
        """
        if p_object in self:
            index2 = self.index(p_object)
            if index2 < index:
                index -= 1
            self.remove(p_object)
        super(DistinctList, self).insert(index, p_object)

    def remove(self, p_object):
        """
        Silently remove the given element from the list.
        :type p_object: mixed
        """
        try:
            super(DistinctList, self).remove(p_object)
        except ValueError:
            pass

    def sanitize(self, f_sanitize):
        """
        Remove all the elements in this list for which the given callable returns False.
        :type f_sanitize: callable.
        """
        for p_object in self:
            if not f_sanitize(p_object):
                self.remove(p_object)

    def __add__(self, p_object):
        """ x.__add__(y) <==> x+y """
        copy = self[:]
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            copy.extend(p_object)
        else:
            copy.append(p_object)
        return copy

    def __radd__(self, p_object):
        """ x.__radd__(y) <==> y+x """
        copy = self[:]
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            for x in range(len(p_object)):
                copy.insert(x, p_object[x])
        else:
            copy.insert(0, p_object)
        return copy

    def __iadd__(self, p_object):
        """ x.__iadd__(y) <==> x+=y """
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            self.extend(p_object)
        else:
            self.append(p_object)
        return self

    def __getitem__(self, p_object):
        """ x.__getitem__(y) <==> x[y] """
        if isinstance(p_object, slice):
            return DistinctList([super(DistinctList, self).__getitem__(x) for x in range(*p_object.indices(len(self)))])
        else:
            return super(DistinctList, self).__getitem__(p_object)

    def __getslice__(self, i, j):
        """
        x.__getslice__(i, j) <==> x[i:j] (built-in CPython types needs this one).
        Use of negative indices is not supported.
        """
        return self[max(0, i):max(0, j):]


class File(object):
    """
    This class is used to manage Files.
    """
    def __init__(self, path=None):
        """
        Initialize the File.
        :type path: str
        """
        self._path = expandPath(path) if path else None

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def edited(self):
        """
        Returns the timestamp when the file has been last modified.
        :rtype: int
        """
        if self.exists():
            return os.path.getmtime(self.path)
        return 0

    @property
    def path(self):
        """
        Returns the path of the File.
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """
        Set the path of the File.
        :type path: str.
        """
        self._path = expandPath(path)

    @property
    def name(self):
        """
        Returns the name of the File.
        :rtype: str
        """
        if not self.path:
            return 'Untitled'
        return os.path.basename(os.path.normpath(self.path))

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def exists(self):
        """
        Tells whether the file exists.
        :rtype: bool
        """
        return self.path and os.path.isfile(self.path)

    def write(self, string, path=None):
        """
        Write the content of 'string' in 'path'.
        :type string: str
        :type path: str
        """
        path = path or self.path
        temp = expandPath('@home/.{}'.format(os.path.basename(os.path.normpath(path))))

        with open(temp, mode='wb') as file:
            file.write(string.encode(encoding='UTF-8'))
            if os.path.isfile(path):
                os.remove(path)
            os.rename(temp, path)
            self.path = path

@unique
class Filetype(Enum):
    """
    This class defines all the available file types supported for graphol document export.
    """
    __order__ = 'Graphol Owl Pdf'

    Graphol = 'Graphol (*.graphol)'
    Owl = 'Owl (*.owl)'
    Pdf = 'PDF (*.pdf)'

    @classmethod
    def forValue(cls, value):
        """
        Returns the filetype matching the given value.
        :type value: str
        :rtype: Filetype
        """
        for x in cls:
            if x.value == value:
                return x
        return None

    @DynamicClassAttribute
    def suffix(self):
        """
        The suffix associated with the Enum member.
        :rtype: str
        """
        return {
            Filetype.Graphol: '.graphol',
            Filetype.Owl: '.owl',
            Filetype.Pdf: '.pdf'
        }[self]


class Font(QFont):
    """
    This class extends PyQt5.QtGui.QFont providing better font rendering on different platforms.
    """
    def __init__(self, family, size=12, weight=-1, italic=False):
        """
        Contruct a new Font instance using the given parameters.
        :type family: str
        :type size: float
        :type weight: float
        :type italic: bool
        """
        if not sys.platform.startswith('darwin'):
            size = int(round(size * 0.75))
        super().__init__(family, size, weight, italic)


@unique
class Identity(IntEnum):
    """
    This class defines all the identities a Graph node may assume.
    """
    Neutral = 0
    Concept = 1
    Role = 2
    Attribute = 3
    DataRange = 4
    Individual = 5
    Literal = 6
    Link = 7
    Unknown = 8

    @DynamicClassAttribute
    def label(self):
        """
        The label of the Enum member.
        :rtype: str
        """
        return {
            Identity.Neutral: 'Neutral',
            Identity.Concept: 'Concept',
            Identity.Role: 'Role',
            Identity.Attribute: 'Attribute',
            Identity.DataRange: 'DataRange',
            Identity.Individual: 'Individual',
            Identity.Literal: 'Literal',
            Identity.Link: 'Link',
            Identity.Unknown: 'Unknown',
        }[self]


@unique
class Item(IntEnum):
    """
    This class defines all the available Graphol items.
    The enum is ordered according to Graphol elements' classes.
    Changing the order of the enum elements will affect node properties results such as 'predicate' and 'constructor'.
    """
    __order__ = 'ConceptNode AttributeNode RoleNode ValueDomainNode IndividualNode ValueRestrictionNode' \
                'DomainRestrictionNode RangeRestrictionNode UnionNode EnumerationNode ComplementNode RoleChainNode' \
                'RoleInverseNode DatatypeRestrictionNode DisjointUnionNode PropertyAssertionNode InclusionEdge' \
                'InputEdge InstanceOfEdge LabelEdge LabelNode Undefined'

    Undefined = 0

    ConceptNode = 1
    AttributeNode = 2
    RoleNode = 3
    ValueDomainNode = 4
    IndividualNode = 5
    ValueRestrictionNode = 6
    DomainRestrictionNode = 7
    RangeRestrictionNode = 8
    UnionNode = 9
    EnumerationNode = 10
    ComplementNode = 11
    RoleChainNode = 12
    IntersectionNode = 13
    RoleInverseNode = 14
    DatatypeRestrictionNode = 15
    DisjointUnionNode = 16
    PropertyAssertionNode = 17

    InclusionEdge = 18
    InputEdge = 19
    InstanceOfEdge = 20

    LabelEdge = 21
    LabelNode = 22

    @DynamicClassAttribute
    def label(self):
        """
        The label of the Enum member.
        :rtype: str
        """
        return {
            Item.AttributeNode: 'attribute node', Item.ComplementNode: 'complement node',
            Item.ConceptNode: 'concept node', Item.DatatypeRestrictionNode: 'datatype restriction node',
            Item.DisjointUnionNode: 'disjoint union node', Item.DomainRestrictionNode: 'domain restriction node',
            Item.EnumerationNode: 'enumeration node', Item.IndividualNode: 'individual node',
            Item.IntersectionNode: 'intersection node', Item.PropertyAssertionNode: 'property assertion node',
            Item.RangeRestrictionNode: 'range restriction node', Item.RoleNode: 'role node',
            Item.RoleChainNode: 'role chain node', Item.RoleInverseNode: 'role inverse node',
            Item.UnionNode: 'union node', Item.ValueDomainNode: 'value domain node',
            Item.ValueRestrictionNode: 'value restriction node', Item.InclusionEdge: 'inclusion edge',
            Item.InputEdge: 'input edge', Item.InstanceOfEdge: 'instanceOf edge',
            Item.LabelNode: 'node label', Item.LabelEdge: 'edge label', Item.Undefined: 'undefined item',
        }[self]


@unique
class OWLSyntax(Enum):
    """
    This class defines available OWL syntax for exporting ontologies.
    """
    __order__ = 'Functional Manchester RDF Turtle'

    Functional = 'Functional-style syntax'
    Manchester = 'Manchester OWL syntax'
    RDF = 'RDF/XML syntax for OWL'
    Turtle = 'Turtle syntax'


@unique
class Platform(Enum):
    """
    This class defines supported platforms.
    """
    __order__ = 'Darwin Linux Windows'

    Darwin = 'Darwin'
    Linux = 'Linux'
    Windows = 'Windows'
    Unknown = 'Unknown'

    @classmethod
    def identify(cls):
        """
        Returns the current platform identifier.
        :rtype: Platform
        """
        return Platform.forValue(sys.platform)

    @classmethod
    def forValue(cls, value):
        """
        Returns the platform identified by the the given value.
        :type value: str
        :rtype: Platform
        """
        if value.startswith('darwin'):
            return Platform.Darwin
        if value.startswith('linux'):
            return Platform.Linux
        if value.startswith('win') or value.startswith('cygwin'):
            return Platform.Windows
        return Platform.Unknown


@unique
class Restriction(Enum):
    """
    This class defines all the available restrictions for the Domain and Range restriction nodes.
    """
    __order__ = 'Exists Forall Cardinality Self'

    Exists = 'Existential: exists'
    Forall = 'Universal: forall'
    Cardinality = 'Cardinality: (min, max)'
    Self = 'Self: self'

    @DynamicClassAttribute
    def label(self):
        """
        The label of the Enum member.
        :rtype: str
        """
        return {
            Restriction.Exists: 'exists',
            Restriction.Forall: 'forall',
            Restriction.Self: 'self',
            Restriction.Cardinality: '({min},{max})',
        }[self]


@unique
class Special(Enum):
    """
    This class defines special nodes types.
    """
    __order__ = 'Top Bottom'

    Top = 'TOP'
    Bottom = 'BOTTOM'

    @classmethod
    def forValue(cls, value):
        """
        Returns the special type matching the given value.
        :type value: str
        :rtype: Special
        """
        for x in cls:
            if x.value == value.upper().strip():
                return x
        return None


@unique
class XsdDatatype(Enum):
    """
    This class defines all the available datatypes for the value-domain node.
    """
    __order__ = 'anyURI base64Binary boolean byte dateTime dateTimeStamp decimal double float hexBinary int integer ' \
                'language literal long Name NCName negativeInteger NMTOKEN nonNegativeInteger nonPositiveInteger ' \
                'normalizedString plainLiteral positiveInteger rational real short string token unsignedByte ' \
                'unsignedInt unsignedLong unsignedShort xmlLiteral'

    anyURI = 'xsd:anyURI'
    base64Binary = 'xsd:base64Binary'
    boolean = 'xsd:boolean'
    byte = 'xsd:byte'
    dateTime = 'xsd:dateTime'
    dateTimeStamp = 'xsd:dateTimeStamp'
    decimal = 'xsd:decimal'
    double = 'xsd:double'
    float = 'xsd:float'
    hexBinary = 'xsd:hexBinary'
    int = 'xsd:int'
    integer = 'xsd:integer'
    language = 'xsd:language'
    literal = 'rdfs:Literal'
    long = 'xsd:long'
    Name = 'xsd:Name'
    NCName = 'xsd:NCName'
    negativeInteger = 'xsd:negativeInteger'
    NMTOKEN = 'xsd:NMTOKEN'
    nonNegativeInteger = 'xsd:nonNegativeInteger'
    nonPositiveInteger = 'xsd:nonPositiveInteger'
    normalizedString = 'xsd:normalizedString'
    plainLiteral = 'rdf:PlainLiteral'
    positiveInteger = 'xsd:positiveInteger'
    rational = 'owl:rational'
    real = 'owl:real'
    short = 'xsd:short'
    string = 'xsd:string'
    token = 'xsd:token'
    unsignedByte = 'xsd:unsignedByte'
    unsignedInt = 'xsd:unsignedInt'
    unsignedLong = 'xsd:unsignedLong'
    unsignedShort = 'xsd:unsignedShort'
    xmlLiteral = 'rdf:XMLLiteral'

    @classmethod
    def forValue(cls, value):
        """
        Returns the XsdDatatype matching the given value.
        :type value: str
        :rtype: XsdDatatype
        """
        for x in cls:
            if x.value.lower() == value.lower().strip():
                return x
        return None

    @DynamicClassAttribute
    def owlapi(self):
        """
        Returns the name of the OWL api datatype enum entry
        :rtype: str
        """
        return {
            XsdDatatype.anyURI: 'XSD_ANY_URI', XsdDatatype.base64Binary: 'XSD_BASE_64_BINARY',
            XsdDatatype.boolean: 'XSD_BOOLEAN', XsdDatatype.byte: 'XSD_BYTE', XsdDatatype.dateTime: 'XSD_DATE_TIME',
            XsdDatatype.dateTimeStamp: 'XSD_DATE_TIME_STAMP', XsdDatatype.decimal: 'XSD_DECIMAL',
            XsdDatatype.double: 'XSD_DOUBLE', XsdDatatype.float: 'XSD_FLOAT', XsdDatatype.hexBinary: 'XSD_HEX_BINARY',
            XsdDatatype.int: 'XSD_INT', XsdDatatype.integer: 'XSD_INTEGER', XsdDatatype.language: 'XSD_LANGUAGE',
            XsdDatatype.literal: 'RDFS_LITERAL', XsdDatatype.long: 'XSD_LONG', XsdDatatype.Name: 'XSD_NAME',
            XsdDatatype.NCName: 'XSD_NCNAME', XsdDatatype.negativeInteger: 'XSD_NEGATIVE_INTEGER',
            XsdDatatype.NMTOKEN: 'XSD_NMTOKEN', XsdDatatype.nonNegativeInteger: 'XSD_NON_NEGATIVE_INTEGER',
            XsdDatatype.nonPositiveInteger: 'XSD_NON_POSITIVE_INTEGER', XsdDatatype.normalizedString: 'XSD_NORMALIZED_STRING',
            XsdDatatype.plainLiteral: 'RDF_PLAIN_LITERAL', XsdDatatype.positiveInteger: 'XSD_POSITIVE_INTEGER',
            XsdDatatype.rational: 'OWL_RATIONAL', XsdDatatype.real: 'OWL_REAL', XsdDatatype.short: 'XSD_SHORT',
            XsdDatatype.string: 'XSD_STRING', XsdDatatype.token: 'XSD_TOKEN', XsdDatatype.unsignedByte: 'XSD_UNSIGNED_BYTE',
            XsdDatatype.unsignedInt: 'XSD_UNSIGNED_INT', XsdDatatype.unsignedLong: 'XSD_UNSIGNED_LONG',
            XsdDatatype.unsignedShort: 'XSD_UNSIGNED_SHORT', XsdDatatype.xmlLiteral: 'RDF_XML_LITERAL',
        }[self]