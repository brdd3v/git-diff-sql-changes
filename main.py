#!/usr/bin/env python3

import os
import re
import git
import pandas as pd
from tqdm import tqdm
import prep

HOME_DIR = os.getcwd()


def prepare_changed_blocks(diff_txt):
    # get a list of blocks starting with @@ (and remove these @@-lines at the end)
    diff_txt_lst = diff_txt.split("\n")
    ids = [diff_txt_lst.index(line) for line in
           diff_txt_lst if line.startswith("@@ ")] + [len(diff_txt_lst)]
    blocks_lst = [diff_txt_lst[id1+1:id2] for id1, id2 in zip(ids, ids[1:])]
    # modify blocks (make lowercase; remove +/-, leading/trailing chars and empty lines)
    blocks_mod_lst = list()
    for block in blocks_lst:
        block_mod = list()
        for line in block:
            if line.startswith("+") or line.startswith("-"):
                line = line[1:].strip()
                if line != "":
                    block_mod.append(line.lower())
        if len(block_mod) > 0:
            blocks_mod_lst.append("\n".join(block_mod))
    return blocks_mod_lst


def check_modify_changed_blocks(blocks_lst, regex, category):
    blocks_mod_lst = list()
    for block in blocks_lst:
        block_mod = list()
        # remove single-line and multi-line comments
        if category == "Comments":
            block = re.sub(regex, "", block, flags=re.M)
            for line in block.split("\n"):
                line_mod = line.strip()
                if line_mod != "":
                    block_mod.append(line_mod)
        else:
            # remove line if match found (all other categories)
            for line in block.split("\n"):
                if not re.search(regex, line.strip(), flags=re.I):
                    block_mod.append(line.strip())
        if len(block_mod) > 0:
            blocks_mod_lst.append("\n".join(block_mod))
    return blocks_mod_lst


def populate_df(df, idx, sql_files, change_type):
    for sql_file in sql_files:
        df.at[idx, change_type].update({sql_file})


def check_for_renaming(type_files_lst):
    renamed_files = list()
    other_renamed_files = list()
    for el in type_files_lst:
        if el[0].startswith("R"):
            if el[0].startswith("R100"):
                renamed_files.append(el[1])
            else:
                other_renamed_files.append(el[1])
    return renamed_files, other_renamed_files


def get_change_type(repo_cmd, commit):
    type_files_lst = list()
    command = ["git", "show", commit, "--oneline", "--name-status"]
    res = repo_cmd.execute(command)
    change_files_lst = res.split("\n")[1:]
    for fc in change_files_lst:
        if fc.startswith("R"):
            type_, old_path, new_path = fc.split("\t")
        else:
            type_, curr_path = fc.split("\t")
            new_path = curr_path
        type_files_lst.append((type_, new_path))
    return type_files_lst


def keep_only_sql_files(type_files_lst):
    return [type_file for type_file in type_files_lst if type_file[1].endswith(".sql")]


def prepare_df(res):
    records_lst = res.split("\n")
    df = pd.DataFrame.from_records(map(lambda record: record.split(";"), records_lst),
                                   columns=["commit", "commit_date", "author_date"])
    # transform type of date-records
    df['commit_date'] = pd.to_datetime(df['commit_date'])
    df['author_date'] = pd.to_datetime(df['author_date'])
    df.sort_values("commit_date", inplace=True)
    # add the remaining columns
    df["ChangedFilesNum"] = 0
    df["SQLFilesNum"] = 0
    columns = ["Whitespace", "DML", "Index", "Comments", "NoDiffInfo",
               "Privilege", "PK", "Engine", "Renaming", "Other"]
    for col in columns:
        df[col] = df.apply(lambda x: set(), axis=1)
    return df


def get_commits(repo_cmd):
    return repo_cmd.execute(["git", "log", "--no-merges",
                             "--pretty=format:%H;%aI;%cI", "--follow", "--", "*.sql"])


def get_commit_file_diff_text(repo_cmd, commit, sql_file):
    return repo_cmd.execute(["git", "show", commit, "--oneline", "--ignore-space-at-eol",
                             "-b", "-w", "--ignore-blank-lines", "-U0", "--", sql_file])


def calculate_total_block_diff_size(blocks_lst):
    return sum([len(block.strip().split("\n")) for block in blocks_lst])


def main():
    projects_json_lst = prep.get_json_data_projects()
    results_dir_path = os.path.join(HOME_DIR, "results")
    prep.check_create_results_folder(results_dir_path)

    data_regex = prep.get_json_data_regex()

    for prj in projects_json_lst:
        repo_cmd = git.cmd.Git(os.path.join(HOME_DIR, "repos", prj["name"]))
        res = get_commits(repo_cmd)
        df = prepare_df(res)

        for idx, row in tqdm(df.iterrows(), total=df.shape[0], desc=prj["name"]):
            type_files_lst = get_change_type(repo_cmd, row["commit"])
            df.at[idx, "ChangedFilesNum"] = len(type_files_lst)

            type_sql_files_lst = keep_only_sql_files(type_files_lst)
            df.at[idx, "SQLFilesNum"] = len(type_sql_files_lst)

            # RENAMING
            renamed_files_lst, other_renamed_files = check_for_renaming(type_sql_files_lst)
            populate_df(df, idx, renamed_files_lst + other_renamed_files, "Renaming")

            for type_, changed_file in type_sql_files_lst:
                if changed_file in renamed_files_lst:
                    continue

                diff_txt = get_commit_file_diff_text(repo_cmd, row["commit"], changed_file)
                # remove the commit message
                diff_txt = "\n".join(diff_txt.split("\n")[1:])
                # remove additional (unnecessary) information from Git
                diff_txt = diff_txt.replace("\\ No newline at end of file", "").strip()

                # WHITESPACE
                if len(diff_txt) == 0:
                    populate_df(df, idx, [changed_file], "Whitespace")
                    continue

                # NO-DIFF-INFO
                if "@@ " not in diff_txt:
                    populate_df(df, idx, [changed_file], "NoDiffInfo")
                    continue

                changed_blocks = prepare_changed_blocks(diff_txt)

                for category in data_regex.keys():
                    # calculate the total block size before and after check/modification.
                    # (if the size has become smaller, mark the presence of a change of the current category)
                    total_block_diff_size_before = calculate_total_block_diff_size(changed_blocks)
                    changed_blocks = check_modify_changed_blocks(changed_blocks,
                                                                 data_regex[category],
                                                                 category)
                    total_block_diff_size_after = calculate_total_block_diff_size(changed_blocks)

                    if total_block_diff_size_before > total_block_diff_size_after:
                        populate_df(df, idx, [changed_file], category)

                    if len(changed_blocks) == 0:
                        break

                # if there are still blocks left, then mark as the presence of not yet identified changes
                if len(changed_blocks) != 0:
                    populate_df(df, idx, [changed_file], "Other")

        df.to_csv(os.path.join(results_dir_path, f'{prj["name"]}.csv'), index=False)


if __name__ == "__main__":  # pragma: no cover
    main()
