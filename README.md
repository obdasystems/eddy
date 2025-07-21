Eddy
====

[![GitHub license](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://raw.githubusercontent.com/obdasystems/eddy/master/LICENSE)
[![Release](https://img.shields.io/github/release/obdasystems/eddy.svg)](https://github.com/obdasystems/eddy/releases)

| Branch    | Status        |
|-----------|---------------|
| [master](https://github.com/obdasystems/eddy/tree/master)   |[![Tests Status](https://github.com/obdasystems/eddy/workflows/tests/badge.svg?branch=master)](https://github.com/obdasystems/eddy/actions)  [![Build Status](https://github.com/obdasystems/eddy/workflows/builds/badge.svg?branch=master)](https://github.com/obdasystems/eddy/actions) |
| [develop](https://github.com/obdasystems/eddy/tree/develop) |[![Tests Status](https://github.com/obdasystems/eddy/workflows/tests/badge.svg?branch=develop)](https://github.com/obdasystems/eddy/actions) [![Build Status](https://github.com/obdasystems/eddy/workflows/builds/badge.svg?branch=develop)](https://github.com/obdasystems/eddy/actions)|

Eddy is a graphical editor for the specification and visualization of Graphol ontologies.
Eddy features a design environment specifically thought out for generating Graphol ontologies through
ad-hoc functionalities. Drawing features allow designers to comfortably edit ontologies in a central
viewport area, while two lateral docking areas contains specifically-tailored widgets for editing,
navigating and inspecting open diagrams. Eddy is equipped with design-time syntax validation functionalities
which prevents ontology designers from constructing invalid Graphol expressions: feedback on the validity of
the expression is given through color coding diagram elements. Eddy also supports the standard profiles of
OWL 2, i.e. OWL 2 QL, OWL 2 RL, and OWL 2 EL (*to appear*). These profiles are less expressive fragments of
OWL 2, and the user can select one of the three from a drop-down menu in the toolbar. When one of the
profiles is selected, all syntactic validation tools will be run with respect to the syntax of the chosen profile.

In order to support interaction with third-party tools such as OWL 2 reasoners and editors like [Protégé],
Eddy is able to export the produced Graphol ontology into an OWL 2 ontology. Other simpler exporting file
formats, like PDF, are also currently provided.

Eddy is written in [Python] and make use of the [PyQt5] python bindings for the cross-platform [Qt5] framework.

### Screenshot

![screenshot](resources/images/shot01.png?raw=true)

### Installing

You can get the latest version of Eddy from the [GitHub releases page](https://github.com/obdasystems/eddy/releases),
or follow more detailed [installation instructions](docs/install.md) on how to set up and
install Eddy on the most common platforms.

### About Graphol

Graphol is a novel language for the specification and visualization of Description Logic (DL) ontologies,
developed by members of the DASI-lab group of the [Dipartimento di Ingegneria Informatica, Automatica e Gestionale "A.Ruberti"]
at [Sapienza] University of Rome. Graphol  offers a completely visual representation of ontologies to users, in order to help
understanding by people who are not skilled in logic. Graphol provides designers with simple graphical primitives for ontology
editing, avoiding complex textual syntax. Graphol's basic components are inspired by Entity Relationship (ER) diagrams, thus
ontologies that can be rendered as ER diagrams have in Graphol a similar diagrammatic shape.

Graphol is licensed under a [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License](https://creativecommons.org/licenses/by-nc-nd/4.0/).

* [Domenico Lembo](http://www.dis.uniroma1.it/~lembo/)
* [Valerio Santarelli](http://www.dis.uniroma1.it/~dottoratoii/students/valerio-santarelli)
* [Domenico Fabio Savo](http://www.dis.uniroma1.it/~savo/)
* [Daniele Pantaleone](https://github.com/danielepantaleone/)
* [Marco Console](http://www.dis.uniroma1.it/~dottoratoii/students/marco-console)

### Related papers

- **Eddy: A Graphical Editor for OWL 2 Ontologies** [PDF](http://www.ijcai.org/Proceedings/16/Papers/646.pdf)<br/>
  Domenico Lembo, Daniele Pantaleone, Valerio Santarelli, Domenico Fabio Savo<br/>
  *Proc. of the 25th International Joint Conference on Artificial Intelligence, IJCAI-16, New York, NY, USA, July 9-15, 2016*

- **Easy OWL Drawing with the Graphol Visual Ontology Language** [PDF](http://www.aaai.org/ocs/index.php/KR/KR16/paper/view/12904/12524)<br/>
  Domenico Lembo, Daniele Pantaleone, Valerio Santarelli, Domenico Fabio Savo<br/>
  *Proc. of the 15th International Conference on Principles of Knowledge Representation and Reasoning, KR-2016, Cape Town, South Africa, April 25-29, 2016*

- **Design and development of an editor for the graphical specification of OWL ontologies** [PDF](https://drive.google.com/file/d/0BwGkBOchEhbJZXVZaU9WNTlCZWc/view)<br/>
  Daniele Pantaleone, Academic Year 2015/2016<br/>
  *Master thesis in Engineering in Computer Science (Advisor. Prof. Domenico Lembo)*

### Contributing

Everyone is welcome to contribute to Eddy. Please read the
[contributing guidelines](docs/contributing.md) before submitting a pull request.

If you have a bug or a feature request to report, please use the
[GitHub issue tracker](https://github.com/obdasystems/eddy/issues).

### License

Eddy is licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
See the LICENSE file included with the distribution.

[Dipartimento di Ingegneria Informatica, Automatica e Gestionale "A.Ruberti"]: http://www.dis.uniroma1.it/en
[Python]: https://www.python.org/
[PyQt5]: https://riverbankcomputing.com/software/pyqt/intro
[Protégé]: http://protege.stanford.edu/
[Qt5]: http://www.qt.io/
[Sapienza]: http://en.uniroma1.it/
