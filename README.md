![Eddy](/artwork/images/eddy_banner.png?raw=true)

[![Circle CI](https://img.shields.io/circleci/project/danielepantaleone/eddy/master.svg)](https://circleci.com/gh/danielepantaleone/eddy/tree/master)
[![Build Status](https://travis-ci.org/danielepantaleone/eddy.svg?branch=master)](https://travis-ci.org/danielepantaleone/eddy)
[![GitHub issues](https://img.shields.io/github/issues/danielepantaleone/eddy.svg)](https://github.com/danielepantaleone/eddy/issues)
[![Code Health](https://landscape.io/github/danielepantaleone/eddy/master/landscape.svg?style=flat)](https://landscape.io/github/danielepantaleone/eddy/master)
[![Coverage Status](https://coveralls.io/repos/github/danielepantaleone/eddy/badge.svg?branch=master&bust=1)](https://coveralls.io/github/danielepantaleone/eddy?branch=master)
[![Python version](https://img.shields.io/badge/python-3.4.3-blue.svg)](https://www.python.org)
[![GitHub license](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://raw.githubusercontent.com/danielepantaleone/eddy/master/LICENSE)
[![Gitter chatroom](https://badges.gitter.im/danielepantaleone/eddy.svg)](https://gitter.im/danielepantaleone/eddy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Eddy is a graphical editor for the specification and visualization of Graphol ontologies. 
Eddy features a design environment specifically thought out for generating Graphol ontologies through 
ad-hoc functionalities. Drawing features allow designers to comfortably edit ontologies in a central 
viewport area, while two lateral docking areas contains specifically-tailored widgets for editing, 
navigating and inspecting open diagrams. Eddy is equipped with design-time syntax validation functionalities 
which prevents ontology designers from constructing invalid Graphol expressions: feedback on the validity of 
the expression is given through color coding diagram elements.

In order to support interaction with third-party tools such as OWL 2 reasoners and editors like [Protégé], 
Eddy is able to export the produced Graphol ontology into an OWL 2 ontology. Other simpler exporting file 
formats, like PDF, are also currently provided.

Eddy is written in [Python] and make use of the [PyQt5] python bindings for the cross-platform [Qt5] framework. 

### About Graphol

[Graphol] is a novel language for the specification and visualization of Description Logic (DL) ontologies, 
developed by members of the DASI-lab group of the [Dipartimento di Ingegneria Informatica, Automatica e Gestionale "A.Ruberti"] 
at [Sapienza] University of Rome. Graphol  offers a completely visual representation of ontologies to users, in order to help 
understanding by people who are not skilled in logic. Graphol provides designers with simple graphical primitives for ontology 
editing, avoiding complex textual syntax. Graphol's basic components are inspired by Entity Relationship (ER) diagrams, thus 
ontologies that can be rendered as ER diagrams have in Graphol a similar diagrammatic shape.

* [Domenico Lembo](http://www.dis.uniroma1.it/~lembo/)                         
* [Valerio Santarelli](http://www.dis.uniroma1.it/~dottoratoii/students/valerio-santarelli)           
* [Domenico Fabio Savo](http://www.dis.uniroma1.it/~savo/) 
* [Daniele Pantaleone](https://github.com/danielepantaleone/) 
* [Marco Console](http://www.dis.uniroma1.it/~dottoratoii/students/marco-console)                 

### Related papers

- **Easy OWL Drawing with the Graphol Visual Ontology Language** [PDF](http://www.aaai.org/ocs/index.php/KR/KR16/paper/view/12904/12524)<br/>
  Domenico Lembo, Daniele Pantaleone, Valerio Santarelli, Domenico Fabio Savo<br/>
  *Proceedings of the 15th International Conference, KR-2016, Cape Town, South Africa, April 25-29, 2016*

### Screenshot

![screenshot](/artwork/images/shot01.png?raw=true)

### License

Eddy is licensed under the GNU General Public License v3. See the LICENSE file included with the distribution.

### Resources

* [Bug tracker](https://github.com/danielepantaleone/eddy/issues)
* [Graphol website](http://www.dis.uniroma1.it/~graphol/)
* [Source code](https://github.com/danielepantaleone/eddy)

[Dipartimento di Ingegneria Informatica, Automatica e Gestionale "A.Ruberti"]: http://www.dis.uniroma1.it/en
[Graphol]: http://www.dis.uniroma1.it/~graphol/
[Python]: https://www.python.org/
[PyQt5]: https://riverbankcomputing.com/software/pyqt/intro
[Protégé]: http://protege.stanford.edu/
[Qt5]: http://www.qt.io/
[Sapienza]: http://en.uniroma1.it/