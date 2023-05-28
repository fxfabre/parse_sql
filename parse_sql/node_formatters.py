from typing import Dict, List

formatters = {}


def register_formatter(func):
    global formatters
    if func.__name__.startswith("format_"):
        node_name = func.__name__[7:]
    else:
        node_name = func.__name__

    formatters[node_name] = func
    return func


@register_formatter
def format_quoted_identifier(node):
    if isinstance(node, str):
        return node.strip("`")
    return node


@register_formatter
def format_table_reference(node):
    if isinstance(node, list):
        return ".".join(node)
    return node


@register_formatter
def format_from_expression(node) -> List[Dict]:
    """Fix for wrong parsing of ", UNNEST(...) instead of CROSS JOIN"""
    # Reformat node as list of dict, 1 key only per dict
    if isinstance(node, list):
        as_list = [
            x
            for item in node
            for x in format_from_expression(item)
        ]
    elif isinstance(node, dict):
        as_list = [{k: v} for k, v in node.items()]
    else:
        raise Exception(f"Unexpected type {type(node)} : {node}")

    # keep only one "from_expression_element" in dicts keys
    return_items = []
    has_from_expression_element = False
    for item in as_list:
        if not has_from_expression_element:
            return_items.append(item)
            has_from_expression_element = "from_expression_element" in item
        elif "from_expression_element" in item:
            return_items.extend(
                {"join_clause" if k == "from_expression_element" else k: v}
                for k, v in item.items()
            )
        else:
            return_items.append(item)
    return return_items


@register_formatter
def format_common_table_expression(node) -> List[List[Dict]]:
    """ Output format :
    [
        [
            {"naked_identifier": "cte_name_1"},
            {"keyword": "as"},
            {
                "bracketed": [
                    {"start_bracket": "("},
                    {"select_statement": {"select_clause": {...}},
                    {"end_bracket": ")"}
                ]
            }
        ],
        [
            {"naked_identifier": "cte_name_2"},
            {"keyword": "as"},
            {
                "bracketed": [
                    {"start_bracket": "("},
                    {"select_statement": { "select_clause": {...},
                    {"end_bracket": ")"}
                ]
            }
        ]
    ]
    """
    if len(node) == 0:
        return []
    return [node]


@register_formatter
def format_select_statement(node) -> List[Dict]:
    return [node]


@register_formatter
def format_select_clause_element(node):
    return [node] if isinstance(node, dict) and node else node
