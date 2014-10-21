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

from setuptools import setup, find_packages
import os


requirements = [
    'crate>=0.12',
    'crash>=0.10.2',
    'setuptools',
    'six'
]


def read(path):
    return open(os.path.join(os.path.dirname(__file__), path)).read()


long_description = (
    read('README.rst')
)

setup(
    name='crate-django',
    version='0.0.1',
    url='https://github.com/crate/crate-django',
    author='CRATE Technology GmbH',
    author_email='office@crate.io',
    package_dir={'': 'src'},
    description='CrateIO backend for the Django web framework',
    long_description=long_description,
    platforms=['any'],
    license='Apache License 2.0',
    keywords='crate db django',
    packages=find_packages('src'),
    namespace_packages=['crate'],
    extras_require=dict(
        test=['lovely.testlayers',
              'mock>=1.0.1',
              'zope.testing',
              'zc.customdoctests>=1.0.1',
              'django>=1.7,<1.8']
    ),
    install_requires=requirements,
    package_data={'': ['*.txt']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Database',
        'Framework :: Django',
    ],
)
