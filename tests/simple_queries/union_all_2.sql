with cte_1 as (
    /* ###########     sub query 1    ############## */
    SELECT col_1
    FROM dataset.table

    UNION ALL

    /* ###########     sub query 2    ############## */
    SELECT col_1
    FROM dataset.table
)

-- inline comment
select col_1 as name_1
from cte_1
