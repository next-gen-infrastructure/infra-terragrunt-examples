import re


def get_repo_name(repo) -> str:
    repo_url = repo.remotes.origin.url
    m = re.search(r"git@github\.com:(.*)\.git", repo_url)
    if m:
        return m.group(1)


def get_repo_version(repo) -> str:
    tags = repo.tags
    if len(tags) > 0:
        current_tag = str(
            sorted(tags, key=lambda t: t.commit.committed_datetime)[-1]
        )
        prefix = 'v' if current_tag.startswith('v') else ''
        version = current_tag.replace(prefix, '').split('.')
        print(f'Current version is {current_tag}. Next release will be:'
              '\n0 | Develop'
              '\n1 | Main'
              '\n2 | Major version'
              '\n3 | Minor version'
              '\n4 | Patch version'
              )
        next_release = int(input(f'Plan next release [0]: ') or 0) - 1
        if next_release >= 0:
            version[next_release] = str(int(version[next_release]) + 1)
            while next_release < len(version) - 1:
                next_release += 1
                version[next_release] = '0'
            return prefix + '.'.join(version)
        return 'develop'
    return 'main'
