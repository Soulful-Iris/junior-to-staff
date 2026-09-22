# Assessor notes: cache and authorization boundaries

Keep this separate from the candidate attempt. These are constructed exercises;
passing reference tests does not establish independent interview readiness.

| Observation | Senior evidence | Lead extension |
|---|---|---|
| One key, ten instances | Counts 1 local versus 10 isolated loads and identifies coordination state | Explains shared limiter or lease failure and tenant budgets |
| Loader fails or is cancelled | Every waiter finishes; slot/flight cleanup; one waiter cannot cancel others | Shutdown, deadlines and all-waiters-gone policy |
| Cache outage | 100 admissions/rolling second, peak 10, 900 rejections in fixture | Fleet-wide dependency allocation and limiter outage policy |
| Lag outlasts stickiness | Shows v7 counterexample then watermark/primary/unavailable choice | Failover epoch and acknowledged-data-loss boundary |
| Warm revoked link | Distinguishes cached object from authorization decision; exact 403/503 | Propagation/clock/error budget and regional evidence |

Score each row 0 (unsupported), 1 (explained), or 2 (independently demonstrated
with a failing counterexample and corrected result). Do not average into a hiring
prediction. Retry a changed prompt: cancel all 200 waiters while the origin hangs;
or make ten processes each own a separate 100/s gate. Expected reasoning names
the missing loader deadline or the multiplied 1,000/s fleet budget before adding
technology. Revocation is incomplete if the learner tests only a cold cache.
