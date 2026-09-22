# 19 · Migrations — five projects

> Staff tier · each one an afternoon · read [the section](README.md) first

Five projects that follow the three phases in order, with de-risk and finish
each getting two, because those are the ones people get wrong in opposite
directions: de-risk by starting with the easiest case, and finish by not
finishing.

The last project is the one that matters. Everything before it is cost, and the
value arrives entirely at the end — so a set of migration projects that stops
before the deletion is the same failure the section is about, rehearsed.

![Two counts of an old system's usage over six months: call sites in the code fall to zero and the migration is declared complete, while requests still hitting the old path have not](../../../assets/diagrams/counter-vs-traffic.svg)

---

### 1. The hardest case first

*You end up having migrated the most awkward user of the old system, and with a written list of what that taught you that the plan had wrong.*

**Build**

Rank everything that uses the old system by *awkwardness*, not by size. Take
the worst one and migrate it. Write down every assumption in your plan that
turned out to be false — there will be some, and that list is the deliverable.

**The thought process**

The first idea is counterintuitive enough that almost everybody does the
opposite: **migrating the simplest service first tells you nothing**, because
the simplest service was never the reason the migration is hard. It produces a
satisfying early win, a plan with false confidence behind it, and a discovery
in month six that would have been available in week two.

Second, what you are buying in this phase is **information, not progress.** The
easy cases have none in them. Find the team with the weirdest usage — the one
that depends on ordering, or uses a feature the new system does not have, or
has a deadline nobody can move — and get them across.

Third: **awkwardness is a structural property, not a size one.** A large
service that uses the old system in the ordinary way is a lot of work with no
information in it. A small service that relies on an implicit behaviour nobody
documented is where the plan breaks. Rank by "what about this does not fit the
new model" rather than by call-site count.

Fourth, and this is what makes the phase honest: **the hardest case will change
your design.** If you migrate it and nothing about your plan was wrong, either
you picked the wrong case or you have not looked carefully. Something is
always missing — a semantics difference, a performance characteristic, an
operational assumption — and finding it early is the entire point.

Fifth: **do it with the team, not to them.** The hardest case usually belongs
to the most sceptical team, and for good reason — they know things about their
usage that are not written down. Their scepticism is the information you came
for.

**How to organise the prompts**

```
Here is the system being migrated and the list of things that use it.

Rank them by how AWKWARD they will be to migrate, not by size. I want
the one most likely to reveal something the plan has not accounted
for.

For the top one, tell me what specifically about it does not fit the
new model.
```

The default is to rank by effort and start small. Asking for awkwardness
inverts it.

```
For the hardest case: list the behaviours of the old system it relies
on that are not in any documentation — implicit ordering, error
semantics, timing, side effects.

How would I confirm each one, from the code or from production?
```

Implicit behaviour is where migrations break, and it is by definition not in
the spec.

```
I migrated it. Here is what went wrong: <list>. For each, tell me
what it implies about the rest of the migration — which other users
are affected by the same thing, and what changes in the plan.
```

```
Given what I learned, is the new system still the right target? Argue
the case for stopping now, honestly.
```

That last question is worth asking sincerely at the end of phase one. Stopping
after the hardest case is the cheapest place to stop, and it is the only point
where stopping is a decision rather than an abandonment.

**On AWS**

Two AWS capabilities make de-risking cheaper than it used to be, and both are
about rehearsing against real data rather than a fixture.

**Aurora fast database cloning** gives you a copy-on-write clone of a
production-sized database in minutes, at negligible storage cost until you
write to it. That means "run the hardest case against real data volumes before
committing" stops being something you skip. **RDS snapshots restored into a
scratch account** is the slower equivalent for non-Aurora engines.

**AWS Database Migration Service** with ongoing replication (change data
capture) is the tool when the migration is between datastores, and the reason
it belongs in phase one rather than phase two is that it lets you run the new
system against live data *before* anything depends on it. Its validation
feature compares source and target row by row, which is the closest thing to a
free parity check you will get.

For the traffic side, this is where the strangler-fig shape earns its
reputation: an **Application Load Balancer** with path-based rules, or
**API Gateway** with per-route integrations, lets you move one route at a time
to the new implementation. The hardest case is one rule change and one rule
change back, which is what makes trying it cheap.

And record the operational differences you find, because they are the ones the
design document will have missed: cold start behaviour, connection limits,
throttling responses, and what happens at your **Service Quotas** on the new
service, which start at defaults.

**What productionising it means**

The hardest case is genuinely migrated and running in production, not
demonstrated in a branch. What it taught is written down where the rest of the
migration can read it, including the parts that make the plan worse. The team
that owns it agreed it was done rather than you declaring it. And the design
document has been updated, because a plan that survived contact unchanged was
not tested.

**The learning**

Phase one is an experiment, not progress, and its success condition is finding
out that you were wrong about something. The reason teams start with the easy
case is that it feels like momentum — and momentum built on a case that was
never representative is what produces the month-six surprise that kills
migrations.

**How you would know it is wrong**

- Ask which case you migrated first and why. If the answer is "the easiest", the plan is untested.
- Check whether anything in the plan changed. Nothing changing means you did not learn anything.
- List the implicit behaviours you found. If the list is empty, you have not looked at the old system hard enough.
- Confirm the owning team agrees it is migrated. Your definition of done and theirs differ more often than you expect.
- Ask whether you would still start this migration knowing what you now know. Phase one is the cheapest place to answer no.

---

### 2. The parity check that can disagree

*You end up running both systems against the same real input and with a count of the cases where they differ — including at least one real divergence you did not expect.*

**Build**

Run the old and new paths against the same live traffic, compare the results,
and record every difference. Do it without the new path affecting anybody: read
from both, serve the old, log the divergences. Then investigate each class of
difference and decide whether it is a bug or an intended change.

**The thought process**

The first idea is why this beats testing: **you cannot write test cases for the
behaviour you do not know the old system has.** Every long-lived system has
accumulated semantics nobody documented — how it rounds, what it does with an
empty list, which error it returns for a malformed input. A parity check
against real traffic finds those without anybody having to remember them.

Second, the shape that makes it safe: **compare in the shadow, serve from the
old.** The new path runs, its result is compared and logged, and nobody
receives it. That means a divergence is a log line rather than an incident, and
you can run it for a week at full traffic before committing to anything.

Third, and this is the part that requires judgment rather than tooling:
**not every divergence is a bug.** Some are intended improvements — the new
system fixes something the old one got wrong. Each difference has to be
classified, and that classification is a decision about what the system's
behaviour *should* be, made deliberately, which is the most valuable side
effect of the whole exercise.

Fourth, the trap: **a comparison that normalises too eagerly proves nothing.**
If you sort both results, round both numbers, and ignore field order before
comparing, you have written a check that passes on systems that behave
differently. Start strict, look at what fires, and relax deliberately with a
recorded reason for each relaxation.

Fifth: **count the divergence rate and drive it down as a number.** "They
mostly agree" is not a finish condition. "0.02% divergence, all in one known
and accepted class" is.

**How to organise the prompts**

```
I want to run the old and new implementations against the same live
traffic, compare results, and serve only the old one.

Design it: where the comparison happens, what it costs in latency on
the serving path, how failures in the new path are prevented from
affecting the request, and what gets logged on a difference.
```

The cost-and-isolation questions come first because a shadow comparison that
can break the real request is worse than no comparison.

```
Write the comparison strictly: exact equality, no normalisation.
Then tell me which normalisations I will be tempted to add, and for
each, what behaviour difference it would hide.
```

This is the prompt that keeps the check honest. Every normalisation is a
blindness you are choosing.

```
Here are the divergences from one day, grouped: <data>. For each
class, tell me whether it is the new system being wrong, the old
system being wrong, or an intended change — and cite the evidence.
```

```
What classes of difference would this comparison NOT catch? Side
effects, timing, anything that is not in the response body.
```

That last one matters, because the parity check compares outputs and most of
the dangerous differences are in effects — a write that happens twice, an email
that does not get sent, a cache that is not invalidated.

**On AWS**

The shadow comparison has a few good shapes on AWS, and which one fits depends
on where you can intercept.

The simplest is **in your own code**: call both, compare, return the old,
publish a **CloudWatch** metric with a dimension for the divergence class, and
write the details to **CloudWatch Logs** or **S3** for inspection. Metric plus
detail is the right split — the metric tells you the rate, the log tells you
what happened, and putting the full payloads in a metric is
[10 · Observability](../../02-senior/10-observability/)'s cardinality mistake.

Do the new-path call asynchronously, or with a short timeout and a swallowed
error, so the shadow cannot slow or break the real request. That is the single
most important implementation detail and it is easy to get wrong.

For data migrations rather than request paths, **DMS data validation** compares
source and target continuously and reports mismatches, which is the same idea
at the row level. For a point-in-time comparison of two datasets, exporting
both to **S3** and running an **Athena** `EXCEPT` query is unglamorous and very
effective — it gives you the rows that differ, not a percentage.

If the new path is a separate service, **Step Functions** with a parallel state
gives you both results and a comparison step with retries and error isolation
handled for you, which is worth it when the calls are slow or expensive.

And watch the cost: a shadow comparison doubles the work for the duration. Tag
it, put it in **Cost Explorer**, and know what the week is costing — because
that number is also your estimate for the dual-running cost in project 5.

**What productionising it means**

The shadow path cannot affect the served request, and somebody has verified
that by making the new path fail deliberately. The divergence rate is a metric
with a graph. Every accepted class of divergence is written down with its
reason. The comparison is strict, with each relaxation recorded. And there is a
target divergence rate that is part of the cutover criteria rather than a
feeling.

**The learning**

The specification of a long-lived system is its behaviour, not its
documentation, and the only honest way to discover that specification is to run
the old thing and the new thing side by side against real input. This is the
same instinct as a test that can fail, applied at the scale of a whole system:
a comparison that never disagrees is a comparison that is not comparing.

**How you would know it is wrong**

- If the divergence rate is zero on day one, check that both paths actually ran. Zero is suspicious.
- Break the new path deliberately and confirm the served request is unaffected.
- Read your normalisations. Each one is a class of difference you chose not to see.
- Ask what the comparison misses — side effects, timing, anything outside the response.
- Classify every divergence. An unclassified difference at cutover is a bug you agreed to ship.

---

### 3. Make it cheap for everybody else

*You end up with tooling that does most of the remaining migration work, and an honest measure of how many hours you pushed onto the teams being migrated.*

**Build**

Write the codemod, the compatibility shim, the generator — whatever moves the
work off the teams being migrated and onto the migration. Then measure it: for
the next case you migrate, count the hours that landed on the owning team
versus on you.

**The thought process**

The first framing is the measure of this whole phase: **how little of the work
lands on the teams being migrated.** Every hour you push onto them is an hour
they will spend arguing about priority instead of migrating, and correctly so —
your migration is not on their roadmap. A migration that requires each team to
do a day of work is a migration that will take years.

Second, the specific artefact that changes the economics: **a codemod.** A
program that rewrites the code mechanically is the difference between a
migration and a request. It does not have to handle every case — if it handles
80% and flags the rest, you have converted a day of work per team into an hour
of review.

Third, the compatibility shim, which is the underrated one: **make the old
interface work against the new implementation.** If callers can keep their call
sites and get the new behaviour, most of the migration happens without anybody
doing anything. The shim then becomes the thing you delete in phase three,
which is a much smaller and more tractable piece of work than chasing every
caller.

Fourth: **write the migration guide as a diff, not as prose.** "Here is
precisely what changes in your code, and here is the command that does it" is
usable. A page of explanation is a thing people put off reading.

Fifth, and this is the honest scoping: **some cases will not be mechanisable**,
and you should know which early. Those are the ones that need a conversation
and a calendar entry, and treating them like the rest is how a migration stalls
at the last five teams.

**How to organise the prompts**

```
Here is the change each caller needs to make: <before and after>.

Write a codemod that does it automatically. It must handle the common
shapes and FLAG anything it cannot safely transform rather than
guessing.

Show me the list of shapes it refuses, with an example of each.
```

The refusal list is the important output. A codemod that silently guesses is
worse than no codemod.

```
Now the shim: can the old interface be implemented on top of the new
system so existing callers work unchanged? What does that cost in
behaviour or performance, and what would I have to give up?

If it is not possible, tell me what specifically prevents it.
```

```
For the cases the codemod refuses: group them, and tell me which
groups are worth extending the tool for versus doing by hand. Give me
the count in each group.
```

```
Write the migration guide as a diff plus a command, not as prose.
Then tell me what a caller still has to think about after running it.
```

**On AWS**

The infrastructure equivalent of a codemod is worth naming, because most
migrations at this tier have an infrastructure half.

If teams define infrastructure with **CDK**, the migration can ship as a new
version of an internal construct — teams upgrade a dependency and get the new
shape. That is the cheapest possible migration mechanism and it is one of the
strongest arguments for having built the construct library in
[18 · Technical strategy](../18-technical-strategy/)'s project 3. With
CloudFormation the equivalent is an updated template plus a stack update; with
Terraform or OpenTofu it is a module version bump and, where resources are
being replaced rather than changed, `moved` blocks or state surgery — which is
the part to rehearse in a scratch account first.

For data movement at scale, **DMS** for databases and **DataSync** or
**S3 Batch Operations** for objects do the bulk work with retries and progress
tracking built in, which is a lot of undifferentiated code you do not have to
write. **Step Functions** with a distributed map is the right orchestration
when you are migrating millions of items and need checkpointing, because the
thing you will actually need is the ability to stop halfway and resume.

And the shim has a concrete form at the network layer: keep the old endpoint
alive and have it proxy to the new service, via **API Gateway** or an
**ALB** rule. That way callers do not have to change anything at all, and the
migration becomes yours to finish rather than theirs — which is exactly the
transfer of work this phase is about.

**What productionising it means**

The codemod is in the repository and runs on demand, not a script on somebody's
laptop. The refusal cases are enumerated with counts. The shim exists, is
documented as temporary, and has a removal ticket. The guide is a diff and a
command. And the hours-per-team number is tracked, because it is the honest
measure of whether this phase worked.

**The learning**

A migration's speed is set by how much work each affected team has to do, not
by how much you have to do — because their willingness is the constraint, not
their capability. The shift that makes migrations finish is treating the
migration itself as the thing that does the work, with the teams as reviewers
rather than participants.

**How you would know it is wrong**

- Count the hours that landed on the owning team for the last case. If it is more than an hour, this phase is not done.
- Check that the codemod refuses rather than guesses. Silent wrong transformations are the worst outcome available.
- Ask whether a shim was possible. If nobody considered one, consider it now — it is usually the cheapest path.
- Read the guide. If it is prose rather than a diff and a command, people will put it off.
- Look at the cases the tool cannot handle. If you do not know how many there are, the end of the migration is unplanned.

---

### 4. The block and the counter

*You end up with a build that fails when somebody adds new usage of the old system, and a number for how much is left that you have verified against reality.*

**Build**

Two artefacts. A mechanical block — a lint rule, a CI check, a failing import —
that makes adding new usage of the old system fail the build, demonstrated
failing. And a counter you can run any day to get the number of remaining
usages, checked against a hand count and against actual traffic.

**The thought process**

The first artefact is the one that decides whether the migration converges at
all: **without a block, you are migrating faster than people add new usage, or
you are not, and you will not know which for months.** Every day without it,
somebody writes new code against the old system in good faith, because it is
documented and it works.

Second, and the section is blunt about this: **a warning is a lint rule that
has decided not to be one.** Warnings are read for a week and then filtered.
The block must fail the build, and the demonstration — add a new usage on a
branch, watch CI go red, remove it, watch it go green — is what tells you it is
real.

Third, the counter: **"how much is left" has to be a number you can produce on
demand, not an estimate somebody maintains.** A tracking spreadsheet is a
second system that goes stale; a query is a fact. And the number going down
publicly is most of what keeps a migration alive politically.

Fourth, and this is the trap this project's diagram is about: **a counter that
only greps the code will hit zero while the old system is still being called.**
Dynamic dispatch, a path built from configuration, another service on the old
endpoint, a nightly job in a repository you did not search — all invisible to a
static count. The check is to count what is *running* as well as what is
written, and they converge only at the real end.

Fifth: **verify the counter itself.** Run the query, then grep by hand, then
compare. If the numbers differ, the counter is wrong and you were about to
declare victory on it.

**How to organise the prompts**

```
Write the check that makes it impossible to add NEW usage of the old
system: a lint rule, a CI check, a failing import — whatever fits
here.

It must fail the build, not warn. Show me it failing on a deliberately
added new usage, then passing when I remove it.
```

```
Now the exception path. Existing usage must still build. How does the
check distinguish existing from new, and what happens when somebody
has a legitimate reason to add one?
```

Without an allowlist of existing usage, the block cannot be turned on until the
migration is finished, which is exactly backwards.

```
Write me a query or a script that counts exactly how many call sites
are still on the old path, that I can run any day and get a number.

Then tell me what it would miss — the usages this will not catch.
```

The second question is the important half.

```
Now the runtime counter: instrument the old system so I know how many
requests it is actually serving, by caller. Tell me how I attribute a
request to a caller when the caller is another service.
```

Serving-side attribution is what turns "something is still calling this" into
"this specific thing is still calling this", which is the difference between a
mystery and a task.

**On AWS**

The runtime counter is where AWS does most of the work for you, and it is the
half people skip.

If the old system is behind an **Application Load Balancer** or **API
Gateway**, the request count is already a **CloudWatch** metric, and access
logs to **S3** give you per-caller detail queryable with **Athena**. That is
the number that has to reach zero, and it is available today without
instrumenting anything.

For attribution, log the caller identity — the IAM principal from
**CloudTrail** for AWS-API-level usage, a user-agent or a service header for
HTTP. **CloudWatch Contributor Insights** over the access logs answers "which
callers account for the remaining traffic" directly, which is exactly the
question at the end of a migration and is tedious to answer any other way.

For infrastructure rather than code, the counter is an **AWS Config** query:
how many resources still use the old launch template, the old security group,
the old encryption setting. Config's advanced queries across your account — or
across the organisation via an aggregator — are the equivalent of the grep, and
they see things created by hand in the console, which the pipeline check
cannot.

And the block has an infrastructure form too: a **service control policy** or a
Config rule with auto-remediation that prevents creating new resources of the
old shape. Same severity question as
[18 · Technical strategy](../18-technical-strategy/)'s project 4 — a hard block
is right for the thing that must stop, a Config finding is right for the thing
that should be visible.

**What productionising it means**

The block fails the build, has an allowlist for existing usage, and has been
demonstrated failing. The counter is a query anybody can run, and its result is
on a dashboard rather than in a document. There is both a static count and a
runtime count, and both are tracked, because they reach zero at different
times. And somebody has cross-checked the counter by hand at least once.

**The learning**

A migration converges only when new usage is blocked, and it is finished only
when the thing that is *running* stops, not when the thing that is *written*
disappears. The static count is the one that is easy to produce and the one
that will let you declare victory early, which is why the runtime count is the
one to put on the dashboard.

**How you would know it is wrong**

- Add a new usage on a branch and push. The build must fail. If it does not, the backlog is still growing behind you.
- Run the counter, then grep by hand, then compare. A difference means the counter is wrong.
- Check whether you have a runtime count as well as a static one. If not, you can only detect the kind of usage you already know about.
- Confirm existing usage still builds. A block that cannot be enabled until the end is not helping.
- Ask who can see the number. A count only you can produce is a count only you believe.

---

### 5. The finish

*You end up with a commit that deletes the old system, a counter at zero on both measures, and the dual-running cost you stopped paying.*

**Build**

Drive both counters to zero. Delete the old system — actually delete it, in a
commit. Then measure what you stopped paying: the infrastructure cost of the
old system, and the ongoing cost of every change having to be made twice.

**The thought process**

The first thing to say plainly: **this is the phase that gets skipped and it is
the phase that pays.** The value of a migration arrives entirely at the end.
Stop at 80% and you have paid the whole cost — the design work, the tooling,
the migration of most callers, the dual running — and bought nothing except a
system with two of something in it.

Second, why it gets skipped, and it is not laziness: **the last 20% is the
worst part of the work.** The interesting engineering is finished. What remains
is chasing four teams who have other priorities, finding the one caller nobody
can identify, and deleting code, and nobody was ever promoted for deleting the
old thing. Knowing that in advance is most of the defence against it.

Third, the technique that makes the end tractable: **try to delete it early.**
Open a branch, remove the old system, and see what breaks. Do this in month one
when it is a five-minute experiment, not in month six when it is a decision.
The list of breakages is your remaining work, discovered mechanically instead
of by asking people.

Fourth: **the finish needs an owner and a date, both named.** A migration with
neither is already abandoned and has not said so. And the owner should not be
the person who started it, if that person has been promoted for starting it —
which is a real pattern and worth naming out loud rather than being surprised
by.

Fifth, and this is what makes the case for finishing to people who are not
you: **measure the double-running cost.** Every quarter you do not finish, you
pay it again, and the remaining work gets slightly harder because more code was
written in the meantime. Turning that into a monthly number is the most
persuasive argument available, and it is one you can compute.

**How to organise the prompts**

```
Delete the old system in a branch and tell me everything that breaks:
compile errors, failing tests, broken deploys, infrastructure that
no longer resolves.

Group them. That list is my remaining work.
```

Doing this early is the trick. The compiler is a better inventory than a
spreadsheet.

```
For each remaining caller: who owns it, what do they have to do, and
what is the smallest thing I could do for them instead of asking?

Rank by which one is most likely to still be there in three months.
```

```
Here is the infrastructure the old system uses and here are the tags:
<data>. Compute what we are spending on running both, per month.

Then estimate the non-infrastructure cost: every change in this area
made twice, every new engineer learning both.
```

```
Write the deprecation timeline with a hard date: when the old system
stops accepting new usage, when it starts returning errors for a
fraction of requests, when it is deleted.

For each step, what I do if somebody is still on it.
```

The fractional-error step is the underused one: making the old path fail for 1%
of requests, then 10%, finds the callers nobody could identify, and it is the
same progressive-delivery mechanism from
[12 · Delivery](../../02-senior/12-delivery/) pointed backwards.

**On AWS**

Finishing has a satisfying, measurable AWS form, and it is the best argument
for finishing you will ever have.

**Cost Explorer** filtered by the tags on the old system gives you the monthly
number you stop paying. Screenshot it before and after. That one graph does
more for the next migration's funding than any document — it is evidence that
the last one delivered something.

The deletion itself should be a real deletion: the **CloudFormation** stack or
Terraform resources destroyed, not just the code removed. An old system whose
infrastructure is still running is still costing money and is still a security
surface, and "we deleted the code" is a common half-finish. Check for the
leftovers specifically: unused **EBS** volumes and snapshots, an old
**RDS** instance in stopped state (which still bills for storage and restarts
itself after seven days), idle **load balancers**, **ECR** repositories,
**Route 53** records pointing nowhere, and IAM roles nobody can delete because
nobody knows what uses them — which **IAM Access Analyzer**'s unused-access
findings will tell you.

For finding the last callers, the fractional-failure trick has a clean
implementation: return errors for a percentage of requests to the old endpoint
via an **ALB** rule or a feature flag in **AppConfig**, and watch which teams
appear. It is blunt and it works, and it is much kinder than a surprise
deletion.

And keep the **CloudTrail** and access-log evidence that the old endpoint
served zero requests for a sustained period before deleting. That is the
artefact that lets you delete without a meeting.

**What productionising it means**

Both counters are at zero and have been for long enough to cover the monthly
and quarterly jobs — a nightly job will not appear in a week of traffic, and a
month-end job will not appear in a month. The infrastructure is destroyed, not
just the code. There is a commit where the deletion happened. The cost saving
is recorded. And if you did stop early, that is written down with the reason,
because "we ran out of interest" is an acceptable and useful thing to have on
record.

**The learning**

Migrations are the only reliable way to reduce technical debt at scale, and
they have a payoff structure that makes them uniquely easy to abandon at the
point where all the value is. The habit that fixes it is measuring the
double-running cost early and publicly, so that not finishing has a number
attached to it rather than being free.

**How you would know it is wrong**

- Check the runtime counter, not just the static one, and check it over a period long enough to include monthly jobs.
- Try to delete it and see what breaks. Do this early, when it is an experiment.
- Look for the infrastructure, not just the code. A stopped RDS instance still bills and restarts itself.
- Find the commit where the old system was deleted. If there is no such commit, the migration is not finished, whatever the status says.
- Compute what you stopped paying. If nobody knows, the next migration will be harder to fund.
