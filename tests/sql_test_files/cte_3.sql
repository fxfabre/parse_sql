WITH

call_tmp AS (
    SELECT DISTINCT
        a.service_nom                                       AS nom_service,
        a.queue_nom                                         AS nom_file,
        a.service_telephone                                 AS service_telephone,
        a.id                                                AS call_id,
        CAST(DATE_TRUNC(a.date_debut, day) AS DATE)         AS call_date,
        a.date_debut                                        AS date_debut,
        a.duree                                             AS duree,
        a.resultat                                          AS resultat_appel,
        CONCAT(0, RIGHT(a.contact_numero_telephone, 9))     AS contact_phone,
        ac.code_cloture_statut                              AS type_cloture,
        ac.code_cloture_nom                                 AS code_cloture,
        IF (LAST_VALUE(a.id) OVER (
            PARTITION BY a.contact_numero_telephone, CAST(DATE_TRUNC(a.date_debut, day) AS DATE), a.resultat
            ORDER BY (a.date_debut) ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) = a.id,True, False) as is_last_call_day
    FROM EFFY_STORE.appels AS a
    LEFT JOIN EFFY_STORE.appels_codes_cloture AS ac ON a.id = ac.appel_id
    WHERE a.service_nom IS NOT NULL
),

call_temoins AS (
    SELECT DISTINCT
        ct.nom_service,
        ct.nom_file,
        ct.service_telephone,
        ct.call_id,
        ct.call_date,
        ct.date_debut,
        ct.duree,
        ct.resultat_appel,
        ct.contact_phone,
        ct.type_cloture,
        ct.code_cloture,
        p.id AS piste_id,
        o.opportunite_gagnee_prime_seule,
        o.opportunite_gagnee_mer,
        o.opportunite_gagnee_solaire,
        o.opportunite_gagnee_chaudiere,
        o.opportunite_gagnee_rampants,
        o.opportunite_gagnee_pac,
        o.opportunite_gagnee_ite,
        o.opportunite_gagnee_sols,
        o.opportunite_gagnee_combles,
        o.opportunite_gagnee_pac_air_air,
        o.opportunite_gagnee_iso_1e,
        o.opportunite_gagnee_iso_rac,
        o.opportunite_gagnee_recrutement_pro
    FROM call_tmp as ct
    LEFT JOIN EFFY_STORE.clients AS c ON ct.contact_phone = c.telephone1
    LEFT JOIN EFFY_STORE.pistes AS p ON p.api_user_id = c.api_user_id
        AND DATE_TRUNC(ct.date_debut, DAY) = DATE_TRUNC(CAST(p.created_at AS DATETIME), DAY)
        AND p.utm_funnel IS NULL
        AND ct.resultat_appel = 'HANDLED'
        AND ct.is_last_call_day is true
    LEFT JOIN EFFY_STORE.opportunites AS o ON o.piste_id = p.id
)

SELECT
    t.call_date,
    t.Nom_Service,
    t.nom_file,
    t.service_telephone,
    t.resultat_appel,
    t.type_cloture,
    t.code_cloture,
    COALESCE(COUNT(DISTINCT t.call_id), 0)                          AS nb_calls,
    COALESCE(COUNT(DISTINCT t.piste_id), 0)                         AS nb_pistes_creees,
    SUM(t.duree)                                                    AS sum_duree_call,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_prime_seule), 0)   AS nb_temoin_prime_seule,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_mer), 0)           AS nb_temoin_mer,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_solaire), 0)       AS nb_temoin_solaire,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_chaudiere), 0)     AS nb_temoin_chaudiere,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_rampants), 0)      AS nb_temoin_rampants,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_pac), 0)           AS nb_temoin_pac,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_ite), 0)           AS nb_temoin_ite,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_sols), 0)          AS nb_temoin_sols,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_combles), 0)       AS nb_temoin_combles,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_pac_air_air), 0)   AS nb_temoin_pacaa,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_iso_1e), 0)        AS nb_temoin_iso1e,
    COALESCE(COUNT(DISTINCT t.opportunite_gagnee_iso_rac), 0)       AS nb_temoin_isorac

FROM call_temoins AS t
GROUP BY 1, 2, 3, 4, 5, 6,7
