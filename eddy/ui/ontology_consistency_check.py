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

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


from eddy.core.datatypes.qt import Font


from eddy.core.output import getLogger
from eddy.core.common import HasThreadingSystem, HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.exporters.owl2 import OWLOntologyFetcher
from eddy.core.datatypes.owl import OWLAxiom,OWLSyntax
from eddy.core.worker import AbstractWorker
from jnius import autoclass, cast, detach

import sys,math


LOGGER = getLogger()


class OntologyConsistencyCheckDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform Ontology Consistency check
    """
    sgnWork = QtCore.pyqtSignal()

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None

        self.msgbox_busy = QtWidgets.QMessageBox(self)
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_busy.setText('Checking consistency of ontology')
        self.msgbox_busy.setTextFormat(QtCore.Qt.RichText)

        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)

        connect(self.sgnWork, self.doWork)

        self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Unsatisfiable_Entity_Explorer')
        self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Explanation_explorer')

        self.project.axioms_to_nodes_edges_mapping = None
        self.project.ontology_OWL = None

        self.project.inconsistent_ontology = None
        self.project.explanations_for_inconsistency = []

        self.project.unsatisfiable_classes = []
        self.project.nodesofunsatisfiable_classes = []
        self.project.explanations_for_unsatisfiable_classes = []

        self.project.get_axioms_of_explanation_to_display_in_widget = []
        self.project.nodesoredges_of_axioms_to_display_in_widget = []

        self.session.BackgrounddeColourNodesAndEdges(call_updateNode=True,call_ClearInconsistentEntitiesAndDiagItemsData=False)
    #############################################
    #   INTERFACE
    #################################

    def dispose(self):
        """
        Gracefully quits working thread.
        """
        if self.workerThread:
            self.workerThread.quit()
            if not self.workerThread.wait(2000):
                self.workerThread.terminate()
                self.workerThread.wait()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for SyntaxValidationDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the dialog is closed.
        :type closeEvent: QCloseEvent
        """
        self.dispose()

    def showEvent(self, showEvent):
        """
        Executed whenever the dialog is shown.
        :type showEvent: QShowEvent
        """
        self.sgnWork.emit()

    #############################################
    #   SLOTS
    #################################


    @QtCore.pyqtSlot()
    def doWork(self):
        """
        Perform on or more advancements step in the validation procedure.
        """
        # RUN THE WORKER
        worker = OntologyConsistencyCheckWorker(self.project,self.session)
        connect(worker.sgnBusy, self.displaybusydialog)
        connect(worker.sgnAllOK, self.onPerfectOntology)
        connect(worker.sgnOntologyInconsistency, self.onOntologicalInconsistency)
        connect(worker.sgnUnsatisfiableClasses, self.onUnsatisfiableClasses)
        self.startThread('OntologyConsistencyCheck', worker)

    @QtCore.pyqtSlot(bool)
    def displaybusydialog(self, activate):

        if activate is True:

            self.msgbox_busy.exec_()
            self.close()

        if activate is False:
            self.msgbox_busy.close()

    @QtCore.pyqtSlot()
    def onPerfectOntology(self):
        """
        Executed when a syntax error is detected.
        :type message: str
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        self.msgbox_done.setText('Ontology is consistent and  all classes are satisfiable')
        self.msgbox_done.exec_()
        self.close()

    @QtCore.pyqtSlot()
    def onOntologicalInconsistency(self):

        self.hide()

        dialog_2 = InconsistentOntologyDialog(self.project,None,self.session)
        dialog_2.exec_()

    @QtCore.pyqtSlot()
    def onUnsatisfiableClasses(self):
        """
        Executed when there is atleast 1 unsatisfiable class
        :type message: str
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        self.msgbox_done.setText('Ontology is consistent however some class(es) are unsatisfiable.\n See Unsatisfiable Entity Explorer for details.\n\
                                 To reset the background colouring of the nodes in the diagram, press the Reset button in the toolbar')
        self.msgbox_done.exec_()
        self.close()

        self.session.pmanager.create_add_and_start_plugin('Unsatisfiable_Entity_Explorer')


class OntologyConsistencyCheckWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will perform the project Ontology Consistency check
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnAllOK = QtCore.pyqtSignal()
    sgnOntologyInconsistency = QtCore.pyqtSignal()
    sgnUnsatisfiableClasses = QtCore.pyqtSignal()

    def __init__(self, project, session):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        """
        super().__init__()
        self.project = project
        self.session = session

        self.Iterator = autoclass('java.util.Iterator')
        self.String = autoclass('java.lang.String')
        self.Object = autoclass('java.lang.Object')

        self.Configuration = autoclass('org.semanticweb.HermiT.Configuration')
        self.Reasoner = autoclass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactory = autoclass('org.semanticweb.HermiT.ReasonerFactory')
        self.Explanation = autoclass('org.semanticweb.owl.explanation.api.Explanation')
        self.ExplanationGenerator = autoclass('org.semanticweb.owl.explanation.api.ExplanationGenerator')
        self.InconsistentOntologyExplanationGeneratorFactory = autoclass('org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')
        self.OWLFunctionalSyntaxFactory = autoclass('org.semanticweb.owlapi.apibinding.OWLFunctionalSyntaxFactory')
        self.OWLManager = autoclass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.IRI = autoclass('org.semanticweb.owlapi.model.IRI')
        self.OWLAxiom = autoclass('org.semanticweb.owlapi.model.OWLAxiom')
        self.OWLClass = autoclass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLClassExpression = autoclass('org.semanticweb.owlapi.model.OWLClassExpression')
        self.OWLDataProperty = autoclass('org.semanticweb.owlapi.model.OWLDataProperty')
        self.OWLDatatype = autoclass('org.semanticweb.owlapi.model.OWLDatatype')
        self.OWLEntity = autoclass('org.semanticweb.owlapi.model.OWLEntity')
        self.OWLNamedIndividual = autoclass('org.semanticweb.owlapi.model.OWLNamedIndividual')
        self.OWLObjectProperty = autoclass('org.semanticweb.owlapi.model.OWLObjectProperty')
        self.OWLOntology = autoclass('org.semanticweb.owlapi.model.OWLOntology')
        self.OWLOntologyCreationException = autoclass('org.semanticweb.owlapi.model.OWLOntologyCreationException')
        self.OWLOntologyManager = autoclass('org.semanticweb.owlapi.model.OWLOntologyManager')
        self.OWLSubClassOfAxiom = autoclass('org.semanticweb.owlapi.model.OWLSubClassOfAxiom')
        self.InconsistentOntologyException = autoclass('org.semanticweb.owlapi.reasoner.InconsistentOntologyException')
        self.Node = autoclass('org.semanticweb.owlapi.reasoner.Node')
        self.BlackBoxExplanation = autoclass('com.clarkparsia.owlapi.explanation.BlackBoxExplanation')

        self.InconsistentOntologyException_string = 'JVM exception occurred: Inconsistent ontology'


    def print_items_of_a_set_of_javaclass(self,set_inp, **kwargs):

        space = kwargs.get('space','')
        replacement = kwargs.get('replacement','')

        itr = set_inp.iterator();
        count = 0

        while itr.hasNext():

            count = count + 1
            ele = itr.next()

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}

    def reason_over_ontology(self):

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional)
        worker.run()

        dict = worker.refined_axiom_to_node_or_edge
        ontology = worker.ontology

        if ontology is None:

            LOGGER.info('ontology is None')

        else:

            LOGGER.info('ontology is not None')

        self.project.axioms_to_nodes_edges_mapping = dict
        self.project.ontology_OWL = ontology

        self.manager = self.OWLManager.createOWLOntologyManager()
        configuration = self.Configuration();
        hermit = self.Reasoner(configuration, ontology);
        #ontology_IRI = ontology.getOntologyID().getOntologyIRI().get();

        try:

            hermit.precomputeInferences()

            emptyNode = hermit.getUnsatisfiableClasses()

            cast(self.Node,emptyNode)

            if hermit.isConsistent() is True:
                self.project.inconsistent_ontology = False
            else:
                LOGGER.info('ontology is inconsistent however exception was not thrown')
                sys.exit(0)

            factory = self.ReasonerFactory()
            bbe = self.BlackBoxExplanation(ontology, factory, hermit)

            entities_of_emptyNode = emptyNode.getEntities()
            entities_of_emptyNode_itr = entities_of_emptyNode.iterator()

            unsatisfiable_classes_string = []
            explanations_for_all_unsatisfiable_classs = []

            while entities_of_emptyNode_itr.hasNext():

                cl = entities_of_emptyNode_itr.next()
                cast(self.OWLClass, cl)

                if self.project.iri in cl.toString():

                    unsatisfiable_classes_string.append(cl.toString())

                    expl_raw = bbe.getExplanation(cl)
                    itr = expl_raw.iterator()
                    count = 0

                    explanations_for_unsatisfiable_class=[]

                    while itr.hasNext():

                        count = count + 1
                        axiom_raw = itr.next()
                        cast(self.OWLAxiom, axiom_raw)

                        explanations_for_unsatisfiable_class.append(axiom_raw.toString())

                    explanations_for_all_unsatisfiable_classs.append(explanations_for_unsatisfiable_class)

            self.project.unsatisfiable_classes = unsatisfiable_classes_string
            self.project.explanations_for_unsatisfiable_classes = explanations_for_all_unsatisfiable_classs

            if len(self.project.unsatisfiable_classes) != len(explanations_for_all_unsatisfiable_classs):

                LOGGER.info('len(self.project.unsatisfiable_classes) != len(explanations_for_all_unsatisfiable_classs)')

                sys.exit(0)

        except Exception as e:

            if str(e) == self.InconsistentOntologyException_string:

                self.project.inconsistent_ontology = True

                factory = self.ReasonerFactory()
                ecf = self.InconsistentOntologyExplanationGeneratorFactory(factory, 0)
                generator = ecf.createExplanationGenerator(ontology)

                axiom = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(self.OWLFunctionalSyntaxFactory.OWLThing(), self.OWLFunctionalSyntaxFactory.OWLNothing())

                try:
                    explanations = generator.getExplanations(axiom)
                    explanations_itr = explanations.iterator()

                    while explanations_itr.hasNext():

                        explanation = explanations_itr.next()
                        self.project.explanations_for_inconsistency.append(explanation)

                except Exception as ex:

                    ex.printStackTrace()

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        self.sgnBusy.emit(True)

        self.reason_over_ontology()
        detach()

        self.sgnBusy.emit(False)

        if self.project.inconsistent_ontology is True:
            self.sgnOntologyInconsistency.emit()
        else:
            if len(self.project.unsatisfiable_classes):
                self.sgnUnsatisfiableClasses.emit()
            else:
                self.sgnAllOK.emit()


class InconsistentOntologyDialog(QtWidgets.QDialog, HasThreadingSystem, HasWidgetSystem):

    sgnWork = QtCore.pyqtSignal()

    def __init__(self,project, path, session):

        super().__init__(session)

        self.msgbox_done = QtWidgets.QMessageBox(self, objectName='msgbox_done')

        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setText('Ontology is inconsistent.\n The link(s) for the explanation(s) are displayed below.\n You may choose to display one explanation at a time in the Explanation\
                                 Explorer in the bottom-right portion of the screen.\
                                 To reset the background colouring of the nodes in the diagram, press the Reset button in the toolbar')

        self.addWidget(self.msgbox_done)

        self.messageBoxLayout = QtWidgets.QVBoxLayout()
        self.messageBoxLayout.setContentsMargins(0, 6, 0, 0)
        self.messageBoxLayout.setAlignment(QtCore.Qt.AlignRight)
        self.messageBoxLayout.addWidget(self.widget('msgbox_done'))

        self.messageBoxArea = QtWidgets.QWidget()
        self.messageBoxArea.setLayout(self.messageBoxLayout)

        self.confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmation.addButton(QtWidgets.QDialogButtonBox.Close)
        self.confirmation.setFont(Font('Roboto', 12))
        self.confirmation.setObjectName('confirmation')

        connect(self.confirmation.rejected, self.close)

        self.addWidget(self.confirmation)

        self.confirmationLayout = QtWidgets.QHBoxLayout()
        self.confirmationLayout.setContentsMargins(0, 0, 0, 0)
        self.confirmationLayout.addWidget(self.widget('confirmation'), 0, QtCore.Qt.AlignRight)

        self.confirmationArea = QtWidgets.QWidget()
        self.confirmationArea.setLayout(self.confirmationLayout)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)
        self.mainLayout.addWidget(self.confirmationArea)

        self.setLayout(self.mainLayout)
        self.setFont(Font('Roboto', 12))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Ontology consistency check complete')

        self.explanationButtonsLayout = QtWidgets.QHBoxLayout()
        self.explanationButtonsArea = QtWidgets.QWidget()

        self.setWindowFlags(QtCore.Qt.Window)

        self.hide()
        self.setWindowModality(QtCore.Qt.NonModal)
        self.show()

        self.project = project
        self.session = session

        connect(self.sgnWork, self.doWork)

        self.sgnWork.emit()

    @QtCore.pyqtSlot()
    def minimize(self):

        self.hide()
        self.setWindowModality(QtCore.Qt.NonModal)
        self.show()

    def set_explanation_to_display_in_widget(self,ip=0):

        axioms = self.project.explanations_for_inconsistency[ip - 1].getAxioms()
        itr = axioms.iterator()

        list_of_axioms = []

        while itr.hasNext():
            ele = itr.next()
            list_of_axioms.append(ele.toString())

        self.project.get_axioms_of_explanation_to_display_in_widget = list_of_axioms
        self.session.pmanager.create_add_and_start_plugin('Explanation_explorer')

    def addAColumnOfButtons(self, floor, ceiling):

        explanationButtonsColumnLayout = QtWidgets.QVBoxLayout()
        explanationButtonsColumnArea = QtWidgets.QWidget()

        for e in range(floor,ceiling+1):

            widget = QtWidgets.QPushButton(objectName=str(e))
            widget.setText('Explanation ' + str(e))
            widget.setFont(Font('Roboto', 12))

            connect(widget.clicked, self.set_explanation_to_display_in_widget, e)

            explanationButtonsColumnLayout.addWidget(widget)
        explanationButtonsColumnArea.setLayout(explanationButtonsColumnLayout)
        self.explanationButtonsLayout.addWidget(explanationButtonsColumnArea)

    @QtCore.pyqtSlot()
    def doWork(self):

        total_no_of_buttons = len(self.project.explanations_for_inconsistency)
        #total_no_of_buttons = 44

        sb = math.sqrt(total_no_of_buttons)
        total_number_of_rows = math.ceil(sb)
        total_no_of_columns = math.ceil(sb)

        if (total_number_of_rows>15) | (total_no_of_buttons > 45):
            total_number_of_rows = 15
            total_no_of_columns = math.ceil(total_no_of_buttons/15)

        if total_no_of_buttons <=45:
            total_no_of_columns = 3
            total_number_of_rows = math.ceil(total_no_of_buttons/3)

        total_number_of_extra_spaces = (total_number_of_rows*total_no_of_columns) - total_no_of_buttons
        extra_space_dec = math.floor(total_number_of_extra_spaces / total_no_of_columns)
        extra_extra_space = int(math.fmod(total_number_of_extra_spaces,total_no_of_columns))

        sp = 1
        ep = sp+total_number_of_rows-1

        for c in range(1,total_no_of_columns+1):

            if extra_extra_space > 0:
                ep = ep - 1
                extra_extra_space = extra_extra_space - 1

            if total_number_of_extra_spaces>0:

                ep = ep-extra_space_dec
                total_number_of_extra_spaces=total_number_of_extra_spaces-extra_space_dec

            self.addAColumnOfButtons(sp, ep)

            new_sp = ep+1
            new_ep = new_sp+total_number_of_rows-1

            sp = new_sp
            ep = new_ep

        self.explanationButtonsArea.setLayout(self.explanationButtonsLayout)
        self.mainLayout.addWidget(self.explanationButtonsArea)
        self.setLayout(self.mainLayout)