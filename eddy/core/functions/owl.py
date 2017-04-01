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

from eddy.core.functions.misc import isEmpty
from eddy.core.regex import RE_OWL_INVALID_CHAR
from eddy.core.regex import RE_OWL_ONTOLOGY_FUNCTIONAL_TAG


def OWLAnnotationText(content):
    """
    Transform the given text returning OWL Annotation compatible text.
    :type content: str
    :rtype: str
    """
    return content.strip()


def OWLFunctionalDocumentFilter(content):
    """
    Properly format the given OWL document for Functional OWL serialization.
    This function is needed because Protege 4.3 does not support comments being generated
    by OWLapi 4 FunctionalSyntaxObjectRenderer, so we need to strip them out of our document.
    :type content: str
    :rtype: str
    """
    result = []
    extend = result.extend
    for row in (i for i in content.split('\n') if not i.startswith('#')):
        if not isEmpty(row):
            if RE_OWL_ONTOLOGY_FUNCTIONAL_TAG.search(row):
                extend(['\n', row, '\n', '\n'])
            else:
                extend([row, '\n'])
    return ''.join(result).rstrip('\n')


def OWLShortIRI(prefix, resource):
    """
    Construct an abbreviated IRI, which is of the form PREFIX_NAME:RC by joining the given values with a colon.
    This function will also take care of removing invalid characters from the given resource.
    :type prefix: str
    :type resource: str
    :rtype: str
    """
    return '{0}:{1}'.format(prefix, OWLText(resource))


def OWLText(resource):
    """
    Construct OWL compatible text using the given resource.
    :param resource:
    :return:
    """
    sp = re.split(RE_OWL_INVALID_CHAR, str(resource))
    resource = sp[0]
    for entry in sp[1:]:
        sep = ''
        if not entry.startswith('_') and not resource.endswith('_'):
            sep = '_'
        resource = '{0}{1}{2}'.format(resource, sep, entry)
    return resource