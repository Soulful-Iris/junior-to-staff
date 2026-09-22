# Review assessor key

| PR | Decision and minimal reproduction | Regression / lead follow-through |
|---|---|---|
| 101 | Block. Store `a,29,USD`, then `a,200,USD`; removing equality check silently accepts a conflicting event | `test_conflicting_duplicate_rolls_back_page`; preserve atomic page rollback and assign finance/partner owners to conflict resolution |
| 102 | Block as written pending service-contract decision. 429 Retry-After 0.75 becomes retry at 0.05 | `test_retry_timing` must still observe 0.75; request an explicit protocol change before releasing early retry behavior |
| 103 | Approve bounded metadata change with a logging assertion; status and attempt contain no transaction payload | Assert one record per transport response and no IDs/amounts; exceptions before response still require error metrics separately |

A strong review distinguishes severe data loss from protocol/operational risk, then
recognizes a narrowly useful change. Rejecting all three without causal evidence is
not strong review. Run the reference tests first, apply a patch only in a disposable
copy, and show the named regression fail. The PRs omit unrelated surrounding context
on purpose; ask to inspect it. See [practice scoring](../../../../../../practice/assessor/practical-debug.md).
