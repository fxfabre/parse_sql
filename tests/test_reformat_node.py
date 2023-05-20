from unittest import TestCase

from parse_sql.parsing_tools import reformat_node
# from_expression_element


class TestReformatNode(TestCase):
    def test_from_expression(self):
        from_expression = [[{"k1": "v1", "k2": "v2"}], {"k3": "v3"}]
        expected = [
            {"k1": "v1"},
            {"k2": "v2"},
            {"k3": "v3"},
        ]
        self.assertEqual(reformat_node("from_expression", from_expression), expected)

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
        self.assertEqual(reformat_node("from_expression", from_expression), expected)
