-- Agent adoption metric on SYNTHETIC data (SQLite). Illustrates the method only.
-- Parameters: :cutoff (old fixed cutoff on raw monthly uses), :pctl (new per-type percentile, 0 to 1).

-- 1. Clean source 2: drop exact duplicate rows from a reloaded batch.
create table usage_clean as
select distinct account_id, agent_type, month, cast(uses as integer) as uses
from agent_usage;

-- 2. Unify the three sources into one dataset. Inner joins drop usage rows for unknown accounts.
create table unified as
select a.account_id, a.segment, u.agent_type, u.month, u.uses,
       cast(v.eligible_tasks as integer) as eligible_tasks,
       1.0 * u.uses / cast(v.eligible_tasks as integer) as uses_per_task
from usage_clean u
join accounts a on a.account_id = u.account_id
join task_volume v on v.account_id = u.account_id and v.agent_type = u.agent_type and v.month = u.month;

-- 3. Rank each account's usage per task within its own agent type.
create table ranked as
select *, percent_rank() over (partition by agent_type order by uses_per_task) as type_pctl
from unified;

-- 4. Score both definitions. The threshold is the lowest qualifying usage per task in each type.
create table scored as
select r.*, t.really_adopted,
       case when r.uses >= :cutoff then 1 else 0 end as adopted_fixed,
       case when r.type_pctl >= :pctl then 1 else 0 end as adopted_pctl,
       (select min(uses_per_task) from ranked r2 where r2.agent_type = r.agent_type and r2.type_pctl >= :pctl) as threshold
from ranked r
join (select account_id, cast(really_adopted as integer) as really_adopted from truth) t on t.account_id = r.account_id;
