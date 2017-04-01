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


import re


RE_CAMEL_SPACE = re.compile("""([a-z])([A-Z])""") # space string on camel case token
RE_CARDINALITY = re.compile("""^\(\s*(?P<min>[\d-]+)\s*,\s*(?P<max>[\d-]+)\s*\)$""") # parse cardinality restriction
RE_DIGIT = re.compile("""\d""") # identify strings composed of only digits
RE_FILE_EXTENSION = re.compile(""".*\(\*(?P<extension>\.\w+)\)""") # to extract the extension from the File enum
RE_FACET = re.compile("""^(?P<facet>[\w:]*)[\s\^]*"(?P<value>.*)"$""") # tokenize facet restriction
RE_ITEM_PREFIX = re.compile("""^(?P<prefix>[^\d])(?P<value>\d+)$""") # split items prefix/id
RE_LOG_MESSAGE = re.compile("""^(?P<date>.{10})\s(?P<time>.{8})\s(?P<level>\w+)\s+(?P<message>.*)$""") # tokenize log messages
RE_QUOTED = re.compile("""^".*"$""") # identify strings fully embraced into quotes
RE_OWL_INVALID_CHAR = re.compile("""[\W]""") # identify OWL invalid characters
RE_OWL_ONTOLOGY_FUNCTIONAL_TAG = re.compile("""^Ontology\s*\(.*$""") # identify OWL ontology tag in Functional OWL
RE_OWL_ONTOLOGY_MANCHESTER_TAG = re.compile("""^Ontology:\s*.*$""") # identify OWL ontology tag in Mancherster OWL
RE_OWL_ONTOLOGY_TURTLE_TAG = re.compile("""^.*owl:Ontology.*$""") # identify OWL ontology tag in Turtle OWL
RE_VALUE = re.compile("""^"(?P<value>.*)"\^\^(?P<datatype>.*)$""") # tokenize string into literal + datatype
RE_VALUE_RESTRICTION = re.compile("""^(?P<facet>.*)\s*"(?P<value>.*)"\^\^(?P<datatype>.*)$""") # tokenize value restriction