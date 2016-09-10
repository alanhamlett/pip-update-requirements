# -*- coding: utf-8 -*-


import os
import shutil
import tempfile
from click.testing import CliRunner
from pip.index import InstallationCandidate, Link, PackageFinder

from pur import pur, __version__

from . import utils
from .utils import u


class BaseTestCase(utils.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_help_contents(self):
        args = ['--help']
        result = self.runner.invoke(pur, args)
        self.assertIsNone(result.exception)
        self.assertEquals(result.exit_code, 0)
        self.assertIn('pur', u(result.output))
        self.assertIn('Usage', u(result.output))
        self.assertIn('Options', u(result.output))

    def test_version(self):
        args = ['--version']
        result = self.runner.invoke(pur, args)
        self.assertIsNone(result.exception)
        expected_output = "pur, version {0}\n".format(__version__)
        self.assertEquals(u(result.output), u(expected_output))
        self.assertEquals(result.exit_code, 0)

    def test_updates_package(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_requirements_long_option_accepted(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['--requirement', requirements]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_updates_package_to_output_file(self):
        tempdir = tempfile.mkdtemp()
        output = os.path.join(tempdir, 'output.txt')
        requirements = open('tests/samples/requirements.txt').read()
        args = ['-r', 'tests/samples/requirements.txt', '--output', output]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            self.assertEquals(open('tests/samples/requirements.txt').read(), requirements)

    def test_exit_code_from_no_updates(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-up-to-date.txt', requirements)
        args = ['-r', requirements, '--nonzero-exit-code']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertEqual(result.exception.code, 10)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 10)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_exit_code_from_some_updates(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '--nonzero-exit-code']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertEqual(result.exception.code, 11)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 11)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_skip_package(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '-s', 'flask']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated Alembic: 0.9 -> 0.10.1\nUpdated sqlalchemy: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_skip_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_skip_multiple_packages(self):
        requirements = 'tests/samples/requirements-multiple.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '-s', 'flask, alembic , SQLAlchemy']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open(requirements).read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_no_version_specified(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '-f']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nUpdated flask: Unknown -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_no_version_specified').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_invalid_package(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            mock_find_all_candidates.return_value = []

            result = self.runner.invoke(pur, args)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEquals(result.exit_code, 0)
            self.assertEquals(open(tmpfile).read(), open(requirements).read())

    def test_no_arguments(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = []

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            with self.cd(tempdir):
                result = self.runner.invoke(pur, args)

            self.assertIsNone(result.exception)
            expected_output = "Updated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_no_arguments_and_no_requirements_file(self):
        tempdir = tempfile.mkdtemp()
        args = []

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            with self.cd(tempdir):
                result = self.runner.invoke(pur, args)

            self.assertEqual(result.exception.code, 1)
            expected_output = "Error: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 1)

    def test_updates_package_with_number_in_name(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-version-in-name.txt', requirements)
        args = ['-r', requirements]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'package1'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated package1: 1 -> 2.0\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_version_in_name').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_updates_package_with_extras(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-with-extras.txt', requirements)
        args = ['-r', requirements]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'firstpackage'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated firstpackage1: 1 -> 2.0\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_extras').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_updates_package_with_max_version_spec(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-with-max-version-spec.txt', requirements)
        args = ['-r', requirements]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated afakepackage: 0.9 -> 0.10.1\nUpdated afakepackage: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_max_version_spec').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_max_version_spec_prevents_updating_package(self):
        requirements = 'tests/samples/requirements-with-max-version-spec.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '2.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open(tmpfile).read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_notequal_version_spec_prevents_updating_package(self):
        requirements = 'tests/samples/requirements-with-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '0.9.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open(tmpfile).read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_multiline_spec(self):
        requirements = 'tests/samples/requirements-with-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '1.0'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "Updated afakepackage: 0.9 -> 1.0\nUpdated afakepackage: 0.9 -> 1.0\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_multiline_spec').read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_does_not_update_package_with_multiline_spec(self):
        requirements = 'tests/samples/requirements-with-multiline.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'afakepackage'
            version = '1.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = "All requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open(requirements).read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_updates_package_with_min_version_spec(self):
        requirements = 'tests/samples/requirements-with-min-version-spec.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'django'
            version = '1.8.13'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            expected_output = "Updated django: 1.8.6 -> 1.8.13\nNew version for django found (1.8.13), but current spec prohibits updating: django > 1.8.6, < 1.9\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertIsNone(result.exception)
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package_with_min_version_spec').read()
            self.assertEquals(open(tmpfile).read(), expected_requirements)

    def test_dry_run(self):
        requirements = 'tests/samples/requirements.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile, '-d']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)
            self.assertIsNone(result.exception)
            expected_output = open('tests/samples/results/test_updates_package').read() + "\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            self.assertEquals(open(tmpfile).read(), open(requirements).read())

    def test_updates_from_alt_index_url(self):
        requirements = 'tests/samples/requirements-with-alt-index-url.txt'
        tempdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tempdir, 'requirements.txt')
        shutil.copy(requirements, tmpfile)
        args = ['-r', tmpfile]

        class PackageFinderSpy(PackageFinder):

            _spy = None

            def __init__(self, *args, **kwargs):
                super(PackageFinderSpy, self).__init__(*args, **kwargs)
                PackageFinderSpy._spy = self

        with utils.mock.patch('pur.PackageFinder', wraps=PackageFinderSpy) as mock_finder:
            with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:

                project = 'flask'
                version = '12.1'
                link = Link('')
                candidate = InstallationCandidate(project, version, link)
                mock_find_all_candidates.return_value = [candidate]

                self.runner.invoke(pur, args)

                self.assertTrue(mock_finder.called)

                self.assertEqual(
                    PackageFinderSpy._spy.index_urls,
                    ['http://pypi.example.com', 'https://pypi.example2.com']
                )
                self.assertEqual(
                    PackageFinderSpy._spy.secure_origins,
                    [('*', 'pypi.example.com', '*')]
                )

    def test_interactive_choice_default(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '-i']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args)

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: \nUpdated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_interactive_choice_yes(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '-i']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='y\n')

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: y\nUpdated flask: 0.9 -> 0.10.1\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_updates_package').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_interactive_choice_no(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements.txt', requirements)
        args = ['-r', requirements, '-i']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='n\n')

            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: n\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/requirements.txt').read()
            self.assertEquals(open(requirements).read(), expected_requirements)

    def test_interactive_choice_quit(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        shutil.copy('tests/samples/requirements-multiple.txt', requirements)
        args = ['-r', requirements, '-i']

        with utils.mock.patch('pip.index.PackageFinder.find_all_candidates') as mock_find_all_candidates:
            project = 'flask'
            version = '0.10.1'
            link = Link('')
            candidate = InstallationCandidate(project, version, link)
            mock_find_all_candidates.return_value = [candidate]

            result = self.runner.invoke(pur, args, input='y\nq\n')
            self.assertIsNone(result.exception)
            expected_output = "Update flask from 0.9 to 0.10.1? (y, n, q) [y]: y\nUpdated flask: 0.9 -> 0.10.1\nUpdate Alembic from 0.9 to 0.10.1? (y, n, q) [y]: q\nAll requirements up-to-date.\n"
            self.assertEquals(u(result.output), u(expected_output))
            self.assertEquals(result.exit_code, 0)
            expected_requirements = open('tests/samples/results/test_interactive_choice_quit').read()
            self.assertEquals(open(requirements).read(), expected_requirements)
