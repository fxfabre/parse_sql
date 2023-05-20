import logging
from typing import Dict
from unittest import TestCase

from parameterized import parameterized

from parse_sql.parsers import parse_sql_file

queries_select_from = [
    """SELECT col_1, table_alias.col_2 as n2, * FROM `project_id.dataset.table_name` table_alias""",
    """
        SELECT col_1,
            table_name.col_2 as n2
        FROM `dataset.table_name`
            As alias_table_name
    """,
    """
        SELECT
            *,
            custom_name.col_2 as n2
        FROM project_id.dataset.table_name AS custom_name
    """,
]
queries_cte = [
    """
    WITH cte_name as (select col_1 FROM dataset.table1),
    cte_2 as (select col_2, col_3 FROM dataset.t2 as t2
        join dataset.table t3 on t2.id = t3.t2_id)
    select col_1, col_2, col_3 FROM cte_name left join cte_2 on cte_name.col_1 = cte_2.col_3
    """
]

logging.getLogger("sqlfluff").setLevel(logging.WARNING)


class TestParseSql(TestCase):
    @parameterized.expand(
        [
            (
                queries_select_from[0],
                {"col_1": "col_1", "n2": "table_alias.col_2", "*": "*"},
            ),
            (queries_select_from[1], {"col_1": "col_1", "n2": "table_name.col_2"}),
            (queries_select_from[2], {"*": "*", "n2": "custom_name.col_2"}),
        ]
    )
    def test_select(self, query, expected):
        parsing_by_cte = parse_sql_file(query)
        actual = parsing_by_cte["__query__"]["select"]
        self.assertEqual(actual, expected)

    @parameterized.expand(
        [
            (queries_select_from[0], {"table_alias": "project_id.dataset.table_name"}),
            (queries_select_from[1], {"alias_table_name": "dataset.table_name"}),
            (queries_select_from[2], {"custom_name": "project_id.dataset.table_name"}),
        ]
    )
    def test_from_join(self, query, expected):
        parsing_by_cte = parse_sql_file(query)
        from_tables = parsing_by_cte["__query__"]["tables"]
        join_conditions = parsing_by_cte["__query__"]["join"]

        self.assertEqual(from_tables, expected)
        self.assertEqual(join_conditions, [])

    @parameterized.expand(
        [
            (
                queries_cte[0],
                {
                    "cte_name": {
                        "select": {"col_1": "col_1"},
                        "tables": {"table1": "dataset.table1"},
                    },
                    "cte_2": {
                        "select": {"col_2": "col_2", "col_3": "col_3"},
                        "tables": {"t2": "dataset.t2", "t3": "dataset.table"},
                        "join": [(["t2", "id"], ["t3", "t2_id"])],
                    },
                    "__query__": {
                        "select": {
                            "col_1": "col_1",
                            "col_2": "col_2",
                            "col_3": "col_3",
                        },
                        "tables": {"cte_name": "cte_name", "cte_2": "cte_2"},
                        "join": [(["cte_name", "col_1"], ["cte_2", "col_3"])],
                    },
                },
            ),
        ]
    )
    def test_parse_cte(self, query, expected: Dict):
        parsing_by_cte = parse_sql_file(query)
        self.assertEqual(list(parsing_by_cte.keys()), list(expected.keys()))
        for key, expected_in_cte in expected.items():
            parsed_in_cte = parsing_by_cte[key]
            self.assertEqual(parsed_in_cte.get("select"), expected_in_cte.get("select"))
            self.assertEqual(parsed_in_cte.get("tables"), expected_in_cte.get("tables"))
            self.assertEqual(parsed_in_cte.get("join"), expected_in_cte.get("join", []))
