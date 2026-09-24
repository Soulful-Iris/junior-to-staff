# Full stack · one user action across every boundary

[Curriculum](../../README.md) · [Connect a usable interface to an API](README.md)

A bookmark title travels through three places: the text field where Alice edits it, the API that accepts the save, and the database that stores the confirmed version. While the save is travelling, Alice can type more. This lesson connects those three places so a delayed response does not erase her newer text.

![The supplied bookmark editor preserves a newer draft after an earlier title has been saved.](../../../assets/ui-lessons/bookmark-confirmed-draft.png)

In the screenshot, the server has version 2 of the shorter title. The input still contains the longer draft. Follow the runnable editor below to inspect its HTTP request, conditional database write and guarded browser update. Your task is to explain and reproduce that behavior, then handle the conflict case where another writer changes the record first.

> “A save looks successful but erases the user's next edit. Follow that action through
> the browser, API and database, then prove the repair under a delayed response.”

Start with [the runnable bookmark editor](labs/bookmark-editor/README.md): HTML/TypeScript,
HTTP routing, SQLite schema/store, owner/version checks, stable tied cursor, idempotent
retry and controlled browser races. It includes local commands, a measured query
improvement, error/empty/retry behavior and keyboard focus checks.

| Route | Purpose |
|---|---|
| [Search race prerequisite](labs/search-race/README.md) | Generations and ignored cancellation |
| [Bookmark editor](labs/bookmark-editor/README.md) | Draft, confirmed, pending mutation and editor lifetime in a real slice |
| [Candidate assessment](../../../practice/candidate/full-stack.md) | Independent attempt before reading reference code |
| [Assessor pack](../../../practice/assessor/full-stack.md) | Held-back schedules, anchors and debrief |

Original illustrations: [browser race](../../../assets/learning/browser-race.svg),
[its static view](../../../assets/learning/browser-race-still.svg),
[independent I/O](../../../assets/learning/io-waterfall.svg), and
[its static view](../../../assets/learning/io-waterfall-still.svg).

Background enrichment remains an extension build brief: write the bookmark and outbox
intent in one transaction; relay duplicates are possible; the worker deduplicates and
applies only a result for the current bookmark version. The supplied editor does not
implement that extension. See the [queue lab](../../03-production/03-infrastructure/aws/labs/job-pipeline/README.md).

Tie rendering choices and virtualization to measurements: query count, payload, input
responsiveness and failed-save behavior. A spinner cannot compensate for erased input.
Senior evidence is independent race correctness plus server authorization; lead scope
adds client/API compatibility, observability, rollout ownership and migration decisions.

[Interview home](../../../practice/interview-guide.md) · [Practical coding](../../../indexes/practical-exercises.md)
