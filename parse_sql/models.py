from typing import Dict, Any, Union, List


TableId = str       # EFFY_STORE.pistes
TableName = str     # pistes
TableAlias = str    # p
ColumnName = str    # piste_id

CteName = str
CteQuery = Dict[str, Union[List, Dict]]
# CteQuery : describe a single query or a cte
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

SimpleQuery = Dict[CteName, CteQuery]
# SimpleQuery : describe a list of CTE, without any UNION ALL

FileQuery = Dict[CteName, List[CteQuery]]
# SimpleQuery : describe a list of CTE, with UNION ALL
