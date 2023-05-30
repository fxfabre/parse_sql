CREATE TEMP FUNCTION PARSE_BOOL(x ANY TYPE) AS (
    CASE
        WHEN LOWER(x) IN ("true", "vrai") THEN TRUE
        WHEN LOWER(x) IN ("false", "faux") THEN FALSE
        ELSE SAFE_CAST(x AS bool)
    END
);
CREATE TEMP FUNCTION OFFRE_ID(offre_name string) AS (
    CASE offre_name
        WHEN "prime" THEN "d24249b9-fa85-445d-8cc0-9f3fb6b35618"
        WHEN "transfert" THEN "695e6e4c-c52f-4e6a-a25c-714117fce302"
        WHEN "serenite" THEN "f81bca91-6cce-492e-bab1-8bbf3701d5b2"
        WHEN "solaire" THEN "9cceb31a-904c-44df-9f04-8afaf3428030"
        WHEN "liberte" THEN "31b00bc0-8d82-4cbb-b495-e54556271586"
        WHEN "data" THEN "3c9db016-92ab-47ce-bfa2-baa6058b6056"
    END
);

WITH

existing_business_tmp AS (
    SELECT
        LOWER(client.email)                 AS email,
        MIN(piste.created_at)               AS piste_created_at,
        MAX(
            CASE
                WHEN opp.opportunite_gagnee IS NOT NULL
                    AND (
                        sol.offre_id != OFFRE_ID("prime")
                        OR opp.opportunite_gagnee_prime_seule IS NOT NULL
                    )
                    THEN piste.id
            END
        )                                   AS piste_with_opportunite_gagnee
    FROM EFFY_STORE.pistes AS piste
    LEFT JOIN EFFY_STORE.opportunites AS opp    ON opp.piste_id = piste.id
    LEFT JOIN EFFY_STORE.solutions AS sol       ON sol.id = opp.solution_id
    LEFT JOIN EFFY_STORE.clients AS client      ON client.api_user_id = piste.api_user_id
    GROUP BY 1
),

deals_demande_prospect_tmp AS (
    SELECT
        piste.id                                            AS piste_id,
        COUNT(DISTINCT CASE
            WHEN opportunites.opportunite_gagnee IS NOT NULL
                AND (
                    solutions.offre_id != OFFRE_ID("prime")
                    OR opportunites.opportunite_gagnee_prime_seule IS NOT NULL
                )
                THEN opportunites.opportunite_gagnee
            END
        )                                                   AS nb_opp_gagnee,
        MAX(stocks.date_sortie_stock)                       AS max_diabolo_date_piste_is_removed_from_stock
    FROM EFFY_STORE.pistes AS piste
    LEFT JOIN EFFY_STORE.opportunites      ON piste.id = opportunites.piste_id
    LEFT JOIN EFFY_STORE.solutions         ON opportunites.solution_id = solutions.id
    LEFT JOIN EFFY_STORE.stocks            ON piste.id = stocks.piste_id
    GROUP BY piste.id
),

piste_last_campagne AS (
    SELECT DISTINCT
        p.id AS piste_id,
        LAST_VALUE(campagne.sherlock_id) OVER(w1) AS last_sherlock_camp,
        LAST_VALUE(campagne.diabolo_id) OVER(w1) AS last_diabolo_camp
    FROM EFFY_STORE.pistes AS p
    LEFT JOIN EFFY_STORE.contacts AS contact ON contact.piste_id = p.id
    LEFT JOIN EFFY_STORE.campagnes AS campagne ON campagne.diabolo_id = contact.campagne_id
    WINDOW w1 AS (
        PARTITION BY p.id ORDER BY contact.created_at ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
),

piste_appelee AS (
    SELECT
        piste.id                        AS piste_id,
        COUNT(DISTINCT calls.id)        AS nb_appel
    FROM EFFY_STORE.pistes AS piste
    LEFT JOIN EFFY_STORE.contacts AS contact
        ON contact.piste_id = piste.id
    LEFT JOIN EFFY_STORE.campagnes AS campagne
        ON campagne.diabolo_id = contact.campagne_id
    INNER JOIN EFFY_STORE.appels AS calls
        ON calls.diabolo_contact_id = contact.id
            AND calls.campagne_id = campagne.diabolo_id
    INNER JOIN EFFY_STORE.appels_codes_cloture AS wrapup
        ON calls.id = wrapup.appel_id
    GROUP BY piste.id
),

selfcare_dossier_non_cree AS (
    SELECT
        p.id AS piste_id,
        COUNT(DISTINCT IF(opp.etat = "gagnee", opp.id, NULL)) AS nb_opp_gagnee
    FROM EFFY_STORE.pistes AS p
    LEFT JOIN EFFY_STORE.opportunites AS opp ON opp.piste_id = p.id
    WHERE p.is_selfcare
    GROUP BY 1
    HAVING nb_opp_gagnee = 0
),

airbnb_non_eligible AS (
    SELECT
        piste.id                                        AS piste_id,
        LOGICAL_OR(
            (
                piste.source = "Airbnb"
                AND lcs.last_sherlock_camp = "e0c8dd4e-1e24-47fb-8908-47b339154b44"
                AND (lcs.last_diabolo_camp != 3163 OR lcs.last_diabolo_camp IS NULL)
                AND (pa.nb_appel = 0 OR pa.nb_appel IS NULL)
            ) OR (
                piste.source = "Airbnb"
                AND lcs.last_diabolo_camp IS NULL
                AND sdne.piste_id IS NULL
                AND (pa.nb_appel = 0 OR pa.nb_appel IS NULL)
            )
        )                                               AS est_airbnb_non_eligible
    FROM EFFY_STORE.pistes AS piste
    LEFT JOIN piste_last_campagne AS lcs        ON lcs.piste_id = piste.id
    LEFT JOIN selfcare_dossier_non_cree AS sdne ON sdne.piste_id = piste.id
    LEFT JOIN piste_appelee AS pa               ON pa.piste_id = piste.id
    GROUP BY piste.id
),

last_wrapup_name_by_piste AS (
    SELECT DISTINCT
        c.piste_id,
        LAST_VALUE(
            wrapup.code_cloture_nom
        ) OVER (
            PARTITION BY c.piste_id
            ORDER BY a.date_debut ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                       AS last_wrapup_name
    FROM EFFY_STORE.contacts AS c
    LEFT JOIN EFFY_STORE.appels AS a
        ON a.diabolo_contact_id = c.id
            AND a.campagne_id = c.campagne_id
    LEFT JOIN EFFY_STORE.appels_codes_cloture AS wrapup
        ON a.id = wrapup.appel_id
),

deals_demande_prospects AS (
    SELECT DISTINCT
        piste.id                                                                                AS piste_id,
        piste.api_user_id                                                                       AS contact_effy_uid,
        IF(
            ddp.nb_opp_gagnee = 0,
            CASE
                WHEN piste.etat = "faux_numero"
                    AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), piste.created_at, DAY) >= 15
                    THEN "Faux numéro"
                WHEN PARSE_BOOL(piste.cree_non_prioritaire) AND piste.confirmee_a IS NULL
                    THEN "Non intentionniste"
                ELSE wrapup.last_wrapup_name
            END,
            NULL
        )                                                                                       AS deals_close_lost_reason,
        IF(ddp.nb_opp_gagnee > 0, wrapup.last_wrapup_name, NULL)                                AS deals_close_won_reason,
        CASE
            WHEN ddp.max_diabolo_date_piste_is_removed_from_stock IS NOT NULL
                AND ddp.max_diabolo_date_piste_is_removed_from_stock <= CURRENT_DATETIME()
                THEN CAST(ddp.max_diabolo_date_piste_is_removed_from_stock AS timestamp)
            WHEN ddp.max_diabolo_date_piste_is_removed_from_stock IS NOT NULL
                AND ddp.max_diabolo_date_piste_is_removed_from_stock > CURRENT_DATETIME()
                THEN NULL
            WHEN PARSE_BOOL(piste.cree_non_prioritaire)
                AND piste.confirmee_a IS NULL
                AND ddp.nb_opp_gagnee = 0
                THEN piste.created_at
            WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), piste.created_at, DAY) >= 15
                THEN TIMESTAMP_ADD(piste.created_at, INTERVAL 15 DAY)
        END                                                                                     AS deals_closed_at,

        UTILITIES_UDF.GREATEST_ARRAY([
            piste.updated_at,
            TIMESTAMP(contact.date_debut_dernier_appel)
        ])                                                                                       AS deals_updated_at,
        CASE
            WHEN eb.piste_created_at < piste.created_at
                AND eb.piste_with_opportunite_gagnee IS NOT NULL
                THEN "Existing Business"
            ELSE "New Business"
        END                                                                                     AS deals_type
    FROM EFFY_STORE.pistes AS piste
    INNER JOIN deals_demande_prospect_tmp AS ddp    ON ddp.piste_id = piste.id
    LEFT JOIN EFFY_STORE.contacts AS contact        ON piste.id = contact.piste_id
    INNER JOIN EFFY_STORE.clients AS client         ON piste.api_user_id = client.api_user_id
    LEFT JOIN existing_business_tmp AS eb           ON eb.email = client.email
    LEFT JOIN last_wrapup_name_by_piste AS wrapup   ON wrapup.piste_id = piste.id
    WHERE piste.etat != "doublon"
),

deals_transfo_non_intentionniste AS (
    SELECT DISTINCT
        piste.id                                                                        AS piste_id,
        piste.api_user_id                                                               AS contact_effy_uid,
        CONCAT(piste.id, " - Intentionniste")                                           AS deals_custom_id,
        piste.utm_funnel                                                                AS deals_name,
        IF(
            ddp.nb_opp_gagnee = 0,
            CASE
                WHEN piste.etat = "faux_numero"
                    AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), piste.created_at, DAY) >= 15
                    THEN "Faux numéro"
                ELSE wrapup.last_wrapup_name
            END,
            NULL
        )                                                                               AS deals_close_lost_reason,
        IF(ddp.nb_opp_gagnee > 0, wrapup.last_wrapup_name, NULL)                        AS deals_close_won_reason,
        CASE
            WHEN ddp.max_diabolo_date_piste_is_removed_from_stock IS NOT NULL
                AND ddp.max_diabolo_date_piste_is_removed_from_stock <= CURRENT_DATETIME()
                THEN CAST(ddp.max_diabolo_date_piste_is_removed_from_stock AS timestamp)
            WHEN ddp.max_diabolo_date_piste_is_removed_from_stock IS NOT NULL
                AND ddp.max_diabolo_date_piste_is_removed_from_stock > CURRENT_DATETIME()
                THEN NULL
            WHEN PARSE_BOOL(piste.cree_non_prioritaire)
                AND piste.confirmee_a IS NULL
                AND ddp.nb_opp_gagnee = 0
                THEN piste.created_at
            WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), piste.created_at, DAY) >= 15
                THEN TIMESTAMP_ADD(piste.created_at, INTERVAL 15 DAY)
        END                                                                             AS deals_closed_at,

        UTILITIES_UDF.GREATEST_ARRAY([
            piste.updated_at,
            TIMESTAMP(contact.date_debut_dernier_appel)
        ])                                                                               AS deals_updated_at,
        CASE
            WHEN eb.piste_created_at < piste.created_at
                AND eb.piste_with_opportunite_gagnee IS NOT NULL
                THEN "Existing Business"
            ELSE "New Business"
        END                                                                           AS deals_type,

        piste.is_selfcare                                                             AS deals_piste_est_selfcare
    FROM EFFY_STORE.pistes AS piste
    INNER JOIN deals_demande_prospect_tmp AS ddp ON ddp.piste_id = piste.id
    LEFT JOIN EFFY_STORE.contacts AS contact    ON contact.piste_id = piste.id
    INNER JOIN EFFY_STORE.clients AS client     ON piste.api_user_id = client.api_user_id
    LEFT JOIN existing_business_tmp AS eb       ON eb.email = client.email
    LEFT JOIN DW_HUBSPOT.deals AS deals         ON deals.deals_custom_id = piste.id
    LEFT JOIN last_wrapup_name_by_piste AS wrapup   ON wrapup.piste_id = piste.id
    WHERE piste.etat != "doublon"
        AND deals.last_modified_timestamp < piste.confirmee_a
        AND piste.confirmee_a IS NOT NULL
),

join_prospect_intentionistes AS (
    /* ###########     PROSPECT    ############## */
    SELECT
        piste.id                                                        AS piste_id,
        ddp.contact_effy_uid                                            AS contact_effy_uid,
        piste.id                                                        AS deals_custom_id,
        piste.created_at                                                AS deals_created_at,

        ddp.deals_close_won_reason                                      AS deals_close_won_reason,
        ddp.deals_close_lost_reason                                     AS deals_close_lost_reason,
        ddp.deals_closed_at                                             AS deals_closed_at,

        UTILITIES_UDF.GREATEST_ARRAY([
            ddp.deals_updated_at,
            ddp.deals_closed_at
        ])                                                              AS deals_updated_at,
        ddp.deals_type                                                  AS deals_type
    FROM deals_demande_prospects AS ddp
    INNER JOIN EFFY_STORE.pistes AS piste
        ON piste.id = ddp.piste_id

    UNION ALL

    /* ###########     Passage Non Intentionniste à Intentionniste    ############## */
    SELECT
        piste.id                                                        AS piste_id,
        ddp.contact_effy_uid                                            AS contact_effy_uid,
        ddp.deals_custom_id                                             AS deals_custom_id,
        piste.confirmee_a                                               AS deals_created_at,

        ddp.deals_close_won_reason                                      AS deals_close_won_reason,
        ddp.deals_close_lost_reason                                     AS deals_close_lost_reason,
        ddp.deals_closed_at                                             AS deals_closed_at,

        UTILITIES_UDF.GREATEST_ARRAY([
            ddp.deals_updated_at,
            ddp.deals_closed_at
        ])                                                              AS deals_updated_at,
        ddp.deals_type                                                  AS deals_type
    FROM deals_transfo_non_intentionniste AS ddp
    INNER JOIN EFFY_STORE.pistes AS piste
        ON piste.id = ddp.piste_id
)

SELECT DISTINCT
    c.contact_effy_uid,
    c.contact_email,
    c.contact_phone_number,
    c.contact_mobile_phone_number,
    c.contact_last_name,
    c.contact_first_name,
    c.contact_civility,
    c.contact_departement,
    c.contact_zip_code,
    c.contact_city,
    c.contact_precarity_level,
    c.contact_creation_date,
    c.contact_last_modified_date,
    c.contact_created_at,
    c.contact_last_modified_at,
    c.contact_site_source,
    c.contact_is_ouvreur_np6,
    c.contact_last_activity,
    c.contact_last_form_submission,
    c.contact_email_optout_newsletter,
    c.contact_is_optout_from_commerce,
    c.contact_lite_consent,

    piste.id                                                        AS deals_piste_id,
    piste.source                                                    AS deals_piste_source,
    CASE PARSE_BOOL(piste.cree_non_prioritaire)
        WHEN TRUE THEN "False"
        WHEN FALSE THEN "True"
    END                                                             AS deals_piste_is_prio,
    piste.confirmee_a                                               AS deals_piste_confirmed_at,
    COALESCE(piste.est_piste_argumente, FALSE)                        AS deals_piste_est_argumente,
    piste.utm_funnel                                                AS deals_piste_parcours,

    # Habitation
    acco.accommodations_type                                        AS deals_piste_type_logement,
    acco.occupant_status                                            AS deals_piste_statut_occupant,
    CAST(acco.living_surface AS string)                             AS deals_piste_surface_habitable,
    acco.adress_postal_code                                         AS deals_piste_code_postal_chantier,
    SUBSTR(acco.adress_postal_code, 0, 2)                           AS deals_piste_departement_chantier,
    acco.adress_line                                                AS deals_piste_adresse_chantier,
    acco.adress_city                                                AS deals_piste_ville_chantier,
    het.label                                                       AS deals_piste_type_energie_chauffage_existant,
    heating_systems.label                                           AS deals_piste_systeme_chauffage,

    airbnb_non_eligible.est_airbnb_non_eligible                     AS deals_piste_est_airbnb_non_eligible,
    IF(piste.type_selfcare = "prime", TRUE, FALSE)                  AS deals_piste_est_selfcare,
    IF(piste.type_selfcare = "mer", TRUE, FALSE)                    AS deals_piste_est_selfcare_mer,
    sdne.piste_id IS NULL                                           AS deals_piste_selfcare_dossier_est_cree,

    join_all.deals_custom_id                                        AS deals_custom_id,
    piste.utm_funnel                                                AS deals_name,
    ""                                                              AS deals_type_offre,
    join_all.deals_close_won_reason                                 AS deals_close_won_reason,
    join_all.deals_close_lost_reason                                AS deals_close_lost_reason,
    FORMAT_TIMESTAMP("%m/%d/%Y", join_all.deals_closed_at)          AS deals_closed_date,

    FORMAT_TIMESTAMP("%m/%d/%Y", join_all.deals_created_at)         AS deals_create_date,
    join_all.deals_created_at                                       AS deals_created_at,
    FORMAT_TIMESTAMP("%m/%d/%Y", join_all.deals_updated_at)         AS deals_update_date,
    join_all.deals_updated_at                                       AS deals_updated_at,
    "Demande"                                                       AS deals_stage,
    join_all.deals_type                                             AS deals_type,
    piste.type_travaux_demande                                      AS deals_works_type,

    # region NULL
    CAST(NULL AS string)                                            AS deals_operation_code,
    NULL                                                            AS deals_amount,
    "Sales Pipeline"                                                AS deal_pipeline,
    CAST(NULL AS string)                                            AS deals_chantier_vt_date_commande,
    CAST(NULL AS string)                                            AS deals_chantier_vt_date_realisation,
    CAST(NULL AS string)                                            AS deals_chantier_devis_date_envoi,
    CAST(NULL AS string)                                            AS deals_chantier_devis_date_signature,
    CAST(NULL AS string)                                            AS deals_chantier_travaux_date_commande,
    CAST(NULL AS string)                                            AS deals_chantier_travaux_date_previsionnel,
    CAST(NULL AS string)                                            AS deals_chantier_travaux_date_realisation,
    CAST(NULL AS string)                                            AS deals_chantier_facture_date_envoi,
    CAST(NULL AS string)                                            AS deals_chantier_facture_date_reglement,
    CAST(NULL AS string)                                            AS deals_source_status,
    CAST(NULL AS string)                                            AS deals_prime_type,
    CAST(NULL AS string)                                            AS deals_prime_date_engagement,
    CAST(NULL AS string)                                            AS deals_prime_date_facture,
    CAST(NULL AS string)                                            AS deals_prime_date_paiement,
    CAST(NULL AS string)                                            AS deals_prime_ah_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_devis_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_facture_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_avis_impot_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_dossier_complet_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_manda_pro_date_envoi,
    CAST(NULL AS string)                                            AS deals_prime_gere_par_le_pro,
    CAST(NULL AS string)                                            AS deals_prime_has_discount_on_quotation,
    CAST(NULL AS string)                                            AS deals_prime_siret_pro,
    CAST(NULL AS boolean)                                           AS deals_prime_a_remonte_son_devis,
    CAST(NULL AS boolean)                                           AS deals_est_activite_isolation,
    CAST(NULL AS boolean)                                           AS deals_est_activite_chauffage,
    CAST(NULL AS boolean)                                           AS deals_est_activite_solaire,
    CAST(NULL AS boolean)                                           AS deals_est_activite_fenetres,
    CAST(NULL AS boolean)                                           AS deals_est_serenite,
    CAST(NULL AS boolean)                                           AS deals_est_liberte
# endregion
FROM DM_MARKETING_AUTOMATION_B2C.contacts AS c
INNER JOIN join_prospect_intentionistes AS join_all
    ON join_all.contact_effy_uid = c.contact_effy_uid
INNER JOIN EFFY_STORE.pistes AS piste
    ON piste.id = join_all.piste_id
LEFT JOIN DW_RCU.accommodations AS acco
    ON acco.accommodations_id = piste.accommodations_id
LEFT JOIN DW_RCU.heating_energies_types AS het
    ON het.id = SAFE_CAST(acco.heating_energy AS int64)
LEFT JOIN DW_RCU.existing_heating_systems AS heating_systems
    ON SAFE_CAST(acco.existing_heating_system AS int64) = heating_systems.id
LEFT JOIN selfcare_dossier_non_cree AS sdne     ON piste.id = sdne.piste_id
LEFT JOIN airbnb_non_eligible                   ON piste.id = airbnb_non_eligible.piste_id
