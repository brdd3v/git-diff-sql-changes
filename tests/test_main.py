import git
import pytest
import pandas as pd
import requests

import main
import prep


change_type_scenarios = {
    "openmrs-core": ["52ce5ca475d20bd1ac5ccfc052f9a3465c21dfa3",
                     [("M", "metadata/model/update-to-latest-db.mysqldiff.sql"),
                      ("M", "src/api/org/openmrs/hl7/handler/ORUR01Handler.java"),
                      ("A", "src/api/org/openmrs/hl7/handler/ProposingConceptException.java"),
                      ("M", "test/api/org/openmrs/test/hl7/ORUR01HandlerTest.java")]],
    "roundcubemail": ["fa898a4a84202f0ba28c27a39e059c6f5a442c4e",
                      [("M", "INSTALL"), ("R100", "SQL/mysql.initial.sql")]],
    "biosql": ["be73e697352f931cc23f9527f70d0f34252c7c80",
               [("M", "sql/biosql-ora/migrate/singapore/migrate-taxon.sql")]]}


commit_file_diff_text_scenarios = {
    "biosql": ["0ca2cd376268ef0a5910660dc6b9260ef6031234",
               "sql/biosql-ora/BS-create-Biosql-usersyns.sql",
               "0ca2cd3 Moved linesize setting into BS-defs.\n"
               "diff --git a/sql/biosql-ora/BS-create-Biosql-usersyns.sql "
               "b/sql/biosql-ora/BS-create-Biosql-usersyns.sql\n"
               "index 9c5b2f6..427fb33 100644\n"
               "--- a/sql/biosql-ora/BS-create-Biosql-usersyns.sql\n"
               "+++ b/sql/biosql-ora/BS-create-Biosql-usersyns.sql\n"
               "@@ -33 +32,0 @@ set feedback off\n"
               "-set lines 200"],
    "biblioteq": ["7859e6add8d78bd53d2cb5ca42c857a5efca3a78",
                  "postgresql_create_schema.sql",
                  "7859e6ad Removed blank."]
}


@pytest.mark.dependency(name="get-commits-check-num",
                        depends=["branch-check"],
                        scope="session")
@pytest.mark.order(12)
def test_get_commits_check_num_gt_zero(get_repo_path):
    _, path = get_repo_path
    repo_cmd = git.cmd.Git(path)
    res = main.get_commits(repo_cmd)
    assert len(res.split("\n")) > 0


@pytest.mark.dependency(name="get-commit-file-diff-text",
                        depends=["repo-validity-check"],
                        scope="session")
@pytest.mark.order(13)
def test_get_commit_file_diff_text(get_repo_path):
    name, path = get_repo_path
    test_data = commit_file_diff_text_scenarios.get(name, None)
    if test_data is None:
        pytest.skip(f"Test data for the project '{name}' is not prepared")
    commit, sql_file, diff_text_expected = test_data
    repo_cmd = git.cmd.Git(path)
    diff_text = main.get_commit_file_diff_text(repo_cmd, commit, sql_file)
    assert diff_text == diff_text_expected


@pytest.mark.dependency(name="check_modify_changed_blocks",
                        depends=["json_valid_schema_regex", "check_regex_privilege",
                                 "check_regex_engine", "check_regex_primary_key",
                                 "check_regex_index", "check_regex_dml", "check_regex_comments"],
                        scope="session")
@pytest.mark.parametrize(
    "blocks_lst, categories_lst, blocks_lst_expected",
    [(["""create index bioentryentry  on bioentry_entry(entry_id);
         # bioentry_id is already the primary key, no index needed
         # create index bioentryentry  on bioentry_taxa(bioentry_id);"""],
      ["Index", "Comments"],
      []),
     (["""insert into seqfeature_qualifier (qualifier_name) values ('unbounded_start');
          insert into seqfeature_qualifier (qualifier_name) values ('unbounded_end');
          insert into seqfeature_qualifier (qualifier_name) values ('end_pos_type');""",
      """insert into seqfeature_qualifier (qualifier_name) values ('start_pos_type');
          insert into seqfeature_qualifier (qualifier_name) values ('location_type');"""],
      ["DML"],
      []),
     (["node_group_id    int(10) unsigned default '0' not null,"],
      ["DML", "Comments", "Index", "PK", "Engine", "Privilege"],
      ["node_group_id    int(10) unsigned default '0' not null,"])]
)
@pytest.mark.order(14)
def test_check_modify_changed_blocks(blocks_lst, categories_lst, blocks_lst_expected):
    data_regex = prep.get_json_data_regex()
    for category in categories_lst:
        blocks_lst = main.check_modify_changed_blocks(blocks_lst, data_regex[category], category)
    assert blocks_lst == blocks_lst_expected


@pytest.mark.parametrize(
    "block, total_block_size",
    [(["CREATE TABLE tab1(\ncolumn1 type1,\ncolumn2 type2,\ncolumn3 type3\n);"], 5),
     (["block_1_line_1\nblock_1_line_2\n", "block_2_line_1\n"], 3)]
)
@pytest.mark.order(15)
def test_calculate_total_block_diff_size(block, total_block_size):
    size = main.calculate_total_block_diff_size(block)
    assert size == total_block_size


@pytest.mark.dependency(name="type-change-check",
                        depends=["repo-validity-check"],
                        scope="session")
@pytest.mark.order(16)
def test_get_change_type(get_repo_path):
    name, path = get_repo_path
    test_data = change_type_scenarios.get(name, None)
    if test_data is None:
        pytest.skip(f"Test data for the project '{name}' is not prepared")
    commit, type_file_lst_expected = test_data
    repo_cmd = git.cmd.Git(path)
    types_files = main.get_change_type(repo_cmd, commit)
    assert len(set(types_files).symmetric_difference(set(type_file_lst_expected))) == 0


@pytest.mark.parametrize(
    "type_files_lst, sql_files_num",
    [([("A", "installation/sql/README.md"),
       ("D", "installation/sql/sample.sql"),
       ("M", "maintenance/postgresql/tables.sql")], 2),
     ([("R", "maintenance/mysql/update_13032004.sql"),
       ("A", "maintenance/mysql/diff_rc1_to_rc2.sql"),
       ("C", "setup/db/sqlite.c"),
       ("R", "config/config.yml"),
       ("A", "tests/db/test_db.py"),
       ("A", "tests/db/test_data.sql")], 3)])
@pytest.mark.order(17)
def test_keep_only_sql_files(type_files_lst, sql_files_num):
    res = main.keep_only_sql_files(type_files_lst)
    assert len(res) == sql_files_num


@pytest.mark.order(18)
def test_df_preparation():
    commits_info_txt = """
    a20812702f34235202384c23842805b923293841;2008-03-28T15:01:43+00:00;2008-03-28T15:01:43+00:00
    b892380230e23123124ac80e8238402739427312;2019-01-12T11:55:37-08:00;2019-01-12T11:55:37-08:00
    c7148304923804223e2342f232342a234234ff33;2011-05-16T11:55:22-04:00;2011-05-16T11:55:22-04:00
    """
    commits_info_txt = commits_info_txt.strip()
    df = main.prepare_df(commits_info_txt)
    assert len(df) == len(commits_info_txt.split("\n"))
    assert df.columns.tolist() == ["commit", "commit_date", "author_date", "ChangedFilesNum",
                                   "SQLFilesNum", "Whitespace", "DML", "Index", "Comments",
                                   "NoDiffInfo", "Privilege", "PK", "Engine", "Renaming", "Other"]
    assert df[['ChangedFilesNum', 'SQLFilesNum']].values.tolist() == [[0, 0], [0, 0], [0, 0]]
    assert df['DML'].values.tolist() == [set(), set(), set()]


@pytest.mark.order(19)
def test_df_population():
    df = pd.DataFrame.from_dict({"column_1": [10, 20, 30],
                                 "column_2": ["text_1", "text_2", "text_3"]})
    for el in ['Index', 'DML']:
        df[el] = df.apply(lambda x: set(), axis=1)
    main.populate_df(df, 0, ['sql_file_0'], 'Index')
    main.populate_df(df, 1, ["sql_file_1", "sql_file_2"], 'Index')
    main.populate_df(df, 2, ["sql_file_3", "sql_file_4"], 'DML')
    assert df.iloc[0]['Index'] == {'sql_file_0'}
    assert df.iloc[1]['Index'] == {"sql_file_1", "sql_file_2"}
    assert df.iloc[2]['DML'] == {'sql_file_3', 'sql_file_4'}


@pytest.mark.order(20)
def test_check_for_renaming():
    files = [("R100", "sql_file_1"), ("A", "sql_file_2"), ("R80", "sql_file_3"),
             ("M", "sql_file_4"), ("R100", "sql_file_5"), ("D", "sql_file_6")]
    renamed_files, other_renamed_files = main.check_for_renaming(files)
    assert renamed_files == ['sql_file_1', 'sql_file_5']
    assert other_renamed_files == ['sql_file_3']


@pytest.mark.parametrize(
    "user, repo, commit_1, commit_2, file_id, blocks_num, total_diff_size",
    [("biosql", "biosql", "3584d7b0537ffb1806dd5602b30d452339ed89d2",
      "a5811031e55664132b794b292b1149e626268c06", 0, 7, 117),
     ("biosql", "biosql", "3584d7b0537ffb1806dd5602b30d452339ed89d2",
      "a5811031e55664132b794b292b1149e626268c06", 1, 6, 111),
     ("biosql", "biosql", "3584d7b0537ffb1806dd5602b30d452339ed89d2",
      "a5811031e55664132b794b292b1149e626268c06", 3, 1, 52),
     ("PowerDNS", "pdns", "f7676f61b3cefa3b2fab4a7d11df27033cc8ec97",
      "0bc2d021f5d1bea4cb63941c4d490f971d783a0d", 0, 1, 2)])
@pytest.mark.order(21)
def test_changed_blocks_preparation(user, repo, commit_1, commit_2,
                                    file_id, blocks_num, total_diff_size):
    try:
        resp = requests.get(f"https://api.github.com/repos/{user}/"
                            f"{repo}/compare/{commit_1}...{commit_2}")
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f"Connection error: {e}")
    resp_json = resp.json()
    diff_text = resp_json['files'][file_id]['patch']
    changed_blocks_lst = main.prepare_changed_blocks(diff_text)
    assert len(changed_blocks_lst) == blocks_num
    assert len("\n".join(changed_blocks_lst).split("\n")) == total_diff_size
