# Assessor key: incident desk

Keep separate from the candidate brief. This key describes constructed inputs; no credit depends on naming a real provider incident.

| Calculation | Expected result |
|---|---|
| Minute 4 short | `(300+240)/12000 / .001 = 45` |
| Minute 4 long | `(120+300+240)/30000 / .001 = 22` → page |
| Minute 6 short | `0/12000 / .001 = 0` |
| Minute 6 long | `(120+300+240)/30000 / .001 = 22` → AND clears |
| Amplification | Offered rate 160/s versus original baseline 80/s = 2× observed aggregate; sample nesting alone does not prove the worst case occurs for every user |
| Minute 2 queue | `(160-10)×60 = 9000` added |
| Minute 3 queue | Another 9000 → 18000 |
| Minute 4 queue | `(160-100)×60 = 3600` → 21600 despite dependency recovery |
| End minute 5 | 20400; spare completion 100−80 = 20/s → ideal 1020 seconds to drain |
| End minute 6 | 19200 → 960 seconds to drain, before expiry or capacity changes |
| All-critical follow-up | 120−100 = 20/s deficit; each minute adds 1200 or forces refusals/expiry |

The supplied oldest-age estimates are measurements, not derivable from queue length alone; changing retry mix changes which oldest item remains. Exact FIFO order and arrival-age distributions are not provided. Do not infer them using Little's law during this transient. Client and SDK retry fragments show overlapping retry ownership, but not the original latency trigger. Need dependency utilization, service-time distribution, per-client attempts, queue age distribution, and change history to diagnose further.

Score each 0–2 (0 absent/wrong, 1 partly correct, 2 correct with evidence):

1. Units and SLO: calculates both windows and identifies distinct read versus refresh denominators.
2. Queue and recovery: derives growth and finite drain with fresh traffic, names fluid-model assumptions.
3. Safe mitigation: caps retry work/intake, protects recovery access, watches useful throughput and downstream latency; does not blindly increase concurrency.
4. Uncertainty: separates observed trigger from sustaining mechanism; states a falsifiable next investigation.
5. Changed constraint: handles expired/superseded jobs and explicit critical refusal; preserves accepted job identity.
6. Lead scope: names budget enforcement/owners across four teams, telemetry loss behavior, stop/rollback criteria and user impact.

Constructed calibration: senior target 8/10 on the first five, with no zero in units or mitigation; lead extension adds row six, target 10/12. These are practice thresholds, not employer pass scores. Reattempt with changed rates and a different hidden retry owner; reciting this key is not assessment evidence.
