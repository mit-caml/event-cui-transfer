set search_path to mimiciii_1v3;

COPY(
SELECT itemid, label FROM d_items
) TO '/tmp/event-cui-transfer/chart.csv' WITH CSV HEADER DELIMITER ';';

COPY(
SELECT itemid, label, fluid, category FROM d_labitems
) TO '/tmp/event-cui-transfer/lab.csv' WITH CSV HEADER DELIMITER ';';

COPY(
SELECT DISTINCT drug_name, route, 'start' as start
FROM prescriptions_generic)
TO '/tmp/event-cui-transfer/prescription_labels.csv' WITH CSV HEADER DELIMITER ';';

COPY (
SELECT DISTINCT ((spec_itemid, org_itemid, ab_itemid)) AS itemid, (spec_type_desc, org_name, ab_name) AS label
FROM microbiologyevents
) TO '/tmp/event-cui-transfer/microbiologyevents_itemids.csv' WITH CSV HEADER DELIMITER ';';

COPY(
SELECT * FROM d_items
) TO '/tmp/event-cui-transfer/itemids.csv' WITH CSV HEADER DELIMITER ';'
