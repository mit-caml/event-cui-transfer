-- define_patient_careunit.sql
-- Creates track_patient_transfers, define_patient_careunit, assoc_dod, patid_dod_saps materialized views.
-- Creates patid_dod_saps.csv

set search_path to mimiciii_1v3;

drop materialized view track_patient_transfers cascade;
create materialized view track_patient_transfers AS (
with prelim AS (
SELECT transfers.subject_id, transfers.hadm_id, transfers.icustay_id, transfers.intime, transfers.outtime, transfers.los*60 AS los_in_min,
	transfers.eventtype, transfers.prev_careunit, transfers.curr_careunit, transfers.prev_wardid, transfers.curr_wardid,
	EXTRACT (DAY FROM (transfers.intime - a.icustay_intime)) * 24 * 60 +
	EXTRACT (HOUR FROM (transfers.intime - a.icustay_intime)) * 60 +
	EXTRACT (MINUTE FROM (transfers.intime - a.icustay_intime)) AS min_icuin_to_transferin,
	EXTRACT (DAY FROM (transfers.outtime - a.icustay_intime)) * 24 * 60 +
	EXTRACT (HOUR FROM (transfers.outtime - a.icustay_intime)) * 60 +
	EXTRACT (MINUTE FROM (transfers.outtime - a.icustay_intime)) AS min_icuin_to_transferout
	--cASe when transfers.prev_careunit = transfers.curr_careunit then 'True' else 'False' end same_unit
FROM transfers
INNER JOIN first_icu_careunit a
ON a.hadm_id = transfers.hadm_id
WHERE (transfers.icustay_id IS NULL or transfers.icustay_id = a.icustay_id) AND
	   transfers.curr_careunit in ('MICU', 'SICU', 'CCU', 'CSRU', 'TSICU')
ORDER BY subject_id, hadm_id, min_icuin_to_transferin
),
get_prev_outtime AS (
SELECT p.subject_id, p.hadm_id, p.icustay_id,
	   p.intime, p.outtime, p.los_in_min,
	   p.prev_careunit, p.curr_careunit,
	   lead(intime, 1) OVER (PARTITION by subject_id, hadm_id, icustay_id order by intime) AS next_intime
FROM prelim p
),
track_movements AS (
SELECT p.subject_id, p.hadm_id, p.icustay_id, min(p.intime) AS intime,
	   max(p.outtime) AS outtime, sum(p.los_in_min) AS los_in_min,
	   p.curr_careunit,
	   (p.next_intime = p.outtime or p.prev_careunit = p.curr_careunit) AS same_unit
FROM get_prev_outtime p
GROUP BY p.subject_id, p.hadm_id, p.icustay_id, p.curr_careunit, same_unit
ORDER BY p.subject_id, p.hadm_id, p.icustay_id
)
SELECT t.*,
	EXTRACT (DAY FROM (t.intime - a.icustay_intime)) * 24 * 60 +
	EXTRACT (HOUR FROM (t.intime - a.icustay_intime)) * 60 +
	EXTRACT (MINUTE FROM (t.intime - a.icustay_intime)) AS min_icuin_to_transferin,
	EXTRACT (DAY FROM (t.outtime - a.icustay_intime)) * 24 * 60 +
	EXTRACT (HOUR FROM (t.outtime - a.icustay_intime)) * 60 +
	EXTRACT (MINUTE FROM (t.outtime - a.icustay_intime)) AS min_icuin_to_transferout
FROM track_movements t
INNER JOIN first_icu_careunit a
ON a.icustay_id = t.icustay_id
order by subject_id, hadm_id, t.icustay_id, intime
);
drop materialized view ordering_icu_visits cascade;
create materialized view ordering_icu_visits AS (
with transfers_from_unit AS (
SELECT t.*, a.curr_careunit AS first_careunit
FROM track_patient_transfers t
INNER JOIN first_icu_careunit a
on a.icustay_id = t.icustay_id
),
total_los AS (
SELECT subject_id, hadm_id, icustay_id, curr_careunit,
 min(intime) AS earliest_in,
 max(outtime) AS latest_out,
 sum(los_in_min) AS total_los
FROM transfers_FROM_unit
group by subject_id, hadm_id,
icustay_id, curr_careunit
)
SELECT total_los.*, a.icustay_intime, a.icustay_outtime, a.gender, a.dob, a.dod, a.age, a.admittime,
a.dischtime, a.hospstay_num, a.icustay_num, a.min_icuin_to_discharge, a.min_icuin_to_dod,a.curr_careunit AS most_in_first24hrs,
row_number() over (partition by total_los.subject_id order by total_los.earliest_in) AS icu_order
FROM total_los
INNER JOIN first_icu_careunit a
on a.icustay_id = total_los.icustay_id
);

DROP MATERIALIZED VIEW define_patient_careunit CASCADE;
CREATE MATERIALIZED VIEW define_patient_careunit AS (
with max_los AS (
SELECT *, max(total_los) over (partition by subject_id, icustay_id) AS max_los
FROM ordering_icu_visits
WHERE icu_order = 1
),
compare AS (
SELECT m.subject_id, m.hadm_id, m.icustay_id, m.earliest_in, m.latest_out, m.icustay_intime, m.icustay_outtime, m.gender,
m.dob, m.dod, m.age, m.admittime, m.dischtime, m.hospstay_num, m.icustay_num, m.min_icuin_to_discharge,
m.min_icuin_to_dod,
m.curr_careunit, m.most_in_first24hrs = m.curr_careunit AS comparison
FROM max_los m
WHERE m.total_los = m.max_los
)
SELECT subject_id, hadm_id, icustay_id, earliest_in, latest_out, icustay_intime, icustay_outtime, admittime, dischtime,
curr_careunit, gender, dob, dod, age, hospstay_num, icustay_num
FROM compare WHERE comparison is true
);


DROP MATERIALIZED VIEW assoc_dod CASCADE;
CREATE MATERIALIZED VIEW assoc_dod AS (
	SELECT a.subject_id, a.hadm_id, a.icustay_id, adm.admission_location, adm.discharge_location, adm.insurance, adm.diagnosis,
		a.earliest_in, a.latest_out,
		a.icustay_intime, a.icustay_outtime, a.admittime, a.dischtime, a.curr_careunit, a.gender,
		a.dob, a.dod, a.age,
		round(cast(EXTRACT (EPOCH FROM (a.dischtime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_discharge,
		round(cast(EXTRACT (EPOCH FROM (a.latest_out - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_unitout,
		round(cast(EXTRACT (EPOCH FROM (a.dod - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_dod,
		round(cast(EXTRACT (EPOCH FROM (a.dod - a.latest_out))/60 AS numeric), 2) AS min_unitout_to_dod,
		round(cast(EXTRACT (EPOCH FROM (a.dod - a.dischtime))/60 AS numeric), 2) AS min_discharge_to_dod
	FROM define_patient_careunit a
	INNER JOIN admissions adm
	on adm.hadm_id = a.hadm_id
);

CREATE MATERIALIZED VIEW patid_dod_saps AS (
	SELECT a.*, s.sapsii FROM assoc_dod a
	INNER JOIN sapsii s
	on s.icustay_id = a.icustay_id

);

COPY (SELECT * FROM patid_dod_saps) TO '/tmp/event-cui-transfer/patid_dod_saps.csv' WITH CSV HEADER DELIMITER ';';
