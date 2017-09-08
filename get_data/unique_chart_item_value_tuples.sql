-- copy_unique_item_value_tuples.sql
-- Creates unique_chart_item_values.csv.

set search_path to mimiciii_1v3;

COPY (
select distinct (c.itemid, d.label, c.value)
from chartevents c, d_items d
where d.itemid = c.itemid
) TO '/tmp/event-cui-transfer/unique_chart_item_values.csv' WITH CSV HEADER DELIMITER ','
