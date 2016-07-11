# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
        :type value: Datatype
        :rtype: list
        """
        allvalues = [x for x in cls]
        numbers = [Facet.maxExclusive, Facet.maxInclusive, Facet.minExclusive, Facet.minInclusive]
        strings = [Facet.langRange, Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]
        binary = [Facet.length, Facet.maxLength, Facet.minLength]
        anyuri = [Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]
        
        return {
            Datatype.anyURI: anyuri,
            Datatype.base64Binary: binary,
            Datatype.boolean: [],
            Datatype.byte: numbers,
            Datatype.dateTime: numbers,
            Datatype.dateTimeStamp: numbers,
            Datatype.decimal: numbers,
            Datatype.double: numbers,
            Datatype.float: numbers,
            Datatype.hexBinary: binary,
            Datatype.int: numbers,
            Datatype.integer: numbers,
            Datatype.language: strings,
            Datatype.literal: allvalues,
            Datatype.long: numbers,
            Datatype.Name: strings,
            Datatype.NCName: strings,
            Datatype.negativeInteger: numbers,
            Datatype.NMTOKEN: strings,
            Datatype.nonNegativeInteger: numbers,
            Datatype.nonPositiveInteger: numbers,
            Datatype.normalizedString: strings,
            Datatype.plainLiteral: strings,
            Datatype.positiveInteger: numbers,
            Datatype.rational: numbers,
            Datatype.real: numbers,
            Datatype.short: numbers,
            Datatype.string: strings,
            Datatype.token: strings,
            Datatype.unsignedByte: numbers,
            Datatype.unsignedInt: numbers,
            Datatype.unsignedLong: numbers,
            Datatype.unsignedShort: numbers,
            Datatype.xmlLiteral: []
        }[value]

    @classmethod
    def forValue(cls, value):
        """
        Returns the Facet matching the given value.
        :type value: str
        :rtype: Datatype
        """
        for x in cls:
            if x.value.lower() == value.lower().strip():
                return x
        return None

    @property
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
class Datatype(Enum):
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
        Returns the Datatype matching the given value.
        :type value: str
        :rtype: Datatype
        """
        for x in cls:
            if x.value.lower() == value.lower().strip():
                return x
        return None

    @property
    def owlapi(self):
        """
        Returns the name of the OWL api datatype enum entry.
        :rtype: str
        """
        return {
            Datatype.anyURI: 'XSD_ANY_URI',
            Datatype.base64Binary: 'XSD_BASE_64_BINARY',
            Datatype.boolean: 'XSD_BOOLEAN',
            Datatype.byte: 'XSD_BYTE',
            Datatype.dateTime: 'XSD_DATE_TIME',
            Datatype.dateTimeStamp: 'XSD_DATE_TIME_STAMP',
            Datatype.decimal: 'XSD_DECIMAL',
            Datatype.double: 'XSD_DOUBLE',
            Datatype.float: 'XSD_FLOAT',
            Datatype.hexBinary: 'XSD_HEX_BINARY',
            Datatype.int: 'XSD_INT',
            Datatype.integer: 'XSD_INTEGER',
            Datatype.language: 'XSD_LANGUAGE',
            Datatype.literal: 'RDFS_LITERAL',
            Datatype.long: 'XSD_LONG',
            Datatype.Name: 'XSD_NAME',
            Datatype.NCName: 'XSD_NCNAME',
            Datatype.negativeInteger: 'XSD_NEGATIVE_INTEGER',
            Datatype.NMTOKEN: 'XSD_NMTOKEN',
            Datatype.nonNegativeInteger: 'XSD_NON_NEGATIVE_INTEGER',
            Datatype.nonPositiveInteger: 'XSD_NON_POSITIVE_INTEGER',
            Datatype.normalizedString: 'XSD_NORMALIZED_STRING',
            Datatype.plainLiteral: 'RDF_PLAIN_LITERAL',
            Datatype.positiveInteger: 'XSD_POSITIVE_INTEGER',
            Datatype.rational: 'OWL_RATIONAL',
            Datatype.real: 'OWL_REAL',
            Datatype.short: 'XSD_SHORT',
            Datatype.string: 'XSD_STRING',
            Datatype.token: 'XSD_TOKEN',
            Datatype.unsignedByte: 'XSD_UNSIGNED_BYTE',
            Datatype.unsignedInt: 'XSD_UNSIGNED_INT',
            Datatype.unsignedLong: 'XSD_UNSIGNED_LONG',
            Datatype.unsignedShort: 'XSD_UNSIGNED_SHORT',
            Datatype.xmlLiteral: 'RDF_XML_LITERAL',
        }[self]