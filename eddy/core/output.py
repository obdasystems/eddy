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


import io
import sys
import logging

from math import ceil, floor
from eddy import APPNAME


class OutputHandler(logging.Logger):
    """
    Custom logging output handler class.
    """
    HeadLength = 92
    Stream = io.StringIO()
    #Stream=open("logger_file.txt", "a", encoding="utf-8")

    #############################################
    #   AUXILIARY METHODS
    #################################

    @classmethod
    def getDefaultStream(cls):
        """
        Returns the default stream for this logger class.
        :rtype: StringIO
        """
        return OutputHandler.Stream

    #############################################
    #   LOGGING METHODS
    #################################

    def frame(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO' decorating it with the frame pattern.
        """
        if self.isEnabledFor(logging.INFO):
            separator = kwargs.pop('separator', '-')
            msg = msg % args % kwargs
            num = OutputHandler.HeadLength - len(msg) - len(separator) * 2 - 2
            msg = '%s %s%s %s' % (separator, msg, ' ' * num, separator)
            self.info(msg)

    def header(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO' decorating it with the heading pattern.
        """
        if self.isEnabledFor(logging.INFO):
            separator = kwargs.pop('separator', '-')
            msg = msg % args % kwargs
            num = (OutputHandler.HeadLength - len(msg) - 2) / 2
            msg = '%s %s %s' % (separator * int(ceil(num)), msg, separator * int(floor(num)))
            self.info(msg)

    def separator(self, separator=''):
        """
        Log a separator with severity 'INFO'.
        """
        if self.isEnabledFor(logging.INFO):
            separator *= OutputHandler.HeadLength
            if len(separator) > OutputHandler.HeadLength:
                separator = separator[:OutputHandler.HeadLength]
            self.info(separator)


logging.addLevelName(logging.CRITICAL, 'CRITICAL')
logging.addLevelName(logging.ERROR,    'ERROR   ')
logging.addLevelName(logging.INFO,     'INFO    ')
logging.addLevelName(logging.WARNING,  'WARNING ')
logging.addLevelName(logging.DEBUG,    'DEBUG   ')

logging.setLoggerClass(OutputHandler)


__output = dict()


def getLogger(name=APPNAME):
    """
    Returns an instance of the logger for the given name.
    :type name: str
    :rtype: logging.Logger
    """
    if not name in __output:
        # CREATE A FORMATTER
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y/%m/%d %H:%M:%S')
        # IN-MEMORY STREAM HANDLER
        handler = logging.StreamHandler(OutputHandler.getDefaultStream())
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        # CONSOLE HANDLER
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        # STORE THE LOGGER INSTANCE
        __output[name] = logger

    return __output.get(name)