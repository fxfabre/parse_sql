WITH

diabolo_contact_treated_tmp2 as (
    select
        contact_id,
        address,
        dt_contrat as date_contact_is_treated
    FROM dataset.table_name
),

diabolo_contact_treated AS (
    SELECT DISTINCT
        c.*,
        LAST_VALUE(u.folder) OVER(w1)       AS contact_treated_by_agent_folder,
        LAST_VALUE(u.first_name) OVER(w1)   AS contact_treated_by_agent_first_name,
        LAST_VALUE(u.last_name) OVER(w1)    AS contact_treated_by_agent_last_name,
        LAST_VALUE(u.email) OVER(w1)        AS contact_treated_by_agent_email
    FROM diabolo_contact_treated_tmp2 AS c
    LEFT JOIN DW_DIABOLO.public_users_folder_histo AS u
        ON CAST(u.id AS STRING) = c.contact_treated_by_agent_id
        AND c.date_contact_is_treated = u.extract_datetime
    WINDOW w1 AS (
        PARTITION BY c.contact_id, c.campaign_id
        ORDER BY u.extract_datetime ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
)

select *
from diabolo_contact_treated
