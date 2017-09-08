set search_path to mimiciii_1v3;


drop materialized view prescriptions_generic;
create materialized view prescriptions_generic as (
  select subject_id, hadm_id, icustay_id, startdate, enddate, drug_type,
	drug, drug_name_poe, drug_name_generic as drug_name, route
  from prescriptions
  where drug_name_generic != ''
  UNION
  select subject_id, hadm_id, icustay_id, startdate, enddate, drug_type,
	drug, drug_name_poe, drug as drug_name, route
  from prescriptions
  where drug_name_generic = ''
)
