# -*- coding: utf-8 -*-
"""
    pip-update-requirements
    ~~~~~~~~~~~~~~~~~~~~~~~
    Update packages in a requirements.txt file to latest versions.
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import click
import os
import sys
try:
    from StringIO import StringIO
except ImportError:  # pragma: nocover
    from io import StringIO

# add local packages folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'packages'))
try:
    from pip.download import PipSession
except (TypeError, ImportError):  # pragma: nocover
    # on Windows, non-ASCII characters in import path can be fixed using
    # the script path from sys.argv[0].
    # More info at https://github.com/wakatime/wakatime/issues/32
    sys.path.insert(0,
                    os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                 'packages'))
    from pip.download import PipSession


from pip.download import get_file_content
from pip.exceptions import InstallationError
from pip.index import PackageFinder
from pip.models.index import PyPI
from pip.req import req_file
from pip.req.req_install import Version

from .__about__ import __version__


@click.command()
@click.option('-r', '--requirement', type=click.Path(),
              help='The requirements.txt file to update; Defaults to using ' +
              'requirements.txt from the current directory if it exist.')
@click.option('-o', '--output', type=click.Path(),
              help='Output updated packages to this file; Defaults to ' +
              'overwriting the input requirements.txt file.')
@click.option('-f', '--force', is_flag=True, default=False,
              help='Force updating packages even when a package has no ' +
              'version specified in the input requirements.txt file.')
@click.option('-z', '--nonzero-exit-code', is_flag=True, default=False,
              help='Exit with status l0 when all packages up-to-date, 11 ' +
              'when some packages were updated. Defaults to exit status zero ' +
              'on success and non-zero on failure.')
@click.option('-s', '--skip', type=click.STRING, help='Comma separated list of ' +
              'packages to skip updating.')
@click.version_option(__version__)
def pur(**options):
    """Command line entry point."""

    if not options['requirement']:
        options['requirement'] = 'requirements.txt'
    if not options['output']:
        options['output'] = options['requirement']
    try:
        options['skip'] = set(x.strip().lower() for x in options['skip'].split(','))
    except AttributeError:
        options['skip'] = set()

    # prevent processing nested requirements files
    patch_pip()

    try:
        requirements = get_requirements_and_latest(options['requirement'],
                                                   force=options['force'])

        buf = StringIO()
        updated = 0
        for line, req, spec_ver, latest_ver in requirements:
            if req and req.name.lower() not in options['skip']:
                if spec_ver and latest_ver and (spec_ver == 'Unknown'
                                                or spec_ver < latest_ver):
                    if spec_ver == 'Unknown':
                        new_line = '{0}=={1}'.format(line, latest_ver)
                    else:
                        new_line = line.replace(str(spec_ver), str(latest_ver), 1)
                    buf.write(new_line)
                    click.echo('Updated {package}: {old} -> {new}'.format(
                        package=req.name,
                        old=spec_ver,
                        new=latest_ver,
                    ))
                    updated += 1
                else:
                    buf.write(line)
            else:
                buf.write(line)
            buf.write("\n")

    except InstallationError as e:
        raise click.ClickException(str(e))

    with open(options['output'], 'w') as output:
        output.write(buf.getvalue())

    buf.close()

    click.echo('All requirements up-to-date.')

    if options['nonzero_exit_code']:
        if updated > 0:
            raise ExitCodeException(11)
        raise ExitCodeException(10)


def get_requirements_and_latest(filename, force=False):
    """Parse a requirements file and get latest version for each requirement.

    Yields a tuple of (original line, InstallRequirement instance,
    spec_version, latest_version).

    :param filename:  Path to a requirements.txt file.
    :param force:     Force getting latest version even for packages without
                      a version specified.
    """
    session = PipSession()

    url, content = get_file_content(filename, session=session)
    for orig_line, line_number, line in yield_lines(content):
        line = req_file.COMMENT_RE.sub('', line)
        line = line.strip()
        req = parse_requirement(line, filename, line_number, session)
        spec_ver = current_version(req, force=force)
        if spec_ver:
            latest_ver = latest_version(req, session)
            yield (orig_line, req, spec_ver, latest_ver)
        else:
            yield (orig_line, None, None, None)


def parse_requirement(line, filename, line_number, session):
    """Parse a requirement line and return an InstallRequirement instance.

    :param line:         One line from a requirements.txt file.
    :param filename:     Path to a requirements.txt file.
    :param line_number:  The integer line number of the current line.
    :param session:      Instance of pip.download.PipSession.
    """

    if not line:
        return None

    reqs = list(req_file.process_line(line, filename,
                                      line_number, session=session))
    return reqs[0] if len(reqs) > 0 else None


def current_version(req, force=False):
    """Get the current version from an InstallRequirement instance.

    :param req:    Instance of pip.req.req_install.InstallRequirement.
    :param force:  Force getting latest version even for packages without
    """

    if not req or not req.req:
        return None

    ver = None
    try:
        ver = Version(req.req.specs[0][1])
    except IndexError:
        pass

    if not ver and force and req.link is None:
        ver = 'Unknown'

    return ver


def yield_lines(content):
    lines = content.splitlines()
    for line_number, line in req_file.join_lines(enumerate(lines)):
        yield (lines[line_number], line_number + 1, line)


def latest_version(req, session, include_prereleases=False):
    """Returns a Version instance with the latest version for the package.

    :param req:                 Instance of
                                pip.req.req_install.InstallRequirement.
    :param session:             Instance of pip.download.PipSession.
    :param include_prereleases: Include prereleased beta versions.
    """
    if not req:  # pragma: nocover
        return None

    index_urls = [PyPI.simple_url]
    finder = PackageFinder(session=session, find_links=[],
                           index_urls=index_urls)

    all_candidates = finder.find_all_candidates(req.name)

    if not include_prereleases:
        all_candidates = [candidate for candidate in all_candidates
                          if not candidate.version.is_prerelease]

    if not all_candidates:
        return None

    best_candidate = max(all_candidates,
                         key=finder._candidate_sort_key)
    remote_version = best_candidate.version
    return remote_version


def patch_pip():
    old_fn = req_file.parse_requirements
    def patched_parse_requirements(*args, **kwargs):
        return []
    req_file.parse_requirements = patched_parse_requirements
    return old_fn


class ExitCodeException(click.ClickException):
    def __init__(self, exit_code):
        self.exit_code = exit_code
    def show(self):
        pass
