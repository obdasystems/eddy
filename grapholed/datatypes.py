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


import sys

from enum import Enum, unique, IntEnum
from types import DynamicClassAttribute

from PyQt5.QtGui import QFont


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
        :param value: the value to match.
        :rtype: Color
        """
        for x in cls:
            if x.value == value.lower():
                return x
        return None


@unique
class DiagramMode(IntEnum):
    """
    This class defines the DiagramScene operational modes.
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
        :param collection: a collection of elements to be used to populate the list.
        """
        super(DistinctList, self).__init__()
        if collection:
            if isinstance(collection, set) or isinstance(collection, frozenset):
                collection = list(collection)
            for item in collection:
                self.append(item)

    def append(self, p_object):
        """
        Append the given element at the end of the list.
        :param p_object: the element to be appended.
        """
        if p_object not in self:
            super(DistinctList, self).append(p_object)

    def extend(self, iterable):
        """
        Extends the current list by appending items of the given iterable (if they are not in the list already).
        :param iterable: the iterable from where to pick items to insert in the list.
        """
        for item in iterable:
            self.append(item)

    def insert(self, index, p_object):
        """
        Insert the given element in the given index.
        :param index: the index where to place the given element.
        :param p_object: the element to be added to the list.
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
        Will NOT raise any exception if the element is not present in the list.
        :param p_object: the element to be removed.
        """
        try:
            super(DistinctList, self).remove(p_object)
        except ValueError:
            pass

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


@unique
class FileType(Enum):
    """
    This class defines all the available file types supported for graphol document export.
    """
    __order__ = 'graphol pdf'

    graphol = 'Graphol (*.graphol)'
    pdf = 'PDF (*.pdf)'

    @classmethod
    def forValue(cls, value):
        """
        Returns the filetype matching the given value.
        :param value: the value to match.
        :rtype: FileType
        """
        for x in cls:
            if x.value == value:
                return x
        return None

    @DynamicClassAttribute
    def suffix(self):
        """The suffix associated with the Enum member."""
        return {
            FileType.graphol: '.graphol',
            FileType.pdf: '.pdf'
        }[self]


class Font(QFont):
    """
    This class extends PyQt5.QtGui.QFont providing better font rendering on different platforms.
    """
    def __init__(self, family, pointSize=12, weight=-1, italic=False):
        """
        Contruct a new Font instance using the given parameters.
        :param family: the font family.
        :param pointSize: the font size in pts.
        :param weight: the font weight.
        :param italic: whether the font should be rendered as italic.
        """
        if not sys.platform.startswith('darwin'):
            pointSize = int(round(pointSize * 0.75))
        super().__init__(family, pointSize, weight, italic)


@unique
class ItemType(IntEnum):
    """
    This class defines all the available Graphol items.
    """
    ## NODES
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

    ## EDGES
    InclusionEdge = 18
    InputEdge = 19
    InstanceOfEdge = 20

    ## LABELS
    LabelEdge = 21
    LabelNode = 22


@unique
class RestrictionType(Enum):
    """
    This class defines all the available restrictions for the Domain and Range restriction nodes.
    """
    __order__ = 'exists forall cardinality self'

    exists = 'Existential: exists'
    forall = 'Universal: forall'
    cardinality = 'Cardinality: (min, max)'
    self = 'Self: self'

    @DynamicClassAttribute
    def label(self):
        """The label of the Enum member."""
        return {
            RestrictionType.exists: 'exists',
            RestrictionType.forall: 'forall',
            RestrictionType.self: 'self',
            RestrictionType.cardinality: '({min},{max})',
        }[self]


@unique
class SpecialConceptType(Enum):
    """
    This class defines special Concept nodes types.
    """
    __order__ = 'TOP BOTTOM'

    TOP = 'TOP'
    BOTTOM = 'BOTTOM'

    @classmethod
    def forValue(cls, value):
        """
        Returns the SpecialConceptType matching the given value.
        :param value: the value to match.
        :rtype: SpecialConceptType
        """
        for x in cls:
            if x.value == value.upper().strip():
                return x
        return None

    @DynamicClassAttribute
    def owl(self):
        """Returns the Owl corrispective of the special Concept node type."""
        return {
            SpecialConceptType.TOP: 'owl:Thing',
            SpecialConceptType.BOTTOM: 'owl:Nothing',
        }[self]


@unique
class XsdDatatype(Enum):
    """
    This class defines all the available datatypes for the value-domain node.
    """
    __order__ = 'anyURI base64Binary boolean byte date dateTime decimal double duration float gDay gMonth gMonthDay ' \
                'gYear gYearMonth hexBinary ID IDREF IDREFS int integer language long Name NCName negativeInteger ' \
                'NMTOKEN NMTOKENS nonNegativeInteger nonPositiveInteger normalizedString positiveInteger QName short ' \
                'string time token unsignedByte unsignedInt unsignedLong unsignedShort'

    anyURI = 'xsd:anyURI' # The data must conform to the syntax of a Uniform Resource Identifier (URI).
    base64Binary = 'xsd:base64Binary' # A sequence of binary octets (bytes) encoded according to RFC 2045.
    boolean = 'xsd:boolean' # A boolean true or false value.
    byte = 'xsd:byte' # A signed 8-bit integer in the range [-128, 127]. Drived from the short datatype.
    date = 'xsd:date' # Represents a specific date. The syntax is the same as that for the date part of dateTime, with an optional time zone indicator.
    dateTime = 'xsd:dateTime' # Represents a specific instant of time. It has the form YYYY-MM-DDThh:mm:ss folowed by an optional time-zone suffix.
    decimal = 'xsd:decimal' # Any base-10 fixed-point number. There must be at least one digit to the left of the decimal point, and a leading "+" or "-" sign is allowed.
    double = 'xsd:double' # A 64-bit floating-point decimal number as specified in the IEEE 754-1985 standard. The external form is the same as the float datatype.
    duration = 'xsd:duration' # Represents a duration of time, as a composite of years, months, days, hours, minutes, and seconds.
    float = 'xsd:float' # A 32-bit floating-point decimal number as specified in the IEEE 754-1985 standard. Allowable values are the same as in the decimal type, optionally followed by an exponent.
    gDay = 'xsd:gDay' # A day of the month in the Gregorian calendar. The syntax is "---DD" where DD is the day of the month. Example: the 27th of each month would be represented as "---27".
    gMonth = 'xsd:gMonth' # A month number in the Gregorian calendar. The syntax is "--MM--", where MM is the month number. For example, "--06--" represents the month of June.
    gMonthDay = 'xsd:gMonthDay' # A Gregorian month and day as "--MM-DD". Example: "--07-04" is the Fourth of July.
    gYear = 'xsd:gYear' # A Gregorian year, specified as YYYY. Example: "1889".
    gYearMonth = 'xsd:gYearMonth' # A Gregorian year and month. The syntax is YYYY-MM. Example: "1995-08" represents August 1995.
    hexBinary = 'xsd:hexBinary' # Represents a sequence of octets (bytes), each given as two hexadecimal digits. Example: "0047dedbef" is five octets.
    ID = 'xsd:ID' # A unique identifier as in the ID attribute type from the XML standard. Derived from the NCName datatype.
    IDREF = 'xsd:IDREF' # An IDREF value is a reference to a unique identifier as defined under attribute types in the XML standard.
    IDREFS = 'xsd:IDREFS' # An IDREFS value is a space-separated sequence of IDREF references.
    int = 'xsd:int' # Represents a 32-bit signed integer in the range [-2,147,483,648, 2,147,483,647]. Derived from the long datatype.
    integer = 'xsd:integer' # Represents a signed integer. Values may begin with an optional "+" or "-" sign. Derived from the decimal datatype.
    language = 'xsd:language' # One of the standardized language codes defined in RFC 1766. Example: "fj" for Fijian. Derived from the token type.
    long = 'xsd:long' # A signed, extended-precision integer; at least 18 digits are guaranteed. Derived from the integer datatype.
    Name = 'xsd:Name' # A name as defined in the XML standard. The first character can be a letter or underbar "_", and the remaining characters may be letters, underbars, digits, hyphen "-", period ".", or colon ":".
    NCName = 'xsd:NCName' # The local part of a qualified name. See the NCName definition in the document Namespaces in XML.
    negativeInteger = 'xsd:negativeInteger' # Represents an integer less than zero. Derived from the nonPositiveInteger datatype.
    NMTOKEN = 'xsd:NMTOKEN' # Any sequence of name characters, defined in the XML standard: letters, underbars "_", hyphen "-", period ".", or colon ":".
    NMTOKENS = 'xsd:NMTOKENS' # A NMTOKENS data value is a space-separated sequence of NMTOKEN values.
    nonNegativeInteger = 'xsd:nonNegativeInteger' # An integer greater than or equal to zero. Derived from the integer datatype.
    nonPositiveInteger = 'xsd:nonPositiveInteger' # An integer less than or equal to zero. Derived from the integer datatype.
    normalizedString = 'xsd:normalizedString' # This datatype describes a "normalized" string, meaning that it cannot include newline (LF), return (CR), or tab (HT) characters.
    positiveInteger = 'xsd:positiveInteger' # An extended-precision integer greater than zero. Derived from the nonNegativeInteger datatype.
    QName = 'xsd:QName' # An XML qualified name, such as "xsl:stylesheet".
    short = 'xsd:short' # A 16-bit signed integer in the range [-32,768, 32,767]. Derived from the int datatype.
    string = 'xsd:string' # Any sequence of zero or more characters.
    time = 'xsd:time' # A moment of time that repeats every day. The syntax is the same as that for dateTime, omitting everything up to and including the separator "T". Examples: "00:00:00" is midnight.
    token = 'xsd:token' # The values of this type represent tokenized strings. They may not contain newline (LF) or tab (HT) characters. They may not start or end with whitespace.
    unsignedByte = 'xsd:unsignedByte' # An unsigned 16-bit integer in the range [0, 255]. Derived from the unsignedShort datatype.
    unsignedInt = 'xsd:unsignedInt' # An unsigned 32-bit integer in the range [0, 4,294,967,295]. Derived from the unsignedLong datatype.
    unsignedLong = 'xsd:unsignedLong' # An unsigned, extended-precision integer. Derived from the nonNegativeInteger datatype.
    unsignedShort = 'xsd:unsignedShort' # An unsigned 16-bit integer in the range [0, 65,535]. Derived from the unsignedInt datatype.


__all__ = [
    'Color',
    'DiagramMode',
    'DistinctList',
    'FileType',
    'Font',
    'ItemType',
    'RestrictionType',
    'SpecialConceptType',
    'XsdDatatype',
]