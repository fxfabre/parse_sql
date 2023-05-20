SELECT
*
from DW_DIABOLO.agents_details_recording
where status_detail in ("login","logout")
