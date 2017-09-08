set search_path to mimiciii_1v3;

COPY
(
SELECT i.subject_id, i.dbsource FROM icustays i
INNER JOIN define_patient_careunit a
ON a.icustay_id = i.icustay_id
) TO '/tmp/event-cui-transfer/patid_dbsource.csv' with CSV HEADER DELIMITER ';';
