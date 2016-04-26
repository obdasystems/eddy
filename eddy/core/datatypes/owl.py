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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from enum import unique, Enum
from types import DynamicClassAttribute


@unique
class Facet(Enum):
    """
    This class defines available Facet restrictions for the value-restriction node.
    """
    __order__ = 'maxExclusive maxInclusive minExclusive minInclusive langRange length maxLength minLength pattern'

    maxExclusive = 'xsd:maxExclusive'
    maxInclusive = 'xsd:maxInclusive'
    minExclusive = 'xsd:minExclusive'
    minInclusive = 'xsd:minInclusive'
    langRange = 'rdf:langRange'
    length = 'xsd:length'
    maxLength = 'xsd:maxLength'
    minLength = 'xsd:minLength'
    pattern = 'xsd:pattern'

    @classmethod
    def forDatatype(cls, value):
        """
        Returns a collection of Facets for the given datatype
        :type value: XsdDatatype
        :rtype: list
        """
        allvalues = [x for x in cls]
        numbers = [Facet.maxExclusive, Facet.maxInclusive, Facet.minExclusive, Facet.minInclusive]
        strings = [Facet.langRange, Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]
        binary = [Facet.length, Facet.maxLength, Facet.minLength]
        anyuri = [Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]
        
        return {
            XsdDatatype.anyURI: anyuri,
            XsdDatatype.base64Binary: binary,
            XsdDatatype.boolean: [],
            XsdDatatype.byte: numbers,
            XsdDatatype.dateTime: numbers,
            XsdDatatype.dateTimeStamp: numbers,
            XsdDatatype.decimal: numbers,
            XsdDatatype.double: numbers,
            XsdDatatype.float: numbers,
            XsdDatatype.hexBinary: binary,
            XsdDatatype.int: numbers,
            XsdDatatype.integer: numbers,
            XsdDatatype.language: strings,
            XsdDatatype.literal: allvalues,
            XsdDatatype.long: numbers,
            XsdDatatype.Name: strings,
            XsdDatatype.NCName: strings,
            XsdDatatype.negativeInteger: numbers,
            XsdDatatype.NMTOKEN: strings,
            XsdDatatype.nonNegativeInteger: numbers,
            XsdDatatype.nonPositiveInteger: numbers,
            XsdDatatype.normalizedString: strings,
            XsdDatatype.plainLiteral: strings,
            XsdDatatype.positiveInteger: numbers,
            XsdDatatype.rational: numbers,
            XsdDatatype.real: numbers,
            XsdDatatype.short: numbers,
            XsdDatatype.string: strings,
            XsdDatatype.token: strings,
            XsdDatatype.unsignedByte: numbers,
            XsdDatatype.unsignedInt: numbers,
            XsdDatatype.unsignedLong: numbers,
            XsdDatatype.unsignedShort: numbers,
            XsdDatatype.xmlLiteral: []
        }[value]

    @classmethod
    def forValue(cls, value):
        """
        Returns the Facet matching the given value.
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
        Returns the name of the OWL api facet enum entry.
        :rtype: str
        """
        # FIXME: missing Xsd:totalDigits and Xsd:fractionDigits
        return {
            Facet.maxExclusive: 'MAX_EXCLUSIVE',
            Facet.maxInclusive: 'MAX_INCLUSIVE',
            Facet.minExclusive: 'MIN_EXCLUSIVE',
            Facet.minInclusive: 'MIN_INCLUSIVE',
            Facet.langRange: 'LANG_RANGE',
            Facet.length: 'LENGTH',
            Facet.maxLength: 'MIN_LENGTH',
            Facet.minLength: 'MIN_LENGTH',
            Facet.pattern: 'PATTERN',
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
class XsdDatatype(Enum):
    """
    This class defines all the available datatypes for the value-domain node.
    """
    __order__ = 'anyURI base64Binary boolean byte dateTime dateTimeStamp decimal ' \
                'double float hexBinary int integer language literal long Name NCName ' \
                'negativeInteger NMTOKEN nonNegativeInteger nonPositiveInteger ' \
                'normalizedString plainLiteral positiveInteger rational real short ' \
                'string token unsignedByte unsignedInt unsignedLong unsignedShort xmlLiteral'

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
        Returns the name of the OWL api datatype enum entry.
        :rtype: str
        """
        return {
            XsdDatatype.anyURI: 'XSD_ANY_URI',
            XsdDatatype.base64Binary: 'XSD_BASE_64_BINARY',
            XsdDatatype.boolean: 'XSD_BOOLEAN',
            XsdDatatype.byte: 'XSD_BYTE',
            XsdDatatype.dateTime: 'XSD_DATE_TIME',
            XsdDatatype.dateTimeStamp: 'XSD_DATE_TIME_STAMP',
            XsdDatatype.decimal: 'XSD_DECIMAL',
            XsdDatatype.double: 'XSD_DOUBLE',
            XsdDatatype.float: 'XSD_FLOAT',
            XsdDatatype.hexBinary: 'XSD_HEX_BINARY',
            XsdDatatype.int: 'XSD_INT',
            XsdDatatype.integer: 'XSD_INTEGER',
            XsdDatatype.language: 'XSD_LANGUAGE',
            XsdDatatype.literal: 'RDFS_LITERAL',
            XsdDatatype.long: 'XSD_LONG',
            XsdDatatype.Name: 'XSD_NAME',
            XsdDatatype.NCName: 'XSD_NCNAME',
            XsdDatatype.negativeInteger: 'XSD_NEGATIVE_INTEGER',
            XsdDatatype.NMTOKEN: 'XSD_NMTOKEN',
            XsdDatatype.nonNegativeInteger: 'XSD_NON_NEGATIVE_INTEGER',
            XsdDatatype.nonPositiveInteger: 'XSD_NON_POSITIVE_INTEGER',
            XsdDatatype.normalizedString: 'XSD_NORMALIZED_STRING',
            XsdDatatype.plainLiteral: 'RDF_PLAIN_LITERAL',
            XsdDatatype.positiveInteger: 'XSD_POSITIVE_INTEGER',
            XsdDatatype.rational: 'OWL_RATIONAL',
            XsdDatatype.real: 'OWL_REAL',
            XsdDatatype.short: 'XSD_SHORT',
            XsdDatatype.string: 'XSD_STRING',
            XsdDatatype.token: 'XSD_TOKEN',
            XsdDatatype.unsignedByte: 'XSD_UNSIGNED_BYTE',
            XsdDatatype.unsignedInt: 'XSD_UNSIGNED_INT',
            XsdDatatype.unsignedLong: 'XSD_UNSIGNED_LONG',
            XsdDatatype.unsignedShort: 'XSD_UNSIGNED_SHORT',
            XsdDatatype.xmlLiteral: 'RDF_XML_LITERAL',
        }[self]