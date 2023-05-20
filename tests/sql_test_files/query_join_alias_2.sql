    SELECT *,
        col_1,
        col_2 as name_2
    FROM `dataset_1.table`   As  alias_T1
    LEFT JOIN dataset_2.table2
        ON table1.c1 = table2.c2
