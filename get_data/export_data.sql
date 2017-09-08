set search_path to mimiciii_1v3;
do
$$
declare
  lower_limit integer;
  upper_limit integer;
  lower_limit_str text;
  upper_limit_str text;
begin
    lower_limit := 0;
    upper_limit := lower_limit + 1;
    raise notice 'day=%', lower_limit;
    lower_limit_str := (lower_limit * 24)::text;
    upper_limit_str := (upper_limit * 24)::text;
    raise notice 'hour lower=%', lower_limit_str;
    raise notice 'hour upper=%', upper_limit_str;

    raise notice 'table = microbiologyevents_withtime';
    perform write_microbiologyevents_withcharttime(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = chartevents';
    perform write_chart_events_with_value(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = labevents';
    perform write_labevents(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = input_mv';
    perform write_inputevents_mv(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = input_cv';
    perform write_inputevents_cv(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = output';
    perform write_outputevents(lower_limit, upper_limit, lower_limit_str, upper_limit_str);

    raise notice 'table = prescriptions';
    perform write_prescriptions(lower_limit, lower_limit::text);

    raise notice 'table = microbiologyevents_notime';
    perform write_microbiologyevents_nocharttime(lower_limit, lower_limit::text);
end$$;
