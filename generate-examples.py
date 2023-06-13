#!/usr/bin/env python3
import os
import sys
from typing import List
from shutil import which

import git

from org.nextgeninfrastructure.scripts import logger
from org.nextgeninfrastructure.scripts.gitcontext import get_repo_name, get_repo_version
from org.nextgeninfrastructure.scripts.processvariables import process_examples


def collect_modules() -> List[str]:
    modules = []
    for root, dirs, files in os.walk(repo_path):
        if '.terraform' not in root:
            for d in dirs:
                if os.path.exists(
                    os.path.join(root, d, 'variables.tf')
                ) and os.path.exists(
                    os.path.join(root, d, 'global-variables.tf')
                ):
                    module_path = str(os.path.relpath(os.path.join(root, d)))
                    modules.append(module_path)
    return modules


def check_dependencies() -> None:
    if which("terraform-config-inspect") is None:
        logger.fatal(f'Please install GO111MODULE=on go get github.com/hashicorp/terraform-config-inspect')
        exit(1)


if __name__ == "__main__":
    check_dependencies()
    repo_path = os.getcwd()
    gitrepo = git.Repo.init(os.getcwd())
    repo_name = get_repo_name(gitrepo)
    repo_version = get_repo_version(gitrepo)

    if len(sys.argv) == 2:
        module_locations = [sys.argv[1]]
    else:
        module_locations = collect_modules()

    for location in module_locations:
        logger.info(f'Processing {location}...')
        process_examples(gitrepo, repo_path, repo_name, repo_version, location)
    if len(gitrepo.index.diff()) > 0:
        logger.info('Committing change to the repository')
        gitrepo.index.commit(f'Update examples: {repo_version}')
