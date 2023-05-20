import sqlfluff

from .cleaning import clean_sql_tree, first_not_null
from .node_formatters import formatters


def parse_raw_query(raw_query):
    parse = sqlfluff.parse(raw_query, dialect="bigquery")["file"]
    cleaned = clean_sql_tree(parse)
    return get(cleaned, ["statement"])


def reformat_node(key, node):
    if key in formatters:
        node = formatters[key](node)
    return node


def get(parsed_query, keys):
    if len(keys) == 0:
        return parsed_query
    key = keys[0]
    if isinstance(key, list):
        return first_not_null(get(parsed_query, [_key] + keys[1:]) for _key in key)

    if isinstance(parsed_query, dict):
        item = parsed_query.get(key, {})
        return reformat_node(key, get(item, keys[1:]))
    if isinstance(parsed_query, list):
        parsed_query = list(parsed_query)
        if len(parsed_query) == 0:
            return {}
        all_possible = [get(item, keys) for item in parsed_query]
        not_null = [x for x in all_possible if x]
        if len(not_null) == 1:
            return not_null[0]
        return not_null
    return None
