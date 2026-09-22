# Withdrawal register for the original research notes

**Status: superseded, 2026-09-22. Do not cite the original 2026-09-21 notes as evidence.** They combined search snippets, author interpretation, historical guidance and exact figures without retaining a retrievable claim-level trail. The original prose is preserved in git history, not silently re-dated.

| Original claim family | Why withdrawn / replacement |
|---|---|
| “Never retry 4XX”; 1h + 6h described as a short/long pair | Incorrect blanket classification and incomplete alert logic; see C01–C02 and executable arithmetic. |
| Netflix prefetch multiplier and availability percentages | Exact original article, event date and applicable workload were not retained; replaced by clearly constructed capacity inputs. |
| Faros PR/review figures; DORA sample/results; GitGuardian survival; passkey/CI/IaC shares | Sample definitions, exact pages and limits absent; no figure is accepted from a named vendor alone. |
| OTel graduation date and all-SDK stability; industry-default Redis/Valkey/OpenTofu/Kafka language | Current claims need exact dated/versioned primary evidence; narrow technical references only in C11–C13. |
| Profiling overhead/cost savings; universal cache-hit targets and lock TTL rules | Workload-sensitive values falsely generalized; measure overhead, exclusion and expiration behavior in the target system. |
| Security incident counts; publishing/provenance shortcuts; universal legal floors | Exact original source/date/scope not established; source-specific verification required before reuse. |
| “Coordination-free” architecture from S3 compare-and-swap | An object precondition is not proof of a whole protocol's safety/liveness; C11 limits the claim. |
| Research search/fetch counts and declarations marked “VERIFIED” | An audit trail of tool activity cannot substitute for source-to-claim provenance. |

The [claim ledger](claim-ledger.md) records what survived, the exact sources inspected, and which assertions were removed. Absence of a replacement means unresolved evidence, not permission to supply a plausible citation.

A direct recheck of [the original AWS Builders’ Library timeout article](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) on 2026-09-22 redirected to a Builder Center page whose text was not extractable. Its original attribution is not counted as newly verified evidence. The chapter retains a clearly constructed percentile tradeoff; verified SDK retry semantics use C02.
