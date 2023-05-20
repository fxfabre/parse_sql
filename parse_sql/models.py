from typing import Dict, Any


TableId = str       # EFFY_STORE.pistes
TableName = str     # pistes
TableAlias = str    # p
ColumnName = str    # piste_id

Query = Dict[str, Any]
# Query : describe a single query or a cte
# {
#     'join': [(['a', 'id'], ['ac', 'appel_id'])],
#     'select': {
#         'call_date': 'function()',
#         'call_id': 'a.id',
#         'code_cloture': 'ac.code_cloture_nom',
#     },
#     'tables': {
#         'a': 'EFFY_STORE.appels',
#         'ac': 'EFFY_STORE.appels_codes_cloture'
#     }
# }
