# -*- coding: utf-8 -*-
"""
    pur.utils
    ~~~~~~~~~
    Update packages in a requirements.txt file to latest versions.
    :copyright: (c) 2016 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import re

import click
from click import echo as _echo
from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.search_scope import SearchScope
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.req.req_file import COMMENT_RE
from pip._vendor.packaging.version import InvalidVersion, Version, parse

from .exceptions import StopUpdating


def build_package_finder(session=None, index_urls=[]):
    search_scope = SearchScope.create(
        find_links=[],
        index_urls=index_urls,
    )
    link_collector = LinkCollector(
        session=session,
        search_scope=search_scope,
    )
    selection_prefs = SelectionPreferences(
        allow_yanked=False,
        allow_all_prereleases=True,
        # ignore_requires_python=True,
    )
    return PackageFinder.create(
        link_collector=link_collector,
        selection_prefs=selection_prefs,
    )


def join_lines(lines_enum):
    """Joins a line ending in '\' with the previous line (except when following
    comments).  The joined line takes on the index of the first line.
    """
    primary_line_number = None
    new_line = []
    orig_lines = []
    for line_number, line in lines_enum:
        original_line = line
        if not line.endswith('\\') or COMMENT_RE.match(line):
            if COMMENT_RE.match(line):
                # this ensures comments are always matched later
                line = ' ' + line
            if new_line:
                new_line.append(line)
                orig_lines.append(original_line)
                assert primary_line_number is not None
                yield primary_line_number, ''.join(new_line), '\n'.join(orig_lines)
                new_line = []
                orig_lines = []
            else:
                yield line_number, line, original_line
        else:
            if not new_line:
                primary_line_number = line_number
            new_line.append(line.strip('\\'))
            orig_lines.append(original_line)

    # last line contains \
    if new_line:
        assert primary_line_number is not None
        yield primary_line_number, ''.join(new_line), '\n'.join(orig_lines)

    # TODO: handle space after '\'.


def current_version(req):
    """Get the current version from an InstallRequirement instance.

    Returns a tuple (ver, eq_ver, gt_ver, gte_ver, lt_ver, lte_ver, not_ver).
    The versions in the returned tuple will be either a
    pip.req.req_install.Version instance or None.

    :param req:    Instance of pip.req.req_install.InstallRequirement.
    """

    eq_ver = None
    gt_ver = None
    gte_ver = None
    lt_ver = None
    lte_ver = None
    not_ver = None
    for spec in req.req.specifier:
        operator, version = spec._spec
        try:
            ver = Version(version)  # TODO: use parse to support LegacyVersion
        except InvalidVersion:
            continue
        if operator == '==':
            eq_ver = ver
        elif operator == '>':
            if not gt_ver or ver > gt_ver:
                gt_ver = ver
        elif operator == '>=':
            if not gte_ver or ver > gte_ver:
                gte_ver = ver
        elif operator == '<':
            if not lt_ver or ver < lt_ver:
                lt_ver = ver
        elif operator == '<=':
            if not lte_ver or ver < lte_ver:
                lte_ver = ver
        elif operator == '!=':
            not_ver = ver

    ver = eq_ver or gt_ver or gte_ver or lt_ver or lte_ver or not_ver
    return ver, eq_ver, gt_ver, gte_ver, lt_ver, lte_ver, not_ver


def old_version(spec_ver):
    """Get the old version that was updated.

    :param spec_ver:  A tuple from current_version.
    """

    eq_ver = spec_ver[1]
    gte_ver = spec_ver[3]

    if eq_ver is not None:
        return eq_ver

    if gte_ver is not None:
        return gte_ver

    return 'Unknown'


def latest_version(req, spec_ver, finder, minor=[], patch=[], pre=[]):
    """Returns a Version instance with the latest version for the package.

    :param req:      Instance of pip.req.req_install.InstallRequirement.
    :param spec_ver: Tuple of current versions from the requirements file.
    :param finder:   Instance of pip.download.PackageFinder.
    :param minor:    List of packages to only update minor and patch versions,
                     never major.
    :param patch:    List of packages to only update patch versions, never
                     minor or major.
    :param pre:      List of packages to allow updating to pre-release
                     versions.
    """
    if not req:  # pragma: no cover
        return None

    all_candidates = finder.find_all_candidates(req.name)

    if req.name.lower() in patch or '*' in patch:
        all_candidates = [c for c in all_candidates
                          if less_than(c.version, spec_ver[0], patch=True)]
    elif req.name.lower() in minor or '*' in minor:
        all_candidates = [c for c in all_candidates
                          if less_than(c.version, spec_ver[0])]

    if req.name.lower() not in pre and '*' not in pre:
        all_candidates = [candidate for candidate in all_candidates
                          if not candidate.version.is_prerelease]

    if not all_candidates:
        return None

    candidate_evaluator = finder.make_candidate_evaluator(
        project_name=req.name,
    )
    applicable_candidates = candidate_evaluator.get_applicable_candidates(all_candidates)
    best_candidate = candidate_evaluator.sort_best_candidate(applicable_candidates)
    if not best_candidate:
        return None

    return best_candidate.version


def can_check_version(req, spec_ver, skip, skip_gt, only):
    if not req:
        return False

    if skip_gt and (spec_ver[2] or spec_ver[3]):
        return False

    if req.name.lower() in skip:
        return False

    return len(only) == 0 or req.name.lower() in only


def should_update(req, spec_ver, latest_ver, force=False, interactive=False):
    """Returns True if this requirement should be updated, False otherwise.

    :param req:          Instance of pip.req.req_install.InstallRequirement.
    :param spec_ver:     Tuple of current versions from the requirements file.
    :param latest_ver:   Latest version from pypi.
    :param force:        Force getting latest version even for packages without
                         a version specified.
    :param interactive:  Interactively prompts before updating each package.
    """

    if latest_ver is None:
        return False

    ver = spec_ver[0]
    eq_ver = spec_ver[1]
    gt_ver = spec_ver[2]
    gte_ver = spec_ver[3]
    lt_ver = spec_ver[4]
    lte_ver = spec_ver[5]
    not_ver = spec_ver[6]

    if not ver and (not force or req.link is not None):
        return False

    if eq_ver is not None and latest_ver <= eq_ver:
        return False

    if gt_ver is not None and latest_ver <= gt_ver:
        return False

    if gte_ver is not None and latest_ver <= gte_ver:
        return False

    if not_ver is not None and latest_ver == not_ver:
        return False

    if lt_ver is not None and not latest_ver < lt_ver:
        return False

    if lte_ver is not None and not latest_ver <= lte_ver:
        return False

    return not interactive or ask_to_update(req, spec_ver, latest_ver)


def ask_to_update(req, spec_ver, latest_ver):
    """Prompts to update the current package.

    Returns True if should update, False if should skip, and raises
    SaveAndStopUpdating or StopUpdating exceptions if the user selected quit.

    :param req:         Instance of pip.req.req_install.InstallRequirement.
    :param spec_ver:    Tuple of current versions from the requirements file.
    :param latest_ver:  Latest version from pypi.
    """

    choices = ['y', 'n', 'q']

    msg = 'Update {package} from {old} to {new}? ({choices})'.format(
        package=req.name,
        old=old_version(spec_ver),
        new=latest_ver,
        choices=', '.join(choices),
    )
    while True:
        value = click.prompt(msg, default='y')
        value = value.lower()
        if value in choices:
            break
        _echo('Please enter either {0}.'.format(', '.join(choices)))

    if value == 'y':
        return True
    if value == 'n':
        return False

    # when value == 'q'
    raise StopUpdating()


def update_requirement_line(req, line, spec_ver, latest_ver):
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

    old_ver = spec_ver[1] or spec_ver[3]
    spec_regex = re.sub(r'(\W)', r'\\\1', str(old_ver))
    pattern = r'((==|>=)\s*){0}'.format(spec_regex)
    match = re.search(pattern, spec_part)
    if match is None:
        return line
    pre_part = match.group(1)
    old = '{0}{1}'.format(pre_part, str(old_ver))
    new = '{0}{1}'.format(pre_part, str(latest_ver))
    new_line = '{package_part}{spec_part}'.format(
        package_part=package_part,
        spec_part=spec_part.replace(old, new, 1),
    )
    return new_line


def requirements_line(line, req):
    return not req and line and line.strip().startswith('-r ')


def less_than(new_ver, old_ver, patch=False):
    if old_ver is None:
        return True
    new_ver = str(new_ver).split('.')
    old_ver = str(old_ver).split('.')
    if old_ver[0] is None:
        return True
    new_major = parse(new_ver[0] or 0)
    old_major = parse(old_ver[0] or 0)
    if new_major > old_major:
        return False
    if patch:
        if len(old_ver) == 1 or old_ver[1] is None:
            return True
        new_minor = parse('1.0.{}'.format((new_ver[1] if len(new_ver) > 1 else 0) or 0))
        old_minor = parse('1.0.{}'.format((old_ver[1] if len(old_ver) > 1 else 0) or 0))
        if new_minor > old_minor:
            return False
    return True


def format_list_arg(options, key):
    try:
        options[key] = set(x.strip().lower() for x in options[key].split(','))
    except AttributeError:
        options[key] = set()


class ExitCodeException(click.ClickException):
    def __init__(self, exit_code, message=None):
        self.exit_code = exit_code
        self.message = message

    def show(self, **kwargs):
        if self.message:
            super().show(**kwargs)
