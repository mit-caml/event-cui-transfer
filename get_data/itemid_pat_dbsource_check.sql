set search_path to mimiciii_1v3;

COPY(
with distinct_items AS (
select distinct icustay_id, itemid FROM chartevents
),
distinct_item_dbsource AS (
select d.*, items.dbsource AS item_dbsource
FROM distinct_items d
INNER JOIN d_items items
ON items.itemid = d.itemid
),
distinct_item_pat_dbsource AS (
select d.*, i.subject_id, i.dbsource AS patient_dbsource
FROM distinct_item_dbsource d
INNER JOIN icustays i
ON d.icustay_id = i.icustay_id
)
select distinct define_patient_careunit.subject_id from distinct_item_pat_dbsource
inner join define_patient_careunit on
distinct_item_pat_dbsource.icustay_id = define_patient_careunit.icustay_id
where patient_dbsource != item_dbsource
) TO '/tmp/event-cui-transfer/mv_cv_patient_intersection.csv' WITH CSV HEADER DELIMITER ';';
