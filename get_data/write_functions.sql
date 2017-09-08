set search_path to mimiciii_1v3;

CREATE OR REPLACE FUNCTION write_chart_events_with_value(
    lower_bound integer,
    upper_bound integer,
    lower_bound_str text,
    upper_bound_str text)
  RETURNS void AS
$BODY$
BEGIN
EXECUTE format ('
COPY(
select c.subject_id, c.itemid, c.value,
       round(cast(EXTRACT (EPOCH from (c.charttime - a.icustay_intime))/60 as numeric), 2) as min_icuin_to_chart,
	extract (hour from c.charttime) as hour_of_day
	from chartevents c
	inner join define_patient_careunit a
	on a.icustay_id = c.icustay_id
	where c.icustay_id is not null AND
	  c.charttime is not NULL AND
	  c.charttime >= a.icustay_intime + %L*interval ''1 day'' and c.charttime < a.icustay_intime + %L * interval ''1 day''
UNION ALL
select c.subject_id, c.itemid, c.value, round(cast(EXTRACT (EPOCH from (c.charttime - a.icustay_intime))/60 as numeric), 2) as min_icuin_to_chart,
	extract (hour from c.charttime) as hour_of_day
from chartevents c
inner join define_patient_careunit a
on a.hadm_id = c.hadm_id
where c.icustay_id is null AND
  c.charttime is not NULL AND
  c.charttime >= a.icustay_intime + %L*interval ''1 day'' and c.charttime < a.icustay_intime + %L * interval ''1 day''
) TO ''/tmp/event-cui-transfer/chartevents_withvalue_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$BODY$
LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION write_inputevents_mv(lower_bound integer, upper_bound integer, lower_bound_str text, upper_bound_str text) RETURNS void AS
$$
BEGIN
EXECUTE format ('
COPY(
    (SELECT c.subject_id, c.itemid,
    	ROUND(CAST(EXTRACT (EPOCH FROM (c.starttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_start
    	FROM inputevents_mv c
    	INNER JOIN define_patient_careunit a
    	ON a.icustay_id = c.icustay_id
    	WHERE c.icustay_id IS NOT NULL AND
    	  c.starttime IS NOT NULL AND
    	  c.starttime >= a.icustay_intime + %L*interval ''1 day'' AND c.starttime < a.icustay_intime + %L * interval ''1 day''
    )
UNION ALL
    (SELECT c.subject_id, c.itemid,
        ROUND(CAST(EXTRACT (EPOCH FROM (c.starttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_start
        FROM inputevents_mv c
        INNER JOIN define_patient_careunit a
        ON a.hadm_id = c.hadm_id
        WHERE c.icustay_id IS NULL AND
          c.starttime IS NOT NULL AND
          c.starttime >= a.icustay_intime + %L*interval ''1 day'' AND
          c.starttime < a.icustay_intime + %L * interval ''1 day''
    )
    ) TO ''/tmp/event-cui-transfer/inputevents_mv_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION write_inputevents_cv(lower_bound integer, upper_bound integer, lower_bound_str text, upper_bound_str text) RETURNS void AS
$$
BEGIN
EXECUTE format ('
COPY(
    (
        SELECT c.subject_id, c.itemid,
               ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
        FROM inputevents_cv c
        INNER JOIN define_patient_careunit a
        ON a.icustay_id = c.icustay_id
        WHERE c.icustay_id IS NOT NULL AND
              c.charttime IS NOT NULL AND
              c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND
              c.charttime < a.icustay_intime + %L * interval ''1 day''
    )
    UNION ALL
    (
        SELECT c.subject_id, c.itemid,
               ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
        FROM inputevents_cv c
        INNER JOIN define_patient_careunit a
        ON a.hadm_id = c.hadm_id
        WHERE c.hadm_id IS NOT NULL AND
          c.icustay_id IS NULL AND
          c.charttime IS NOT NULL AND
          c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND
          c.charttime < a.icustay_intime + %L * interval ''1 day''
    )
    UNION ALL
    (
        SELECT c.subject_id, c.itemid,
               ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
        FROM inputevents_cv c
        INNER JOIN define_patient_careunit a
        ON a.subject_id = c.subject_id
        WHERE c.hadm_id IS NULL AND
          c.icustay_id IS NULL AND
          c.charttime IS NOT NULL AND
          c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND
          c.charttime < a.icustay_intime + %L * interval ''1 day''
    )
) TO ''/tmp/event-cui-transfer/inputevents_cv_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION write_outputevents(lower_bound integer, upper_bound integer, lower_bound_str text, upper_bound_str text) RETURNS void AS
$$
BEGIN
EXECUTE format ('
COPY(
  SELECT c.subject_id,
         c.itemid,
         ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
  	FROM outputevents c
  	INNER JOIN define_patient_careunit a
  	ON a.icustay_id = c.icustay_id
  	WHERE c.icustay_id IS NOT NULL AND
  	  c.charttime IS NOT NULL AND
  	  c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND c.charttime < a.icustay_intime + %L * interval ''1 day''
  UNION ALL
  SELECT c.subject_id,
         c.itemid,
         ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
  FROM outputevents c
  INNER JOIN define_patient_careunit a
  ON a.hadm_id = c.hadm_id
  WHERE c.hadm_id IS NOT NULL AND
    c.icustay_id IS NULL AND
    c.charttime IS NOT NULL AND
    c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND c.charttime < a.icustay_intime + %L * interval ''1 day''
  UNION ALL
  SELECT c.subject_id,
         c.itemid,
         ROUND(CAST(EXTRACT (EPOCH FROM (c.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
  FROM outputevents c
  INNER JOIN define_patient_careunit a
  ON a.subject_id = c.subject_id
  WHERE c.hadm_id IS NULL AND
    c.icustay_id IS NULL AND
    c.charttime IS NOT NULL AND
    c.charttime >= a.icustay_intime + %L*interval ''1 day'' AND c.charttime < a.icustay_intime + %L * interval ''1 day''
) TO ''/tmp/event-cui-transfer/outputevents_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION write_microbiologyevents_withcharttime(lower_bound integer, upper_bound integer, lower_bound_str text, upper_bound_str text) RETURNS void AS
$$
BEGIN
EXECUTE format ('
COPY(
SELECT m.subject_id,
       (m.spec_itemid, m.org_itemid, m.ab_itemid) AS id,
       ROUND(CAST(EXTRACT (EPOCH FROM (m.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
FROM microbiologyevents m
INNER JOIN define_patient_careunit a
ON a.hadm_id = m.hadm_id
WHERE m.charttime IS NOT NULL AND
      m.hadm_id IS NOT NULL AND
      m.charttime >= a.icustay_intime + %L * interval ''1 day'' AND
      m.charttime < a.icustay_intime + %L * interval ''1 day''
UNION ALL
SELECT m.subject_id,
       (m.spec_itemid, m.org_itemid, m.ab_itemid) AS id,
       ROUND(CAST(EXTRACT (EPOCH FROM (m.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
FROM microbiologyevents m
INNER JOIN define_patient_careunit a
ON a.subject_id = m.subject_id
WHERE m.charttime IS NOT NULL AND
      m.hadm_id IS NULL AND
      m.charttime >= a.icustay_intime + %L * interval ''1 day'' AND
      m.charttime < a.icustay_intime + %L *interval ''1 day''
) TO ''/tmp/event-cui-transfer/microbiologyevents_withtime_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION write_labevents(lower_bound integer, upper_bound integer, lower_bound_str text, upper_bound_str text) RETURNS void AS
$$
BEGIN
EXECUTE format ('
COPY(
SELECT l.subject_id, l.itemid, ROUND(CAST(EXTRACT (EPOCH FROM (l.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
FROM labevents l
INNER JOIN define_patient_careunit a
ON a.hadm_id = l.hadm_id
WHERE l.charttime IS NOT NULL
AND l.hadm_id IS NOT NULL
AND l.charttime >= a.icustay_intime + %L*interval ''1 day'' AND l.charttime < a.icustay_intime + %L * interval ''1 day''
UNION ALL
SELECT l.subject_id, l.itemid,
       ROUND(CAST(EXTRACT (EPOCH FROM (l.charttime - a.icustay_intime))/60 AS numeric), 2) AS min_icuin_to_chart
FROM labevents l
INNER JOIN define_patient_careunit a
ON a.subject_id = l.subject_id
WHERE l.charttime IS NOT NULL AND
      l.hadm_id IS NULL AND
      l.charttime >= a.icustay_intime + %L*interval ''1 day'' AND l.charttime < a.icustay_intime + %L * interval ''1 day''
) TO ''/tmp/event-cui-transfer/labevents_%sto%shrs.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, upper_bound, lower_bound, upper_bound, lower_bound_str, upper_bound_str
);
END;
$$ LANGUAGE plpgsql;


-- For events with date but no timestamp, make sure the day occurs before the time interval
-- of interest.
CREATE OR REPLACE FUNCTION write_prescriptions(lower_bound integer, lower_bound_str text) RETURNS void as
$$
BEGIN

EXECUTE format ('
COPY(
select p.subject_id, extract (day from (p.startdate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin,
(trim(both ''"'' from p.drug_name), trim(both ''"'' from p.route), ''start'') as id
from prescriptions_generic p
inner join define_patient_careunit a
on a.hadm_id = p.hadm_id
where p.hadm_id is not null and p.icustay_id is null and p.startdate is not null
AND extract (day from (p.startdate - date_trunc(''day'', a.icustay_intime))) = %L
UNION ALL
select p.subject_id, extract (day from (p.startdate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin,
(trim(both ''"'' from p.drug_name), trim(both ''"'' from p.route), ''start'') as id
from prescriptions_generic p
inner join define_patient_careunit a
on a.icustay_id = p.icustay_id
where p.icustay_id is not null and p.startdate is not null
AND extract (day from (p.startdate - date_trunc(''day'', a.icustay_intime))) = %L
UNION ALL
select p.subject_id, extract (day from (p.enddate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin,
(trim(both ''"'' from p.drug_name), trim(both ''"'' from p.route), ''end'') as id
from prescriptions_generic p
inner join define_patient_careunit a
on a.icustay_id = p.icustay_id
where p.icustay_id is not null and p.enddate is not null
AND extract (day from (p.enddate - date_trunc(''day'', a.icustay_intime))) = %L
UNION ALL
select p.subject_id, extract (day from (p.enddate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin,
(trim(both ''"'' from p.drug_name), trim(both ''"'' from p.route), ''end'') as id
from prescriptions_generic p
inner join define_patient_careunit a
on a.hadm_id = p.hadm_id
where p.hadm_id is not null and p.icustay_id is null and p.enddate is not null
AND extract (day from (p.enddate - date_trunc(''day'', a.icustay_intime))) = %L

) TO ''/tmp/event-cui-transfer/prescriptions_%sday.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, lower_bound, lower_bound, lower_bound, lower_bound_str
);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION write_microbiologyevents_nocharttime(lower_bound integer, lower_bound_str text) RETURNS void as
$$
BEGIN

EXECUTE format ('
COPY(

select m.subject_id, (m.spec_itemid, m.org_itemid, m.ab_itemid) as id,
extract (day from (m.chartdate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin
from microbiologyevents m
inner join define_patient_careunit a
on a.hadm_id = m.hadm_id
where m.charttime is null and m.chartdate is not null
and m.hadm_id is not null
and extract (day from (m.chartdate - date_trunc(''day'', a.icustay_intime))) = %L
UNION ALL
select m.subject_id, (m.spec_itemid, m.org_itemid, m.ab_itemid) as id,
extract (day from (m.chartdate - date_trunc(''day'', a.icustay_intime))) as days_from_icuin
from microbiologyevents m
inner join define_patient_careunit a
on a.subject_id = m.subject_id
where m.charttime is null and m.chartdate is not null
and m.hadm_id is null and
extract (day from (m.chartdate - date_trunc(''day'', a.icustay_intime))) = %L
) TO ''/tmp/event-cui-transfer/microbiologyevents_notime_%sday.csv'' WITH CSV HEADER DELIMITER '';'' ;',
lower_bound, lower_bound, lower_bound_str
);
END;
$$ LANGUAGE plpgsql;
