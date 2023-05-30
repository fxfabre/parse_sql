with cte_1 as (
    SELECT col_1
    FROM dataset.table

    UNION ALL

    SELECT col_1
    FROM dataset.table
)
select col_1 as name_1
from cte_1

UNION ALL

select col_1 as name_1
from cte_1
