"""
First script : read SQL files & generate "joins_frequency.csv"
"""

import json
import os
import sys
from pathlib import Path
from pprint import pprint

import pandas as pd
import traceback
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

    join_conditions = []
    is_parsing_success = []
    files = [dag_dir] if dag_dir.is_file() else iter_files(dag_dir)
    for file_path in files:
        print(file_path.as_posix())
        try:
            parsing_by_cte = read_and_parse_sql_file(file_path)
            counter_for_file = extract_all_joins_from_file(parsing_by_cte)
            join_conditions.extend(
                (join_condition, frequency, file_path.stem)
                for join_condition, frequency in counter_for_file.items()
            )
            is_parsing_success.append(True)
        except Exception as e:
            print("  Failed :", e)
            traceback.print_tb(e.__traceback__)
            is_parsing_success.append(False)

    df_join_conditions = pd.DataFrame(
        join_conditions, columns=["join_condition", "frequency", "file_name"]
    )

    print(f"parsing success : {sum(is_parsing_success)} / {len(is_parsing_success)}")
    pprint(
        df_join_conditions[["join_condition", "frequency"]]
        .groupby("join_condition", as_index=False)
        .agg({"frequency": sum})
        .sort_values("frequency", ascending=False)
        .head(30)
        .to_dict("records")
    )
    save_file_joins_frequency(df_join_conditions)


def save_file_joins_frequency(df):
    csv_file_path = os.path.join("joins_frequency")  # os.getenv("DATA_DIR"), "parse_sql"
    # os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
    df.sort_values("frequency", ascending=False).to_csv(csv_file_path + "_raw.csv", index=False)

    df = df.assign(
        file_name=lambda _df: _df["file_name"].map(lambda x: x.split("_to_").pop()),
        join_condition=lambda _df: _df["join_condition"].str.lower(),

        left=lambda _df: _df["join_condition"].map(lambda join: join.split("=")[0].strip().lower()),
        left_table=lambda _df: _df["left"].map(lambda x: x.split(":")[0] if ":" in x else ""),
        left_col=lambda _df: _df["left"].map(lambda x: x.split(":")[1] if ":" in x else x),

        right=lambda _df: _df["join_condition"].map(lambda join: join.split("=")[1].strip().lower()),
        right_table=lambda _df: _df["right"].map(lambda x: x.split(":")[0] if ":" in x else ""),
        right_col=lambda _df: _df["right"].map(lambda x: x.split(":")[1] if ":" in x else x),
    ).where(
        # rm tmp tables
        lambda _df: _df["left_table"].str.contains(".", regex=False) &
                    _df["right_table"].str.contains(".", regex=False)
    )[["file_name", "left_table", "left_col", "right_table", "right_col", "frequency"]].dropna()

    df.sort_values("frequency", ascending=False).to_csv(csv_file_path + ".csv", index=False)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        dag_dir = Path(sys.argv[1])
    else:
        dag_dir = Path(os.getenv("WORK_DIR")) / "data-flow" / "dags"
    extract_join_from_all_files(dag_dir)
