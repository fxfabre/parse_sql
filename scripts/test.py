from pathlib import Path
from pprint import pprint

from parse_sql.extract_from_parsed import extract_all_joins_from_file
# from parse_sql.file_io import get_bq_schema_with_cols
from parse_sql.parsers import read_and_parse_sql_file

# bq_schema = get_bq_schema_with_cols()
bq_schema = {
    "dataset.table_name": ["id", "contact_id", "address", "dt_contrat"],
    "dw_diabolo.public_users_folder_histo": [
        "folder", "first_name", "email", "date_contact_is_treated"
    ],
}

file_path = Path("tests/complex_queries/star_select.sql")
parsing_by_cte = read_and_parse_sql_file(file_path)

res = extract_all_joins_from_file(parsing_by_cte, bq_schema)
pprint(res)
