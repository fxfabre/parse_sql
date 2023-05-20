CREATE TEMP FUNCTION CAST_NONE(param_to_cast STRING) AS (
    NULLIF(param_to_cast, 'None')
);

SELECT
    CAST(CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupId")) AS INT64)                                                      AS code_cloture_id,
    callId                                                                                                                    AS appel_id,
    o.id                                                                                                                      AS operateur_id,
    CAST(CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.agentId")) AS INT64)                                                       AS agent_id,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.agentName"))                                                                    AS agent_nom,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.userGroupIds"))                                                                 AS user_groupe_ids,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.userGroupNames"))                                                               AS user_groupe_noms,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupStatus"))                                                                 AS code_cloture_statut,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupPath"))                                                                   AS code_cloture_path,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupName"))                                                                   AS code_cloture_nom,
    CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupComment"))                                                                AS code_cloture_comment,
    IF(callstart <= '2021-12-14',
       CAST(CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupDuration")) AS INT64) / 1000,
       CAST(CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrapupDuration")) AS INT64))                                            AS duree,
    DATETIME(PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', CAST_NONE(JSON_EXTRACT_SCALAR(wrapups, "$.wrappedAt")), 'Europe/Paris'))    AS cree_a
FROM DW_DIABOLO.calls_details_recording         AS cdr,
    UNNEST(JSON_EXTRACT_ARRAY(cdr.callWrapups)) AS wrapups
LEFT JOIN DW_DIABOLO.public_users AS u ON cdr.callWrapups_agentId = CAST(u.id AS STRING)
LEFT JOIN DW_SHERLOCK.operateurs AS o ON LOWER(u.email) = LOWER(o.email)
