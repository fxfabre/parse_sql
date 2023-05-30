import json
from collections import OrderedDict
from unittest import TestCase

from parameterized import parameterized

from parse_sql.parsers import read_and_parse_sql_file

queries = {
    "tests/basic_queries/select_1.sql": OrderedDict(
        __query__=[{
            "select": {"col_1": "col_1", "n2": "table_alias.col_2", "*": "*"},
            "tables": {"table_alias": "project_id.dataset.table_name"},
            "join": [],
        }]
    ),
    "tests/basic_queries/select_2.sql": OrderedDict(
        __query__=[{
            "select": {"col_1": "col_1", "n2": "table_name.col_2"},
            "tables": {"alias_table_name": "dataset.table_name"},
            "join": [],
        }]
    ),
    "tests/basic_queries/select_3.sql": OrderedDict(
        __query__=[{
            "select": {"*": "*", "n2": "custom_name.col_2"},
            "tables": {"custom_name": "project_id.dataset.table_name"},
            "join": [],
        }]
    ),
    "tests/basic_queries/query_groupby.sql": OrderedDict(
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
    "tests/basic_queries/query_groupby_2.sql": OrderedDict(
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
    "tests/basic_queries/query_join.sql": OrderedDict(
        __query__=[{
                "join": [(["table1", "c1"], ["table2", "c2"])],
                "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
                "tables": {"table": "dataset_1.table", "table2": "dataset_2.table2"},
            }]
    ),
    "tests/basic_queries/query_join_2.sql": OrderedDict(
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
    "tests/basic_queries/query_join_alias.sql": OrderedDict(
        __query__=[{
            "join": [(["table1", "c1"], ["table2", "c2"])],
            "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
            "tables": {"alias_T1": "dataset_1.table", "table2": "dataset_2.table2"},
        }]
    ),
    "tests/basic_queries/query_join_alias_2.sql": OrderedDict(
        __query__=[{
            "join": [(["table1", "c1"], ["table2", "c2"])],
            "select": {"*": "*", "col_1": "col_1", "name_2": "col_2"},
            "tables": {"alias_T1": "dataset_1.table", "table2": "dataset_2.table2"},
        }]
    ),
    "tests/basic_queries/query_where.sql": OrderedDict(
        __query__=[{
            "join": [],
            "select": {"*": "*"},
            "tables": {"agents_details_recording": "DW_DIABOLO.agents_details_recording"},
        }]
    ),
}


class TestParseBasicSql(TestCase):
    @parameterized.expand(queries.items())
    def test_basic_queries(self, file_name, expected):
        parsing_by_cte = read_and_parse_sql_file(file_name)
        self.assertEqual(parsing_by_cte, expected, json.dumps(parsing_by_cte, indent=4))
