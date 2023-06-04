SELECT
  user_id,
  user_name,
  status_id,
  status_name,
  campaign_id,
  campaign_name,
  cast(date as date) as date,
  sum(duration) as duration
from DW_DIABOLO.agents_details_recording
group by 1,2,3,4,5,6,7;
