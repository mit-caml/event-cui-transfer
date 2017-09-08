-- create_firsticu_careunit_view.sql
-- Creates first_icu_careunit materialized view.

-- Uses transfers to determine where patients spent the maximum amount of time
-- in the first 24 hours of their stay.

set search_path to mimiciii_1v3;


-- For each ICU stay, find the careunit where the patient spent the maximum amount of time in the first 24 hours.
DROP MATERIALIZED VIEW first_icu_careunit CASCADE;
CREATE MATERIALIZED VIEW first_icu_careunit AS (
with fix_los as ( --get max length of stay in each careunit for each icustay_id, as long as icu_in is in the first 24 hrs.
  SELECT transfers.subject_id,
         transfers.hadm_id,
         transfers.icustay_id,
         transfers.intime,
         transfers.outtime,
         icustays.intime as icustay_intime,
	     least(transfers.outtime, icustays.intime + interval '1 day') AS outtime2, transfers.curr_careunit
  FROM transfers, icustays
  WHERE icustays.icustay_id = transfers.icustay_id AND
	EXTRACT (DAY FROM (transfers.intime - icustays.intime )) * 24 * 60 +
	EXTRACT (HOUR FROM (transfers.intime - icustays.intime )) * 60 +
	EXTRACT (MINUTE FROM (transfers.intime - icustays.intime )) <= 24*60
),
max_los as (
  SELECT subject_id, hadm_id, icustay_id, curr_careunit,
         EXTRACT (DAY FROM (outtime2 - intime)) * 24 * 60 +
	       EXTRACT (HOUR FROM (outtime2 - intime)) * 60 +
	       EXTRACT (MINUTE FROM (outtime2 - intime)) AS time_spent,
	       row_number() over (partition by icustay_id order by EXTRACT (DAY FROM (outtime2 - intime)) * 24 * 60 +
	       EXTRACT (HOUR FROM (outtime2 - intime)) * 60 +
	       EXTRACT (MINUTE FROM (outtime2 - intime)) desc) AS unit_by_time_spent
  FROM fix_los
),
group_max_los as (
  SELECT subject_id, hadm_id, icustay_id, curr_careunit,
         SUM(time_spent) OVER (PARTITION BY icustay_id, curr_careunit) AS time_spent, unit_by_time_spent
  FROM max_los
),
filtered_transfers AS (
  SELECT subject_id, hadm_id, icustay_id, time_spent,
         unit_by_time_spent, curr_careunit
  FROM group_max_los
  WHERE unit_by_time_spent = 1
),
-- Find the first (earliest) hospital admission for each subject_id where data exists.
admission_withfirsttime AS (
  select p.subject_id, p.dob, p.dod, p.gender,
         a.hadm_id, a.admittime, a.dischtime, a.admission_type,
         a.admission_location, a.discharge_location, a.insurance, a.diagnosis,
         min(a.admittime) over (partition by p.subject_id) AS first_admittime,
         row_number() over (partition by a.subject_id order by a.admittime) AS hospstay_num
  FROM admissions a
  INNER JOIN patients p
  on p.subject_id = a.subject_id
  WHERE a.has_ioevents_data = 1 AND
        a.has_chartevents_data = 1
),
-- Find the first icu stay.
first_icu AS (
  SELECT i.subject_id, i.hadm_id, i.icustay_id, i.intime AS icustay_intime,
         min(i.intime) over (partition by i.hadm_id) AS first_icutime,
         i.outtime AS icustay_outtime, p.gender, p.dob, p.dod,
         EXTRACT (YEAR FROM (age(i.intime, p.dob))) AS age,
           p.admittime, p.dischtime, p.hospstay_num,
           row_number() over (partition by i.subject_id, i.hadm_id ORDER BY i.intime) AS icustay_num,
    	   EXTRACT (YEAR FROM (dischtime - i.intime)) * 365.25 * 24 * 60 +
  	       EXTRACT (DAY FROM (dischtime - i.intime)) * 24 * 60 +
  	       EXTRACT (HOUR FROM (dischtime - i.intime)) * 60 +
  	       EXTRACT (MINUTE FROM (dischtime - i.intime)) AS min_icuin_to_discharge,
    	   EXTRACT (YEAR FROM (dod - i.intime)) * 365.25 * 24 * 60 +
  	       EXTRACT (DAY FROM (dod - i.intime)) * 24 * 60 +
  	       EXTRACT (HOUR FROM (dod - i.intime)) * 60 +
  	       EXTRACT (MINUTE FROM (dod - i.intime)) AS min_icuin_to_dod,
  	       EXTRACT (YEAR FROM (i.outtime - i.intime)) * 365.25 * 24 * 60 +
  	       EXTRACT (DAY FROM (i.outtime - i.intime)) * 24 * 60 +
  	       EXTRACT (HOUR FROM (i.outtime - i.intime)) * 60 +
  	       EXTRACT (MINUTE FROM (i.outtime - i.intime)) AS time_in_icu
  FROM icustays i
  INNER JOIN admission_withfirsttime p
  ON p.hadm_id = i.hadm_id
),
first_icu_careunit AS (
	select first_icu.*, filtered_transfers.curr_careunit
	FROM first_icu
	INNER JOIN filtered_transfers
	on filtered_transfers.icustay_id = first_icu.icustay_id
	WHERE age >= 18 AND
       hospstay_num = 1 AND
       time_in_icu > 24*60 AND
       (min_icuin_to_dod > 24*60 OR (dod IS NULL))
)
select * FROM first_icu_careunit
WHERE icustay_num = 1
);
