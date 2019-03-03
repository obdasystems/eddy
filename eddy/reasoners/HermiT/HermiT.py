###########################################################
#                                                         #
#  This specific module is written by ASHWIN RAVISHANKAR.
#  It includes some of the Hermit java classes
#                                                         #
###########################################################

from eddy.core.common import HasThreadingSystem
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.reasoner import AbstractReasoner

LOGGER = getLogger()


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
        pass

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        try:
            self.vm = getJavaVM()
            if not self.vm.isRunning():
                self.vm.initialize()
            self.vm.attachThreadToJVM()
            self.Configuration = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
            self.Reasoner = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
            self.ReasonerFactory = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
            self.Explanation = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.Explanation')
            self.ExplanationGenerator = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.ExplanationGenerator')
            self.InconsistentOntologyExplanationGeneratorFactory = self.vm.getJavaClass(
                'org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')
            self.BlackBoxExplanation = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.BlackBoxExplanation')
        except Exception as e:
            self.onErrored(e)
