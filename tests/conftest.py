import os
import sys
import pytest

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import prep

prep.main()


def get_repos():
    repos_path = os.path.join(parent, "repos")
    if os.path.exists(repos_path):
        return list(map(lambda dir_name: (dir_name, os.path.join(repos_path, dir_name)),
                        os.listdir(repos_path)))
    return []


@pytest.fixture(params=get_repos())
def get_repo_path(request):
    return request.param


@pytest.fixture()
def get_repos_path():
    return get_repos()


@pytest.fixture()
def get_json_data_projects():
    return prep.get_json_data_projects()
