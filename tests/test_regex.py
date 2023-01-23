import pytest
import re

import prep


@pytest.mark.dependency(name="check_regex_comments",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(2)
def test_check_regex_comments():
    text = """
    /* Delete */
    Keep 1.1 /* Delete */ Keep 1.2
    /* Delete
    * Delete
    */ Keep 2
    /* Delete */ Keep 3
    Keep 4
    -- Delete
    Keep 5 -- Delete
    /*  Delete

    Delete
    */ Keep 6
    Keep 7 -- Delete
    Keep 8.1 /* Delete */ Keep 8.2
    # Delete
    Keep 9 #Delete
    Keep 10 -- / Delete
    /*Delete  */ Keep 11
    /* Delete*/ Keep 12 /* Delete */
    """
    data_regex = prep.get_json_data_regex()
    text_mod = re.sub(data_regex['Comments'], "", text, flags=re.M)
    assert "Delete" not in text_mod
    assert text_mod.count("Keep") == 14


@pytest.mark.dependency(name="check_regex_dml",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(3)
def test_check_regex_dml():
    text = """
    INSERT INTO tab_1 ( col_1, col_2 ) VALUES ( val_1, val_2);
    delete data from database -- invalid query
    insert into public.info (col_id, col_num, col_date) values('12', 178, 12.01.2022)
    delete  from  customers where customer_id = '14';
    select  from -- invalid query
    select column_1from table where col_3 > 100 -- invalid query
    select * from table;
    """
    data_regex = prep.get_json_data_regex()
    queries_lst = list()
    for line in text.split("\n"):
        if re.search(data_regex['DML'], line, re.I):
            queries_lst.append(line)
    assert "invalid query" not in "\n".join(queries_lst)
    assert len(queries_lst) == 4


@pytest.mark.dependency(name="check_regex_index",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(4)
def test_check_regex_index():
    text = """
    create index node_path_idx on node_path (parent_node_id);
    CREATE INDEX domain_id ON records(domain_id)
    create uniqe index -- invalid query
    DROP INDEX IF EXISTS index_customer_name ON info.customers;
    """
    data_regex = prep.get_json_data_regex()
    queries_lst = list()
    for line in text.split("\n"):
        if re.search(data_regex['Index'], line, re.I):
            queries_lst.append(line)
    assert "invalid query" not in "\n".join(queries_lst)
    assert len(queries_lst) == 3


@pytest.mark.dependency(name="check_regex_primary_key",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(5)
def test_check_regex_primary_key():
    text = """
    value            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT;

    cache_id integer not null primary key,
    """
    data_regex = prep.get_json_data_regex()
    queries_lst = list()
    for line in text.split("\n"):
        if re.search(data_regex['PK'], line, re.I):
            queries_lst.append(line)
    assert len(queries_lst) == 2


@pytest.mark.dependency(name="check_regex_engine",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(6)
def test_check_regex_engine():
    text = """
    ALTER TABLE my_table ENGINE = InnoDB;
    ) ENGINE=MyISAM MAX_ROWS=10000;
    )  engine=MyISAM;
    Change engine -- invalid query
    Engine is more than = -- invalid query
    Engine =innodb
    engine= ; -- invalid query
    ENGINE = -- invalid query
    ALTER TABLE tab_name ENGINE=InnoDB;
    """
    data_regex = prep.get_json_data_regex()
    queries_lst = list()
    for line in text.split("\n"):
        if re.search(data_regex['Engine'], line, re.I):
            queries_lst.append(line)
    assert "invalid query" not in "\n".join(queries_lst)
    assert len(queries_lst) == 5


@pytest.mark.dependency(name="check_regex_privilege",
                        depends=["json_valid_schema_regex"],
                        scope="session")
@pytest.mark.order(7)
def test_check_regex_privilege():
    text = """
    GRANT DELETE, INSERT, SELECT, UPDATE ON tab TO administrator;
    grant update ( column_1, column_2 ) on table_2 to user1;

    REVOKE SELECT ON employees FROM public;
    revoke all on employees from user2;
    """
    data_regex = prep.get_json_data_regex()
    queries_lst = list()
    for line in text.split("\n"):
        if re.search(data_regex['Privilege'], line.strip(), re.I):
            queries_lst.append(line)
    assert len(queries_lst) == 4
