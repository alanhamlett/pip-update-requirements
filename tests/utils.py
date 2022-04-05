# -*- coding: utf-8 -*-

import os
import logging
import unittest
from contextlib import contextmanager
from unittest.mock import patch


def u(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return str(text)


class TestCase(unittest.TestCase):
    patch_these = []

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)

        self.patched = {}
        if hasattr(self, 'patch_these'):
            for patch_this in self.patch_these:
                namespace = patch_this[0] if isinstance(patch_this, (list, set)) else patch_this

                patcher = patch(namespace)
                mocked = patcher.start()
                mocked.reset_mock()
                self.patched[namespace] = mocked

                if isinstance(patch_this, (list, set)) and len(patch_this) > 0:
                    retval = patch_this[1]
                    if callable(retval):
                        retval = retval()
                    mocked.return_value = retval

    def tearDown(self):
        patch.stopall()

    def normalize_list(self, items):
        return sorted([u(x) for x in items])

    def assertListsEqual(self, first_list, second_list):
        self.assertEqual(self.normalize_list(first_list), self.normalize_list(second_list))

    @contextmanager
    def cd(self, newdir):
        prevdir = os.getcwd()
        os.chdir(os.path.expanduser(newdir))
        try:
            yield
        finally:
            os.chdir(prevdir)
