pip-update-requirements
=======================

.. image:: https://travis-ci.org/alanhamlett/pip-update-requirements.svg?branch=master
    :target: https://travis-ci.org/alanhamlett/pip-update-requirements
    :alt: Tests

.. image:: https://coveralls.io/repos/alanhamlett/pip-update-requirements/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/alanhamlett/pip-update-requirements?branch=master
    :alt: Coverage

.. image:: https://gemnasium.com/badges/github.com/alanhamlett/pip-update-requirements.svg
    :target: https://gemnasium.com/github.com/alanhamlett/pip-update-requirements
    :alt: Dependencies


Update the packages in a ``requirements.txt`` file.

.. image:: https://raw.githubusercontent.com/alanhamlett/pip-update-requirements/master/pur.gif
    :alt: Purring Cat


Installation
------------

::

    pip install pur


Usage
-----

Give pur your ``requirements.txt`` file and it updates all your packages to
the latest versions.

For example, given a ``requirements.txt`` file::

    flask==0.9
    sqlalchemy==0.9.10
    alembic==0.8.4

Running pur on that file updates the packages to current latest versions::

    $ pur requirements.txt
    Updated flask: 0.9 -> 0.10.1
    Updated sqlalchemy: 0.9.10 -> 1.0.12
    Updated alembic: 0.8.4 -> 0.8.6
    All requirements up-to-date.


Pur never modifies your environment or installed packages, it only modifies
your ``requirements.txt`` file.


Options
-------

There is an optional ``--output`` argument to write the new
``requirements.txt`` file to a different location than the default. By
default, pur overwrites your ``requirements.txt`` file.


Contributing
------------

Before contributing a pull request, make sure tests pass::

    virtualenv venv
    . venv/bin/activate
    pip install tox
    tox

Many thanks to all `contributors <https://github.com/alanhamlett/pip-update-requirements/blob/master/AUTHORS>`_!
