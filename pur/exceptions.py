# -*- coding: utf-8 -*-
"""
    pur.exceptions
    ~~~~~~~~~~~~~~
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


class InvalidPackage(Exception):
    """The package has no releases."""
    pass


class StopUpdating(Exception):
    """Stop updating a requirements file and exit."""
    pass
