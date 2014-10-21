# -*- coding: utf-8; -*-
#
# Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

# -*- coding: utf-8; -*-
#
# Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

from __future__ import absolute_import

import unittest
import doctest
import re
import os

from pprint import pprint

from zope.testing.renormalizing import RENormalizing

from crate.testing.layer import CrateLayer
from crate.client import connect

from crate.client import http
from crate.client.compat import cprint

def crate_path(*parts):
    return os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ),
            '..',
            '..',
            'parts',
            'crate',
            *parts)
    )



crate_port = 44209
crate_transport_port = 44309
crate_layer = CrateLayer('crate',
                         crate_home=crate_path(),
                         crate_exec=crate_path('bin', 'crate'),
                         port=crate_port,
                         transport_port=crate_transport_port)

crate_host = "127.0.0.1:{port}".format(port=crate_port)
crate_uri = "http://%s" % crate_host


def setUpForDjango(test):
    connect(crate_host)
    import os
    os.environ["DJANGO_SETTINGS_MODULE"] = "crate.django.testing.settings"

    from django.test.runner import setup_databases
    from django import setup
    setup()
    setup_databases(3, False)

def test_suite():
    suite = unittest.TestSuite()
    flags = (doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    checker = RENormalizing([
        # python 3 drops the u" prefix on unicode strings
        (re.compile(r"u('[^']*')"), r"\1"),

        # python 3 includes module name in exceptions
        (re.compile(r"crate.client.exceptions.ProgrammingError:"),
         "ProgrammingError:"),
        (re.compile(r"crate.client.exceptions.ConnectionError:"),
         "ConnectionError:"),
        (re.compile(r"crate.client.exceptions.DigestNotFoundException:"),
         "DigestNotFoundException:"),
        (re.compile(r"crate.client.exceptions.BlobsDisabledException:"),
         "BlobsDisabledException:"),
        (re.compile(r"<type "),
         "<class "),
    ])

    # DJANGO TESTS
    django_suite = doctest.DocFileSuite(
        'testing/backend.txt',
        checker=checker,
        setUp=setUpForDjango,
        optionflags=flags
    )
    django_suite.layer = crate_layer
    suite.addTest(django_suite)

    return suite
