# 02 · Working with an AI that writes the code — five projects

> Junior tier · each one an afternoon · read [the section](README.md) first

Five projects, rising. No new features in any of them: each one builds an
instrument, and every instrument points at you. A specification whose precision
you can measure, checks for code you could not have written, asks that provably
transfer, a review you can repeat when you are tired, and a record of your own
judgment scored a week later.

The section said the job is specifying and verifying. These afternoons are where
that stops being a slogan.

![A vague ask fans out into five different but plausible systems. The same ask rewritten as a precise specification produces nearly the same system twice, and the remaining diff is noise. Every place two builds differ is a sentence missing from the spec.](../../../assets/diagrams/spec-fidelity.svg)

---

### 1. The spec that survives a stranger

*You end up with a specification that two fresh sessions turned into nearly the
same system, and a diff showing exactly where it leaked.*

**Build**

One specification for one small, real feature — tagging from P1 is the right
size. Hand the identical document to two fresh sessions with no other context,
let each build it, and compare what comes back. The spec is the deliverable; the
two builds are its test.

**The thought process**

The first decision is what gets pinned and what stays free. The workable rule:
if two correct implementations could differ on it and nobody would notice,
leave it out; if the difference would reach a user or a caller, pin it. Pin
everything and the spec is code in worse syntax. Pin nothing and it is a wish.

Second: what "the same system" means, because you cannot diff source —
different variable names are not disagreement, different behaviour on the same
input is. So before the first build you fix the probes: the empty tag, the
duplicate, the 200-character one, two users tagging one item. Deciding what to
probe turns out to be discovering what the spec was supposed to pin, which is
why the probes come first.

Third: what a divergence means. Not that the model guessed badly — that you
left a question open and it was answered by coin flip, twice, differently.
Every behavioural difference is a missing sentence. Add it, run a third
stranger, watch the fan close.

**How to organise the prompts**

**1 — get the holes listed before paying for them.**

```
Read this specification. Do not build it.

List every question you would have to answer yourself because the spec
does not. Group them: ones where any answer is fine, and ones where I
would care which answer you picked.
```

The second group is your fan-out, visible before it costs anything. Fix the
cheap holes; re-run until the list contains only questions you are leaving open
on purpose.

**2 — the build, verbatim, to two fresh sessions.**

```
Build exactly what this specification says. Where it is silent, choose
reasonably — and record every such choice in ASSUMPTIONS.md as you go:
the question, the answer you picked, the nearest alternative.

Stop when it runs and the spec's examples pass.
```

Fresh means fresh: no shared history, no memory. Check each session ends with
something that runs and a non-empty `ASSUMPTIONS.md` before comparing anything.

**3 — the comparison, which is also a prompt.**

```
Here are two builds' answers to the same twelve probes, and both
ASSUMPTIONS.md files. List every behavioural difference. For each one,
write the single sentence missing from the spec that would have
prevented it. Pin behaviour, not implementation.
```

You accept or reject each sentence yourself. The check is a third stranger:
given the revised spec, the differences you fixed must not reappear.

**On AWS**

The stranger must actually be a stranger, and a chat app is not one — it
carries memory and custom instructions you have stopped seeing. A pinned model
id behind an API is the clean subject. **Amazon Bedrock** and a provider's own
API offer the same models; Bedrock earns it when your work already lives in AWS
— IAM credentials you already have, invocation logging, the cost sitting next
to the rest of the bill. Otherwise the direct API is simpler. This project
needs nothing else: the artefact is a text file, and git is its home.

**What productionising it means**

The convention outlives the afternoon: silent choices always land in
`ASSUMPTIONS.md`, and a changed spec gets a fresh stranger run, because specs
rot the way tests do. On a team this becomes spec review before code review —
arguing about a sentence is cheaper than arguing about the four hundred lines
that answered it wrong.

**The learning**

The model was never guessing badly; it was answering questions you did not know
you had left open. And precision stops being a feeling — it is measurable, as
the distance between two strangers.

**How you would know it is wrong**

- The builds agree on things the spec never mentions. That is leaked context,
  not a good spec — check the sessions were actually independent.
- Delete one sentence you know matters and re-run. If the probes surface no
  divergence, the probe set is too weak to measure anything.
- The third stranger diverges in a place you already fixed. Your added sentence
  pinned an implementation detail, not the behaviour.
- An empty `ASSUMPTIONS.md`. The recording failed; it does not mean the spec
  was complete.

---

### 2. The verification you could not have written yourself

*You end up trusting a piece of code you still could not write, for reasons you
can say out loud.*

**Build**

Ask for something genuinely past your ability to produce — a sliding-window
rate limiter for P1's sign-in is the classic; a URL canonicaliser works too.
Then build the apparatus that would catch it being wrong: properties, a dumb
reference implementation, adversarial inputs, and a one-page argument for why
you now trust it.

**The thought process**

Pick the subject by the gap: beyond you to write, not beyond you to *specify*.
You can state what "no more than five attempts in any sixty-second window"
means without being able to implement it efficiently. That gap is where a model
puts you every working day; this afternoon you stand in it deliberately.

Then the real question: where does truth come from, if not from reading the
code? Three places. Properties that must hold for every input. An oracle — a
slower, dumber version you *can* write and read, which must always agree. And
known answers, worked by hand. Which of the three your behaviour admits is the
design decision. For the rate limiter the oracle is almost insultingly simple:
keep every timestamp, count the ones inside the window.

Last: who checks the checker. Code and tests from the same hand are not two
opinions — the section already warned you. So the chain has to bottom out in
something you can actually read, which is why the oracle stays dumb on purpose:
a clever oracle is just a second implementation you cannot read. And the
harness must be shown able to fail before its passing means anything.

**How to organise the prompts**

**1 — properties first, and a reference you can read.**

```
Do not write the implementation yet.

State the properties that must hold for every input to this rate
limiter, the inputs most likely to break an implementation, and a
brute-force reference version optimised for being obviously correct,
not for speed.
```

Read the reference until you believe it. If you cannot hold it in your head,
this step failed — ask for a dumber one.

**2 — the implementation, and the harness that compares.**

```
Now write the real implementation. Then a harness that runs both
versions against the same generated inputs — include empty history,
bursts exactly at the window edge, and a clock that goes backwards —
and reports any input where they disagree.

The harness may only call the public interface of each.
```

Check it by reading the input generator, not the implementation: the generator
is short, and it is the place this can quietly test nothing.

**3 — the blind mutation run.**

```
Produce five variants of the implementation, each with one subtle
behavioural bug. Number them. Do not tell me which bug is which.
```

Run the harness against all five; it has to flag every one. Then ask for the
reveal. A survivor is not bad luck — it is a map reference for the exact hole
in your harness. Fix it, re-run, keep the note.

**On AWS**

Honestly: none. The point is a harness that runs on your machine in seconds,
and infrastructure here would be decoration. The pattern does scale — when an
input space is too large for an afternoon, this same differential harness is
what you fan out across **Fargate** tasks — but that is a later tier's problem.

**What productionising it means**

The harness outlives the implementation, and that is the payoff of black-box
checks: when you regenerate the component, upgrade the model that wrote it, or
replace it with a library, the same harness re-proves the replacement. Wire it
into CI, and keep the trust argument next to the code so the next person knows
what is defended and what is merely assumed.

**The learning**

Trust can be manufactured without comprehension, but only out of parts you can
comprehend — a dumb oracle, a readable generator, a harness that has been seen
to catch. After this, "the tests pass" stops being evidence until you know who
wrote the tests and what they have been shown to catch.

**How you would know it is wrong**

- A planted bug survives the harness. That is the harness wrong, precisely
  there.
- Break the *oracle* on purpose. If nothing disagrees, the harness is comparing
  nothing.
- Grep the harness for imports of the implementation's internals. Any hit means
  it is not black-box, and it dies with the first rewrite.
- Print fifty generated inputs and look. If the timestamps only ever increase,
  the clock-goes-backwards property was never once exercised.

---

### 3. The prompt library

*You end up with a page of named asks — constraints, not phrasings — and a
measured answer to whether they hold on work they were not written for.*

**Build**

Mine three or four of your own real transcripts for the asks you keep retyping.
Compress them into five to ten named entries — each one a constraint, when it
applies, and what to check after — then run the library on a task from a
different area and count what needed editing.

**The thought process**

First: what is worth extracting, and it is not sentences. In every ask that
ever worked for you, one clause did the work — *show me it failing first*, *do
not mock the database*, *stop when it runs* — and the rest was upholstery. The
mining question is which clause was load-bearing, and the standard of evidence
is what the output did differently because of it. Phrasing was the 2023 skill;
a constraint with a reason attached is the durable one.

Second: the unit of reuse. Often it is not the ask but the sequence — describe
it back, then slice, then prove — because ordering is what protects your
judgment, and a great prompt in the wrong order protects nothing. So the
library holds both kinds, and a sequence entry names its checkpoints.

Third, what separates a library from a superstition: the transfer test. A
prompt polished on the task it was written for is fitted to that task, the same
way a test written after the code asserts whatever the code does. So the
measure is a holdout — a task from somewhere else, success defined before you
run. One afternoon establishes "no worse than ad hoc, cheaper to type, and the
checks fired". That is enough, and more than most people ever establish.

**How to organise the prompts**

**1 — mine with evidence, not nostalgia.**

```
Here are three transcripts of me working with a model.

List every constraint I imposed. Rank them by how much work each did,
citing the exact moment in the transcript where the output changed
because of it. If you cannot point at a moment, put it at the bottom.
```

The check is the citations. A ranking that speaks in generalities gets asked
again; anything with no moment attached gets cut.

**2 — compress into entries.**

```
Rewrite the top five as reusable asks. For each: the ask itself, the
constraint doing the work, when it applies, and what I should check
after using it. Strip everything specific to those three tasks.
```

Grep the entries for your project's nouns. Any hit means that entry is still
fitted, not reusable.

**3 — transfer, then interrogate the misses.**

```
Here is my library and the list of edits I had to make to use it on
today's unrelated task. For each edit: is it a parameter I should
turn into a blank, or an assumption that should kill the entry?
Answer per entry: keep, blank it, or delete.
```

Every entry ends the afternoon blanked, rewritten, or deleted. No entry
survives on charm — for each survivor you can name the failure it prevents.

**On AWS**

Prompts live in git — versioned, diffed and blamed like anything load-bearing.
**Bedrock Prompt Management** is the managed neighbour, and it earns a place
when people who do not ship code must edit prompts, or prompts must change at
runtime without a deploy; a personal library meets neither test. The genuinely
useful piece is measurement: run your asks through **Bedrock** with invocation
logging on and every entry gets token counts in **CloudWatch** — "this ask is
efficient" becomes a number per call instead of a feeling.

**What productionising it means**

Libraries rot when models change under them. Date-stamp every entry with the
model it was measured against, and re-run the transfer test after an upgrade
the way you re-run tests after a dependency bump. Shared with a team, edits get
reviewed like code, because a quietly deleted constraint degrades everyone's
output at once — and nobody's diff shows why.

**The learning**

Most of what you retype does nothing, and the clause that works is shorter than
you thought. Once you have watched one constraint survive transfer and three
collapse, you stop collecting phrasings for good.

**How you would know it is wrong**

- An entry whose prevented failure you cannot name. That is decoration with a
  title.
- Ablate: run the same task with and without an entry's constraint, in fresh
  sessions. Equally good outputs mean the constraint does nothing — or the task
  was too easy to tell, which is also worth knowing.
- You defined success after seeing the output. That is tinkering with a ledger,
  and the measurement is void.
- Every entry survived transfer untouched. Your two domains were too close, and
  the clean result is the suspicious one.

---

### 4. The review harness

*You end up with a repeatable interrogation for any diff, and one number from
ten real ones: how often nothing would have caught an accidental change.*

**Build**

A written procedure plus a small evidence-collecting script that answers three
questions about any diff: what behaviour changed, what could have changed
accidentally, and which existing test would catch the accident. Then a log of
ten real diffs from your own history, and the tally of how often the third
answer was "none". This is the section's third request turned into equipment.

**The thought process**

Start with what a harness is *for*, because it is not for replacing your
reading. It is for making your tenth review of the day as good as your first.
Attention degrades invisibly; a procedure carries quality through fatigue,
which is the same reason pilots with twenty years still run the checklist.

Then the middle question, the one that needs machinery. The commit message
describes the intended change; the accidental one lives in the blast radius —
every caller of a changed function, every other user of a touched helper or
config key. That is mechanical, greppable. So the design decision is what
evidence answers each question, and the script exists to fetch evidence, not to
hold opinions.

Third: the last question must end in a test's name or the word "none" — never
"probably the auth tests". A named test is checkable: break the behaviour and
watch that test fail. A "none" is checkable too: plant the accident and watch
the whole suite stay green. And if all ten diffs come back covered, do not
congratulate the suite yet — ask what the answer would look like if coverage
were bad. If it looks the same, the harness is agreeing with you, not
reviewing. In my own record, results shaped exactly like good news have been
wrong often enough to make that question a reflex.

**How to organise the prompts**

**1 — design the procedure against real diffs.**

```
Here are three recent diffs from this repository. Draft the procedure
for interrogating any diff here: for each of the three questions, the
mechanical evidence that answers it — commands, not judgment. The
third question's answer must be a test name or the word NONE.
```

The check: the procedure names commands you can run. Any step that begins
"consider whether" is judgment smuggled in as evidence; send it back.

**2 — build the collector.**

```
Write the evidence collector: given a diff, list the changed
functions, their callers, every other file that uses a helper or
config key this diff touches, and the tests that exercise any of
those. Output file:line lists only. No prose, no conclusions.
```

Run it on a diff whose blast radius you already know by hand. It must find the
caller you know about, or it never gets to tell you about the ones you do not.

**3 — the ten runs.**

```
Here is diff 4 of 10 and the collector's output for it. Answer the
three questions. Every claim must cite a file:line from the evidence.
If no existing test would catch the accidental change, write NONE
rather than naming the nearest test.
```

Spot-verify two of the NONEs: make the accidental change for real and run the
suite. A green suite means the NONE was true and your tally is data; anything
else means the harness missed a test, which also earns a line in the log.

**On AWS**

It runs where the diff lives: **GitHub Actions**, on every pull request, free
for public repositories. AWS enters only if the harness calls a model per diff
— then route it through **Bedrock** with invocation logging on, so each review
has a visible cost in **CloudWatch**, because a review bot nobody meters gets
quietly expensive. And whatever runs it gets read-only credentials: it
comments, it never merges.

**What productionising it means**

The tally is the real product: a none-rate, tracked over time, that says
whether the suite is growing with the code or falling behind it. As a pull
request comment the harness is useful; the failure mode is ritual — people
reading its answers instead of the diff. Counter that by making it cite
evidence and ask questions rather than conclude "looks good", and alarm on the
none-rate rising, which is the one trend it exists to catch.

**The learning**

The dangerous part of a change is the part the message never mentions, and
"none" is the most informative answer a review can produce — untooled reviews
almost never produce it. Ten diffs teach you your actual safety margin in a way
a coverage percentage never has.

**How you would know it is wrong**

- Plant an in-passing edit to a shared helper in a test diff. If question two's
  answer does not list it, the blast-radius logic is decorative.
- Verify a named test the way you verify a NONE: break the behaviour; that
  test, specifically, must fail.
- Run the harness twice on the same diff. Materially different answers mean you
  built a rumour generator; pin every claim to collector output.
- Ten out of ten covered. Possible — but check the instrument before you
  believe it.

---

### 5. The honest log

*You end up with a week of recorded acceptances and three counts you cannot get
any other way: how many were fine, how many were debt, how many were wrong.*

**Build**

The `DECISIONS.md` the section told you to start, run as a full loop: one line
at every moment you accept something you do not fully understand, across a week
of real P1 work — then a revisit that ends each entry as *fine*, *debt* or
*wrong*, with an action attached. The deliverable is the three counts, and what
you changed because of them.

**The thought process**

The first decision is the bar for "did not fully understand", and both failure
directions are real. Too strict, and you are logging every line, which lasts a
day. Too loose, and the log stays empty — which reads as competence and is
actually blindness. The workable bar: log it if, had this been wrong, you would
not have caught it.

Second: an entry has to survive a week, and its reader is future-you, who has
lost all of this context. So the template is fixed: the commit or file:line,
the claim you accepted, the check you deferred. "Accepted the retry logic" is
dead in seven days; "accepted that retrying the fetch is safe because it is
claimed idempotent — did not verify" can be reopened by a stranger. That is the
property the spec in project one needed, and it is no coincidence: future-you
is a fresh session with no context.

Third: the revisit must not be re-reading and nodding, because you will agree
with yourself — the same instrument measuring twice. So verdicts cost
something. *Fine* means you can now explain why it is right. *Debt* means you
still cannot, and a ticket or a test now exists. *Wrong* means it was
incorrect, is fixed, and you wrote down what would have caught it sooner. And
the loop only works if writing an entry is cheaper than pretending to
understand: one line, no shame attached. A log kept to look good measures
nothing.

**How to organise the prompts**

**1 — instrument the moment of acceptance, at the end of every slice.**

```
List everything in this change I accepted without questioning:
defaults you chose, libraries you picked, behaviour you inferred from
my silence. For each, one line: the choice, the nearest alternative,
and what would reveal the wrong one.
```

If the list comes back empty it is flattering you; ask instead for the three
most fragile choices in the change. You pick which lines enter the log — the
model proposes, the log is yours.

**2 — the revisit, one week later, in a fresh session.**

```
Here is an entry from my decisions log, and the current code. State
what the decision assumed, whether this week's changes relied on or
contradicted that assumption, and the one check that would settle it.
End with SETTLED or UNSETTLED. Do not reassure me.
```

Fresh session, because it has no stake in defending last week's choices. The
check: every item ends in something runnable, and you actually run at least
three of them.

**3 — the verdicts are yours; the model gets one job.**

```
Argue the strongest case that this entry was WRONG, citing the code
as it is now. One paragraph. If the case is weak, say it is weak.
```

Use it on anything you are about to mark *fine*. An entry that survives the
strongest opposing case, with the checks run, has earned the verdict. Then
count.

**On AWS**

`DECISIONS.md` in git is the right store: the log must live where the diff
lives, commit with it, and get reviewed with it. **DynamoDB** is the neighbour,
and it earns a place only when the log spans many repositories and you want
"all unresolved debt older than thirty days" answered across a team — partition
key the repository, sort key the date, and that is the entire schema. The
weekly revisit needs a schedule, and the honest tool is a calendar entry; the
AWS version — **EventBridge Scheduler** invoking a **Lambda** that opens an
issue listing entries turning seven days old — is worth building once the team
is bigger than you.

**What productionising it means**

The log becomes provenance. The next person to touch the codebase reads it and
learns which parts are load-bearing guesses, which no amount of clean code
communicates. The counts become a gauge: a *wrong* count that is not shrinking
means the acceptance bar is too low; an empty week means the bar drifted, not
that you suddenly understand everything.

**The learning**

The section quotes a trial in which developers believed they were faster while
measurably being slower. That gap does not close with effort; it closes with a
record. The ratio of fine to debt to wrong is a measurement of your own
judgment, and until this week you were running on the feeling of it.

**How you would know it is wrong**

- A week of real work and an empty log. The bar is wrong; the work was not that
  clean.
- Every verdict came back *fine*. You graded your own homework — run the
  strongest-case argument on three of them and see if they hold.
- Take one real bug from the week and trace it. If the acceptance that caused
  it is not in the log, the log is measuring diligence, not risk.
- An entry you cannot act on at revisit — "accepted some async stuff" — failed
  the future-reader test. Tighten the template, not the intention.
