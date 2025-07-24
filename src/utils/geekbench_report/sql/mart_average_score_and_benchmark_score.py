sql = """-- Base dataset: only the relevant columns
with base as (
	select
		cpu_model_id,
		single_core_score,
		multi_core_score,
		uploaded
	from cpu_model_results
),

-- Main stats: mean, stddev, median, min/max, and counts
with_stats as (
	select
		cpu_model_id,
		AVG(single_core_score) as mean_single_core_score,
		STDDEV_POP(single_core_score) as stddev_single_core_score,
		PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY single_core_score) as median_single_core_score,
		AVG(multi_core_score) as mean_multi_core_score,
		STDDEV_POP(multi_core_score) as stddev_multi_core_score,
		PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY multi_core_score) as median_multi_core_score,
		MAX(single_core_score) as max_single_core_score,
		MIN(multi_core_score) as min_multi_core_score,
		MAX(uploaded) as max_uploaded,
		MIN(uploaded) as min_uploaded,
		COUNT(*) as data_count
	from base
	group by cpu_model_id
),

-- Trimmed mean: exclude first and last rows after sorting for each score
trimmed as (
	select
		cpu_model_id,
		AVG(single_core_score) as trimmed_mean_single_core_score,
		AVG(multi_core_score) as trimmed_mean_multi_core_score
	from (
		select
			cpu_model_id,
			single_core_score,
			multi_core_score,
			row_number() over (partition by cpu_model_id order by single_core_score) as rn_single,
			row_number() over (partition by cpu_model_id order by multi_core_score) as rn_multi,
			count(*) over (partition by cpu_model_id) as cnt
		from base
	) ranked
	where
		-- remove first and last records for trimmed mean
		rn_single > 1 and rn_single < cnt
		and rn_multi > 1 and rn_multi < cnt
	group by cpu_model_id
),

cpu_codename_dim as (
	select
		cpu_model_id,
		max(cpu_codename) as cpu_codename
	from cpu_model_details
	group by cpu_model_id
),

-- Final output: combine stats and model name
final_table as (
	select
		dim.cpu_model,
		detail.cpu_codename,
		ROUND(s.mean_single_core_score) as mean_single_core_score,
		ROUND(s.stddev_single_core_score) as stddev_single_core_score,
		ROUND(s.median_single_core_score) as median_single_core_score,
		ROUND(t.trimmed_mean_single_core_score) as trimmed_mean_single_core_score,
		ROUND(b.single_core_score) as benchmark_single_core_score,
		ROUND(s.mean_multi_core_score) as mean_multi_core_score,
		ROUND(s.stddev_multi_core_score) as stddev_multi_core_score,
		ROUND(s.median_multi_core_score) as median_multi_core_score,
		ROUND(t.trimmed_mean_multi_core_score) as trimmed_mean_multi_core_score,
		ROUND(b.multi_core_score) as benchmark_multi_core_score,
		ROUND(s.max_single_core_score) as max_single_core_score,
		ROUND(s.min_multi_core_score) as min_multi_core_score,
		s.max_uploaded,
		s.min_uploaded,
		s.data_count
	from with_stats s
	left join trimmed t
		on s.cpu_model_id = t.cpu_model_id
	left join cpu_model_names dim
		on s.cpu_model_id = dim.cpu_model_id
	left join cpu_model_benchmarks b
		on dim.cpu_model = b.cpu_model
	left join cpu_codename_dim detail
		on s.cpu_model_id = detail.cpu_model_id
-- 	order by dim.cpu_model
)

select
	cpu_codename as "Generation",
	cpu_model as "Processor name",
	median_single_core_score as "Single core (Median)",
	median_multi_core_score as "Multi core (Median)",
	benchmark_single_core_score as "Single core (Ranking)",
	benchmark_multi_core_score as "Multi core (Ranking)",
	mean_single_core_score as "Single core (Mean)",
	mean_multi_core_score as "Multi core (Mean)",
	trimmed_mean_single_core_score as "Single core (Mean excl. max/min)",
	trimmed_mean_multi_core_score as "Multi core (Mean excl. max/min)",
	max_single_core_score as "Max for single core",
	min_multi_core_score as "Min for Multi core",
	stddev_single_core_score as "Std for Single core",
	stddev_multi_core_score as "Std for Multi core",
	max_uploaded as "The lastest upload",
	min_uploaded as "The earliest upload",
	data_count as "Data count"
from final_table
order by cpu_codename
;"""
