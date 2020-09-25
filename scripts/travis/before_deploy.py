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

import os
import json
from eddy import APPNAME, VERSION, PROJECT_HOME, BUG_TRACKER

OS_NAME = os.getenv('TRAVIS_OS_NAME') or 'windows'
BRANCH = os.getenv('TRAVIS_BRANCH') or os.getenv('APPVEYOR_REPO_BRANCH') or 'master'
BUILD_DIR = os.getenv('TRAVIS_BUILD_DIR') or os.getenv('APPVEYOR_BUILD_FOLDER') or os.getenv('PWD')
BINTRAY_USER = os.getenv('BINTRAY_USER') or os.getenv('USER')
BINTRAY_SUBJECT = os.getenv('BINTRAY_SUBJECT') or os.getenv('BINTRAY_USER') or os.getenv('USER')
BINTRAY_REPO = os.getenv('BINTRAY_REPO')

# Setup package descriptor
descriptor = {
    'package': {
        'name': APPNAME,
        'repo': BINTRAY_REPO,
        'subject': BINTRAY_SUBJECT,
        'issue_tracker_url': BUG_TRACKER,
        'vcs_url': PROJECT_HOME,
        'labels': ['Graphol', 'OWL 2', 'Modeling'],
        'licenses': ['GPL-3.0'],
        'public_download_numbers': False,
        'public_stats': False
    },
    'version': {
        'name': VERSION,
    },
    'files': [
        {
            'includePattern': 'dist/(.*)',
            'uploadPattern': '/'.join([VERSION, '$1']),
            'matrixParams': {'override': 1}
        },
    ],

    'publish': True
}

with open(os.path.join(BUILD_DIR, 'descriptor.json'), 'w') as descriptor_fd:
    json.dump(descriptor, descriptor_fd, indent=True)
