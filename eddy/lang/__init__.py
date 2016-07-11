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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from eddy import ORGANIZATION, APPNAME

from importlib import import_module

from PyQt5.QtCore import QSettings


try:
    settings = QSettings(ORGANIZATION, APPNAME)
    code = settings.value('general/language', 'en', str)
    mo = import_module('eddy.lang.{0}'.format(code))
except ImportError:
    mo = import_module('eddy.lang.en')
finally:
    en = import_module('eddy.lang.en')


def gettext(key, *args, **kwargs):
    """
    Returns the translation of the text associated with the given keyword.
    Differently from the builtin gettext.gettext this function accepts a
    message keyword as mandatory argument and a sequence of tokens to
    substitute to the associated message pattern, if any is required.
    :type key: str
    :type args: list
    :type kwargs: dict
    :rtype: str
    """
    try:
        return getattr(mo, key).format(*args, **kwargs)
    except AttributeError:
        return getattr(en, key, key).format(*args, **kwargs)