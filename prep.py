#!/usr/bin/env python3

import os
import json
import git

HOME_DIR = os.getcwd()


def get_json_data_regex():
    with open(os.path.join(HOME_DIR, "conf", "regex.json"), encoding="utf-8") as json_f:
        json_data = json.load(json_f)
        for key, val in json_data.items():
            json_data[key] = "".join(val) if type(val) == list else val
        return json_data


def get_json_data_projects():
    with open(os.path.join(HOME_DIR, "conf", "projects.json"), encoding="utf-8") as json_f:
        json_data = json.load(json_f)
        return [prj for prj in json_data["projects"] if prj["check"] is True]


def check_create_repos_folder():
    if not os.path.exists(os.path.join(HOME_DIR, "repos")):
        print("Folder 'repos' created.")
        os.mkdir(os.path.join(HOME_DIR, "repos"))


def check_clone_repos(projects_json_lst):
    for prj in projects_json_lst:
        project_name = prj["name"]
        repo_path = os.path.join(HOME_DIR, "repos", project_name)
        if (not os.path.exists(repo_path)) or (len(os.listdir(repo_path)) < 2):
            print(f"Cloning repo '{project_name}'...")
            git.Repo.clone_from(prj["url"], repo_path, branch="master")


def main():
    projects_json_lst = get_json_data_projects()
    if len(projects_json_lst) > 0:
        check_create_repos_folder()
        check_clone_repos(projects_json_lst)


if __name__ == "__main__":
    main()
