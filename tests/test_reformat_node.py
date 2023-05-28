from unittest import TestCase

from parse_sql.parsing_tools import reformat_node


class TestReformatNode(TestCase):
    def test_from_expression(self):
        from_expression = [[{"k1": "v1", "k2": "v2"}], {"k3": "v3"}]
        expected = [
            {"k1": "v1"},
            {"k2": "v2"},
            {"k3": "v3"},
        ]
        self.assertEqual(
            reformat_node("from_expression", from_expression),
            expected
        )

    def test_from_expression_from_expression_element(self):
        from_expression = [
            [{"from_expression_element": "v1", "k2": "v2"}],
            {"from_expression_element": "v3"}
        ]
        expected = [
            {"from_expression_element": "v1"},
            {"k2": "v2"},
            {"join_clause": "v3"},
        ]
        self.assertEqual(
            reformat_node("from_expression", from_expression),
            expected
        )

    def test_format_select_statement_to_list(self):
        select_statement = {
            'from_clause': {
                'from_expression': {
                    'from_expression_element': {'table_expression': {'table_reference': [
                        {'naked_identifier': 'DW_DIABOLO'}, {'dot': '.'}, {'naked_identifier': 'agents_details_recording'}
                    ]}}
                },
                'keyword': 'from'
            },
            'groupby_clause': [
                {'keyword': 'group'}, {'keyword': 'by'}, {'numeric_literal': '1'}, {'numeric_literal': '2'}
            ],
            'select_clause': [
                {'keyword': 'SELECT'},
                {'select_clause_element': {'column_reference': {'naked_identifier': 'user_id'}}},
                {'select_clause_element': {
                    'alias_expression': {'keyword': 'as', 'naked_identifier': 'date'},
                    'function': {}
                }},
                {
                    'select_clause_element': {
                        'alias_expression': {'keyword': 'as', 'naked_identifier': 'duration'},
                        'function': {}
                    }
                }
            ]
        }

        self.assertEqual(
            reformat_node("select_statement", select_statement),
            [select_statement]
        )
