.. image:: https://img.shields.io/github/actions/workflow/status/alanhamlett/pip-update-requirements/tests.yml?branch=master
    :target: https://github.com/alanhamlett/pip-update-requirements/actions
    :alt: Tests

.. image:: https://codecov.io/gh/alanhamlett/pip-update-requirements/branch/master/graph/badge.svg?token=Ob1I7eMhiS
    :target: https://codecov.io/gh/alanhamlett/pip-update-requirements
    :alt: Coverage

.. image:: https://img.shields.io/pypi/v/pur.svg
    :target: https://pypi.python.org/pypi/pur
    :alt: Version

.. image:: https://img.shields.io/pypi/pyversions/pur.svg
    :target: https://pypi.python.org/pypi/pur
    :alt: Supported Python Versions

.. image:: https://wakatime.com/badge/github/alanhamlett/pip-update-requirements.svg
    :target: https://wakatime.com/badge/github/alanhamlett/pip-update-requirements


pip-update-requirements
=======================

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

    $ pur -r requirements.txt
    Updated flask: 0.9 -> 1.0.2
    Updated sqlalchemy: 0.9.10 -> 1.2.8
    Updated alembic: 0.8.4 -> 0.9.9
    All requirements up-to-date.


Pur never modifies your environment or installed packages, it only modifies
your ``requirements.txt`` file.

You can also use Pur directly from Python::

    $ python
    Python 3.6.1
    >>> from pur import update_requirements
    >>> print([x[0]['message'] for x in update_requirements(input_file='requirements.txt').values()])
    ['Updated flask: 0.9 -> 1.0.2', 'Updated sqlalchemy: 0.9.10 -> 1.2.8', 'Updated alembic: 0.8.4 -> 0.9.9']
    >>> print(open('requirements.txt').read())
    flask==1.0.2
    sqlalchemy==1.2.8
    alembic==0.9.9


Options
-------

-r, --requirement PATH   The requirements.txt file to update; Defaults to
                         using requirements.txt from the current directory
                         if it exist.
-o, --output PATH        Output updated packages to this file; Defaults to
                         overwriting the input requirements.txt file.
--interactive            Interactively prompts before updating each package.
-f, --force              Force updating packages even when a package has no
                         version specified in the input requirements.txt
                         file.
-d, --dry-run            Output changes to STDOUT instead of overwriting the
                         requirements.txt file.
--dry-run-changed        When running with --dry-run, only output packages
                         with updates, not packages that are already the
                         latest.
-n, --no-recursive       Prevents updating nested requirements files.
--skip TEXT              Comma separated list of packages to skip updating.
--skip-gt                Skip updating packages using > or >= spec, to allow
                         specifying minimum supported versions of packages.
--index-url TEXT         Base URL of the Python Package Index. Can be
                         provided multiple times for extra index urls.
--cert PATH              Path to PEM-encoded CA certificate bundle. If
                         provided, overrides the default.
--no-ssl-verify          Disable verifying the server's TLS certificate.
--only TEXT              Comma separated list of packages. Only these
                         packages will be updated.
--minor TEXT             Comma separated list of packages to only update
                         minor versions, never major. Use "*" to limit every
                         package to minor version updates.
--patch TEXT             Comma separated list of packages to only update
                         patch versions, never major or minor. Use "*" to
                         limit every package to patch version updates.
--pre TEXT               Comma separated list of packages to allow updating
                         to pre-release versions. Use "*" to allow all
                         packages to be updated to pre-release versions. By
                         default packages are only updated to stable
                         versions.
-z, --nonzero-exit-code  Exit with status 1 when some packages were updated,
                         0 when no packages updated, or a number greater
                         than 1 when there was an error. By default, exit
                         status 0 is used unless there was an error
                         irregardless of whether packages were or not
                         updated.
--version                Show the version and exit.
--help                   Show this message and exit.


Contributing
------------

Before contributing a pull request, make sure tests pass::

    virtualenv venv
    . venv/bin/activate
    pip install tox
    tox

Many thanks to all `contributors <https://github.com/alanhamlett/pip-update-requirements/blob/master/AUTHORS>`_!
