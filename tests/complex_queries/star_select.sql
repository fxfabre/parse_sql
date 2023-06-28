WITH

step_1 as (
    select
        contact_id,
        address,
        dt_contrat as date_contact
    FROM dataset.table_name
),

step_2 as (
    select *
    FROM step_1
),

step_3 AS (
    SELECT DISTINCT
        c.*,
        LAST_VALUE(u.folder) OVER(w1)       AS folder,
        LAST_VALUE(u.first_name) OVER(w1)   AS first_name,
        LAST_VALUE(u.last_name) OVER(w1)    AS last_name,
        LAST_VALUE(u.email) OVER(w1)        AS email
    FROM step_2 AS c
    LEFT JOIN dataset.data_histo AS u
        ON CAST(u.id AS STRING) = c.contact_id
    WINDOW w1 AS (
        PARTITION BY c.contact_id
        ORDER BY u.extract_datetime ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
)

select
    contact_id,
    address
from step_3
