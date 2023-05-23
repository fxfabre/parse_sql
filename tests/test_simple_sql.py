import json
import logging
from collections import OrderedDict
from pathlib import Path
from unittest import TestCase

from parameterized import parameterized

from parse_sql.parsers import read_and_parse_sql_file

logging.getLogger("sqlfluff").setLevel(logging.WARNING)


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


queries = {
    "query_groupby.sql": OrderedDict(
        __query__=[{
            "join": [],
            "select": {
                "campaign_id": "campaign_id",
                "campaign_name": "campaign_name",
                "date": "function()",
                "duration": "function()",
                "status_id": "status_id",
                "status_name": "status_name",
                "user_id": "user_id",
                "user_name": "user_name",
            },
            "tables": {"agents_details_recording": "DW_DIABOLO.agents_details_recording"},
        }]
    ),
    "query_groupby_2.sql": OrderedDict(
        __query__=[{
            "join": [],
            "select": {
                "callType": "callType",
                "displayedNumber": "displayedNumber",
                "mois": "function()",
                "nb_calls": "function()",
                "nb_repondeurs": "function()",
            },
            "tables": {"calls_details_recording": "DW_DIABOLO.calls_details_recording"},
        }]
    ),
    "query_join.sql": OrderedDict(
        __query__=[{
                "join": [(["table1", "c1"], ["table2", "c2"])],
                "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
                "tables": {"table": "dataset_1.table", "table2": "dataset_2.table2"},
            }]
    ),
    "query_join_2.sql": OrderedDict(
        __query__=[{
            "join": [
                (["ab", "chantier_id"], ["c", "id"]),
                (["f", "PES_Chantier__c"], ["c", "id"]),
                (["p", "Facture__c"], ["f", "id"]),
                (["t", "Dossier__c"], ["c", "id"]),
                (["a", "id"], ["c", "PES_Compte_associe__c"]),
                (["o", "id"], ["t", "IdOpportuniteSherlock__c"]),
                (["o", "solution_id"], ["s", "id"]),
                (["s", "vulcain_type_travaux_id"], ["tt", "id"]),
                (["devis_post_vt_envoye", "PES_Chantier__c"], ["c", "id"]),
                (["devis_post_vt_signe", "PES_Chantier__c"], ["c", "id"]),
            ],
            "select": {
                "chantier_devis_montant": "function()",
                "chantier_id": "c.id",
                "chantier_statut": "c.PES_Statut_Chantier__c",
                "chantier_vt_date_commande": "c.Date_de_la_commande_VT__c",
                "chantier_vt_date_realisation": "c.PES_Date_Visite_Technique__c",
            },
            "tables": {
                "a": "DW_SALESFORCE_PES.account",
                "ab": "DW_SALESFORCE_PES.chantier_history_abandon_iso_chauffage",
                "c": "DW_SALESFORCE_PES.pes_chantier",
                "devis_post_vt_envoye": "chantier_isolation_devis_post_vt_envoye",
                "devis_post_vt_signe": "chantier_isolation_devis_post_vt_signe",
                "f": "DW_SALESFORCE_PES.pes_facture",
                "o": "DW_SHERLOCK.opportunites",
                "p": "DW_SALESFORCE_PES.pes_paiement",
                "s": "DW_SHERLOCK.solutions",
                "t": "DW_SALESFORCE_PES.temoin",
                "tt": "DW_VULCAIN.types_travaux",
            },
        }]
    ),
    "query_join_alias.sql": OrderedDict(
        __query__=[{
            "join": [(["table1", "c1"], ["table2", "c2"])],
            "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
            "tables": {"alias_T1": "dataset_1.table", "table2": "dataset_2.table2"},
        }]
    ),
    "query_join_alias_2.sql": OrderedDict(
        __query__=[{
            "join": [(["table1", "c1"], ["table2", "c2"])],
            "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
            "tables": {"alias_T1": "dataset_1.table", "table2": "dataset_2.table2"},
        }]
    ),
    "query_where.sql": OrderedDict(
        __query__=[{
            "join": [],
            "select": {"*": "*"},
            "tables": {"agents_details_recording": "DW_DIABOLO.agents_details_recording"},
        }]
    ),
}


class TestParseSimpleSql(TestCase):
    @parameterized.expand(
        [
            (
                queries_select_from[0],
                [{"col_1": "col_1", "n2": "table_alias.col_2", "*": "*"}],
            ),
            (queries_select_from[1], [{"col_1": "col_1", "n2": "table_name.col_2"}]),
            (queries_select_from[2], [{"*": "*", "n2": "custom_name.col_2"}]),
        ]
    )
    def test_select(self, query, expected):
        parsing_by_cte = read_and_parse_sql_file(query)
        actual = [x["select"] for x in parsing_by_cte["__query__"]]
        self.assertEqual(actual, expected)

    @parameterized.expand(
        [
            (queries_select_from[0], [{"table_alias": "project_id.dataset.table_name"}]),
            (queries_select_from[1], [{"alias_table_name": "dataset.table_name"}]),
            (queries_select_from[2], [{"custom_name": "project_id.dataset.table_name"}]),
        ]
    )
    def test_from_join(self, query, expected):
        parsing_by_cte = read_and_parse_sql_file(query)
        from_tables = [x["tables"] for x in parsing_by_cte["__query__"]]
        join_conditions = [x['join'] for x in parsing_by_cte["__query__"]]

        self.assertEqual(from_tables, expected)
        self.assertEqual(join_conditions, [[]])

    @parameterized.expand(queries.items())
    def test_join_group_by(self, file_name, expected):
        file_path = Path("tests/sql_test_files") / file_name
        parsing_by_cte = read_and_parse_sql_file(file_path.read_text())
        # from pprint import pprint
        # pprint(parsing_by_cte)
        # pprint(expected)
        self.assertEqual(parsing_by_cte, expected, json.dumps(parsing_by_cte, indent=4))
