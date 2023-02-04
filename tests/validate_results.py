import os
import glob
import datetime
import pandas as pd
import pandera as pa
from pandera import Column, Check


HOME_DIR = os.getcwd()


def transform_date_column(col_name):
    return pd.to_datetime(df[col_name], utc=True).dt.tz_localize(None)


def check_cat_columns(c):
    return ((c.str.len() == 5) and (c.str == "set()")) or \
           ((c.str.len() > 5) and (".sql" in c.str))


def check_date_columns(c):
    return c >= pd.to_datetime("01/01/2000  01:01:01 PM")


schema = pa.DataFrameSchema({
    "commit":           Column(str, [Check.str_length(40),
                                     Check.str_matches(r'^[a-z,0-9]+$')]),
    "commit_date":      Column(datetime.datetime, Check(lambda c: check_date_columns)),
    "author_date":      Column(datetime.datetime, Check(lambda c: check_date_columns)),
    "ChangedFilesNum":  Column(int, Check(lambda c: c > 0)),
    "SQLFilesNum":      Column(int, Check(lambda c: c > 0)),
    "Whitespace":       Column(str, Check(lambda c: check_cat_columns)),
    "DML":              Column(str, Check(lambda c: check_cat_columns)),
    "Index":            Column(str, Check(lambda c: check_cat_columns)),
    "Comments":         Column(str, Check(lambda c: check_cat_columns)),
    "NoDiffInfo":       Column(str, Check(lambda c: check_cat_columns)),
    "Privilege":        Column(str, Check(lambda c: check_cat_columns)),
    "PK":               Column(str, Check(lambda c: check_cat_columns)),
    "Engine":           Column(str, Check(lambda c: check_cat_columns)),
    "Renaming":         Column(str, Check(lambda c: check_cat_columns)),
    "Other":            Column(str, Check(lambda c: check_cat_columns))
})

csv_files = glob.glob(os.path.join(HOME_DIR, "results", "*.csv"))
for csv_file in csv_files:
    print(f"Checking {csv_file}")
    df = pd.read_csv(csv_file)
    df['commit_date'] = transform_date_column('commit_date')
    df['author_date'] = transform_date_column('author_date')
    schema.validate(df)
