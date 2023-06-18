import json
import os.path
from typing import Dict, List

from .models import ColumnName, TableId


def get_bq_schema_with_cols() -> Dict[TableId, List[ColumnName]]:
    """
    returns { "dataset.table_name": [col1, ..., coln] }
    """
    bq_schema_path = os.path.join(os.getenv("DATA_DIR"), "parse_sql", "bq_schema.json")

    with open(bq_schema_path, "r") as f:
        return {
            table_id.lower(): [c["name"] for c in table_infos["schema"]]
            for table_id, table_infos in json.load(f).items()
        }

