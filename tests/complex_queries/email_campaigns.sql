------------------- UTILITIES ----------------------------------------
CREATE TEMP FUNCTION UNIX_TIMESTAMP_TO_DATETIME(UNIX_TIMESTAMP STRING) AS (
    DATETIME(TIMESTAMP_MILLIS(CAST(CAST(UNIX_TIMESTAMP AS FLOAT64) AS INT64)), 'Europe/Paris')
);
----------------------------------------------------------------------


WITH last_state AS (
  SELECT
    id,
    MAX(extract_date) AS extract_date
  FROM `ODS_HUBSPOT.email_campaigns_raw`
  GROUP BY 1
)
SELECT DISTINCT
    CAST(ec.id AS INT64)                                       AS id,
    CAST(ec.appId AS INT64)                                    AS app_id,
    ec.appName                                                 AS app_name,
    CAST(CAST(ec.contentId AS FLOAT64) as INT64)               AS content_id,
    ec.subject                                                 AS subject,
    ec.name                                                    AS name,
    ec.counters                                                AS counters,
    UNIX_TIMESTAMP_TO_DATETIME(ec.lastProcessingFinishedAt)    AS last_processing_finished_at,
    UNIX_TIMESTAMP_TO_DATETIME(ec.lastProcessingStartedAt)     AS last_processing_started_at,
    UNIX_TIMESTAMP_TO_DATETIME(ec.lastProcessingStateChangeAt) AS last_processing_state_change_at,
    CAST(CAST(ec.numIncluded AS FLOAT64) AS INT64)             AS num_included,
    ec.processingState                                         AS processing_state,
    UNIX_TIMESTAMP_TO_DATETIME(ec.scheduledAt)                 AS scheduled_at,
    ec.type                                                    AS type
FROM `ODS_HUBSPOT.email_campaigns_raw` ec
INNER JOIN last_state USING(id, extract_date)
