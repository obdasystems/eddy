###########################################################
#                                                         #
#  This specific module is written by ASHWIN RAVISHANKAR  #
#                                                         #
###########################################################



import sys

from eddy.core.output import getLogger

LOGGER = getLogger()

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore

from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin
from eddy.core.datatypes.owl import OWLAxiom,OWLSyntax
from eddy.core.common import HasThreadingSystem
from eddy.core.exporters.owl2 import OWLOntologyFetcher

from jnius import autoclass, cast, detach

class CheckForConsistencyPlugin(AbstractPlugin, HasThreadingSystem):

    def __init__(self, spec, session):

        super().__init__(spec, session)
        self.afwset = set()
        self.view = None
        self.ontology = None
        self.man = None

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(Exception)
    def onErrored(self, exception):
        """
        """
    @QtCore.pyqtSlot()
    def onCompleted(self):
        """
        """
    @QtCore.pyqtSlot(int, int)
    def onProgress(self, current, total):
        """
        """
    @QtCore.pyqtSlot()
    def onStarted(self):
        """
        """

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}


    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Update the state of the hermit reasoner controls according to the active diagram.
        """
        self.refresh(enabled=self.session.mdi.activeDiagram() is not None)

    @QtCore.pyqtSlot()
    def reason_over_ontology(self):

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional)
        worker.run()

        dict = worker.refined_axiom_to_node_or_edge
        ontology = worker.ontology

        count = 1

        for d in dict.items():
            print('[',count,']')
            print('key-',d[0].replace(self.project.iri,''))
            print('     value-',d[1])

            count = count + 1

        """
        entry = []

        for i in range(1,11):
            temp = []
            for j in range(21,31):
                ele = '('+str(i)+'.'+str(j)+')'
                temp.append(ele)
            entry.append(temp)

        count = 0

        for e in entry:

            print(count,'-',entry[count])
            count=count+1
        """


        """
        print('self.inconsistent_ontology',self.inconsistent_ontology)
        print('self.explanations_for_inconsistency',self.explanations_for_inconsistency)

        print('self.unsatisfiable_classes',self.unsatisfiable_classes)
        print('self.nodesofunsatisfiable_classes',self.nodesofunsatisfiable_classes)
        print('self.explanations_for_unsatisfiable_classes',self.explanations_for_unsatisfiable_classes)

        print('self.get_axioms_of_explanation_to_display_in_widget',self.get_axioms_of_explanation_to_display_in_widget)
        print('self.nodesoredges_of_axioms_to_display_in_widget',self.nodesoredges_of_axioms_to_display_in_widget)
        """

        """
        OWLAxiom = autoclass('org.semanticweb.owlapi.model.OWLAxiom')

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional, return_dict=False)
        ontology = worker.run()
        print('type(ontology)',type(ontology))

        worker_2 = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional, return_dict=True)
        dict = worker_2.run()
        print('type(dict)',type(dict))
        print('len(dict)', len(dict))

        keys = dict.keys()
        print('len(keys)',len(keys))

        items = dict.items()
        print('for i in items:')

        for i in items:
            owl_axiom = i[0]
            cast(OWLAxiom, owl_axiom)

            raw_owl_axiom = owl_axiom.toString()
            owl_axiom = raw_owl_axiom.replace(self.project.iri,'')

            print(owl_axiom)
            print(i[1],'\n')

        print('for i in items:END')
        """
        #self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='IUN_explorer')
        """
        diagrams = self.project.diagrams()

        for d in diagrams:

            print('d-',d.name)

            lst_nodes = list(d.nodes())
            lst_edges = list(d.edges())

            print('     no_nodes,no_edges ',len(lst_nodes), len(lst_edges))
        


        plugins_info = self.session.pmanager.info

        installed_plugins = self.session.plugins()

        print('***  for entry in plugins_info:  ***')

        for idx,entry in enumerate(plugins_info):

            plugin_name = entry[0].get('plugin', 'name')
            plugin_id = entry[0].get('plugin', 'id')
            print(idx,"* plugin_name-%s, plugin_id-%s" % (plugin_name,plugin_id))

        print('***  for entry in plugins_info:  END ***\n')

        installed_plugin_ids = []

        print('***  for p in installed_plugins:     ***')

        for idx,p in enumerate(installed_plugins):

            plugin_name = p.name()
            plugin_id = p.id()

            installed_plugin_ids.append(plugin_id)

            print(idx,"*[installed] plugin_name-%s, plugin_id-%s" % (plugin_name,plugin_id))

        print('***  for p in installed_plugins:     END ***\n')

        for idx,entry in enumerate(plugins_info):

            plugin_id = entry[0].get('plugin', 'id')

            if plugin_id == 'IUN_explorer':

                print('plugin_id == IUN_explorer:')

                if plugin_id not in installed_plugin_ids:

                    print('plugin_id not in installed_plugin_ids:')

                    IUN_plugin = self.session.pmanager.create(entry[1], entry[0])

                    INU_started = self.session.pmanager.start(IUN_plugin)
                    print('INU_started? ', INU_started)

                    self.session.addPlugin(IUN_plugin)

                else:

                    print('plugin_id in installed_plugin_ids')

        installed_plugins = self.session.plugins()

        print('IUN_plugin should be added by now\n')
        print('***  for p in installed_plugins:     ***')

        for idx,p in enumerate(installed_plugins):

            plugin_name = p.name()
            plugin_id = p.id()
            print(idx,"*[installed] plugin_name-%s, plugin_id-%s" % (plugin_name,plugin_id))


        print('***  for p in installed_plugins:     END ***\n')

        print('***  try to dispose and remove the plugin from the session ***\n')

        plugin_to_dispose_and_remove = None

        for idx,p in enumerate(installed_plugins):

            plugin_name = p.name()
            plugin_id = p.id()

            if plugin_id == 'IUN_explorer':

                plugin_to_dispose_and_remove = p

        disposed = self.session.pmanager.dispose(plugin_to_dispose_and_remove)

        print('disposed?', disposed)

        if disposed:

            self.session.removePlugin(plugin_to_dispose_and_remove)

        print('IUN_plugin should be disposed and removed by now')

        print('***  for p in installed_plugins:     ***')

        for idx,p in enumerate(installed_plugins):

            plugin_name = p.name()
            plugin_id = p.id()

            installed_plugin_ids.append(plugin_id)

            print(idx,"*[installed] plugin_name-%s, plugin_id-%s" % (plugin_name, plugin_id))

        print('***  for p in installed_plugins:     END ***\n')
        
        self.debug('button_reason_with_hermit')


        #self.ontology.sync_reasoner()

        #print('ontology.OWLOntologyID - ', self.ontology.OWLOntologyID)
        #print('ontology.axiomsList - ', self.ontology.axiomsList.__sizeof__())

        #self.Node = autoclass('org.semanticweb.owlapi.reasoner.Node')
        #self.OWLClass = autoclass('org.semanticweb.owlapi.model.OWLClass')
        self.Iterator = autoclass('java.util.Iterator')
        self.Reasoner = autoclass('org.semanticweb.HermiT.Reasoner')
        self.Configuration = autoclass('org.semanticweb.HermiT.Configuration')
        self.OWLOntology = autoclass('org.semanticweb.owlapi.model.OWLOntology')
        self.OWLManager = autoclass('org.semanticweb.owlapi.apibinding.OWLManager')

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False,
                                           syntax=OWLSyntax.Functional, export_to_file=False)

        ont = worker.run()

        print('worker.IRI ', worker.IRI)

        print('worker.ontology', ont)

        print('worker.project', worker.project)
        print('worker.OWLOntology', worker.OWLOntology)

        print('')

        self.conf = self.Configuration()
        self.conf.throwInconsistentOntologyException = False

        self.reasoner = self.Reasoner(self.conf, ont)

        self.consistent = self.reasoner.isConsistent()
        print('self.consistent ', self.consistent)

        # self.usc = self.reasoner.getUnsatisfiableClasses()
        # self.usc_pt = self.usc.toString()

        # print('self.usc_pt ', self.usc_pt)

        usc_i = self.reasoner.getUnsatisfiableClasses().iterator()

        unsatisfiable_classes_list_raw = []

        iri = self.project.iri
        print('iri', iri)

        while usc_i.hasNext():

            ele = usc_i.next().toString()

            unsatisfiable_classes_list_raw.append(ele)

            print('ele ', ele)

        print('unsatisfiable_classes_list_raw ', unsatisfiable_classes_list_raw)

        unsatisfiable_classes_list = []

        print('*********')

        for ele_us_lst in unsatisfiable_classes_list_raw:

            if iri in ele_us_lst:

                ele_wanted = ele_us_lst
                print('1. ele_wanted',ele_wanted)
                ele_wanted = ele_wanted.replace(iri+'#', '')
                ele_wanted = ele_wanted.replace('<', '')
                ele_wanted = ele_wanted.replace('>', '')
                print('2. ele_wanted', ele_wanted)

                unsatisfiable_classes_list.append(ele_wanted)

        print('*********')

        print('unsatisfiable_classes_list ', unsatisfiable_classes_list)

        inf_r = ReasonerManager(self.session).info
        inf_p = PluginManager(self.session).info
        
        """
        ###########################

    #############################################
    #   INTERFACE
    #################################

    def refresh(self, enabled):
        """
        Refresh the status of the hermit reasoner controls
        :type enabled: bool
        """
        self.widget('button_reason_with_hermit').setEnabled(enabled)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """

        # DISCONNECT FROM ACTIVE SESSION
        #disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        disconnect(self.session.sgnUpdateState, self.doUpdateState)

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling hermitreasoner from "view" toolbar')
        for action in self.afwset:
            self.session.widget('view_toolbar').removeAction(action)


    def start(self):
        """
        Perform initialization tasks for the plugin.
        """

        # INITIALIZE THE WIDGETS
        self.debug('Creating hermit reasoner widget')

        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/24/ic_zoom_in_black'),
            enabled=False, checkable=False, clicked=self.reason_over_ontology,
            objectName='button_reason_with_hermit'))

        # CONFIGURE SIGNALS/SLOTS
        self.debug('Configuring session and MDI area specific signals/slots')
        #connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        connect(self.session.sgnUpdateState, self.doUpdateState)

        # CREATE VIEW TOOLBAR BUTTONS
        self.debug('Installing hermit reasoner widget in "view" toolbar')
        self.afwset.add(self.session.widget('view_toolbar').addSeparator())
        self.afwset.add(self.session.widget('view_toolbar').addWidget(self.widget('button_reason_with_hermit')))




