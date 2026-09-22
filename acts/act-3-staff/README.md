# Act 3 · Staff — five projects

> Change what gets built · a weekend each, spread over weeks · pick one
>
> Integrates sections [16](../../tiers/03-staff/16-scope-and-leverage/) through
> [21](../../tiers/03-staff/21-making-others-faster/).

These five are different in kind from the first two acts, and it is worth saying
why before you pick one.

In Act 1 the deliverable was a system. In Act 2 it was the same system,
survivable. **In Act 3 the deliverable is usually a document, a deletion, or
somebody else's changed situation** — and the code, where there is any, is
incidental. That is not a softening of the material. It is the actual job, and
it is the part that cannot be handed to a model, because every one of these five
turns on a judgment somebody has to own.

Four of them you can do alone. One of them needs another person, and that is
deliberate.

| | project | the deliverable | alone? |
|---|---|---|---|
| 1 | the migration you actually finish | a deletion commit | yes |
| 2 | the strategy you found rather than invented | half a page, cited | yes |
| 3 | the incident you caused on purpose | a postmortem with a done action item | yes |
| 4 | the paved road | a mistake nobody can make silently | needs one other person |
| 5 | the thing you decided not to build | a written no | yes |

---

## 1. The migration you actually finish

*You end up with a commit that deletes the old thing, and a counter at zero.*

**Build**

Replace something load-bearing in your Act 2 system — how items are stored, how
authentication works, the job runner — with the full apparatus around it: a
design doc, the hardest case first, a mechanical block on new usage, a
remaining-work counter, and the deletion.

**The thought process**

The decision that makes or breaks this is **which thing to replace**. Too small
and it teaches nothing; too large and you will abandon it at 80% and prove the
point the expensive way. The test: it should be something where a mistake means
data in two shapes, and where you can feel yourself not wanting to start.

Then the ordering people get backwards: **hardest case first.** Migrating the
easy thing produces confidence and no information. What you want out of phase
one is the discovery that your plan was wrong about something, and the easy case
has no such discovery in it.

Third, the one that decides whether this converges: **you need a mechanical
block on new usage.** Without it you are migrating in one direction while new
code arrives in the other, and you will not know which is winning for months.

**How to organise the prompts**

```
Here is the thing I am replacing and everything that uses it.

Rank the users by how AWKWARD they are to migrate, not by size. I want
the one most likely to break my plan. For the top one, tell me what
specifically does not fit the new model.
```

```
Write the check that makes NEW usage of the old path fail the build. Not
a warning — a failure. Show me it failing on a deliberately added usage,
then passing when I remove it.
```

```
Write a query or script that counts remaining call sites on the old
path, that I can run any day.

Then tell me what it will MISS — dynamic usage, reflection, config,
anything it cannot see.
```

That second question is the one that stops you declaring victory on a blind
counter.

```
Now the design doc: context with a number in it, goals, at least three
non-goals, two alternatives argued at their strongest with a stated
reason each lost, the rollout, and the kill criteria.

Keep it under four pages.
```

**On AWS**

The mechanics depend on what you are migrating, but three patterns come up
constantly and are worth knowing by name.

**Dual-write with a reconciliation job.** Write to old and new, read from old,
and run a scheduled comparison — an **EventBridge** rule triggering a **Lambda**
that samples both and reports differences to **CloudWatch**. The reconciliation
is the whole safety mechanism: it turns "I think they agree" into a number.

**Shadow reads.** Serve from the old path, call the new one too, compare and log
the difference without using it. At small scale, a few lines in your API; at
larger scale this is what a **Lambda** deployed alongside can do cheaply.

**The cutover itself.** If it is a database, **DMS** exists for the heavy
version and is probably more than you need; a **read replica** promoted at a
quiet moment is the simpler answer for a small system, and you should be able to
say which situation calls for which. If it is a service, **weighted routing** in
**Route 53** or a **target group** weight on your load balancer gives you a
percentage cutover you can turn back in seconds.

**What productionising it means**

The block on new usage is in CI, not in a message to yourself. The counter runs
on a schedule and the number is somewhere you see it. And the old code is
**gone** — not deprecated, not commented out, deleted, in a commit you can point
at. That last part is the phase everybody skips and the only one that pays.

**The learning**

The value of a migration arrives entirely at the end, which is why most are
abandoned at 80% with the whole cost paid and none of the benefit collected.
Once you have finished one you will never again believe "we'll finish it next
quarter".

**How you would know it is wrong**

- Push a branch that adds new usage of the old path. The build must fail.
- Run the counter, then grep by hand. A discrepancy means the counter is the broken thing.
- Try deleting the old system early, in a branch. Find out what screams while it is cheap.
- Check both paths are not documented as current. A new reader will pick whichever they read first.
- Read your kill criteria back at the end. Were they observable? Would you have noticed?

**Stage it**

1. The design doc, with the non-goals and the two alternatives.
2. The hardest case migrated, and what it taught written down.
3. The mechanical block and the counter, both demonstrated.
4. The deletion, with the counter at zero.

---

## 2. The strategy you found rather than invented

*You end up with half a page that stops an argument recurring.*

**Build**

Read back the real decisions you made across Acts 1 and 2. Find the one you kept
making from scratch. Write it once, with its reasoning and its cost. Then cite it
in the next decision and see whether the argument got shorter.

**The thought process**

The instinct is to write a strategy by thinking about the future. That produces
a document full of adjectives that nobody cites. **Strategy is synthesis, not
prophecy** — you find it by reading decisions you already made and noticing
which one keeps coming up unargued.

So the real first move is archaeology on your own work: what did you decide about
where errors surface, where validation lives, what gets retried, how state is
stored? If you decided the same thing three times without reference to the
previous two, that is your strategy, and it has been costing you the argument
each time.

Then the part that makes it real rather than decorative: **a strategy must have
a cost.** If it makes nothing worse, it has not chosen anything, and it is a
preference with formatting. Name what you are giving up.

**How to organise the prompts**

```
Here are five decisions I made across this project — in commits, docs
and code comments.

Find the decisions that appear in more than one of them, argued from
scratch each time. Where I reached DIFFERENT conclusions in different
places, show me that specifically. That is what I most want to see.
```

The inconsistencies are the gold. A decision made two different ways in two
places is exactly the cost a strategy removes.

```
Here is my draft strategy. Tell me what it makes WORSE, and for whom.

If your answer is that it makes nothing worse, then it is not a
strategy, it is a preference. Say that instead.
```

```
Rewrite this as plainly as possible. Remove every word that is there to
sound ambitious. Then tell me whether what remains is obvious — if it
is, say so, because that is the result I want and not a problem to fix.
```

**On AWS**

This project is mostly prose, and pretending otherwise would be the forced-AWS
paragraph the spec warns against. Two places it genuinely touches infrastructure:

**Where the decision is enforced.** A strategy that says "all configuration
comes from Parameter Store, never from a file" can be *checked* — a scheduled
**Config** rule, or simply a CI step that greps. A strategy nobody can violate
detectably is advisory.

**Where the document lives.** In the repository, beside the code it governs, so
it is reviewed when the code is. A strategy in a wiki drifts from the system
within a quarter, and nobody notices because the wiki does not fail a build.

**What productionising it means**

It is cited in at least one later decision, by you, and citing it visibly
shortened the argument. The rationale is written next to the ruling, so a future
reader can tell whether it still applies. And it has a stated cost, so a person
who disagrees can disagree with something specific.

**The learning**

The decisions you make repeatedly are the ones worth making once, and you cannot
find them by introspection — only by reading your own record. Which is also why
almost nobody has a real strategy: it requires going back through work you
consider finished.

**How you would know it is wrong**

- Search your own commits and docs for a citation of it after a month. Zero means it is not operating.
- Ask somebody to state it from memory after reading it once. If they cannot, it is not written clearly enough to follow.
- Try to violate it in a change and see whether anything objects.
- Check the rationale is still true. The constraint that produced it may have gone, and nobody will notice unless the reasoning is on the page.

**Stage it**

1. The archaeology: five real decisions, listed with where they were made.
2. The recurring one, and the places you resolved it differently.
3. Half a page: ruling, rationale, cost.
4. A later decision that cites it, and a note on whether the argument got shorter.

---

## 3. The incident you caused on purpose

*You end up with a measured detection time and one change that actually happened.*

**Build**

Pick a failure you have never tried. Break your own system with it, deliberately,
in daylight. Run it as an incident: note the timeline, mitigate before you
diagnose, then write the postmortem and complete one action item.

**The thought process**

The first decision is **which failure**, and the useful criterion is the one you
are least sure about. Not the database going away — you have probably thought
about that. The certificate expiring, the disk filling, a dependency returning
slow-but-successful responses, a clock skewing, a config change that is valid
and wrong.

Then the discipline that is genuinely hard and is the whole practice:
**mitigate before you diagnose.** Your instinct will be to find out why. Roll
back, fail over, shed load first, and satisfy the curiosity afterwards with the
system up. Doing this once, in a drill, is how you will manage it at 3am.

Third: **the timeline before the theory.** Write what happened and when, with
"it broke" and "I knew" as separate entries, before you write a single sentence
about cause. A cause offered early becomes the frame everything else is read
through.

**How to organise the prompts**

```
Here is my system. List failure modes I have probably NOT considered —
not the obvious ones. For each, tell me how I could induce it safely in
my own environment.
```

```
Here are the logs and metrics from the window. Build a timeline: what
happened and when. Mark separately the moment the system broke and the
moment I first knew.

Do not propose a cause yet.
```

```
Given the timeline: list the contributing factors, plural. For each, say
what would have had to be different.

Do not name a single root cause, and do not list anything a PERSON
should have done differently.
```

Banning both single causes and human error is what turns a story into a system
description.

```
For this failure, what check would have caught it before I did? Be
specific: what it measures, what threshold, what it would have said.
Then tell me what that check costs — in noise as well as money.
```

**On AWS**

Two things worth knowing exist for this. **AWS Fault Injection Service** is the
managed way to induce real failures — stop instances, add latency, throttle an
API — with a stop condition tied to a **CloudWatch** alarm so the experiment
ends itself if it goes further than you meant. That stop condition is the feature
that makes it safe enough to run against something you care about.

The homemade versions are fine and teach more: a security-group rule that blocks
your dependency, a `stress` process on the instance, a deliberately expired
certificate in a staging environment, an IAM permission revoked for ten minutes.

And use this project to check the thing everyone's monitoring gets wrong: set a
CloudWatch alarm to **treat missing data as alarming** for at least one critical
metric. Then stop the component entirely. If nothing fires, silence means
nothing in your system, which is the most common quiet failure there is.

**What productionising it means**

The drill is on a schedule rather than a one-off, because the value is in the
trend. The detection time is written down and compared to last time. And the
action item is *done* — with a commit or a config change to point at — because
the honest measure of an incident practice is the percentage of action items
completed, not the quality of the writing.

**The learning**

You cannot shorten the gap between "it broke" and "we knew" during an incident.
You can only shorten it beforehand, and a drill is the only way to find out what
it currently is without waiting for a real one.

**How you would know it is wrong**

- Time the gap. If you cannot produce both timestamps, it is unmeasured, which usually means large.
- Read your postmortem for the word "should". Every one marks where the investigation stopped early.
- Check the action item is done. Not planned.
- Stop a component and see whether anything notices the silence.
- Do a second drill a month later and compare the detection time.

**Stage it**

1. The failure list, and the one you picked, with how to induce it safely.
2. The drill, with a timeline written as it happens.
3. The postmortem: contributing factors, no people, one action item with a date.
4. The action item done, and the next drill scheduled.

---

## 4. The paved road

*You end up with a mistake that nobody on your project can make silently again.*

**Build**

Find the thing you have explained more than twice — to yourself, in notes, or to
a model — and make it structurally unavailable to get wrong. A default, a
template, a generator, a failing check. Then hand it to another person and watch
without helping.

**The thought process**

The first decision is **what to pick**, and the signal is repetition. Anything
you have explained three times is either genuinely subtle or badly designed, and
the second is far more common.

Then the ranking that matters, from weakest to strongest: documentation, a
warning, a review checklist, a failing check, a default that is correct, and the
footgun deleted. **Prefer the strongest option you can afford**, because every
weaker one depends on somebody remembering at the exact moment they are busy.

Third, and this is the part that makes it a staff project rather than a tooling
one: **you have to watch somebody else use it.** Your own tool always feels
obvious to you. The information is entirely in the other person's confusion, and
you only get it by shutting up.

**How to organise the prompts**

```
Here is a mistake that keeps happening on this project: <describe it>.

Give me three ways to make it structurally impossible or loudly
obvious, ranked by how little anybody has to remember. Do not suggest
documentation or a guideline.
```

```
Implement the strongest one. Then show me it failing on a deliberately
wrong case, and passing on a correct one.
```

```
Now the first-run experience. Write down every step a person who has
never seen this has to take. Then tell me which of those steps I would
be tempted to leave undocumented because it is obvious to me.
```

**On AWS**

The AWS-shaped version of a paved road is worth knowing because it is what
platform teams actually build.

**Service Catalog** or a **CloudFormation**/**CDK** template that provisions the
approved shape — right tags, right logging, right permissions boundary — so the
easy path is the compliant one. **Config rules** to detect drift from it, and
**SCPs** or a permissions boundary to make the wrong thing impossible rather than
discouraged. That escalation — easy, then detected, then impossible — is exactly
the ranking above, in infrastructure.

At one-person scale the same idea is a repository template with the CI, the
`.env.example`, the health endpoint and the link checker already in it. Small,
and it means the boring correct things exist before you are tired.

**What productionising it means**

The wrong thing fails rather than warns. Somebody other than you used it, and you
asked what was annoying. And you wrote down what you stopped doing to make room —
if the answer is nothing, you added work rather than creating leverage.

**The learning**

A rule that depends on memory is a rule that fails on the busy day. Moving it
into a default or a failing check is the difference between being careful and
being unable to get it wrong — and the second one keeps working when you are not
there.

**How you would know it is wrong**

- Do the wrong thing on purpose. It must fail, not warn.
- Watch a person use it for the first time without helping. Every question is a documentation bug.
- Check adoption honestly. A paved road nobody walks solves a problem you had rather than theirs.
- Ask what you stopped doing.

**Stage it**

1. The repetition audit: what have you explained three times?
2. The three options, ranked, and the strongest one implemented.
3. It failing on a wrong case and passing on a right one.
4. Somebody else's first run, watched in silence, and what you changed after.

---

## 5. The thing you decided not to build

*You end up with a written no that somebody could disagree with specifically.*

**Build**

Take a feature or a project you genuinely want to build. Investigate it properly.
Then write the decision **not** to — with the alternatives argued at their
strongest, the evidence, the cost of being wrong, and the one sentence that would
change your mind.

**The thought process**

This is the project people find hardest and it is the one that most resembles the
job. The staff skill is not building — it is **deciding what not to build**, and
doing it in a way that stops the question being reopened every quarter by
somebody who does not know it was asked.

The decision that makes it honest is **doing the investigation first.** A no
written from a feeling is an opinion. A no written after you have costed it,
found the existing options, and worked out who it would serve is a decision, and
it holds.

Then the part that separates it from a shrug: **name the sentence that would
change it.** "We are not building this" is a position. "We are not building this
until X, and here is what X looks like" is a decision with a trigger, and it is
the difference between a closed question and a buried one.

**How to organise the prompts**

```
I am considering building <the thing>. Before any opinion: what already
exists that does this, who pays for it, and what does it cost?

Be specific about whether anything you tell me is verified or inferred.
```

```
Make the strongest possible case FOR building it. Assume the person
arguing is better informed than me. What would they know about the
users or the cost that I do not?

Do not balance it. Argue one side.
```

```
Now the cost of being wrong in each direction: what does it cost me if I
build it and nobody wants it, and what does it cost me if I do not build
it and somebody else does?

Which of those two is recoverable?
```

That asymmetry — which mistake you can come back from — is usually the whole
decision, and it is the question nobody asks.

```
Write the decision as a document: context, the alternatives at their
strongest, the evidence, the decision, and the single observation that
would reverse it.
```

**On AWS**

The AWS content here is genuinely small, and saying so is more useful than
inventing some. Two real things:

**Cost the thing before you reject it on cost.** The **Pricing Calculator** and
a small spike with real numbers beat an intuition, and "it would be too
expensive" is the most common unexamined reason for a no. Ruling something out
on a price you never looked up is a preference wearing a number.

**And check what you already have.** Ask the account, not your memory: what is
running, what is costing money, what did you build and forget. A surprising share
of "should we build X" questions end with finding X, half-built, from six weeks
ago. **Cost Explorer** grouped by tag and a **Resource Groups** query are four
minutes and they have settled this more than once.

**What productionising it means**

The document exists where the next person will find it, so the question is closed
rather than merely unanswered. The trigger sentence is specific enough to notice
if it becomes true. And the investigation is attached, so a disagreer can argue
with your evidence rather than with your conclusion.

**The learning**

Saying no with a written reason is cheaper than building the wrong thing and
more useful than saying nothing. It is also the most durable artefact in this
act: a decision with its reasoning attached stays decided, and one without it
gets re-argued for years.

**How you would know it is wrong**

- Show the "for" case to somebody who wants the thing. If they say "that is not why I would argue for it", your steelman is a strawman.
- Check the trigger is observable. "If demand increases" is not; "if three people ask in a month" is.
- Come back in three months. Did the thing you predicted happen? This is the only calibration you will get on your own judgment, and it is almost never collected.
- Count how many times the question has been reopened since. That number is what the document was for.

**Stage it**

1. The investigation: what exists, who pays, what it costs.
2. The strongest case for, argued honestly.
3. The asymmetry: which mistake is recoverable.
4. The document, with the trigger sentence, somewhere findable.
