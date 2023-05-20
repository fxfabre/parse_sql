from collections import OrderedDict
from pathlib import Path
from typing import Dict

from .from_join import extract_from_join
from .parsing_tools import get, parse_raw_query


def parse_sql_file(file_path_or_query: str):
    if file_path_or_query.endswith(".sql"):
        query = Path(file_path_or_query).read_text()
    else:
        query = file_path_or_query

    sql_nodes = parse_raw_query(query)

    ctes = get(sql_nodes, ["with_compound_statement", "common_table_expression"])
    select = get(sql_nodes, ["with_compound_statement", "select_statement"]) or get(
        sql_nodes, ["select_statement"]
    )

    parsing_by_cte = OrderedDict()
    for cte in ctes:
        cte_name, query_desc = parse_cte(cte)
        parsing_by_cte[cte_name] = query_desc

    parsing_by_cte["__query__"] = parse_query(select)
    return parsing_by_cte


def parse_select(query: str) -> Dict[str, str]:
    """
    Return {column_alias_name : [table_name.]column_name}
    """
    root_node = parse_raw_query(query)
    select_node = get(root_node, ["select_statement"])
    return extract_select(select_node)


def extract_select(select_node):
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


def parse_from_join(query):
    root_node = parse_raw_query(query)
    select_node = get(root_node, ["select_statement"])
    return extract_from_join(select_node)


def parse_cte(cte):
    sql_nodes = get(cte, ["bracketed"])
    cte_name = get(cte, ["naked_identifier"])

    sql_nodes = get(sql_nodes, ["select_statement"])
    source_tables, join_conditions = extract_from_join(sql_nodes)

    return cte_name, {
        "select": extract_select(sql_nodes),
        "tables": source_tables,
        "join": join_conditions,
    }


def parse_query(sql_node):
    source_tables, join_conditions = extract_from_join(sql_node)

    return {
        "select": extract_select(sql_node),
        "tables": source_tables,
        "join": join_conditions,
    }
