###########################################################
#                                                         #
#  This specific module is written by ASHWIN RAVISHANKAR.
#  It includes some of the Hermit java classes
#                                                         #
###########################################################

import sys

from eddy.core.output import getLogger

LOGGER = getLogger()

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore

from eddy.core.reasoner import AbstractReasoner
from eddy.core.common import HasThreadingSystem
from jnius import autoclass, cast, detach


class HermitReasoner(AbstractReasoner, HasThreadingSystem):

    def __init__(self, spec, session):

        super().__init__(spec, session)
        self.afwset = set()

    #############################################
    #   SLOTS
    #################################
    def onErrored(self, exception):
        """
        """
        LOGGER.info('exception occured -')


    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        detach()


    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        try:

            self.Configuration = autoclass('org.semanticweb.HermiT.Configuration')
            self.Reasoner = autoclass('org.semanticweb.HermiT.Reasoner')
            self.ReasonerFactory = autoclass('org.semanticweb.HermiT.ReasonerFactory')
            self.Explanation = autoclass('org.semanticweb.owl.explanation.api.Explanation')
            self.ExplanationGenerator = autoclass('org.semanticweb.owl.explanation.api.ExplanationGenerator')
            self.InconsistentOntologyExplanationGeneratorFactory = autoclass(
                'org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')
            self.BlackBoxExplanation = autoclass('com.clarkparsia.owlapi.explanation.BlackBoxExplanation')

        except Exception as e:

            self.onErrored(e)
