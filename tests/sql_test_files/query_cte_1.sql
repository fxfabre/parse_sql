WITH

cte_name as (
    select col_1
    FROM dataset.table1
),

cte_2 as (
    select col_2, col_3
    FROM dataset.t2 as t2
    join dataset.table t3
        on t2.id = t3.t2_id
)

select col_1, col_2, col_3
FROM cte_name
left join cte_2
    on cte_name.col_1 = cte_2.col_3
