#!/usr/bin/env python3
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

import argparse
import logging
import os
import sys

from bintray.bintray import Bintray

LOGGER = logging.getLogger('bintray_upload')
LOGGER.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
LOGGER.addHandler(_handler)


def main(args):
    """
    Entry point.
    :type args: list
    """
    # PARSE COMMAND LINE ARGUMENTS
    parser = argparse.ArgumentParser(description='Upload files to Bintray using the REST API.')
    # UPLOAD PARAMETERS
    parser.add_argument('--username', type=str, required=True,
                        help='Bintray API username.')
    parser.add_argument('--api-key', type=str, required=True,
                        help='Bintray API key.')
    parser.add_argument('--subject', type=str,
                        help='Username or organization of the target repository.')
    parser.add_argument('--repo', type=str, required=True,
                        help='The repository name.')
    parser.add_argument('--package', type=str, required=True,
                        help='The package name.')
    parser.add_argument('--version', type=str, required=True,
                        help='The package version.')
    parser.add_argument('--prefix-path', type=str,
                        help='Prefix path to prepend to the remote filename.')
    parser.add_argument('--publish', action='store_true', default=False,
                        help='Whether to publish the artifact after uploading.')
    parser.add_argument('--override', action='store_true', default=False,
                        help='Whether to override conflicting artifacts.')
    parser.add_argument('files', type=str, metavar='artifact', nargs='+',
                        help='Artifact to upload.')
    options = parser.parse_args(args)

    try:
        # INITIALIZE BINTRAY CLIENT
        LOGGER.info('Initialising Bintray client...')
        api = Bintray(options.username, options.api_key)
        subject = options.subject or options.username
        repo = options.repo
        package = options.package
        version = options.version

        # ATTEMPT TO ACCESS VERSION INFO
        try:
            api.get_version(subject, repo, package, version)
            LOGGER.info('Found existing version %s', version)
        except Exception as e:
            # CREATE A NEW VERSION IF NEEDED
            try:
                LOGGER.info('Creating new version %s', version)
                api.create_version(subject, repo, package, version)
            except Exception as e:
                LOGGER.exception('Unable to create new version: %s', e, exc_info=e)
                return 3

        # UPLOAD ARTIFACTS
        for local_file in options.files:
            remote_file = '/'.join([options.prefix_path, os.path.basename(local_file)]) \
                if options.prefix_path else os.path.basename(local_file)
            LOGGER.info('Uploading %s -> %s', local_file, remote_file)
            api.upload_content(
                subject, repo, package, version,
                remote_file, local_file,
                publish=options.publish,
                override=options.override
            )
    except Exception as e:
        LOGGER.exception('Error during content upload: %s', e, exc_info=e)
        return 2

    LOGGER.info('Upload completed successfully.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)
