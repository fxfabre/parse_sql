

def clean_sql_tree(sql_node):
    if isinstance(sql_node, list):
        cleaned = map(clean_sql_tree, sql_node)
        return agg_join_exp([x for x in cleaned if len(x) > 0])
    if isinstance(sql_node, dict):
        return {
            key: clean_sql_tree(value)
            for key, value in sql_node.items()
            if key not in ("whitespace", "newline", "comma", "block_comment", "inline_comment")
        }
    elif isinstance(sql_node, str):
        return sql_node.strip()
    else:
        raise Exception(f"Unknown type {type(sql_node)} : {sql_node}")


def agg_join_exp(items):
    """Transform [{'keyword': 'LEFT'}, {'keyword': 'JOIN'}] -> [{'keyword': 'LEFT JOIN'}]"""
    if len(items) <= 1:
        return items
    return_items = []
    previous = items[0]
    for i, current in enumerate(items[1:]):
        if (previous.get("keyword") in ["LEFT", "RIGHT", "CROSS", "INNER"]) and (
            current.get("keyword") == "JOIN"
        ):
            return_items.append(
                {"keyword": " ".join([previous.get("keyword"), current.get("keyword")])}
            )
            return return_items + list(items[i + 2 :])
        return_items.append(previous)
        previous = current
    return_items.append(previous)
    return return_items


def first_not_null(items):
    for item in items:
        if item:
            return item
    return None
