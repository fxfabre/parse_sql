import json
import logging
from collections import OrderedDict
from typing import Dict
from unittest import TestCase

import pytest
from parameterized import parameterized

from parse_sql.parsers import read_and_parse_sql_file

logging.getLogger("sqlfluff").setLevel(logging.WARNING)


union_all = {
    "tests/sql_test_files/b2c_demandes.sql": OrderedDict(
        existing_business_tmp=[{
            "join": [
                (["opp", "piste_id"], ["piste", "id"]),
                (["sol", "id"], ["opp", "solution_id"]),
                (["client", "api_user_id"], ["piste", "api_user_id"]),
            ],
            "select": {
                "email": "function()",
                "piste_created_at": "function()",
                "piste_with_opportunite_gagnee": "function()",
            },
            "tables": {
                "client": "EFFY_STORE.clients",
                "opp": "EFFY_STORE.opportunites",
                "piste": "EFFY_STORE.pistes",
                "sol": "EFFY_STORE.solutions",
            },
        }],
        deals_demande_prospect_tmp=[{
            "join": [
                (["piste", "id"], ["opportunites", "piste_id"]),
                (["opportunites", "solution_id"], ["solutions", "id"]),
                (["piste", "id"], ["stocks", "piste_id"]),
            ],
            "select": {
                "max_diabolo_date_piste_is_removed_from_stock": "function()",
                "nb_opp_gagnee": "function()",
                "piste_id": "piste.id",
            },
            "tables": {
                "opportunites": "EFFY_STORE.opportunites",
                "piste": "EFFY_STORE.pistes",
                "solutions": "EFFY_STORE.solutions",
                "stocks": "EFFY_STORE.stocks",
            },
        }],
        piste_last_campagne=[{
            "join": [
                (["contact", "piste_id"], ["p", "id"]),
                (["campagne", "diabolo_id"], ["contact", "campagne_id"]),
            ],
            "select": {
                "last_diabolo_camp": "function()",
                "last_sherlock_camp": "function()",
                "piste_id": "p.id",
            },
            "tables": {
                "campagne": "EFFY_STORE.campagnes",
                "contact": "EFFY_STORE.contacts",
                "p": "EFFY_STORE.pistes",
            },
        }],
        piste_appelee=[{
            "join": [
                (["contact", "piste_id"], ["piste", "id"]),
                (["campagne", "diabolo_id"], ["contact", "campagne_id"]),
                (["calls", "diabolo_contact_id"], ["contact", "id"]),
                (["calls", "campagne_id"], ["campagne", "diabolo_id"]),
                (["calls", "id"], ["wrapup", "appel_id"]),
            ],
            "select": {"nb_appel": "function()", "piste_id": "piste.id"},
            "tables": {
                "calls": "EFFY_STORE.appels",
                "campagne": "EFFY_STORE.campagnes",
                "contact": "EFFY_STORE.contacts",
                "piste": "EFFY_STORE.pistes",
                "wrapup": "EFFY_STORE.appels_codes_cloture",
            },
        }],
        selfcare_dossier_non_cree=[{
            "join": [(["opp", "piste_id"], ["p", "id"])],
            "select": {"nb_opp_gagnee": "function()", "piste_id": "p.id"},
            "tables": {"opp": "EFFY_STORE.opportunites", "p": "EFFY_STORE.pistes"},
        }],
        airbnb_non_eligible=[{
            "join": [
                (["lcs", "piste_id"], ["piste", "id"]),
                (["sdne", "piste_id"], ["piste", "id"]),
                (["pa", "piste_id"], ["piste", "id"]),
            ],
            "select": {"est_airbnb_non_eligible": "function()", "piste_id": "piste.id"},
            "tables": {
                "lcs": "piste_last_campagne",
                "pa": "piste_appelee",
                "piste": "EFFY_STORE.pistes",
                "sdne": "selfcare_dossier_non_cree",
            },
        }],
        last_wrapup_name_by_piste=[{
            "join": [
                (["a", "diabolo_contact_id"], ["c", "id"]),
                (["a", "campagne_id"], ["c", "campagne_id"]),
                (["a", "id"], ["wrapup", "appel_id"]),
            ],
            "select": {"last_wrapup_name": "function()", "piste_id": "c.piste_id"},
            "tables": {
                "a": "EFFY_STORE.appels",
                "c": "EFFY_STORE.contacts",
                "wrapup": "EFFY_STORE.appels_codes_cloture",
            },
        }],
        deals_demande_prospects=[{
            "join": [
                (["ddp", "piste_id"], ["piste", "id"]),
                (["piste", "id"], ["contact", "piste_id"]),
                (["piste", "api_user_id"], ["client", "api_user_id"]),
                (["eb", "email"], ["client", "email"]),
                (["wrapup", "piste_id"], ["piste", "id"]),
            ],
            "select": {
                "contact_effy_uid": "piste.api_user_id",
                "deals_close_lost_reason": "function()",
                "deals_close_won_reason": "function()",
                "deals_closed_at": "",
                "deals_type": "",
                "deals_updated_at": "function()",
                "piste_id": "piste.id",
            },
            "tables": {
                "client": "EFFY_STORE.clients",
                "contact": "EFFY_STORE.contacts",
                "ddp": "deals_demande_prospect_tmp",
                "eb": "existing_business_tmp",
                "piste": "EFFY_STORE.pistes",
                "wrapup": "last_wrapup_name_by_piste",
            },
        }],
        deals_transfo_non_intentionniste=[{
            "join": [
                (["ddp", "piste_id"], ["piste", "id"]),
                (["contact", "piste_id"], ["piste", "id"]),
                (["piste", "api_user_id"], ["client", "api_user_id"]),
                (["eb", "email"], ["client", "email"]),
                (["deals", "deals_custom_id"], ["piste", "id"]),
                (["wrapup", "piste_id"], ["piste", "id"]),
            ],
            "select": {
                "contact_effy_uid": "piste.api_user_id",
                "deals_close_lost_reason": "function()",
                "deals_close_won_reason": "function()",
                "deals_closed_at": "",
                "deals_custom_id": "function()",
                "deals_name": "piste.utm_funnel",
                "deals_piste_est_selfcare": "piste.is_selfcare",
                "deals_type": "",
                "deals_updated_at": "function()",
                "piste_id": "piste.id",
            },
            "tables": {
                "client": "EFFY_STORE.clients",
                "contact": "EFFY_STORE.contacts",
                "ddp": "deals_demande_prospect_tmp",
                "deals": "DW_HUBSPOT.deals",
                "eb": "existing_business_tmp",
                "piste": "EFFY_STORE.pistes",
                "wrapup": "last_wrapup_name_by_piste",
            },
        }],
        join_prospect_intentionistes___1=[
            {"join": [], "select": {}, "tables": {}},
            {"join": [], "select": {}, "tables": {}}
        ],
        __query__=[{
            "join": [
                (["join_all", "contact_effy_uid"], ["c", "contact_effy_uid"]),
                (["piste", "id"], ["join_all", "piste_id"]),
                (["acco", "accommodations_id"], ["piste", "accommodations_id"]),
                (["piste", "id"], ["sdne", "piste_id"]),
                (["piste", "id"], ["airbnb_non_eligible", "piste_id"]),
            ],
            "select": {
                "contact_city": "c.contact_city",
                "contact_civility": "c.contact_civility",
                "contact_created_at": "c.contact_created_at",
                "contact_creation_date": "c.contact_creation_date",
                "contact_departement": "c.contact_departement",
                "contact_effy_uid": "c.contact_effy_uid",
                "contact_email": "c.contact_email",
                "contact_email_optout_newsletter": "c.contact_email_optout_newsletter",
                "contact_first_name": "c.contact_first_name",
                "contact_is_optout_from_commerce": "c.contact_is_optout_from_commerce",
                "contact_is_ouvreur_np6": "c.contact_is_ouvreur_np6",
                "contact_last_activity": "c.contact_last_activity",
                "contact_last_form_submission": "c.contact_last_form_submission",
                "contact_last_modified_at": "c.contact_last_modified_at",
                "contact_last_modified_date": "c.contact_last_modified_date",
                "contact_last_name": "c.contact_last_name",
                "contact_lite_consent": "c.contact_lite_consent",
                "contact_mobile_phone_number": "c.contact_mobile_phone_number",
                "contact_phone_number": "c.contact_phone_number",
                "contact_precarity_level": "c.contact_precarity_level",
                "contact_site_source": "c.contact_site_source",
                "contact_zip_code": "c.contact_zip_code",
                "deal_pipeline": "",
                "deals_amount": "",
                "deals_chantier_devis_date_envoi": "function()",
                "deals_chantier_devis_date_signature": "function()",
                "deals_chantier_facture_date_envoi": "function()",
                "deals_chantier_facture_date_reglement": "function()",
                "deals_chantier_travaux_date_commande": "function()",
                "deals_chantier_travaux_date_previsionnel": "function()",
                "deals_chantier_travaux_date_realisation": "function()",
                "deals_chantier_vt_date_commande": "function()",
                "deals_chantier_vt_date_realisation": "function()",
                "deals_close_lost_reason": "join_all.deals_close_lost_reason",
                "deals_close_won_reason": "join_all.deals_close_won_reason",
                "deals_closed_date": "function()",
                "deals_create_date": "function()",
                "deals_created_at": "join_all.deals_created_at",
                "deals_custom_id": "join_all.deals_custom_id",
                "deals_est_activite_chauffage": "function()",
                "deals_est_activite_fenetres": "function()",
                "deals_est_activite_isolation": "function()",
                "deals_est_activite_solaire": "function()",
                "deals_est_liberte": "function()",
                "deals_est_serenite": "function()",
                "deals_name": "piste.utm_funnel",
                "deals_operation_code": "function()",
                "deals_piste_adresse_chantier": "acco.adress_line",
                "deals_piste_code_postal_chantier": "acco.adress_postal_code",
                "deals_piste_confirmed_at": "piste.confirmee_a",
                "deals_piste_departement_chantier": "function()",
                "deals_piste_est_airbnb_non_eligible": "airbnb_non_eligible.est_airbnb_non_eligible",
                "deals_piste_est_argumente": "function()",
                "deals_piste_est_selfcare": "function()",
                "deals_piste_est_selfcare_mer": "function()",
                "deals_piste_id": "piste.id",
                "deals_piste_is_prio": "",
                "deals_piste_parcours": "piste.utm_funnel",
                "deals_piste_selfcare_dossier_est_cree": "",
                "deals_piste_source": "piste.source",
                "deals_piste_statut_occupant": "acco.occupant_status",
                "deals_piste_surface_habitable": "function()",
                "deals_piste_systeme_chauffage": "heating_systems.label",
                "deals_piste_type_energie_chauffage_existant": "het.label",
                "deals_piste_type_logement": "acco.accommodations_type",
                "deals_piste_ville_chantier": "acco.adress_city",
                "deals_prime_a_remonte_son_devis": "function()",
                "deals_prime_ah_date_envoi": "function()",
                "deals_prime_avis_impot_date_envoi": "function()",
                "deals_prime_date_engagement": "function()",
                "deals_prime_date_facture": "function()",
                "deals_prime_date_paiement": "function()",
                "deals_prime_devis_date_envoi": "function()",
                "deals_prime_dossier_complet_date_envoi": "function()",
                "deals_prime_facture_date_envoi": "function()",
                "deals_prime_gere_par_le_pro": "function()",
                "deals_prime_has_discount_on_quotation": "function()",
                "deals_prime_manda_pro_date_envoi": "function()",
                "deals_prime_siret_pro": "function()",
                "deals_prime_type": "function()",
                "deals_source_status": "function()",
                "deals_stage": "",
                "deals_type": "join_all.deals_type",
                "deals_type_offre": "",
                "deals_update_date": "function()",
                "deals_updated_at": "join_all.deals_updated_at",
                "deals_works_type": "piste.type_travaux_demande",
            },
            "tables": {
                "acco": "DW_RCU.accommodations",
                "airbnb_non_eligible": "airbnb_non_eligible",
                "c": "DM_MARKETING_AUTOMATION_B2C.contacts",
                "heating_systems": "DW_RCU.existing_heating_systems",
                "het": "DW_RCU.heating_energies_types",
                "join_all": "join_prospect_intentionistes",
                "piste": "EFFY_STORE.pistes",
                "sdne": "selfcare_dossier_non_cree",
            },
        }],
    ),
    """
        SELECT col_1
        FROM dataset.table

        UNION ALL

        SELECT col_1
        FROM dataset.table
    """: OrderedDict(),
}

ctes = {
    "tests/sql_test_files/query_cte.sql_2": OrderedDict(
        call_tmp=[{
            "select": {
                "call_date": "function()",
                "call_id": "a.id",
                "code_cloture": "ac.code_cloture_nom",
                "contact_phone": "function()",
                "date_debut": "a.date_debut",
                "duree": "a.duree",
                "is_last_call_day": "function()",
                "nom_file": "a.queue_nom",
                "nom_service": "a.service_nom",
                "resultat_appel": "a.resultat",
                "service_telephone": "a.service_telephone",
                "type_cloture": "ac.code_cloture_statut",
            },
            "tables": {"a": "EFFY_STORE.appels", "ac": "EFFY_STORE.appels_codes_cloture"},
            "join": [
                (["a", "id"], ["ac", "appel_id"])
            ],
        }],
        call_temoins=[{
            "select": {
                "call_date": "ct.call_date",
                "call_id": "ct.call_id",
                "code_cloture": "ct.code_cloture",
                "contact_phone": "ct.contact_phone",
                "date_debut": "ct.date_debut",
                "duree": "ct.duree",
                "nom_file": "ct.nom_file",
                "nom_service": "ct.nom_service",
                "opportunite_gagnee_chaudiere": "o.opportunite_gagnee_chaudiere",
                "opportunite_gagnee_combles": "o.opportunite_gagnee_combles",
                "opportunite_gagnee_iso_1e": "o.opportunite_gagnee_iso_1e",
                "opportunite_gagnee_iso_rac": "o.opportunite_gagnee_iso_rac",
                "opportunite_gagnee_ite": "o.opportunite_gagnee_ite",
                "opportunite_gagnee_mer": "o.opportunite_gagnee_mer",
                "opportunite_gagnee_pac": "o.opportunite_gagnee_pac",
                "opportunite_gagnee_pac_air_air": "o.opportunite_gagnee_pac_air_air",
                "opportunite_gagnee_prime_seule": "o.opportunite_gagnee_prime_seule",
                "opportunite_gagnee_rampants": "o.opportunite_gagnee_rampants",
                "opportunite_gagnee_recrutement_pro": "o.opportunite_gagnee_recrutement_pro",
                "opportunite_gagnee_solaire": "o.opportunite_gagnee_solaire",
                "opportunite_gagnee_sols": "o.opportunite_gagnee_sols",
                "piste_id": "p.id",
                "resultat_appel": "ct.resultat_appel",
                "service_telephone": "ct.service_telephone",
                "type_cloture": "ct.type_cloture",
            },
            "tables": {
                "c": "EFFY_STORE.clients",
                "ct": "call_tmp",
                "o": "EFFY_STORE.opportunites",
                "p": "EFFY_STORE.pistes",
            },
            "join": [
                (["ct", "contact_phone"], ["c", "telephone1"]),
                (["p", "api_user_id"], ["c", "api_user_id"]),
                (["o", "piste_id"], ["p", "id"]),
            ],
        }],
        __query__=[{
            "select": {
                "Nom_Service": "t.Nom_Service",
                "call_date": "t.call_date",
                "code_cloture": "t.code_cloture",
                "nb_calls": "function()",
                "nb_pistes_creees": "function()",
                "nb_temoin_chaudiere": "function()",
                "nb_temoin_combles": "function()",
                "nb_temoin_iso1e": "function()",
                "nb_temoin_isorac": "function()",
                "nb_temoin_ite": "function()",
                "nb_temoin_mer": "function()",
                "nb_temoin_pac": "function()",
                "nb_temoin_pacaa": "function()",
                "nb_temoin_prime_seule": "function()",
                "nb_temoin_rampants": "function()",
                "nb_temoin_solaire": "function()",
                "nb_temoin_sols": "function()",
                "nom_file": "t.nom_file",
                "resultat_appel": "t.resultat_appel",
                "service_telephone": "t.service_telephone",
                "sum_duree_call": "function()",
                "type_cloture": "t.type_cloture",
            },
            "tables": {"t": "call_temoins"},
            "join": [],
        }],
    ),
    "tests/sql_test_files/query_cte.sql_1": OrderedDict(
        cte_name=[{
            "select": {"col_1": "col_1"},
            "tables": {"table1": "dataset.table1"},
        }],
        cte_2=[{
            "select": {"col_2": "col_2", "col_3": "col_3"},
            "tables": {"t2": "dataset.t2", "t3": "dataset.table"},
            "join": [(["t2", "id"], ["t3", "t2_id"])],
        }],
        __query__=[{
            "select": {
                "col_1": "col_1",
                "col_2": "col_2",
                "col_3": "col_3",
            },
            "tables": {"cte_name": "cte_name", "cte_2": "cte_2"},
            "join": [(["cte_name", "col_1"], ["cte_2", "col_3"])],
        }],
    ),
}

unnest_queries = {
    "tests/sql_test_files/appel_code_cloture.sql": OrderedDict(
        __query__=[{
            'select': {
                'code_cloture_id': 'function()',
                'appel_id': 'callId',
                'operateur_id': 'o.id',
                'agent_id': 'function()',
                'agent_nom': 'function()',
                'user_groupe_ids': 'function()',
                'user_groupe_noms': 'function()',
                'code_cloture_statut': 'function()',
                'code_cloture_path': 'function()',
                'code_cloture_nom': 'function()',
                'code_cloture_comment': 'function()',
                'duree': 'function()',
                'cree_a': 'function()'
            },
            'tables': {
                'cdr': 'DW_DIABOLO.calls_details_recording',
                'u': 'DW_DIABOLO.public_users',
                'o': 'DW_SHERLOCK.operateurs',
                # "wrapups": "UNNEST(...)"
            },
            'join': [
                (["cdr", "callWrapups_agentId"], ["u", "id"]),
                (["u", "email"], ["o", "email"]),
            ]
        }]
    )
}


class TestEachSql(TestCase):
    @parameterized.expand(ctes.items())
    def test_parse_cte(self, query, expected: Dict):
        pytest.skip()
        parsing_by_cte = read_and_parse_sql_file(query)
        # from pprint import pprint
        # pprint(parsing_by_cte)
        # pprint(expected)
        self.assertEqual(parsing_by_cte, expected, json.dumps(parsing_by_cte, indent=4))

    @parameterized.expand(union_all.items())
    def test_union_all(self, file_path, expected):
        pytest.skip()
        parsing_by_cte = read_and_parse_sql_file(file_path)
        # from pprint import pprint
        # pprint(parsing_by_cte)
        # pprint(expected)
        self.assertEqual(parsing_by_cte, expected, json.dumps(parsing_by_cte, indent=4))
