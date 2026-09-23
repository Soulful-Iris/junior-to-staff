# 02 · Working with an AI that writes the code — five projects

> Junior tier · each one an afternoon · read [the section](../../../curriculum/01-code/01-problem-solving/working-with-ai.md) first

Five projects, rising. No new features in any of them: each builds an
instrument, and every instrument points at you — a specification whose precision
you can measure, checks for code you could not have written, asks that provably
transfer, a review that survives fatigue, and a record of your own judgment
scored a week later.

The section said the job is now specifying and verifying; these five afternoons
are where that stops being a slogan.

![A vague ask fans out into five different plausible systems; the same ask rewritten as a precise specification produces nearly the same system twice. Every place two builds differ is a sentence missing from the spec.](../../../assets/diagrams/spec-fidelity.svg)

---

### 1. The spec that survives a stranger

*You end up with a specification two fresh sessions turned into nearly the same
system, and a diff showing exactly where it leaked.*

**Build**

One specification for one small, real feature — tagging from P1 is the right
size. Hand the identical document to two fresh sessions with no other context
and let each build it. The spec is the deliverable; the two builds are its test.

**The thought process**

The first decision is what gets pinned and what stays free. The rule: if two
correct implementations could differ on it and nobody would notice, leave it
out; if the difference would reach a user or a caller, pin it. Pin everything
and the spec is code in worse syntax; pin nothing and it is a wish.

Second: what "the same" means. You cannot diff source — variable names are not
disagreement; behaviour on the same input is. So you fix the probes before the
first build: the empty tag, the duplicate, the 200-character one, two users
tagging one item. When the builds diverge anyway, that is not bad guessing — it
is a question you left open, answered by coin flip, twice, differently. Every
difference is a missing sentence: add it, run a third stranger, watch the fan
close.

**How to organise the prompts**

**1 — the holes, before you pay for them.**

```
Read this specification. Do not build it.

List every question you would have to answer yourself because the
spec does not. Split them: any answer fine, versus I would care
which.
```

The second list is your fan-out, visible before it costs anything: fix the
cheap holes now.

**2 — the build, verbatim, to two fresh sessions.**

```
Build exactly what this specification says. Where it is silent,
choose reasonably and record each choice in ASSUMPTIONS.md:
question, your answer, nearest alternative.

Stop when it runs and the spec's examples pass.
```

Fresh means fresh: no shared history, no memory. Each session ends with
something that runs plus a non-empty `ASSUMPTIONS.md`.

**3 — the comparison.**

```
Here are two builds' answers to the same probes, plus both
ASSUMPTIONS.md files. List every behavioural difference; for each,
write the one missing spec sentence that would have prevented it.
Pin behaviour, not implementation.
```

Accept or reject each sentence yourself; the check is a third stranger, who
must not reproduce the differences you fixed.

**On AWS**

The stranger must actually be a stranger, and a chat app is not one — it
carries memory and custom instructions you have stopped seeing; the clean
subject is a pinned model id behind an API. **Amazon Bedrock** and a provider's
own API offer the same models. Bedrock earns it when your work already lives in
AWS — IAM credentials you already have, invocation logging, cost beside the
rest of the bill; otherwise the direct API is simpler. Nothing else here needs
AWS: the artefact is a text file, and git is its home.

**What productionising it means**

The convention outlives the afternoon: silent choices always land in
`ASSUMPTIONS.md`, and a changed spec gets a fresh stranger run, because specs
rot the way tests do. On a team this becomes spec review before code review — a
sentence is cheaper to argue about than four hundred lines that answered it
wrong.

**The learning**

The model was never guessing badly; it was answering questions you did not know
you had left open. And precision stops being a feeling — it is measurable, as
the distance between two strangers.

**How you would know it is wrong**

- The builds agree on things the spec never mentions. That is leaked context —
  check the sessions were independent.
- Delete one sentence you know matters and re-run. No divergence means the
  probe set is too weak to measure anything.
- The third stranger diverges where you already fixed. Your sentence pinned an
  implementation detail, not the behaviour.
- An empty `ASSUMPTIONS.md`. The recording failed, not the spec succeeded.

---

### 2. The verification you could not have written yourself

*You end up trusting a piece of code you still could not write, for reasons you
can say out loud.*

**Build**

Ask for something genuinely past your ability — a sliding-window rate limiter
for P1's sign-in is the classic; a URL canonicaliser works too. Then build the
apparatus that catches it being wrong: properties, a dumb reference
implementation, adversarial inputs, a one-page trust argument.

**The thought process**

Pick the subject by the gap: beyond you to write, not beyond you to *specify*.
You can state what "five attempts in any sixty-second window" means without
being able to implement it efficiently. A model puts you in that gap daily;
here you stand in it on purpose.

Then the real question: where does truth come from, if not from reading the
code? Three places: properties that must hold for every input; an oracle — a
slower, dumber version you *can* write and read, which must always agree; and
known answers worked by hand. For the rate limiter the oracle is insultingly
simple: keep every timestamp, count those inside the window. It stays dumb on
purpose — code and checks from the same hand are not two opinions, so trust
must bottom out in something you can actually read. And the harness must be
shown able to fail before its passing means anything.

**How to organise the prompts**

**1 — properties first, and a readable reference.**

```
Do not write the implementation yet.

State the properties that must hold for every input to this rate
limiter, the inputs most likely to break an implementation, and a
brute-force reference optimised for being obviously correct, not
fast.
```

Read the reference until you believe it; if you cannot hold it in your head,
ask for a dumber one.

**2 — the implementation, and the harness.**

```
Now the real implementation, and a harness running both versions on
the same generated inputs — include empty history, bursts at the
window edge, a clock going backwards — reporting any input where
they disagree.

The harness may only call the public interface of each.
```

Check it by reading the input generator, not the implementation — the
generator is where this can quietly test nothing.

**3 — the blind mutation run.**

```
Produce five variants of the implementation, each with one subtle
behavioural bug. Number them. Do not tell me which bug is which.
```

The harness must flag all five before the reveal; a survivor marks the exact
hole in your harness. Fix, re-run.

**On AWS**

Honestly: none. The point is a harness that runs on your machine in seconds;
infrastructure here would be decoration. The pattern does scale — fanning a
differential harness over a huge input space across **Fargate** tasks — but
that is a later tier's problem.

**What productionising it means**

The harness outlives the implementation, which is the payoff of black-box
checks: regenerate the component, upgrade the model that wrote it, or swap in a
library, and the same harness re-proves the replacement. Wire it into CI; keep
the trust argument next to the code so the next person knows what is defended
and what is assumed.

**The learning**

Trust can be manufactured without comprehension, but only out of parts you can
comprehend — a dumb oracle, a readable generator, a harness seen to catch.
"The tests pass" stops being evidence until you know who wrote the tests.

**How you would know it is wrong**

- A planted bug survives the harness. The harness is wrong, precisely there.
- Break the *oracle* on purpose. If nothing disagrees, the harness compares
  nothing.
- Grep the harness for imports of the implementation's internals. Any hit is
  not black-box, and dies with the first rewrite.
- Print fifty generated inputs. If timestamps only ever increase, the
  clock-goes-backwards property was never exercised.

---

### 3. The prompt library

*You end up with a page of named asks — constraints, not phrasings — and a
measured answer to whether they hold on work they were not written for.*

**Build**

Mine three or four of your own transcripts for the asks you keep retyping.
Compress them into five to ten named entries — a constraint, when it applies,
what to check after — then run the library on a task from a different area and
count the edits.

**The thought process**

What is worth extracting is not sentences. In every ask that worked, one clause
did the work — *show me it failing first*, *do not mock the database*, *stop
when it runs* — and the rest was upholstery. The mining question is which
clause was load-bearing, and the evidence is what the output did differently.
Sometimes the unit is a sequence, not an ask — describe it back, then slice,
then prove — because ordering protects your judgment; a sequence entry names
its checkpoints.

Then the part that separates a library from a superstition: the transfer test.
A prompt polished on the task it was written for is fitted to it — the same
failure as a test written after the code. So the measure is a holdout: a task
from somewhere else, success defined before you run. One afternoon establishes
"no worse than ad hoc, cheaper to type, the checks fired" — more than most
people ever measure.

**How to organise the prompts**

**1 — mine with evidence, not nostalgia.**

```
Here are three transcripts of me working with a model.

List every constraint I imposed and rank them by how much work each
did, citing the moment the output changed because of it. No moment,
bottom of the list.
```

The check is the citations; anything with no moment attached gets cut.

**2 — compress into entries.**

```
Rewrite the top five as reusable asks. For each: the ask, the
constraint doing the work, when it applies, what to check after
using it. Strip everything specific to those tasks.
```

Grep the entries for your project's nouns — any hit means still fitted, not
reusable.

**3 — transfer, then interrogate the misses.**

```
Here is my library and the edits it needed on today's unrelated
task. For each edit: a parameter to turn into a blank, or an
assumption that should kill the entry? Verdict per entry: keep,
blank, delete.
```

Every entry ends the afternoon blanked, rewritten, or deleted; for each
survivor you can name the failure it prevents.

**On AWS**

Prompts live in git — versioned, diffed and blamed like anything load-bearing.
**Bedrock Prompt Management** is the managed neighbour; it earns a place when
non-engineers must edit prompts, or prompts must change at runtime without a
deploy — a personal library meets neither test. The useful piece is
measurement: asks run through **Bedrock** with invocation logging get token
counts in **CloudWatch**, and "this ask is efficient" becomes a number per
call.

**What productionising it means**

Libraries rot when models change under them: date-stamp each entry with the
model it was measured on, and re-run the transfer test after an upgrade, like
tests after a dependency bump. On a team, edits get reviewed like code —
a quietly deleted constraint degrades everyone's output, and nobody's diff
shows why.

**The learning**

Most of what you retype does nothing, and the clause that works is shorter than
you thought. Watch one constraint survive transfer and three collapse, and you
stop collecting phrasings for good.

**How you would know it is wrong**

- An entry whose prevented failure you cannot name. Decoration with a title.
- Ablate: same task, with and without the constraint, fresh sessions. Equally
  good outputs mean it does nothing — or the task was too easy to tell.
- Success defined after seeing the output. That is tinkering with a ledger.
- Every entry survived transfer untouched. Your domains were too close; the
  clean result is the suspicious one.

---

### 4. The review harness

*You end up with a repeatable interrogation for any diff, and one number from
ten real ones: how often nothing would have caught an accidental change.*

**Build**

A written procedure plus a script that collects evidence and answers three
questions of any diff: what behaviour changed, what could have changed
accidentally, which existing test would catch the accident. Run it on ten real
diffs and tally how often the third answer is "none".

**The thought process**

A harness is not for replacing your reading; it is for making your tenth review
of the day as good as your first. Attention degrades invisibly, and a procedure
carries quality through fatigue. The commit message describes the intended
change; the accidental one lives in the blast radius — every caller of a
changed function, every other user of a touched helper or config key. That is
greppable, so the script fetches evidence and holds no opinions.

The third question must end in a test's name or the word "none" — never
"probably the auth tests". Both answers are checkable: break the behaviour and
the named test must fail; plant the accident and a true "none" leaves the suite
green. If all ten diffs come back covered, ask what the answers would look like
if coverage were bad — the same, and the harness is agreeing with you, not
reviewing.

**How to organise the prompts**

**1 — design the procedure against real diffs.**

```
Here are three recent diffs from this repository. Draft the
procedure for interrogating any diff: for each of the three
questions, the mechanical evidence answering it — commands, not
judgment. The third answer must be a test name or NONE.
```

The procedure must name commands you can run; a step beginning "consider
whether" is judgment smuggled in as evidence.

**2 — build the collector.**

```
Write the evidence collector: given a diff, list the changed
functions, their callers, every file using a helper or config key
the diff touches, and the tests exercising any of those. Output
file:line lists only — no prose, no conclusions.
```

Run it on a diff whose blast radius you already know: it must find the caller
you know about.

**3 — the ten runs.**

```
Here is diff 4 of 10 and the collector's output. Answer the three
questions; every claim must cite file:line from the evidence. If no
existing test would catch the accidental change, write NONE — not
the nearest test.
```

Spot-verify two NONEs by making the accidental change for real: a green suite
means the NONE was true and the tally is data.

**On AWS**

It runs where the diff lives: **GitHub Actions**, on every pull request, free
for public repositories. AWS enters only if the harness calls a model per diff
— then route it through **Bedrock** with invocation logging, so each review has
a visible cost in **CloudWatch**; an unmetered review bot gets quietly
expensive. Whatever runs it gets read-only credentials: it comments, it never
merges.

**What productionising it means**

The tally is the real product: a none-rate over time, saying whether the suite
grows with the code or falls behind. The failure mode is ritual — people
reading the harness instead of the diff — so it cites evidence and asks
questions, never concludes "looks good". Alarm on the none-rate rising.

**The learning**

The dangerous part of a change is the part the message never mentions, and
"none" is the most informative answer a review can produce — untooled reviews
almost never do. Ten diffs teach you your real safety margin as no coverage
percentage has.

**How you would know it is wrong**

- Plant an in-passing edit to a shared helper in a test diff. If question two
  does not list it, the blast-radius logic is decorative.
- Verify a named test the way you verify a NONE: break the behaviour; that
  test, specifically, must fail.
- Run the harness twice on one diff. Different answers mean a rumour generator;
  pin every claim to collector output.
- Ten out of ten covered. In my own record, answers shaped that much like good
  news are usually the instrument — check it before believing it.

---

### 5. The honest log

*You end up with a week of recorded acceptances and three counts you cannot get
any other way: how many were fine, how many were debt, how many were wrong.*

**Build**

The `DECISIONS.md` the section told you to start, run as a full loop: one line
each time you accept something you do not fully understand, across a week of
real P1 work — then a revisit ending each entry *fine*, *debt* or *wrong*, with
an action attached.

**The thought process**

The first decision is the bar for "did not fully understand": too strict lasts
a day; too loose leaves an empty log that
reads as competence and is actually blindness. The workable bar — log it if,
had this been wrong, you would not have caught it. An entry must also survive a
week: its reader is future-you, minus the context. "Accepted the
retry logic" is dead in seven days; "accepted that the retry is safe because
the fetch is claimed idempotent — did not verify" can be reopened by a
stranger.

And the revisit must not be re-reading and nodding — you will agree with
yourself, the same instrument twice. So verdicts cost something. *Fine*: you
can now explain why it is right. *Debt*: you still cannot, and a ticket or test
now exists. *Wrong*: incorrect, now fixed, and you wrote down what would have
caught it sooner. An entry must stay cheaper than pretending to
understand: one line, no shame attached. A log kept to look good measures
nothing.

**How to organise the prompts**

**1 — instrument the moment of acceptance.**

```
List everything in this change I accepted without questioning:
defaults, library choices, behaviour you inferred from my silence.
One line each: the choice, the nearest alternative, what would
reveal the wrong one.
```

An empty list is flattery — ask instead for the three most fragile choices. The
model proposes; you pick what enters the log.

**2 — the revisit, one week later, in a fresh session.**

```
Here is an entry from my decisions log, and the current code. State
what the decision assumed, whether this week's changes relied on or
contradicted it, and the one check that would settle it. End
SETTLED or UNSETTLED. Do not reassure me.
```

Fresh, because it has no stake in defending last week's choices. Every item
ends in something runnable; run at least three.

**3 — the verdicts are yours; the model gets one job.**

```
Argue the strongest case that this entry was WRONG, citing the code
as it is now. One paragraph. If the case is weak, say it is weak.
```

Use it on anything you are about to mark *fine*; what survives the strongest
opposing case, checks run, has earned it. Then count.

**On AWS**

`DECISIONS.md` in git is the right store: the log lives where the diff lives,
commits with it, gets reviewed with it. **DynamoDB** earns a place only when
the log spans many repositories and you want "all unresolved debt older than
thirty days" across a team — partition key the repository, sort key the date. The revisit needs a schedule; the honest tool is a calendar entry.
The AWS version — **EventBridge Scheduler** invoking a **Lambda** that
opens an issue listing week-old entries — earns it once the team is bigger than
you.

**What productionising it means**

The log becomes provenance: the next person reads it and learns which parts of
the codebase are load-bearing guesses, something clean code cannot communicate.
The counts become a gauge — a *wrong* count that is not shrinking means the
acceptance bar is too low; an empty week means the bar drifted, not that you
understand everything now.

**The learning**

The section quotes a trial where developers believed they were faster while
measurably slower. That gap closes with a record, not effort. The ratio of fine
to debt to wrong measures your own judgment; until now you were running on the
feeling of it.

**How you would know it is wrong**

- A week of real work and an empty log. The bar is wrong; the work was not that
  clean.
- Every verdict came back *fine*. You graded your own homework — run the
  strongest-case argument on three and see if they hold.
- Trace one real bug from the week. If its acceptance is not in the log, the
  log measures diligence, not risk.
- An entry you cannot act on at revisit — "accepted some async stuff" — failed
  the future-reader test. Tighten the template, not the intention.
