import json
import os.path
from typing import Dict, List

from .models import ColumnName, Query, TableId
from itertools import product
from collections import OrderedDict, Counter

bq_schema = None


def get_bq_schema_with_cols() -> Dict[TableId, List[ColumnName]]:
    """
    returns { "dataset.table_name": [col1, ..., coln] }
    """
    bq_schema_name = "bq_schema.json"
    if not os.path.exists(bq_schema_name):
        bq_schema_name = "../" + bq_schema_name

    with open(bq_schema_name, "r") as f:
        return {
            k: [c["name"] for c in table_infos["schema"]]
            for k, table_infos in json.load(f).items()
        }


# replace_alias_in_cte_query
def get_available_cols_names(cte_name: str, parsing_by_cte: Dict[str, Query]):
    """
    Return { col_name: table_id}
    eg : {'civilite': 'EFFY_STORE.clients', 'sous_type_travaux': 'EFFY_STORE.opportunites'}
    """
    cte_query = parsing_by_cte[cte_name]
    bq_schema = get_bq_schema_with_cols()

    # split tables in BQ & tables from cte in same file
    tables_alias: dict = cte_query["tables"]
    tables_from_bq = {
        table_alias: bq_schema[table_id]
        for table_alias, table_id in tables_alias.items()
        if table_id in bq_schema
    }
    # tables_from_cte = {"c": ["col1", ..., "coln"]}
    tables_from_cte = {
        table_alias: list(parsing_by_cte[table_id]["select"].keys())
        for table_alias, table_id in tables_alias.items()
        if table_id not in bq_schema
    }

    return {
        col: tables_alias[table_alias]
        for table_alias, columns in {**tables_from_bq, **tables_from_cte}.items()
        for col in columns
    }


def resolve_table_alias(table_alias, col_name, parsing_by_cte):
    global bq_schema
    if bq_schema is None:
        bq_schema = get_bq_schema_with_cols()

    if table_alias in bq_schema:
        return ":".join((table_alias, col_name))
    if table_alias not in parsing_by_cte:
        print("ERROR : Unable to find table alias", table_alias)
        return ""

    cte_query = parsing_by_cte[table_alias]
    select_cols = cte_query["select"]
    if col_name not in select_cols:
        print("ERROR : Unable to find", col_name, "in cte", table_alias)
        return ""
    col_source = select_cols[col_name].split(".")

    if len(col_source) == 2:
        # col_source = ["t", "type_cloture"]
        return resolve_table_alias(
            cte_query["tables"][col_source[0]], col_source[1], parsing_by_cte
        )
    if len(col_source) == 1:
        new_col_name = col_source[0]
        if new_col_name == "function()":
            return new_col_name

        available_cols = get_available_cols_names(
            cte_name=table_alias, parsing_by_cte=parsing_by_cte
        )
        if new_col_name in available_cols:
            print(f"  Guessing {table_alias}.{select_cols[col_name]}", "is from", available_cols[new_col_name])
            return ":".join((available_cols[new_col_name], new_col_name))

    print(f"  ERROR : Unable to resolve col {table_alias}.{col_name}")
    return ""


def extract_all_joins_from_file(parsing_by_cte_with_unions: Dict[str, List[Query]]) -> Counter:
    """
    parsing_by_cte = OrderedDict(
        cte_1=[{
            "select": {"col_1": "col_1"},
            "tables": {"table": "dataset.table"},
            "join": [],
        }, {
            "select": {"col_1": "col_1"},
            "tables": {"table": "dataset.table"},
            "join": [],
        }],
        __query__=[{
            "select": {"name_1": "col_1"},
            "tables": {"cte_1": "cte_1"},
            "join": [],
        }]
    ),
    """
    all_conditions = []
    cte_names = list(parsing_by_cte_with_unions.keys())
    queries_combinations = list(product(*list(parsing_by_cte_with_unions.values())))

    nb_combinations = len(queries_combinations)
    if nb_combinations > 30:
        raise Exception("Too many combinations in file. Skip")

    for queries in queries_combinations:
        parsing_by_cte = OrderedDict(zip(cte_names, queries))
        queries_conditions = extract_all_joins_from_query(parsing_by_cte)
        all_conditions.extend(queries_conditions)

    counter = Counter(all_conditions)
    return Counter({k: v / nb_combinations for k, v in counter.items()})


def extract_all_joins_from_query(parsing_by_cte: Dict[str, Query]):
    """
    parsing_by_cte = OrderedDict(
        cte_1={
            "select": {"col_1": "col_1"},
            "tables": {"table": "dataset.table"},
            "join": [],
        },
        __query__={
            "select": {"name_1": "col_1"},
            "tables": {"cte_1": "cte_1"},
            "join": [],
        }
    ),
    """
    all_conditions = []
    for cte_name, cte_query in parsing_by_cte.items():
        tables_alias = cte_query["tables"]

        for left_cond, right_cond in cte_query["join"]:
            if len(left_cond) != 2 or len(right_cond) != 2:
                print("ignoring condition", left_cond, right_cond)
                continue

            left_alias, left_col = left_cond
            left = resolve_table_alias(
                tables_alias[left_alias], left_col, parsing_by_cte
            )

            right_alias, right_col = right_cond
            right = resolve_table_alias(
                tables_alias[right_alias], right_col, parsing_by_cte
            )

            if left and right and left.lower() != right.lower():
                all_conditions.append(" = ".join(sorted([left, right], key=str.lower)))

    return all_conditions
