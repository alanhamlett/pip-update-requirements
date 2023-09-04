# -*- coding: utf-8 -*-


import os
import shutil
import tempfile
from unittest.mock import patch

from pur import pur, update_requirements, __version__

from click.testing import CliRunner
from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.link import Link
from pip._internal.req.req_install import Version

from . import utils
from .utils import u


class PurTestCase(utils.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None

    def test_help_contents(self):
        args = ['--help']
        result = self.runner.invoke(pur, args)
        self.assertIsNone(result.exception)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('pur', u(result.output))
        self.assertIn('Usage', u(result.output))
        self.assertIn('Options', u(result.output))

    def test_version(self):
        args = ['--version']
        result = self.runner.invoke(pur, args)
        self.assertIsNone(result.exception)
        expected_output = "pur, version {0}\n".format(__version__)
        self.assertEqual(u(result.output), u(expected_output))
        self.assertEqual(result.exit_code, 0)

    def test_updates_package(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_updates_package_in_nested_requirements(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated readtime: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements_nested').read()
            self.assertEqual(open(requirements_nested).read(), expected_requirements)

    def test_requirements_long_option_accepted(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['--requirement', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_updates_package_to_output_file(self):
        tempdir = tempfile.mkdtemp()
        output = os.path.join(tempdir, 'output.txt')
        previous = open('tests/samples/requirements.txt').read()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--output', output]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open('tests/samples/requirements.txt').read(), previous)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(output).read(), expected_requirements)

    def test_updates_nested_requirements_to_output_file(self):
        tempdir = tempfile.mkdtemp()
        tempdir = tempfile.mkdtemp()
        output = os.path.join(tempdir, 'output.txt')
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements, '--output', output]

        expected_output = "Updated readtime: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
        expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements').read()
        expected_requirements = expected_requirements.replace('-r requirements-nested.txt\n', open('tests/samples/results/test_updates_package_in_nested_requirements_nested').read())

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(requirements_nested).read(), open('tests/samples/requirements-nested.txt').read())
            self.assertEqual(open(requirements).read(), open('tests/samples/requirements-with-nested-reqfile.txt').read())
            self.assertEqual(open(output).read(), expected_requirements)

    def test_exit_code_from_no_updates(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-up-to-date.txt', requirements)
        args = ['-r', requirements, '--nonzero-exit-code']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_exit_code_from_some_updates(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--nonzero-exit-code']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertEqual(result.exception.code, 1)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 1)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_exit_code_from_nested_requirements_file(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements, '--nonzero-exit-code']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertEqual(result.exception.code, 1)
            expected_output = "Updated readtime: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 1)
            expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements_nested').read()
            self.assertEqual(open(requirements_nested).read(), expected_requirements)

    def test_no_recursive_option(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements, '-n']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)

            expected_requirements = open('tests/samples/requirements-with-nested-reqfile.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            expected_requirements = open('tests/samples/requirements-nested.txt').read()
            self.assertEqual(open(requirements_nested).read(), expected_requirements)

    def test_skip_package(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '--skip', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated Alembic: 0.9 -> 0.10.1\nUpdated sqlalchemy: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_skip_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_skip_package_in_nested_requirements(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements, '--skip', 'readtime']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            expected_requirements = open('tests/samples/results/test_skip_package_in_nested_requirements_nested').read()
            self.assertEqual(open(requirements_nested).read(), expected_requirements)

    def test_minor_upgrades(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--minor', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '12.1.3'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 12.0 -> 12.1.3\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_minor').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_minor_skips(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--minor', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '13.0.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_minor_skips_with_wildcard(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--minor', '*']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '13.0.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_patch_upgrades(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--patch', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '12.0.3'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 12.0 -> 12.0.3\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_patch').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_patch_skips(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--patch', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '12.1.3'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_patch_skips_with_wildcard(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--patch', '*']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '12.1.3'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_only_stable_versions_selected(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '13.0.0.dev0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_pre_upgrades(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--pre', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '13.0.0.dev0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 13.0.0.dev0\nUpdated flask: 12.0 -> 13.0.0.dev0\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_pre_release').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_pre_upgrades_with_wildcard(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--pre', '*']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '13.0.0.dev0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 13.0.0.dev0\nUpdated flask: 12.0 -> 13.0.0.dev0\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_pre_release').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_skip_multiple_packages(self):
        requirements = 'tests/samples/requirements-multiple.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--skip', 'flask, alembic , SQLAlchemy']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open(requirements).read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_only(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '--only', 'flask']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_only').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_only_multiple_packages(self):
        requirements = 'tests/samples/requirements-multiple.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--only', 'flask, sqlalchemy']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nUpdated sqlalchemy: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_only_multiple_packages').read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_no_version_specified(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '-f']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nUpdated flask: Unknown -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_no_version_specified').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_invalid_package(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            mock_find_all_candidates.return_value = []

            result = self.runner.invoke(pur, args)
            expected_output = 'No matching distribution found for flask==0.9 from -r ' + tmpfile + ' (line 1)\n' + \
                'No matching distribution found for flask==12.0 from -r ' + tmpfile + ' (line 2)\n' + \
                'No matching distribution found for flask from -r ' + tmpfile + ' (line 6)\n' + \
                'All requirements up-to-date.\n'
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_no_arguments(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = []

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            with self.cd(tempdir):
                result = self.runner.invoke(pur, args)

            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_no_arguments_and_no_requirements_file(self):
        tempdir = tempfile.mkdtemp()
        args = []

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            with self.cd(tempdir):
                result = self.runner.invoke(pur, args)

            self.assertEqual(result.exception.code, 2)
            expected_output = "Error: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 2)

    def test_missing_requirements_file(self):
        tempdir = tempfile.mkdtemp()
        args = ['-r', 'missing.txt']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            with self.cd(tempdir):
                result = self.runner.invoke(pur, args)

            self.assertEqual(result.exception.code, 2)
            expected_output = "Error: Could not open requirements file: [Errno 2] No such file or directory: 'missing.txt'\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 2)

    def test_updates_package_with_number_in_name(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-version-in-name.txt', requirements)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'package1'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated package1: 1 -> 2.0\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_version_in_name').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_updates_package_with_extras(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-with-extras.txt', requirements)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'firstpackage'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated firstpackage1: 1 -> 2.0\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_extras').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_updates_package_with_max_version_spec(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-with-max-version-spec.txt', requirements)
        args = ['-r', requirements]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated afakepackage: 0.9 -> 0.10.1\nUpdated afakepackage: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_max_version_spec').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_max_version_spec_prevents_updating_package(self):
        requirements = 'tests/samples/requirements-with-max-version-spec.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open(tmpfile).read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_notequal_version_spec_prevents_updating_package(self):
        requirements = 'tests/samples/requirements-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '0.9.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open(tmpfile).read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_multiline_spec(self):
        requirements = 'tests/samples/requirements-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '1.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated afakepackage: 0.9 -> 1.0\nUpdated afakepackage: 0.9 -> 1.0\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_multiline_spec').read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_does_not_update_package_with_multiline_spec(self):
        requirements = 'tests/samples/requirements-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '1.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open(requirements).read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_min_version_spec(self):
        requirements = 'tests/samples/requirements-with-min-version-spec.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'fakewebserver'
            version = '1.8.13'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated fakewebserver: 1.8.6 -> 1.8.13\nNew version for fakewebserver found (1.8.13), but current spec prohibits updating: fakewebserver > 1.8.6, < 1.9\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_min_version_spec').read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_does_not_update_package_with_wildcard_spec(self):
        requirements = 'tests/samples/requirements-with-wildcard-spec.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'fakewebserver'
            version = '0.9.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated flask: 0.9 -> 0.9.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_does_not_update_package_with_wildcard_spec').read()
            self.assertEqual(open(tmpfile).read(), expected_requirements)

    def test_dry_run(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '-d']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = '==> ' + tmpfile + ' <==\n' + \
                open('tests/samples/results/test_updates_package').read() + "\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_dry_run_with_nested_requirements_file(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = ['-r', requirements, '-d']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)

            expected_output = '==> ' + requirements_nested + ' <==\n' + \
                open('tests/samples/results/test_updates_package_in_nested_requirements_nested').read() + "\n" + \
                '==> ' + requirements + ' <==\n' + \
                open('tests/samples/results/test_updates_package_in_nested_requirements').read() + "\n"
            self.assertEqual(u(result.output), u(expected_output))

            expected_requirements = open('tests/samples/requirements-with-nested-reqfile.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            expected_requirements = open('tests/samples/requirements-nested.txt').read()
            self.assertEqual(open(requirements_nested).read(), expected_requirements)

    def test_dry_run_invalid_package(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--dry-run']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            mock_find_all_candidates.return_value = []

            result = self.runner.invoke(pur, args)
            expected_output = 'No matching distribution found for flask==0.9 from -r ' + tmpfile + ' (line 1)\n' + \
                'No matching distribution found for flask==12.0 from -r ' + tmpfile + ' (line 2)\n' + \
                'No matching distribution found for flask from -r ' + tmpfile + ' (line 6)\n' + \
                '==> ' + tmpfile + ' <==\n' + \
                open('tests/samples/results/test_dry_run_invalid_package').read() + "\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_dry_run_changed(self):
        requirements = 'tests/samples/requirements-multiple.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--dry-run-changed']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = '==> ' + tmpfile + ' <==\n' + open('tests/samples/results/test_dry_run_changed').read()
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_dry_run_changed_no_updates(self):
        requirements = 'tests/samples/requirements-up-to-date.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--dry-run-changed']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = ''
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_dry_run_changed_invalid_package(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '--dry-run-changed']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            mock_find_all_candidates.return_value = []

            result = self.runner.invoke(pur, args)
            expected_output = 'No matching distribution found for flask==0.9 from -r ' + tmpfile + ' (line 1)\n' + \
                'No matching distribution found for flask==12.0 from -r ' + tmpfile + ' (line 2)\n' + \
                'No matching distribution found for flask from -r ' + tmpfile + ' (line 6)\n'
            self.assertEqual(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(open(tmpfile).read(), open(requirements).read())

    def test_updates_from_alt_index_url(self):
        requirements = 'tests/samples/requirements-with-alt-index-url.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with patch('pip._vendor.requests.adapters.HTTPAdapter.send') as mock_send:
            self.runner.invoke(pur, args)
            self.assertEqual(mock_send.call_args_list[0][0][0].url, 'http://pypi.example.com/flask/')

    def test_updates_from_alt_index_url_command_line_arg(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['--index-url', 'http://pypi.example.com', '--index-url', 'https://pypi2.example.com', '-r', tmpfile]

        with patch('pip._vendor.requests.adapters.HTTPAdapter.send') as mock_send:
            self.runner.invoke(pur, args)
            self.assertEqual(mock_send.call_args_list[0][0][0].url, 'https://pypi2.example.com/flask/')

    def test_updates_from_alt_index_url_with_verify_command_line_arg(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['--index-url', 'https://example.com', '--cert', '/path/to/cert/file', '-r', tmpfile]

        with patch('pip._vendor.requests.adapters.HTTPAdapter.send') as mock_send:
            self.runner.invoke(pur, args)
            self.assertEqual(mock_send.call_args_list[0][0][0].url, 'https://example.com/flask/')
            self.assertEqual(mock_send.call_args_list[0][1]['verify'], '/path/to/cert/file')

    def test_interactive_choice_default(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--interactive']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: \nUpdated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_interactive_choice_yes(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--interactive']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='y\n')

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: y\nUpdated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_interactive_choice_no(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--interactive']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='n\n')

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: n\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_interactive_choice_quit(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '--interactive']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='y\nq\n')
            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: y\nUpdated flask: 0.9 -> 0.10.1\nUpdate Alembic from 0.9 to 0.10.1? (y, n, q) [y]: q\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_interactive_choice_quit').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_interactive_choice_invalid(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '--interactive']

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='z\nn\ny\nq\n')
            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: z\nPlease enter either y, n, q.\nUpdate flask from 0.9 to 0.10.1? (y, n, q) [y]: n\nUpdate Alembic from 0.9 to 0.10.1? (y, n, q) [y]: y\nUpdated Alembic: 0.9 -> 0.10.1\nUpdate sqlalchemy from 0.9 to 0.10.1? (y, n, q) [y]: q\nAll requirements up-to-date.\n"
            self.assertEqual(u(result.output), u(expected_output))
            self.assertEqual(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_interactive_choice_invalid').read()
            self.assertEqual(open(requirements).read(), expected_requirements)

    def test_updates_package_without_command_line(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = {
            'input_file': requirements,
        }
        expected_result = {
            'current': Version('0.9'),
            'updated': True,
            'latest': Version('0.10.1'),
            'message': 'Updated flask: 0.9 -> 0.10.1',
            'package': 'flask',
        }

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = update_requirements(**args)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEqual(open(requirements).read(), expected_requirements)
            self.assertEqual(result['flask'][0], expected_result)

    def test_updates_package_in_nested_requirements_without_command_line(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements-with-nested-reqfile.txt')
        requirements_nested = os.path.join(tempdir, 'requirements-nested.txt')
        shutil.copy('tests/samples/requirements-with-nested-reqfile.txt', requirements)
        shutil.copy('tests/samples/requirements-nested.txt', requirements_nested)
        args = {
            'input_file': requirements,
        }
        expected_result = {
            'current': Version('0.9'),
            'updated': True,
            'latest': Version('0.10.1'),
            'message': 'Updated readtime: 0.9 -> 0.10.1',
            'package': 'readtime',
        }
        expected_requirements = open('tests/samples/results/test_updates_package_in_nested_requirements').read()
        expected_requirements_nested = open('tests/samples/results/test_updates_package_in_nested_requirements_nested').read()

        with patch('pip._internal.index.package_finder.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'readtime'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = update_requirements(**args)
            self.assertEqual(open(requirements).read(), expected_requirements)
            self.assertEqual(open(requirements_nested).read(), expected_requirements_nested)
            self.assertEqual(result['readtime'][0], expected_result)
