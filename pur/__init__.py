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
import re
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
                if should_update(req, spec_ver, latest_ver,
                                 force=options['force']):
                    if not spec_ver[0]:
                        new_line = '{0}=={1}'.format(line, latest_ver)
                    else:
                        new_line = update_requirement(req, line, spec_ver,
                                                      latest_ver)
                    buf.write(new_line)
                    click.echo('Updated {package}: {old} -> {new}'.format(
                        package=req.name,
                        old=spec_ver[1] if spec_ver[0] else 'Unknown',
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


def patch_pip():
    """Patch pip to prevent parsing nested requirements files."""

    old_fn = req_file.parse_requirements
    def patched_parse_requirements(*args, **kwargs):
        return []
    req_file.parse_requirements = patched_parse_requirements
    return old_fn


def get_requirements_and_latest(filename, force=False):
    """Parse a requirements file and get latest version for each requirement.

    Yields a tuple of (original line, InstallRequirement instance,
    spec_versions, latest_version).

    :param filename:  Path to a requirements.txt file.
    :param force:     Force getting latest version even for packages without
                      a version specified.
    """
    session = PipSession()

    url, content = get_file_content(filename, session=session)
    for line_number, line, orig_line in yield_lines(content):
        line = req_file.COMMENT_RE.sub('', line)
        line = line.strip()
        req = parse_requirement(line, filename, line_number, session)
        spec_ver = current_version(req)
        if spec_ver or force:
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


def current_version(req):
    """Get the current version from an InstallRequirement instance.

    Returns a tuple (found, eq_ver, gt_ver, gte_ver, lt_ver, lte_ver, not_ver).
    The versions in the returned tuple will be either a
    pip.req.req_install.Version instance or None.

    :param req:    Instance of pip.req.req_install.InstallRequirement.
    """

    if not req or not req.req:
        return None

    eq_ver = None
    gt_ver = None
    gte_ver = None
    lt_ver = None
    lte_ver = None
    not_ver = None
    for spec in req.req.specs:
        ver = Version(spec[1])
        if spec[0] == '==':
            eq_ver = ver
        elif spec[0] == '>':
            if not gt_ver or ver > gt_ver:
                gt_ver = ver
        elif spec[0] == '>=':
            if not gte_ver or ver > gte_ver:
                gte_ver = ver
        elif spec[0] == '<':
            if not lt_ver or ver < lt_ver:
                lt_ver = ver
        elif spec[0] == '<=':
            if not lte_ver or ver < lte_ver:
                lte_ver = ver
        elif spec[0] == '!=':
            not_ver = ver

    found = (eq_ver is not None or gt_ver is not None or gte_ver is not None or
             lt_ver is not None or lte_ver is not None or not_ver is not None)

    return found, eq_ver, gt_ver, gte_ver, lt_ver, lte_ver, not_ver


def yield_lines(content):
    """Yields a tuple of each line in a requirements file string.

    The tuple contains (lineno, joined_line, original_line).

    :param content:  Text content of a requirements.txt file.
    """
    lines = content.splitlines()
    for lineno, joined, orig in join_lines(enumerate(lines, start=1)):
        yield lineno, joined, orig


def join_lines(lines_enum):
    """Joins a line ending in '\' with the previous line.

    (except when following comments). The joined line takes on the index of the
    first line.
    """
    COMMENT_RE = re.compile(r'(^|\s)+#.*$')
    primary_line_number = None
    new_line = []
    orig_lines = []
    for line_number, orig_line in lines_enum:
        line = orig_line
        if not line.endswith('\\') or COMMENT_RE.match(line):
            if COMMENT_RE.match(line):
                # this ensures comments are always matched later
                line = ' ' + line
            if new_line:
                new_line.append(line)
                orig_lines.append(orig_line)
                yield (primary_line_number, ''.join(new_line),
                       "\n".join(orig_lines))
                new_line = []
                orig_lines = []
            else:
                yield line_number, line, orig_line
        else:
            if not new_line:
                primary_line_number = line_number
            new_line.append(line.rstrip('\\'))
            orig_lines.append(orig_line)

    # last line contains \
    if new_line:
        yield primary_line_number, ''.join(new_line), "\n".join(orig_lines)


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


def should_update(req, spec_ver, latest_ver, force=False):
    """Returns True if this requirement should be updated, False otherwise.

    :param req:         Instance of pip.req.req_install.InstallRequirement.
    :param spec_ver:    Tuple of current versions from the requirements file.
    :param latest_ver:  Latest version from pypi.
    :param force:       Force getting latest version even for packages without
                        a version specified.
    """

    if latest_ver is None:
        return False

    found = spec_ver[0]
    eq_ver = spec_ver[1]
    lt_ver = spec_ver[4]
    lte_ver = spec_ver[5]
    not_ver = spec_ver[6]

    if not found and (not force or req.link is not None):
        return False

    if eq_ver is not None and latest_ver <= eq_ver:
        return False

    if not_ver is not None and latest_ver == not_ver:
        return False

    if lt_ver is not None and not latest_ver < lt_ver:
        return False

    if lte_ver is not None and not latest_ver <= lte_ver:
        return False

    return True


def update_requirement(req, line, spec_ver, latest_ver):
    """Updates the version of a requirement line.

    Returns a new requirement line with the package version updated.

    :param req:         Instance of pip.req.req_install.InstallRequirement.
    :param line:        The requirement line string.
    :param spec_ver:    Tuple of current versions from the requirements file.
    :param latest_ver:  Latest version from pypi.
    """

    start_of_spec = (line.index(']') + 1 if ']' in line.split('#')[0]
                     else len(req.name))
    package_part = line[:start_of_spec]
    spec_part = line[start_of_spec:]

    pattern = r'(==\s*){0}'.format(re.sub(r'(\W)', r'\\\1', str(spec_ver[1])))
    match = re.search(pattern, spec_part)
    pre_part = match.group(1)
    old = '{0}{1}'.format(pre_part, str(spec_ver[1]))
    new = '{0}{1}'.format(pre_part, str(latest_ver))
    new_line = '{package_part}{spec_part}'.format(
        package_part=package_part,
        spec_part=spec_part.replace(old, new, 1),
    )
    return new_line


class ExitCodeException(click.ClickException):
    def __init__(self, exit_code):
        self.exit_code = exit_code
    def show(self):
        pass
