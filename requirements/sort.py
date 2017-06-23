import argparse
import json
import re

LINE_REGEX = re.compile(r'^(?P<disabled>[#!]* *)?'
                        r'(?P<install>(?P<name>[\w\-.\[\]]+)'
                        r'(?:[=]{1,2}(?P<version>[\da-z.?\-]+))?)'
                        r'(?:\s*#+\s*(?P<notes>.*))*?$',
                        re.I)
VCS_REGEX = re.compile(r'^(?P<disabled>[#!]* *)?'
                       r'(?P<install>(?P<vcs>git|hg)\+(?P<repo>.*?)(?:\.git)?'
                       r'@(?P<version>[\da-z]+)'
                       r'#egg=(?P<name>[\w\-.\[\]]+)'
                       r'(?:&subdirectory=(?P<repo_subdir>.*?))?)'
                       r'(?:\s*#+\s*(?P<notes>.*))*?$',
                       re.I)


def _readlines(file_path):
    with open(file_path, 'r') as fh:
        return fh.readlines()


def _write(file_path, string):
    with open(file_path, 'wb') as fh:  # use 'wb' to avoid CR-LF
        fh.write(string)


def sort_key(val):
    # Ignore comments
    comment = re.search(r'^[#!]+\s', val)
    if comment:
        val = val[comment.end(0):]

    vcs = re.search(r'^(?:git|hg)\+.*?#egg=([\w\-.\[\]]+)(?:$|)', val, re.I)
    if vcs:
        val = val[vcs.start(1):vcs.end(1)]

    # Ignore special chars
    val = val.translate(None, '.-_[]')

    # Ignore case
    val = val.lower()

    return val


def file_to_dict(file_path):
    reqs = []
    for pkg in _readlines(file_path):
        pkg = pkg.strip()
        if not pkg:
            continue

        pkg_obj = dict()
        pkg_match = re.match(LINE_REGEX, pkg)
        pkg_vcs_match = re.match(VCS_REGEX, pkg)

        if not (pkg_match or pkg_vcs_match):
            print('Unable to read package line: {}'.format(pkg))
            reqs = None
            break

        if pkg_match:
            name = pkg_match.group('name')
            version = str(pkg_match.group('version'))

            if re.match(r'[\da-z]{40}', version, re.I):
                version_warning = 'Uses commit hash instead of version number'
            else:
                version_warning = None

            pypi_url = None
            if not version_warning:
                pypi_url = 'https://pypi.python.org/pypi/{0}/{1}'.format(name, version)

            pkg_obj = {
                'active': not bool(pkg_match.group('disabled')),
                'name': name,
                'version': version,
                'notes': pkg_match.group('notes') or version_warning,
                'url': pypi_url,
                'install': pkg_match.group('install') if not version_warning else None,
            }
        elif pkg_vcs_match:
            vcs = pkg_vcs_match.group('vcs')
            repo = pkg_vcs_match.group('repo')
            version = pkg_vcs_match.group('version')
            repo_subdir = pkg_vcs_match.group('repo_subdir')

            repo_url = None
            if vcs == 'git' and 'github.com' in repo:
                if repo_subdir:
                    repo_url = '{0}/tree/{1}/{2}'.format(repo, version, repo_subdir)
                else:
                    repo_url = '{0}/tree/{1}'.format(repo, version)
            elif vcs == 'hg' and 'bitbucket.org' in repo:
                if repo_subdir:
                    repo_url = '{0}/src/{1}/{2}'.format(repo, version, repo_subdir)
                else:
                    repo_url = '{0}/src/{1}'.format(repo, version)

            pkg_obj = {
                'active': not bool(pkg_vcs_match.group('disabled')),
                'name': pkg_vcs_match.group('name'),
                'version': version,
                'notes': pkg_vcs_match.group('notes'),
                'url': repo_url,
                'install': pkg_vcs_match.group('install'),
            }

        if pkg_obj:
            reqs.append(pkg_obj)

    if not reqs:
        return False

    reqs.sort(key=lambda x: x['name'].translate(None, '.-_[]').lower())
    return reqs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Requirements file sorter')
    parser.add_argument('file', metavar='requirements-file', help='requirements file to sort')
    parser.add_argument('-j', '--json', action='store_true', help='parse and export as json')
    args = parser.parse_args()

    if not args:
        parser.print_help()
        exit(1)

    result = False
    if not args.json:
        print('Sorting [{}]...'.format(args.file))
        lines = _readlines(args.file)
        lines = ''.join(sorted(lines, key=sort_key))
        _write(args.file, lines)
        result = True
    else:
        new_file = args.file.rpartition('.')[0] + '.json'
        print('Exporting [{0}] as [{1}]...'.format(args.file, new_file))
        data = file_to_dict(args.file)
        if data:
            _write(new_file, json.dumps(data, indent=4, sort_keys=True, separators=(',', ': ')))
            result = True

    print('Done' if result else 'Failed')
