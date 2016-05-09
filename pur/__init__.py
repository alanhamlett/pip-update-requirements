# -*- coding: utf-8 -*-
"""
    pip-update-requirements
    ~~~~~~~~~~~~~~~~~~~~~~~
    Update packages in a requirements.txt file to latest versions.
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


__title__ = 'pur'
__description__ = 'Update packages in a requirements.txt file to latest versions.'
__url__ = 'https://github.com/alanhamlett/pip-update-requirements'
__version_info__ = ('2', '0', '0')
__version__ = '.'.join(__version_info__)
__author__ = 'Alan Hamlett'
__author_email__ = 'alan.hamlett@gmail.com'
__license__ = 'BSD'
__copyright__ = 'Copyright 2016 Alan Hamlett'


import click
try:
    from StringIO import StringIO
except ImportError:  # pragma: nocover
    from io import StringIO

from pip.download import PipSession, get_file_content
from pip.index import PackageFinder
from pip.models.index import PyPI
from pip.req import req_file
from pip.req.req_install import Version


@click.command()
@click.argument('requirements_file', type=click.Path())
@click.option('--output', type=click.Path(),
              help='Output updated packages to this file; Defaults to ' +
              'writing back to REQUIREMENTS_FILE.')
@click.version_option(__version__)
def pur(requirements_file, **options):
    """Command line entry point."""

    if not options.get('output'):
        options['output'] = requirements_file

    # prevent processing nested requirements files
    patch_pip()

    requirements = get_requirements_and_latest(requirements_file)

    buf = StringIO()
    for line, req, spec_ver, latest_ver in requirements:
        if req:
            if spec_ver < latest_ver:
                new_line = line.replace(str(spec_ver), str(latest_ver), 1)
                buf.write(new_line)
                click.echo('Updated {package}: {old} -> {new}'.format(
                    package=req.name,
                    old=spec_ver,
                    new=latest_ver,
                ))
            else:
                buf.write(line)
        else:
            buf.write(line)
        buf.write("\n")

    with open(options['output'], 'w') as output:
        output.write(buf.getvalue())

    buf.close()

    click.echo('All requirements up-to-date.')
    return 0


def get_requirements_and_latest(filename):
    """Parse a requirements file and get latest version for each requirement.

    Yields a tuple of (original line, InstallRequirement instance,
    spec_version, latest_version).

    :param filename:  Path to a requirements.txt file.
    """
    session = PipSession()

    url, content = get_file_content(filename, session=session)
    lines = req_file.join_lines(enumerate(content.splitlines(), start=1))
    for line_number, line in lines:
        stripped_line = req_file.COMMENT_RE.sub('', line)
        stripped_line = stripped_line.strip()
        if stripped_line:
            reqs = list(req_file.process_line(stripped_line, filename,
                                              line_number, session=session))
            if len(reqs) > 0:
                req = reqs[0]
                try:
                    spec_ver = Version(req.req.specs[0][1])
                except IndexError:
                    spec_ver = None
                if spec_ver:
                    latest_ver = latest_version(req, session)
                    yield (line, req, spec_ver, latest_ver)
                else:
                    yield (line, None, None, None)
            else:
                yield (line, None, None, None)
        else:
            yield (line, None, None, None)


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


if __name__ == '__main__':
    pur()
