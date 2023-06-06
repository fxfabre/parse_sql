"""
First script : read SQL files & generate "joins_frequency.csv"
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path
from pprint import pprint

import pandas as pd

from parse_sql.extract_from_parsed import extract_all_joins_from_file
from parse_sql.parsers import read_and_parse_sql_file


def pretty_print(json_content):
    print(json.dumps(json_content, indent=4))


def debug_file():
    query = "query_groupby.sql"
    file_path = Path("tests/sql_test_files") / query

    r = read_and_parse_sql_file(file_path)
    print("\n\n\nResult : ")
    pretty_print(r)


def extract_join_from_all_files(dag_dir: Path):
    def iter_files(start_folder: Path):
        for root, dirs, files in os.walk(start_folder.as_posix()):
            root_folder = Path(root).absolute()
            yield from (
                root_folder / file_name
                for file_name in files
                if file_name.endswith(".sql")
            )

    c = Counter()
    is_parsing_success = []
    files = [dag_dir] if dag_dir.is_file() else iter_files(dag_dir)
    for file_path in files:
        print(file_path.as_posix())
        try:
            parsing_by_cte = read_and_parse_sql_file(file_path)
            counter_for_file = extract_all_joins_from_file(parsing_by_cte)
            c.update(counter_for_file)
            is_parsing_success.append(True)
        except Exception as e:
            print("  Failed :", e)
            is_parsing_success.append(False)

    print(f"parsing success : {sum(is_parsing_success)} / {len(is_parsing_success)}")
    pprint(c.most_common(30))

    csv_file_path = os.path.join(os.getenv("DATA_DIR"), "bq_prod", "joins_frequency.csv")
    pd.DataFrame(
        c.items(), columns=["join_condition", "frequency"]
    ).sort_values("frequency", ascending=False).to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        dag_dir = Path(sys.argv[1])
    else:
        dag_dir = Path(os.getenv("WORK_DIR")) / "data-flow" / "dags"
    extract_join_from_all_files(dag_dir)
