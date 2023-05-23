from .parsing_tools import get


def extract_from_join(sql_nodes):
    """Root node : "from_clause" """
    tables_from_join = get(sql_nodes, ["from_clause", "from_expression"])

    all_from_tables = {}
    all_join_conditions = []
    for table_def in tables_from_join:
        table_exp = get(table_def, ["join_clause"]) or table_def
        table_from, table_alias = read_table_ids(table_exp)

        if isinstance(table_alias, list):
            # File has implicit cross join, with ", unnest(...)"
            # Should raise an error, parsing is incomplete
            for _table_from, _table_alias in zip(table_from, table_alias):
                all_from_tables[_table_alias] = _table_from
        else:
            all_from_tables[table_alias] = table_from

        join_exp = get(table_exp, ["join_on_condition", "expression"])
        all_join_conditions.extend(parse_join_condition(join_exp))

    all_join_conditions = [x for x in all_join_conditions if len(x) > 1]

    return all_from_tables, all_join_conditions


def parse_join_condition(join_condition):
    blocs_join = (
        bloc for bloc in split_join_operator_and(join_condition) if len(bloc) > 0
    )

    for bloc in blocs_join:
        cols_eq = []
        for column_reference in bloc:
            if "column_reference" in column_reference:
                cols_eq.append(
                    get(
                        column_reference,
                        ["column_reference", ["quoted_identifier", "naked_identifier"]],
                    )
                )
            elif (
                "quoted_literal" in column_reference
                or "numeric_literal" in column_reference
            ):
                """Column equals to a string or value : skip it, not useful for us for now"""
                cols_eq = []
            elif "binary_operator" in column_reference:
                yield tuple(cols_eq)
                cols_eq = []
        if len(cols_eq) > 0:
            yield tuple(cols_eq)


def split_join_operator_and(join_condition):
    join_group = []
    for column_reference in join_condition:
        if "binary_operator" in column_reference:
            yield join_group
            join_group = []
        else:
            join_group.append(column_reference)
    yield join_group


def read_table_ids(table_exp):
    table_name = get(
        table_exp,
        [
            "from_expression_element",
            "table_expression",
            "table_reference",
            ["quoted_identifier", "naked_identifier"],
        ],
    )
    table_alias = get(
        table_exp,
        [
            "from_expression_element",
            "alias_expression",
            ["quoted_identifier", "naked_identifier"],
        ],
    )

    if not table_alias:
        table_alias = table_name.split(".").pop()

    return table_name, table_alias
