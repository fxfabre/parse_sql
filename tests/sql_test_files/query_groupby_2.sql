select
    callType,
    displayedNumber,
    cast(date_trunc(callStart, month) as date)                          as mois,
    count(*)                                                            as nb_calls,
    count(case when callResult = 'ANSWERING_MACHINE' then callId end)   as nb_repondeurs
from DW_DIABOLO.calls_details_recording
where callStart >= '2021-01-01'
    and callType like 'OUTBOUND%'
group by 1, 2, 3;
