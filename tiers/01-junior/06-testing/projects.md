# 06 · Testing — five projects

> Junior tier · each one an afternoon · read [the section](README.md) first

Five projects, rising. Each one isolates a different thing testing is for, and
each one ends with a number you did not have before.

The code is the least important part of all five. What you are practising is
deciding **what would prove this**, and then getting an AI to build the thing
that proves it without letting it hand you a check that cannot fail.

![A grid of one hundred test runs. Most are solid green, a handful flicker between pass and fail, and the caption explains that a flaky test is a bug in the test rather than bad luck](../../../assets/diagrams/flake-grid.svg)

---

### 1. The suite that can fail

*You end up with a number: what share of deliberately planted bugs your existing
test suite catches.*

**Build**

A script that takes your P1 repository, makes one small semantic change (flip a
comparison, drop a line, invert a boolean, off-by-one a slice), runs the suite,
records whether it went red, and reverts. Twenty mutations, one report.

**The thought process**

The decision that has to come first is **which mutations count**. Change a log
message and no test should fail — that is not a gap. Change a rounding rule and
something must. So before writing any code you are writing a list of *semantic*
edits, and that list is a statement about what your software is for.

Second decision: what does a score mean? 100% caught on twenty hand-picked
mutations does not mean your suite is good, it means your twenty were easy. The
honest output is the *list of survivors*, not the percentage.

**How to organise the prompts**

```
Read this repository. List 20 small SEMANTIC changes I could make to the
source that SHOULD make a test fail. Exclude anything cosmetic: logs,
comments, formatting, variable names.

For each, say which behaviour it breaks. Do not write code yet.
```

That list is the project. Argue with it before it becomes a script.

```
Now write a runner that, for each mutation: applies it, runs the suite,
records pass/fail, reverts, and confirms the tree is clean again before
the next one.

If the tree is not clean after a revert, stop the whole run and tell me.
```

The last sentence is the one that matters. A mutation runner that leaves
edits behind will poison every later result, and the failure looks like a
suddenly worse score.

```
Report only the SURVIVORS: mutations where the suite stayed green.
For each, name the test that should have caught it.
```

**On AWS**

Run it in **GitHub Actions** first — free for public repositories and already
next to your code. Move to **AWS CodeBuild** only when you need something
Actions cannot give you: a machine with more memory than the hosted runner, or
a build that must sit inside your VPC to reach a private database. CodeBuild
bills per build-minute with a small free tier, so a mutation run of twenty
suites is cents, not dollars.

What you do **not** want is EC2. A permanently-running instance to do
occasional work is the most common early AWS mistake, and it costs money while
you sleep.

**What productionising it means**

Nightly, not on every push — twenty suite runs is too slow for a pull request.
Store the survivor list somewhere durable (an S3 object keyed by commit is
enough) so the trend is visible, and alert only when the list *grows*. A
mutation score that silently drifts down is the exact thing you built this to
notice.

**The learning**

Coverage tells you which lines ran. This tells you which lines are *defended*.
After one run you will never read a coverage percentage the same way, because
you will have seen a fully-covered function survive four mutations untouched.

**How you would know it is wrong**

- Plant a mutation you are certain is caught. If the runner reports it as a survivor, the runner is broken, not the suite.
- Check the tree is clean after the run: `git status` must be empty.
- Run it twice and compare. Different results on identical input means something is not being reverted.
- Read three survivors by hand and confirm they are real gaps rather than mutations that changed nothing.

---

### 2. The contract nobody breaks by accident

*You end up able to change one service and find out in seconds whether you broke
another one, without running both.*

**Build**

Split P1's link-fetching into a second service with an HTTP interface. Then
write the contract: a machine-readable description of what the caller sends and
what the callee promises, and a test on **each side** that checks itself against
that same file.

**The thought process**

The first decision is **who owns the contract**. If the provider owns it, the
consumer discovers breakage after the fact. If the consumer owns it, the
provider cannot change anything. Real answer: the contract is a third artefact
that both sides test against and neither owns alone.

The second decision is what belongs in it. Field names and types, obviously.
But the expensive breakages are semantic: a field that used to always be
present becoming optional, a timestamp changing zone, an id switching from
numeric to opaque. Those are contract terms too, and they are the ones a schema
alone will not catch.

**How to organise the prompts**

```
Here are the two sides of this call. Write the contract as a schema plus
a written list of promises that a schema cannot express — optionality,
units, ordering, idempotency, what "empty" means.

Do not write tests yet.
```

```
Now write two tests that read that same contract file: one that checks
the provider's real response satisfies it, and one that checks the
consumer's code only relies on what it promises.

Neither test may contain a literal copy of the schema.
```

That last constraint is the whole design. Two tests with their own copies of the
truth drift apart, and you will trust them right up until they disagree.

```
Break the contract on purpose in three ways: rename a field, make a
required field optional, change a unit. Show me which test catches
which, and tell me plainly if any of the three is caught by neither.
```

**On AWS**

If the two services are **Lambda** functions behind **API Gateway**, the
contract has an obvious home: API Gateway can validate request and response
bodies against a JSON Schema model, so the contract is enforced at the edge and
not only in tests. That is the "why this service" answer — you get enforcement
for free from something you were deploying anyway.

Keep the contract file in the repository, not only in the API Gateway
configuration. Configuration that exists nowhere in git is configuration nobody
can review. If you want it shared across repositories, an S3 object with
versioning on is enough; **AWS CodeArtifact** is the heavier answer and only
earns its place once several teams consume it.

**What productionising it means**

The contract test runs in both services' pipelines, and the provider's pipeline
fails if it breaks the contract even when its own tests pass. That is the point
of the whole exercise: making a breakage loud on the side that caused it, not
on the side that suffers it.

**The learning**

Two services that pass all their own tests can still be broken together, and
the thing that catches it is not a bigger test suite — it is a shared artefact
that neither side is allowed to quietly redefine.

**How you would know it is wrong**

- Change a field name in the provider only. The provider's pipeline must go red.
- Delete the contract file. Both tests must fail loudly, not pass vacuously.
- Search both tests for a hard-coded field name that should have come from the contract.
- Make a *compatible* change (add an optional field). Nothing should fail. A contract test that blocks safe changes gets deleted within a month.

---

### 3. The flake hunter

*You end up with a list of your tests that are not deterministic, and the
evidence to prove it.*

**Build**

A runner that executes your suite one hundred times, records pass or fail per
test per run, and reports any test that was not unanimous.

**The thought process**

The decision that changes everything is how you treat a flake. The common
instinct is to re-run it and move on. The correct position is that **a test that
passes and fails on identical input is a bug — in the test, in the code, or in
your assumptions about time and ordering — and "re-run it" is deciding not to
find out which.**

Then a practical decision: one hundred sequential runs takes too long, and
parallel runs change the conditions you are measuring. Both are legitimate, and
which you pick depends on whether you are hunting order-dependence (run
sequentially, shuffled) or resource contention (run in parallel).

**How to organise the prompts**

```
Run the suite 100 times. After each run, record per-test pass/fail with a
run number and a seed. Shuffle test order each run and record the seed.

Report only tests that were not unanimous, with the count and the seeds
they failed on.
```

```
For the top flake, tell me the three most likely mechanisms: shared
state between tests, a real clock, or an ordering assumption.

Then write the smallest experiment that distinguishes them.
```

The second half is the important one. A model will happily fix a flake by adding
a sleep, which converts a fast intermittent failure into a slow one.

```
Fix it without adding a sleep or a retry. If you believe a sleep is the
only option, explain what we are actually waiting for and why we cannot
wait for that thing directly.
```

**On AWS**

One hundred suite runs is embarrassingly parallel, so this is where
**AWS Fargate** earns its place: a task definition, one hundred tasks, no
servers to manage, and you pay for the seconds used. **AWS Batch** is the
alternative and is the better answer once you want queueing, retries and
priorities across many such jobs — it is a scheduler, where Fargate on its own
is just compute.

Lambda is tempting and usually wrong here: a fifteen-minute maximum and a
read-only filesystem outside `/tmp` make it a poor fit for a full test suite.
That comparison — *why not Lambda* — is worth being able to make quickly.

**What productionising it means**

Weekly, on a schedule, with the results kept over time. Flakiness is a trend,
not an event. Quarantine is a real mechanism and needs a rule: a flake gets
tagged, excluded from blocking merges, and given an owner and a date — and the
quarantine list has a maximum size, because an unbounded one is just a disabled
suite with paperwork.

**The learning**

Flakiness is not bad luck, it is unexamined non-determinism, and there is
always a mechanism. Once you have found three of them — shared state, a real
clock, an ordering assumption — you will recognise the fourth in minutes.

**How you would know it is wrong**

- Write a test that fails exactly one time in ten by construction. The hunter must find it and report roughly that rate.
- Run the hunter twice and compare the lists. Wildly different lists mean you are measuring your machine, not your tests.
- Check the seeds are recorded and a failure actually reproduces from its seed. A flake report you cannot replay is a rumour.

---

### 4. The load test that finds the real limit

*You end up knowing which component breaks first, at what rate, and what the
failure looks like from outside.*

**Build**

A load generator that ramps traffic against P1 until something fails, and a
record of what failed, at what throughput, and what a user saw.

**The thought process**

First decision: **find the limit, do not verify a target.** "Can it do 100
requests per second" is a yes/no that teaches nothing. "What breaks first, and
at what number" gives you both a limit and a to-do list.

Second decision: what counts as failure. Errors, obviously — but latency past a
threshold you choose is also failure, and so is success with stale data. Decide
before you run, or you will pick the definition that makes the graph look good.

Third, and the one people skip: **where the load comes from.** A generator on
your laptop measures your home broadband. A generator in the same VPC measures
the system without the internet in front of it. Both are useful and they answer
different questions.

**How to organise the prompts**

```
Write a load test that ramps from 1 to N concurrent users, increasing
every 30 seconds, recording per-step throughput, p50 and p99 latency, and
error rate.

Stop automatically when error rate passes 1% or p99 passes 2 seconds.
Report the step where it stopped and what the errors were.
```

```
Now tell me, from the numbers: what resource ran out? Name the evidence
in the data that points at it rather than guessing from the
architecture.
```

Asking for the evidence rather than the diagnosis is what keeps this honest.
The answer is very often the connection pool or the file descriptor limit, not
the thing anyone expected.

```
Run it again with only that one limit raised. Report the new breaking
point and what broke instead.
```

**On AWS**

The generator wants to be somewhere with real network capacity. **Fargate**
tasks in the same region as the system, several of them, is the straightforward
answer; a single **EC2** instance is fine too and is cheaper per hour if you
already have one running.

Where AWS genuinely changes the exercise is on the observed side: with
**CloudWatch** metrics on the load balancer and the database you can see *which
component* saturated rather than inferring it. Turn on **Enhanced Monitoring**
on RDS for the duration of the test and off afterwards, because it is billed per
instance per interval and it is easy to leave on.

One caution worth stating plainly: load-testing your own infrastructure is
fine, and load-testing anything you do not own is not. Point it at your own
account only.

**What productionising it means**

A smaller version of the same test runs on a schedule against staging, and the
breaking point is recorded over time. A limit that halves after a release is the
single most useful performance signal you can have, and nobody has it, because
the test is written once and never re-run.

**The learning**

The thing that breaks first is almost never the thing you optimised, and you
cannot find it by reasoning about the architecture — only by pushing until
something gives and then reading the evidence.

**How you would know it is wrong**

- Run the generator against a deliberately slow endpoint. It must report a low limit, not a high one.
- Check the generator itself is not the bottleneck: double the generators and see whether the reported limit moves. If it does, you were measuring your load test.
- Compare p99 against a hand-timed request during the run. If they disagree, the measurement is wrong.
- Confirm the run stopped on your stated condition rather than on a crash.

---

### 5. The test that runs in production, forever

*You end up finding out about breakage before a person tells you.*

**Build**

A small check that exercises the real system from outside — sign in, add a link,
read it back, delete it — on a schedule, against production, alerting when it
fails.

**The thought process**

The first decision is **what it does with data.** A synthetic test that writes
to production writes real rows. You either accept that and clean up after
yourself, or you carve out a dedicated account whose data is ignored everywhere
else. Both are real choices; not choosing means a test user slowly polluting
every metric you own.

Second: what it checks. The temptation is a health endpoint, which tells you the
process is alive — a much weaker claim than "a person could use this". The
valuable check is the *journey*, because that is what exercises the parts that
depend on each other.

Third, and this is the one that separates a useful check from noise: **what is
worth waking someone for.** One failed run of a five-step journey is often a
network blip. Two consecutive is a signal. Deciding that ratio in advance, while
calm, is the whole difference between an alert people trust and one they mute.

**How to organise the prompts**

```
Write a check that performs this journey against a real deployment:
sign in, create an item, read it back, assert the content, delete it,
and assert it is gone.

Every step must fail loudly with which step failed and what it saw.
No step may be skipped on the failure of a previous one.
```

```
Now make it clean up after itself even when it fails partway. Show me
what happens if the assertion fails between create and delete.
```

Half-cleaned synthetic data is the commonest way this kind of check becomes a
nuisance nobody removes.

```
Make it alert only after two consecutive failures, and make the alert
say which step failed and for how long it has been failing.
```

**On AWS**

This is the one place where a managed service is clearly the right answer:
**CloudWatch Synthetics** canaries exist for exactly this — a scheduled script
in a managed Lambda, with screenshots, a results dashboard and CloudWatch
alarms wired in. You write the journey and stop maintaining a runner.

The build-it-yourself version is a **Lambda** on an **EventBridge** schedule
publishing a custom **CloudWatch** metric with an alarm on it, and it is worth
understanding because it is three small pieces you will reuse for everything
else. Synthetics costs per canary run; the Lambda version is effectively free at
this frequency. The comparison is the lesson: pay for the dashboard and the
screenshots, or assemble it for nothing and maintain it.

And run it from **outside** your VPC. A check that runs inside the network it is
checking cannot see the failures that matter most — DNS, certificates, the load
balancer, the internet.

**What productionising it means**

It already is production; that is the point. What makes it durable is that its
own failure is visible — a canary that stops running looks exactly like a canary
that is passing, which is the single most repeated failure mode in my own
record. Alarm on missing data, not only on failures.

**The learning**

The gap between "it broke" and "we knew" is the number that decides how bad an
incident is, and it is the only one you can shrink before anything goes wrong.
This project is how you find out what yours currently is.

**How you would know it is wrong**

- Break the journey on purpose (revoke the test user's permission) and time how long until the alert arrives. That number is your detection time.
- Stop the canary entirely. Something must notice. If nothing does, silence means nothing and the check is decorative.
- Check what it leaves behind after a mid-journey failure. Then check again a week later.
- Confirm the alert names the failing step. "Canary failed" at 3am is a puzzle, not a page.
