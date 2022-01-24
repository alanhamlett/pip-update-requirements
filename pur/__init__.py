# -*- coding: utf-8 -*-
"""
    pur
    ~~~
    Update packages in a requirements.txt file to latest versions.
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import os
import sys
from collections import defaultdict

import click
from click import echo as _echo

try:
    from StringIO import StringIO
except ImportError:  # pragma: no cover
    from io import StringIO

# add local packages folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'packages'))
try:
    from pip._internal.network.session import PipSession
except (TypeError, ImportError):  # pragma: no cover
    # on Windows, non-ASCII characters in import path can be fixed using
    # the script path from sys.argv[0].
    # More info at https://github.com/wakatime/wakatime/issues/32
    sys.path.insert(0,
                    os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                 'packages'))
    from pip._internal.network.session import PipSession

from pip._internal.exceptions import InstallationError
from pip._internal.models.index import PyPI
from pip._internal.req.constructors import install_req_from_parsed_requirement
from pip._internal.req.req_file import (COMMENT_RE, SCHEME_RE,
                                        OptionParsingError, ParsedLine,
                                        RequirementsFileParser,
                                        get_file_content, get_line_parser,
                                        handle_line)

from .__about__ import __version__
from .exceptions import StopUpdating
from .utils import (ExitCodeException, build_package_finder, can_check_version,
                    current_version, format_list_arg, join_lines,
                    latest_version, old_version, requirements_line,
                    should_update, update_requirement_line)


__all__ = ["update_requirements"]


PUR_GLOBAL_UPDATED = 0


@click.command()
@click.option('-r', '--requirement', type=click.Path(),
              help='The requirements.txt file to update; Defaults to using ' +
              'requirements.txt from the current directory if it exist.')
@click.option('-o', '--output', type=click.Path(),
              help='Output updated packages to this file; Defaults to ' +
              'overwriting the input requirements.txt file.')
@click.option('--interactive', is_flag=True, default=False,
              help='Interactively prompts before updating each package.')
@click.option('-f', '--force', is_flag=True, default=False,
              help='Force updating packages even when a package has no ' +
              'version specified in the input requirements.txt file.')
@click.option('-d', '--dry-run', is_flag=True, default=False,
              help='Output changes to STDOUT instead of overwriting the ' +
              'requirements.txt file.')
@click.option('-n', '--no-recursive', is_flag=True, default=False,
              help='Prevents updating nested requirements files.')
@click.option('--skip', type=click.STRING, help='Comma separated list ' +
              'of packages to skip updating.')
@click.option('--index-url', type=click.STRING, multiple=True, help='Base ' +
              'URL of the Python Package Index. Can be provided multiple ' +
              'times for extra index urls.')
@click.option('--cert', type=click.Path(), help='Path to PEM-encoded CA ' +
              'certificate bundle. If provided, overrides the default.')
@click.option('--no-ssl-verify', is_flag=True, default=False,
              help='Disable verifying the server\'s TLS certificate.')
@click.option('--only', type=click.STRING, help='Comma separated list of ' +
              'packages. Only these packages will be updated.')
@click.option('--minor', type=click.STRING, help='Comma separated ' +
              'list of packages to only update minor versions, never major. ' +
              'Use "*" to limit every package to minor version updates.')
@click.option('--patch', type=click.STRING, help='Comma separated ' +
              'list of packages to only update patch versions, never major '+
              'or minor. Use "*" to limit every package to patch version ' +
              'updates.')
@click.option('--pre', type=click.STRING, help='Comma separated ' +
              'list of packages to allow updating to pre-release versions. ' +
              'Use "*" to allow all packages to be updated to pre-release ' +
              'versions. By default packages are only updated to stable ' +
              'versions.')
@click.option('-z', '--nonzero-exit-code', is_flag=True, default=False,
              help='Exit with status 10 when all packages up-to-date, 11 ' +
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
        cert=options['cert'],
        no_ssl_verify=options['no_ssl_verify'],
    )

    if not options['dry_run']:
        _echo('All requirements up-to-date.')

    if options['nonzero_exit_code']:
        if PUR_GLOBAL_UPDATED > 0:
            raise ExitCodeException(11)
        raise ExitCodeException(10)


def update_requirements(input_file=None, output_file=None, force=False,
                        interactive=False, skip=[], only=[], dry_run=False,
                        minor=[], patch=[], pre=[], no_recursive=False,
                        echo=False, index_urls=[], cert=None,
                        no_ssl_verify=False):
    """Update a requirements file.
    Returns a dict of package update info.
    :param input_file:    Path to a requirements.txt file.
    :param output_file:   Path to the output requirements.txt file.
    :param force:         Force updating packages even when a package has no
                          version specified in the input requirements.txt file.
    :param interactive:   Interactively prompts before updating each package.
    :param dry_run:       Output changes to STDOUT instead of overwriting the
                          requirements.txt file.
    :param no_recursive:  Prevents updating nested requirements files.
    :param skip:          List of packages to skip updating.
    :param only:          List of packages to update, skipping all others.
    :param minor:         List of packages to only update minor and patch
                          versions, never major.
    :param patch:         List of packages to only update patch versions, never
                          minor or major.
    :param pre:           List of packages to allow updating to pre-release
                          versions.
    :param index_urls:    List of PyPI index urls.
    :param cert:          Path to PEM-encoded CA certificate bundle. If
                          provided, overrides the default.
    :param no_ssl_verify: Disable verifying the server's TLS certificate.
    """

    obuffer = StringIO()
    updates = defaultdict(list)

    _update_requirements(
        obuffer, updates,
        input_file=input_file,
        output_buffer=obuffer if output_file else None,
        force=force,
        interactive=interactive,
        skip=skip,
        only=only,
        minor=minor,
        patch=patch,
        pre=pre,
        dry_run=dry_run,
        no_recursive=no_recursive,
        echo=echo,
        index_urls=index_urls,
        cert=cert,
        no_ssl_verify=no_ssl_verify,
    )

    if not dry_run:
        if not output_file:
            output_file = input_file
        with open(output_file, 'w') as output:
            output.write(obuffer.getvalue())

    obuffer.close()
    return updates


def _update_requirements(obuffer, updates, input_file=None,
                         output_buffer=None,
                         output_file=None,
                         force=False,
                         interactive=False, skip=[], only=[],
                         minor=[], patch=[], pre=[],
                         no_recursive=False,
                         dry_run=False, echo=False,
                         index_urls=[], cert=None,
                         no_ssl_verify=False):
    global PUR_GLOBAL_UPDATED

    updated = 0

    try:
        requirements = _get_requirements_and_latest(
            input_file,
            updates=updates,
            force=force,
            interactive=interactive,
            minor=minor,
            patch=patch,
            pre=pre,
            index_urls=index_urls,
            cert=cert,
            no_ssl_verify=no_ssl_verify,
            no_recursive=no_recursive,
            output_buffer=output_buffer,
            echo=echo,
            dry_run=dry_run,
        )

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

            elif not output_buffer or not requirements_line(line, req):
                obuffer.write(line)

            if not output_buffer or not requirements_line(line, req):
                obuffer.write('\n')

    except InstallationError as e:
        raise click.ClickException(str(e))

    if dry_run and echo:
        _echo('==> ' + (output_file or input_file) + ' <==')
        _echo(obuffer.getvalue())

    PUR_GLOBAL_UPDATED += updated


def _get_requirements_and_latest(filename, updates=[], force=False,
                                 interactive=False, minor=[], patch=[], pre=[],
                                 index_urls=[], cert=None, no_ssl_verify=False,
                                 no_recursive=False, output_file=None,
                                 output_buffer=None, echo=False,
                                 dry_run=False):
    """Parse a requirements file and get latest version for each requirement.

    Yields a tuple of (original line, InstallRequirement instance,
    spec_versions, latest_version).
    """

    index_urls = index_urls or [PyPI.simple_url]

    session = PipSession(
        index_urls=index_urls,
    )
    if cert:
        session.verify = cert
    if no_ssl_verify:
        session.verify = False
    session.auth.prompting = interactive

    finder = build_package_finder(
        session=session,
        index_urls=index_urls,
    )
    if pre:
        finder.set_allow_all_prereleases()

    requirements = _parse_requirements(
        filename, finder, session,
        updates=updates,
        force=force,
        interactive=interactive,
        minor=minor,
        patch=patch,
        pre=pre,
        index_urls=index_urls,
        cert=cert,
        no_ssl_verify=no_ssl_verify,
        no_recursive=no_recursive,
        output_file=output_file,
        output_buffer=output_buffer,
        echo=echo,
        dry_run=dry_run,
    )

    for parsed_req, orig_line in requirements:
        if parsed_req is None:
            yield (orig_line, None, None, None)
            continue

        install_req = install_req_from_parsed_requirement(
            parsed_req,
            user_supplied=True,
        )

        if install_req.name is None or SCHEME_RE.match(install_req.name):
            yield (orig_line, None, None, None)
            continue
        spec_ver = current_version(install_req)
        if spec_ver or force:
            latest_ver = latest_version(install_req, spec_ver, finder, minor=minor, patch=patch, pre=pre)
            yield (orig_line, install_req, spec_ver, latest_ver)


def _parse_requirements(filename, finder, session, updates=None, **options):
    line_parser = get_line_parser(finder)
    parser = PatchedRequirementsFileParser(session, line_parser)
    parser.pur_updates = updates
    parser.pur_options = options

    constraint = False
    for parsed_line, orig_line in parser.parse(filename, constraint):
        if parsed_line is None:
            yield None, orig_line
            continue
        parsed_req = handle_line(
            parsed_line,
            finder=finder,
            session=session
        )
        yield parsed_req, orig_line


class PatchedRequirementsFileParser(RequirementsFileParser):

    def _parse_and_recurse(self, filename, constraint):
        for line, orig_line in self._parse_file(filename, constraint):
            if (
                line is not None and
                not line.is_requirement and
                (line.opts.requirements or line.opts.constraints)
            ):
                # parse a nested requirements file
                if line.opts.requirements:
                    req_path = line.opts.requirements[0]
                else:
                    req_path = line.opts.constraints[0]

                if self.pur_options['no_recursive'] or SCHEME_RE.search(req_path):
                    yield None, orig_line
                    continue

                req_path = os.path.join(
                    os.path.dirname(filename), req_path,
                )

                buf = StringIO()

                _update_requirements(
                    buf, self.pur_updates,
                    input_file=req_path,
                    **self.pur_options,
                )

                if not self.pur_options['dry_run']:
                    if self.pur_options['output_buffer']:
                        self.pur_options['output_buffer'].write(buf.getvalue())
                    else:
                        with open(req_path, 'w') as output:
                            output.write(buf.getvalue())

                buf.close()

                if not self.pur_options['output_file']:
                    yield None, orig_line
            else:
                yield line, orig_line

    def _parse_file(self, filename, constraint):
        _, content = get_file_content(filename, self._session)

        lines_enum = enumerate(content.splitlines(), start=1)
        lines_enum = join_lines(lines_enum)

        for line_number, line, orig_line in lines_enum:
            line = COMMENT_RE.sub('', line)
            try:
                args_str, opts = self._line_parser(line)
            except OptionParsingError:
                yield None, orig_line
                continue

            yield ParsedLine(
                filename,
                line_number,
                args_str,
                opts,
                constraint,
            ), orig_line
