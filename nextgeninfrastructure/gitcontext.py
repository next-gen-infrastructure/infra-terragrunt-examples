import re


def get_repo_name(repo) -> str:
    repo_url = repo.remotes.origin.url
    m = re.search(r"git@github\.com:(.*)\.git", repo_url)
    if m:
        return m.group(1)


def get_repo_version(repo) -> str:
    tags = repo.tags
    if len(tags) > 0:
        tag = str(
            sorted(tags, key=lambda t: t.commit.committed_datetime)[-1]
        )
        module_name = ''
        if "/" in tag:
            module_name, version = tag.split('/', maxsplit=2)
            module_name += '/'
        else:
            version = tag
        version = version.split('.')

        print(f'Current version is {version}. Next release will be:'
              '\n0 | No changes'
              '\n1 | Main branch'
              '\n2 | Major version'
              '\n3 | Minor version'
              '\n4 | Patch version'
              )
        next_release = int(input(f'Plan next release [0]: ') or 0) - 2
        if next_release >= 0:
            version[next_release] = str(int(version[next_release]) + 1)
            while next_release < len(version) - 1:
                next_release += 1
                version[next_release] = '0'
            return module_name + '.'.join(version)
        return tag
    return 'main'
