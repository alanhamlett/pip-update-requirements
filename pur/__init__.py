# -*- coding: utf-8 -*-
"""
    pur
    ~~~
    Update packages in a requirements.txt file to latest versions.
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import click
import os
import sys
from click import echo as _echo
from collections import defaultdict
try:
    from StringIO import StringIO
except ImportError:  # pragma: nocover
    from io import StringIO

# add local packages folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'packages'))
try:
    from pip._internal.download import PipSession
except (TypeError, ImportError):  # pragma: nocover
    # on Windows, non-ASCII characters in import path can be fixed using
    # the script path from sys.argv[0].
    # More info at https://github.com/wakatime/wakatime/issues/32
    sys.path.insert(0,
                    os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                 'packages'))
    from pip._internal.download import PipSession

from pip._internal.download import get_file_content
from pip._internal.exceptions import InstallationError
from pip._internal.index import PackageFinder
from pip._internal.models.index import PyPI
from pip._internal.req import req_file

from .__about__ import __version__
from .exceptions import StopUpdating
from .utils import (ExitCodeException, can_check_version, should_update,
                    old_version, requirements_line, update_requirement_line,
                    yield_lines, parse_requirement_line, current_version,
                    latest_version, format_list_arg)


PUR_GLOBAL_UPDATED = 0


@click.command()
@click.option('-r', '--requirement', type=click.Path(),
              help='The requirements.txt file to update; Defaults to using ' +
              'requirements.txt from the current directory if it exist.')
@click.option('-o', '--output', type=click.Path(),
              help='Output updated packages to this file; Defaults to ' +
              'overwriting the input requirements.txt file.')
@click.option('-i', '--interactive', is_flag=True, default=False,
              help='Interactively prompts before updating each package.')
@click.option('-f', '--force', is_flag=True, default=False,
              help='Force updating packages even when a package has no ' +
              'version specified in the input requirements.txt file.')
@click.option('-d', '--dry-run', is_flag=True, default=False,
              help='Output changes to STDOUT instead of overwriting the ' +
              'requirements.txt file.')
@click.option('-n', '--no-recursive', is_flag=True, default=False,
              help='Prevents updating nested requirements files.')
@click.option('-s', '--skip', type=click.STRING, help='Comma separated list ' +
              'of packages to skip updating.')
@click.option('--index-url', type=click.STRING, multiple=True, help='Base ' +
              'URL of the Python Package Index. Can be provided multiple ' +
              'times for extra index urls.')
@click.option('--only', type=click.STRING, help='Comma separated list of ' +
              'packages. Only these packages will be updated.')
@click.option('-m', '--minor', type=click.STRING, help='Comma separated ' +
              'list of packages to only update minor versions, never major. ' +
              'Use "*" to limit every package to minor version updates.')
@click.option('-p', '--patch', type=click.STRING, help='Comma separated ' +
              'list of packages to only update patch versions, never major '+
              'or minor. Use "*" to limit every package to patch version ' +
              'updates.')
@click.option('--pre', type=click.STRING, help='Comma separated ' +
              'list of packages to allow updating to pre-release versions. ' +
              'Use "*" to allow all packages to be updated to pre-release ' +
              'versions. By default packages are only updated to stable ' +
              'versions.')
@click.option('-z', '--nonzero-exit-code', is_flag=True, default=False,
              help='Exit with status l0 when all packages up-to-date, 11 ' +
              'when some packages were updated. Defaults to exit status zero ' +
              'on success and non-zero on failure.')
@click.version_option(__version__)
def pur(**options):
    """Command line entry point."""

    if not options['requirement']:
        options['requirement'] = 'requirements.txt'

    format_list_arg(options, 'skip')
    format_list_arg(options, 'only')
    format_list_arg(options, 'minor')
    format_list_arg(options, 'patch')
    format_list_arg(options, 'pre')

    options['echo'] = True

    global PUR_GLOBAL_UPDATED
    PUR_GLOBAL_UPDATED = 0

    update_requirements(
        input_file=options['requirement'],
        output_file=options['output'],
        force=options['force'],
        interactive=options['interactive'],
        skip=options['skip'],
        only=options['only'],
        minor=options['minor'],
        patch=options['patch'],
        pre=options['pre'],
        dry_run=options['dry_run'],
        no_recursive=options['no_recursive'],
        echo=options['echo'],
        index_urls=options['index_url'],
    )

    if not options['dry_run']:
        _echo('All requirements up-to-date.')

    if options['nonzero_exit_code']:
        if PUR_GLOBAL_UPDATED > 0:
            raise ExitCodeException(11)
        raise ExitCodeException(10)


def update_requirements(input_file=None, output_file=None, force=False,
                        interactive=False, skip=[], only=[], minor=[],
                        patch=[], pre=[], dry_run=False,
                        no_recursive=False, echo=False, index_urls=[]):
    """Update a requirements file.

    Returns a dict of package update info.

    :param input_file:   Path to a requirements.txt file.
    :param output_file:  Path to the output requirements.txt file.
    :param force:        Force updating packages even when a package has no
                         version specified in the input requirements.txt file.
    :param interactive:  Interactively prompts before updating each package.
    :param dry_run:      Output changes to STDOUT instead of overwriting the
                         requirements.txt file.
    :param no_recursive: Prevents updating nested requirements files.
    :param skip:         List of packages to skip updating.
    :param only:         List of packages to update, skipping all others.
    :param minor:        List of packages to only update minor and patch
                         versions, never major.
    :param patch:        List of packages to only update patch versions, never
                         minor or major.
    :param pre:          List of packages to allow updating to pre-release
                         versions.
    :param index_urls:   List of PyPI index urls.
    """

    obuffer = StringIO()
    updates = defaultdict(list)

    # patch pip for handling nested requirements files
    _patch_pip(obuffer, updates, input_file=input_file, output_file=output_file,
              force=force, interactive=interactive, skip=skip, only=only,
              minor=minor, patch=patch, pre=pre, dry_run=dry_run,
              no_recursive=no_recursive, echo=echo, index_urls=index_urls)

    _internal_update_requirements(obuffer, updates,
                                  input_file=input_file,
                                  output_file=output_file,
                                  force=force,
                                  skip=skip,
                                  only=only,
                                  minor=minor,
                                  patch=patch,
                                  pre=pre,
                                  interactive=interactive,
                                  dry_run=dry_run,
                                  no_recursive=no_recursive,
                                  echo=echo,
                                  index_urls=index_urls,
                                  )

    if not dry_run:
        if not output_file:
            output_file = input_file
        with open(output_file, 'w') as output:
            output.write(obuffer.getvalue())

    obuffer.close()

    return updates


def _internal_update_requirements(obuffer, updates, input_file=None,
                                  output_file=None, force=False,
                                  interactive=False, skip=[], only=[],
                                  minor=[], patch=[], pre=[],
                                  dry_run=False, no_recursive=False,
                                  index_urls=[], echo=False):
    global PUR_GLOBAL_UPDATED

    updated = 0

    try:
        requirements = _get_requirements_and_latest(input_file, force=force,
                                                    minor=minor, patch=patch,
                                                    pre=pre,
                                                    index_urls=index_urls)

        stop = False
        for line, req, spec_ver, latest_ver in requirements:

            if not stop and can_check_version(req, skip, only):

                try:
                    if should_update(req, spec_ver, latest_ver, force=force,
                                     interactive=interactive):

                        if not spec_ver[0]:
                            new_line = '{0}=={1}'.format(line, latest_ver)
                        else:
                            new_line = update_requirement_line(req, line,
                                                               spec_ver,
                                                               latest_ver)
                        obuffer.write(new_line)

                        if new_line != line:
                            msg = 'Updated {package}: {old} -> {new}'.format(
                                package=req.name,
                                old=old_version(spec_ver),
                                new=latest_ver,
                            )
                            updated += 1
                            was_updated = True
                        else:
                            msg = 'New version for {package} found ({new}), ' \
                                  'but current spec prohibits updating: ' \
                                  '{line}'.format(package=req.name,
                                                  new=latest_ver,
                                                  line=line)
                            was_updated = False

                        updates[req.name].append({
                            'package': req.name,
                            'current': old_version(spec_ver),
                            'latest': latest_ver,
                            'updated': was_updated,
                            'message': msg,
                        })
                        if echo and not dry_run:
                            _echo(msg)

                    else:
                        obuffer.write(line)
                except StopUpdating:
                    stop = True
                    obuffer.write(line)

            elif not output_file or not requirements_line(line, req):
                obuffer.write(line)

            if not output_file or not requirements_line(line, req):
                obuffer.write('\n')

    except InstallationError as e:
        raise click.ClickException(str(e))

    if dry_run and echo:
        _echo('==> ' + (output_file or input_file) + ' <==')
        _echo(obuffer.getvalue())

    PUR_GLOBAL_UPDATED += updated


def _patch_pip(obuffer, updates, **options):
    """Patch pip to also update nested requirements files.

    :param obuffer:  Output buffer for new requirements file.
    :param updates:  Dict for saving information about updated packages.
    :param options:  Dict containing original command line arguments.
    """

    seen = []

    def patched_parse_requirements(*args, **kwargs):
        if not options['no_recursive']:
            filename = args[0]
            if filename not in seen:
                if os.path.isfile(filename):
                    seen.append(filename)
                    buf = StringIO()
                    _internal_update_requirements(
                        buf, updates,
                        input_file=filename,
                        output_file=options['output_file'],
                        force=options['force'],
                        interactive=options['interactive'],
                        skip=options['skip'],
                        only=options['only'],
                        minor=options['minor'],
                        patch=options['patch'],
                        pre=options['pre'],
                        dry_run=options['dry_run'],
                        no_recursive=options['no_recursive'],
                        echo=options['echo'],
                        index_urls=options['index_urls']
                    )
                    if not options['dry_run']:
                        if options['output_file']:
                            obuffer.write(buf.getvalue())
                        else:
                            with open(filename, 'w') as output:
                                output.write(buf.getvalue())
                    buf.close()
        return []
    req_file.parse_requirements = patched_parse_requirements


def _get_requirements_and_latest(
        filename,
        force=False,
        minor=[],
        patch=[],
        pre=[],
        index_urls=[]):
    """Parse a requirements file and get latest version for each requirement.

    Yields a tuple of (original line, InstallRequirement instance,
    spec_versions, latest_version).

    :param filename:   Path to a requirements.txt file.
    :param force:      Force getting latest version even for packages without
                       a version specified.
    :param minor:      List of packages to only update minor and patch versions,
                       never major.
    :param patch:      List of packages to only update patch versions, never
                       minor or major.
    :param pre:        List of packages to allow updating to pre-release
                       versions.
    :param index_urls: List of base URLs of the Python Package Index.
    """
    session = PipSession()
    finder = PackageFinder(
        session=session,
        find_links=[],
        index_urls=index_urls or [PyPI.simple_url],
    )

    _, content = get_file_content(filename, session=session)
    for line_number, line, orig_line in yield_lines(content):
        line = req_file.COMMENT_RE.sub('', line)
        line = line.strip()
        req = parse_requirement_line(line, filename, line_number, session, finder)
        if req is None or req.name is None or req_file.SCHEME_RE.match(req.name):
            yield (orig_line, None, None, None)
            continue
        spec_ver = current_version(req)
        if spec_ver or force:
            latest_ver = latest_version(req, spec_ver, session, finder,
                                        minor=minor, patch=patch, pre=pre)
            yield (orig_line, req, spec_ver, latest_ver)
