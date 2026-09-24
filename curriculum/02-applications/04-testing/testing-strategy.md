# Choose checks that reveal the behavior a change can break

An account page lets Ada change the email address she uses to sign in. The update returns success, but her next login fails. The update handler and login handler disagree about how the address is stored or compared. A check that only inspects the update's success message would miss the broken journey.

This lesson teaches how to choose evidence for a particular behavior. You will define an expected result, choose which real boundaries the check needs to cross, and explain what a passing result does and does not establish. The testing exercises are sample projects to study, not a requirement to add gates to every repository.

## Define the behavior before selecting the tool

For this constructed product, email comparison is case-insensitive under a documented normalization policy. A new address must be confirmed before replacing the login address. Those are application choices, not universal rules to infer from an email string.

| Starting state and action | Expected observation |
|---|---|
| Ada requests a new address | Existing login continues working until confirmation |
| Ada confirms the new address | New address can authenticate under the chosen comparison policy |
| Another account already owns the normalized address | Change is rejected without damaging either account |
| Confirmation expires | Existing identity remains usable |

The expected result is an **oracle**: the criterion used to judge what happened. If it comes only from copying the implementation, it may repeat the same misunderstanding.

For example, `assert result == result` always agrees with itself. It supplies no evidence that Ada can log in. A useful check asks the login boundary to authenticate after the confirmed update and compares the result with the contract above.

## Choose the smallest boundary that can reveal the failure

| Check | What runs | What it can reveal | What it does not establish |
|---|---|---|---|
| Unit | A normalization function with explicit inputs | Inconsistent handling of case or invalid values | Whether the real database stores the result correctly |
| Integration | Update and login logic using a real disposable database | Mismatched stored/query representations and constraints | Whether browser focus and messages are usable |
| Contract | One service's wire messages against agreed consumer expectations | Renamed fields, changed units or unsupported status behavior | Every runtime property of the full deployment |
| End-to-end | The visible update/confirm/login journey | Whether the assembled user flow works in that environment | Every input, device, dependency failure or future release |

![Different checking boundaries trade isolation and execution cost against the parts of the running system they exercise.](../../../assets/diagrams/test-tradeoff.svg)

No fixed ratio of check types solves every system. Start from the consequence of being wrong and the boundary that owns it. A tiny pure function may need no browser. A database transaction claim needs evidence from the database behavior being claimed.

## Work through the email regression

A useful reproduction has three phases:

1. Create an account with a known login address and confirm it can sign in.
2. Execute the real address-change and confirmation operations.
3. Sign in using the new address and inspect the stored identity if it fails.

Keep external mail delivery controlled so it does not introduce unrelated waiting. Preserve the actual database and normalization path when those are the suspected cause. A **fake** is a substitute dependency with controlled behavior. A **mock** commonly records or supplies expected interactions. Neither substitutes for the real integration when its behavior is the claim.

Suppose the update stores a normalized lowercase value, while login still compares against an unnormalized input. Record both values and the query predicate. A repair should use the agreed policy consistently. Do not merely change the expected result to accept failed login.

**Evidence to hand over:** the starting account, the operation sequence, the old failure, the repaired result and the boundary exercised. Keep secrets and real personal addresses out of the example.

## Use a known defect to check sensitivity

A **negative control** deliberately introduces a known wrong behavior in an isolated exercise. Restoring the inconsistent normalizer should make the relevant login check fail. That establishes sensitivity to this particular defect.

A passing first run can still be useful when its expectation is independently justified. Conversely, seeing one deliberate failure does not prove that every other defect will be caught. Some source changes are equivalent under the supported contract and should not produce a failure.

| Observation | Appropriate conclusion |
|---|---|
| Known normalization defect is detected | This case catches that defect |
| Repaired implementation passes the same case | This case supports the repair |
| Equivalent refactor remains passing | Expected if the supported behavior is unchanged |
| Twenty selected mutations are caught | Those twenty sampled changes were detected |
| A dependency was replaced with a fake | Claims stop at the controlled boundary unless separately exercised |

Do not secretly plant defects in a real teammate's work. Keep deliberate faults labeled and disposable.

## Control time and ordering when they cause the defect

A **flaky** check changes outcome under supposedly equivalent conditions. Shared state, uncontrolled time, network dependencies and races are possible causes. Retrying until green can hide the evidence rather than repair the cause.

For a browser race, pause response A, complete response B, then release A. That forces the ordering the contract must handle. A long sleep only makes the race more or less likely. For timeout logic, an injected clock can make time progression explicit. Use the real clock separately when measuring actual elapsed performance.

The [search-race lab](../03-frontend/labs/search-race/README.md) and [bookmark editor](../03-frontend/labs/bookmark-editor/README.md) show the user-visible state that ordering must preserve. The [flake investigation project](projects/03-the-flake-hunter.md) develops diagnosis and quarantine policy.

## Keep failure reports useful

A report should distinguish assertion failure, timeout, crash, skipped execution and unavailable infrastructure. “Not run” is not a pass. Preserve the input and enough state to reproduce the result.

Use names describing the behavior, such as preserving a newer draft after an earlier save. An assertion should show the relevant expected and observed values. Avoid forcing one giant scenario to diagnose every subsystem at once, but keep the full journey where integration is the risk.

If a check is temporarily removed from a blocking decision, record the coverage gap, owner and expiry. The choice of automated gates belongs to the application's operating policy. It should be proportionate to the actual risk and workflow.

## Practice with an unfamiliar implementation

For a small starting example, use the [quantity investigation](labs/quantity-debug/README.md): zero is valid input, omission means no change, and null needs an explicit policy. For a larger exercise, use the [transaction importer](labs/importer/README.md), which includes multiple modules and real persistence boundaries.

Before opening a reference answer, state the user contract and predict the normal, empty, invalid and interrupted outcomes that matter. Run or inspect the relevant path, locate the cause and make a coherent repair. Then explain what remains unexamined. The goal is evidence that another engineer can evaluate, not a large count of passing checks.
