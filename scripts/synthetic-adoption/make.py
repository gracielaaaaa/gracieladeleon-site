"""Synthetic recreation of an agent adoption metric: one fixed cutoff vs. a
per-task percentile threshold.

ALL DATA HERE IS SYNTHETIC. No company data, table names, fields, or real
distributions are used. It illustrates the method only. Parameters were tuned so the results land
near the real ones (15% to 2.8%); the synthetic numbers are not evidence of them.

Writes:
  public/data/adoption-synthetic/accounts.csv       source 1
  public/data/adoption-synthetic/agent_usage.csv    source 2 (has duplicates and orphans to clean)
  public/data/adoption-synthetic/task_volume.csv    source 3
  public/data/adoption-synthetic/truth.csv          ground truth, known only because the data is synthetic
  src/data/adoption-synthetic.json                  summary the case page renders
Then runs public/data/adoption-synthetic/adoption_metric.sql in SQLite and checks it matches.
"""
import csv, json, math, pathlib, random, sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "public" / "data" / "adoption-synthetic"
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(45)

N = 3000
TYPES = {  # typical uses per eligible task when an account really uses the agent
    "Triage": 3.0,     # fires on almost every task, so raw counts run high
    "Q&A": 0.60,
    "Actions": 0.25,
    "Requests": 0.10,
}
VOLUME = {"Triage": 3.0, "Q&A": 1.0, "Actions": 1.0, "Requests": 1.0}  # triage sees ~3x the tasks
CUTOFF = 400          # old metric: an account "adopted" if raw monthly uses >= CUTOFF
PCTL = 0.45           # new metric: usage per task at or above this percentile of its agent type

accounts, usage, volume, truth = [], [], [], []
for i in range(N):
    acc = f"A{i:04d}"
    seg = rng.choices(["Enterprise", "Mid-market", "Public sector"], [0.5, 0.35, 0.15])[0]
    typ = rng.choices(list(TYPES), [0.3, 0.3, 0.2, 0.2])[0]
    engaged = rng.random() < 0.55
    tasks = int(math.exp(rng.gauss(6.0 if seg == "Enterprise" else 5.2, 0.9)) * VOLUME[typ])
    base = TYPES[typ] * (1.0 if engaged else 0.10)
    upt = base * math.exp(rng.gauss(0, 0.6))
    uses = int(round(tasks * upt))
    accounts.append({"account_id": acc, "segment": seg})
    usage.append({"account_id": acc, "agent_type": typ, "month": "2026-06", "uses": uses})
    volume.append({"account_id": acc, "agent_type": typ, "month": "2026-06", "eligible_tasks": tasks})
    truth.append({"account_id": acc, "really_adopted": int(engaged)})

# Messy source 2: a reloaded batch (exact duplicates) and rows for accounts not in source 1.
dups = rng.sample(usage, 90)
orphans = [{"account_id": f"X{j:03d}", "agent_type": rng.choice(list(TYPES)), "month": "2026-06", "uses": rng.randint(5, 900)} for j in range(37)]
usage_raw = usage + [dict(d) for d in dups] + orphans
rng.shuffle(usage_raw)

def write(name, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
write("accounts.csv", accounts); write("agent_usage.csv", usage_raw)
write("task_volume.csv", volume); write("truth.csv", truth)

# ---- run the SQL, exactly as published ----
db = sqlite3.connect(":memory:")
for name in ["accounts", "agent_usage", "task_volume", "truth"]:
    rows = list(csv.DictReader(open(OUT / f"{name}.csv")))
    cols = list(rows[0].keys())
    db.execute(f"create table {name} ({', '.join(cols)})")
    db.executemany(f"insert into {name} values ({', '.join('?' * len(cols))})", [tuple(r[c] for c in cols) for r in rows])
sql = (OUT / "adoption_metric.sql").read_text().replace(":cutoff", str(CUTOFF)).replace(":pctl", str(PCTL))
db.executescript(sql)

def q(s): return db.execute(s).fetchall()
cleaning = {
    "usage_rows_raw": len(usage_raw),
    "duplicates_removed": q("select count(*) from agent_usage")[0][0] - q("select count(*) from (select distinct * from agent_usage)")[0][0],
    "orphans_dropped": q("select count(*) from (select distinct * from agent_usage) u where u.account_id not in (select account_id from accounts)")[0][0],
    "accounts_in_dataset": q("select count(*) from unified")[0][0],
}
def score(col):
    tp, fp, fn, tn = q(f"""select sum({col}=1 and really_adopted=1), sum({col}=1 and really_adopted=0),
                                 sum({col}=0 and really_adopted=1), sum({col}=0 and really_adopted=0) from scored""")[0]
    return {"counted": tp + fp, "true_pos": tp, "false_pos": fp, "missed": fn, "true_neg": tn,
            "fp_share": fp / (tp + fp), "recall": tp / (tp + fn)}
old, new = score("adopted_fixed"), score("adopted_pctl")
by_type = []
for t in TYPES:
    r = q(f"""select count(*), sum(adopted_fixed=1 and really_adopted=0), sum(adopted_fixed=1),
                     sum(adopted_pctl=1 and really_adopted=0), sum(adopted_pctl=1), max(threshold)
              from scored where agent_type='{t}'""")[0]
    by_type.append({"type": t, "accounts": r[0], "fixed_fp": r[1], "fixed_counted": r[2], "pctl_fp": r[3], "pctl_counted": r[4], "threshold": round(r[5], 3)})

# Python cross-check of the SQL result.
U = {u["account_id"]: u for u in usage}; V = {v["account_id"]: v for v in volume}; T = {t["account_id"]: t for t in truth}
fp_py = sum(1 for a in U if U[a]["uses"] >= CUTOFF and not T[a]["really_adopted"])
assert fp_py == old["false_pos"], (fp_py, old)

summary = {"synthetic": True, "accounts": N, "cutoff": CUTOFF, "percentile": PCTL, "cleaning": cleaning,
           "fixed": old, "percentile_metric": new, "by_type": by_type}
(ROOT / "src" / "data").mkdir(exist_ok=True)
(ROOT / "src" / "data" / "adoption-synthetic.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({"cleaning": cleaning, "fixed": old, "pctl": new}, indent=1)); print(by_type)
