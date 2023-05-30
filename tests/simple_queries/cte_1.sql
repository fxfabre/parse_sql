WITH

cte_name as (
    select col_1
    FROM dataset.table1
)

select col_1 as col_2
FROM cte_name
