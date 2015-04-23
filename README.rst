============
CRATE Django
============

A django database backend for Crate.IO

**Disclaimer**

This piece of software is still in pre-alpha state
and is in no means ready for production.

Development
===========

Preferrably inside a virtualenv::

    python bootstrap.py
    bin/buildout

This will setup a sandboxed environment for development and testing purposes.

Tests
-----

To run the tests, simply run::

    bin/test

Usage
=====

Configure the backend in you ``settings.py``::

    DATABASES = {
        'default': {
            'ENGINE': 'crate.django.backend',
            'SERVERS': ["127.0.0.1:4200", "127.0.0.2:4200", ...]
        }
    }


Features
========

* primitive datatypes like strings and numeric types are supported
* configuring and executing Fulltext search in string columns

Missing Features
----------------

* creating Tables from CrateModels (syncdb)
* Refreshing
* Aggregates
* Array and Object columns
