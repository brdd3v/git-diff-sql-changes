import os
import git
import pytest

import prep


@pytest.mark.order(8)
def test_num_of_repos_gte_num_in_config(get_repos_path, get_json_data_projects):
    assert len(get_repos_path) >= len(get_json_data_projects)


@pytest.mark.dependency(name="repo-validity-check",
                        scope="session")
@pytest.mark.order(9)
def test_is_valid_git_repo(get_repo_path):
    name, path = get_repo_path
    try:
        git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        pytest.fail(f"Invalid Git Repo: {name}")


@pytest.mark.dependency(name="branch-check",
                        depends=["repo-validity-check"],
                        scope="session")
@pytest.mark.order(10)
def test_is_master_branch(get_repo_path):
    _, path = get_repo_path
    repo = git.Repo(path)
    assert repo.active_branch.name == "master"


@pytest.mark.order(11)
def test_check_create_results_folder():
    results_dir_path = os.path.join(prep.HOME_DIR, "results")
    assert not os.path.exists(results_dir_path)
    prep.check_create_results_folder(results_dir_path)
    assert os.path.exists(results_dir_path)
    os.rmdir(results_dir_path)
