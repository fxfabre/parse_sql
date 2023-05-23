from collections import OrderedDict
from pathlib import Path
from typing import Dict, List
import logging

from .from_join import extract_from_join
from .parsing_tools import get, parse_raw_query

logger = logging.getLogger(__name__)


def pretty_print(json_content):
    import json
    print(json.dumps(json_content, indent=4))


def read_and_parse_sql_file(file_path_or_query: str):
    if isinstance(file_path_or_query, Path) or file_path_or_query.endswith(".sql"):
        query = Path(file_path_or_query).read_text()
    else:
        query = file_path_or_query

    file_nodes = parse_raw_query(query)

    with_statement = get(file_nodes, ["with_compound_statement"]) or file_nodes
    return parse_sql_file(with_statement)


def parse_sql_file(sql_nodes) -> OrderedDict:
    ctes = get(sql_nodes, ["common_table_expression"])

    parsing_by_cte = OrderedDict()
    for cte in ctes:
        cte_name, query_desc = parse_cte(cte)
        parsing_by_cte[cte_name] = query_desc

    parsing_by_cte["__query__"] = parse_query(sql_nodes)
    return parsing_by_cte


def parse_cte(cte):
    cte_name = get(cte, ["naked_identifier"])
    sql_nodes = get(cte, ["bracketed"])
    return cte_name, parse_query(sql_nodes)


def parse_query(sql_node) -> List[Dict]:
    set_expression = get(sql_node, ["set_expression"]) or sql_node

    return_statements = []
    for select_statement in get(set_expression, ["select_statement"]):
        source_tables, join_conditions = extract_from_join(select_statement)

        return_statements.append(
            {
                "select": extract_select(select_statement),
                "tables": source_tables,
                "join": join_conditions,
            }
        )

    return return_statements


def extract_select(select_node):
    """Extract columns in select"""
    columns = get(select_node, ["select_clause", "select_clause_element"])

    select_columns = {}
    for col in columns:
        col_name = (
            get(col, ["column_reference", "naked_identifier"])
            or get(col, ["wildcard_expression", "wildcard_identifier", "star"])
            or ("function()" if get(col, ["function"]) else "")
        )
        col_name = ".".join(col_name) if isinstance(col_name, list) else col_name

        col_alias = (
            get(col, ["alias_expression", "naked_identifier"])
            or col_name.split(".")[-1]
        )
        select_columns[col_alias] = col_name

    return select_columns
