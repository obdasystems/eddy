###########################################################
#                                                         #
#  This specific module is written by ASHWIN RAVISHANKAR  #
#                                                         #
###########################################################

from eddy.core.plugin import PluginManager
from eddy.core.reasoner import ReasonerManager

from eddy.core.reasoner import AbstractReasoner
from eddy.core.common import HasThreadingSystem

class PelletReasoner(AbstractReasoner, HasThreadingSystem):

    def __init__(self, spec, session):

        super().__init__(spec, session)
        self.afwset = set()
        self.view = None
        self.ontology = None
        self.man = None