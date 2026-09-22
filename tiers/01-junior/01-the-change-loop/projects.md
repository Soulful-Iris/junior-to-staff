# 01 · The change loop — five projects

> Junior tier · each one an afternoon · read [the section](README.md) first

Five projects, rising. Each one isolates a different thing the change loop is
for, and each one ends with a number or a proof you did not have before.

None of them adds a feature to [P1](../../../projects/p1-it-works/). That is
deliberate. The loop is the machinery your changes travel through, and the only
way to study machinery is to run something through it and watch. So these
projects run your own work through the loop twice, measure the difference, and
finish with a loop that can refuse things the old one waved through.

![The same week of work shipped two ways. As one 38-file commit, a production failure implicates all 38 cells and a cursor sweeps the whole row, searching. As five small changes run one at a time, the same fault implicates only Thursday's seven files; the other four changes stay proven good and the revert is one small commit.](../../../assets/diagrams/batch-size.svg)

---

### 1. The history a stranger can debug from

*You end up with the same week of work told two ways, and a number: how long a
stranger takes to find out why a line changed in each.*

**Build**

Take a real week of your P1 history — the honest, messy one with `wip` in it.
On a copy, rewrite it into the sequence you would want at 3am: same final code,
different story. Then run the experiment: a reader with no context gets one
line and one question — why is this here — against each version, timed.

**The thought process**

The first decision is not a git command, it is a list: what were the actual
decisions made that week? A `fixes` commit usually contains three. Until that
list exists you cannot say what the commits should have been, because commits
are supposed to map to decisions one for one — the rewrite is just making the
history match a list you should have been able to write on Friday.

Second: where rewriting is allowed. Shared history is a record other people
have built on; rewriting it deletes their context. On a branch that was never
pushed, it is a drill. The skill being practised is knowing that line, not the
rebase syntax.

Third, the constraint that keeps the whole exercise honest: the final tree must
be byte-identical. You are changing the story, never the code, and `git diff`
between the two tips is the proof.

Last: what the measurement means. Time-to-answer only counts if the answer is
right and cited — the stranger must point at the commit that justifies the
line. A fresh model session with nothing but the clone is the perfect
stranger: no memory of the ticket, no reluctance to say the history is
useless.

**How to organise the prompts**

**1. The inventory.**

```
Read `git log -p` for the last week on this branch. List the distinct
decisions buried in it: behaviour changes, refactors, reversals, dead
ends. One line each. Do not touch the repository yet.
```

Check the list against your own memory of the week. A decision you remember
that it missed was recorded nowhere — that is a finding before you have done
anything.

**2. The plan.**

```
Plan a rewritten history for a copy of this branch: one commit per
decision on that list, refactors separate from behaviour changes, each
message one line of what plus a body saying why and what we tried that
did not work. The final tree must be byte-identical to the current tip.
Show me the plan before touching anything.
```

Read the plan as prose. Any commit that needs the word "and" gets split before
you approve it.

**3. The execution.**

```
Execute the plan on a new branch. When done, run
`git diff <old-tip> <new-tip>` and show me the output. It must be empty.
If it is not, stop and tell me what differs.
```

The empty diff is the checkpoint: story changed, code untouched.

**4. The experiment**, in a fresh session with only the clone:

```
Why does line <N> of <file> say what it says? Use only git log, git
blame and the code. Cite the commit that justifies your answer.
```

Time it against both branches. Wrong-but-fast counts as wrong.

**On AWS**

This project is where you decide where the record lives. **GitHub** is the
default, because the machinery the rest of this section depends on — merge
queue, machine first pass, stacked PRs — lives there. **CodeCommit** is the
neighbour: it closed to new customers in July 2024 and returned to general
availability on 2025-11-24 (checked 2026-09-22). Choose it when the record must
sit inside your IAM, VPC and CloudTrail boundary; choose GitHub for everything
else. That eighteen-month wobble is also the lesson: a host is a bet, so keep
the record exportable. It already is — `git bundle` packs the entire history
into one file; a scheduled copy into an **S3** bucket with versioning on is an
offsite record for effectively nothing at repository sizes, and it needs no
service fancier than S3 because a bundle is just an object.

**What productionising it means**

The rewrite is a drill, not a workflow. The production version is writing
history well on the way in: a commit-message check in the pipeline you will
build in project 3, a protected main so nobody rewrites what others built on,
and the habit of running the inventory prompt *before* a week of work instead
of after it.

**The learning**

A history has a reader, and the reader arrives at the worst possible moment.
Once you have watched a stranger answer "why is this line here" in ninety
seconds against one telling and give up against the other, "backup versus
record" stops being a slogan.

**How you would know it is wrong**

- `git diff` between the two tips is not empty: you edited code, not story. Start over.
- The stranger answers as fast against the messy history: your question was answerable from the code alone. Pick a line whose *why* is not in the file.
- You cannot answer the same question about your own rewritten history a week later.
- Messages that narrate the diff — first word "update", "change", "fix" — survived the rewrite. Grep for them.

---

### 2. The change small enough to judge

*You end up with one feature built as a single 40-file pull request and again
as a stack of five small ones, and numbers for what review actually caught in
each.*

**Build**

One real P1 feature — tagging is the right size, since it wants a rename, a
migration, behaviour and UI — built twice from the same plan: once as one
branch and one PR, once as a stack of five, each layer green and runnable on
its own. Two bugs planted in both versions at the same spots, by a session
that is not the one reviewing. Then review both forms, timed, and open the
sealed answers last.

**The thought process**

The first decision is where the cut lines go, and it is a dependency question
before it is a size question. The order that works: mechanical rename first
(behaviour identical, tests untouched), schema next (harmless while nothing
consumes it), behaviour, then wiring. The test for a cut is double: can you
state the layer without "and", and is main still runnable if the stack stops
here forever — because stacks do get abandoned mid-way, and every layer is a
place that has to be safe to stop.

Second: what to measure. Minutes-to-review is easy to game and reviewers game
it unconsciously. The honest instrument is the planted bugs — found or not
found — which is why they must be planted blind. If you know where they are,
you are not measuring review, you are measuring memory.

**How to organise the prompts**

**1. The stack plan**, before any code:

```
Here is the feature: <one sentence>. Split it into a stack of at most
five layers. For each: one line of what, what it depends on, and why
main is still runnable if the stack stops here. Renames and refactors
get their own layer.
```

Check that no layer needs "and" and that every stop-here claim is plausible.
This plan is the project; argue with it before anything is built.

**2. The blob.**

```
Build the whole feature from that plan on one branch, tests included,
and open it as a single pull request.
```

Check the suite is green. This is the control.

**3. The stack.**

```
Now build the same feature as the planned stack, one branch per layer,
each branched from the last. After each layer, run the suite and stop
so I can check before you continue.
```

At each stop: check out the layer, run it, and describe the diff in one
sentence. At the top, `git diff` against the blob tip — empty, or every
difference explained.

**4. The planting**, in a separate session:

```
Here are two branches containing the same change. Plant the same two
subtle bugs in both — one inverted condition, one off-by-one — at the
same logical spots. Write the locations to sealed.txt and do not show
me its contents.
```

Then review both forms — the section's first-pass prompt plus your own full
read — recording minutes and findings. Open `sealed.txt` only when both
reviews are done.

**On AWS**

"Each layer leaves main runnable" is a claim you can demonstrate instead of
assert: give every PR a preview environment. **Amplify Hosting** is the
zero-glue answer when the app fits its build model — it deploys a preview per
branch automatically. **App Runner** is the container-shaped neighbour, but a
per-PR App Runner service idles at a cost while the PR sits open, which is the
same mistake as a permanent EC2 box in miniature. The assemble-it-yourself
option is a **Lambda** function URL deployed by the PR's pipeline job through
an OIDC role — it scales to zero between review clicks, and review traffic is
too small to notice on a bill. Pick by what the app is, not by habit.

**What productionising it means**

Stacks are a practice, not a trick: GitHub's native stacked PRs (in preview,
per [the section](README.md)) or plain rebase discipline. The recurring cost
is keeping the stack rebased when review changes a bottom layer — budget for
it. And preview environments need a reaper wired to PR close, because idle
previews are money and attack surface accumulating quietly.

**The learning**

A big diff does not get reviewed more slowly; it gets reviewed less. Attention
per line collapses as the line count grows, and after this afternoon you will
have your own numbers for that instead of a slogan from a book.

**How you would know it is wrong**

- The stack's final tree differs from the blob's and you cannot explain each difference.
- A middle layer fails checkout-and-run: the stack is one PR wearing five hats.
- Neither review form caught either bug: the instrument is broken — bugs too subtle, or review is theatre. Find out which before trusting anything else here.
- You opened `sealed.txt` early. Say so in the writeup; a contaminated measurement reported clean is worse than no measurement.

---

### 3. The pipeline that can refuse

*You end up unable to merge into main until four named checks pass, with one
closed PR per check proving each one can actually go red.*

**Build**

Four checks on P1 as separate named jobs — build-and-test, format-and-lint,
secret scan, and the behavioural invariant that nobody can touch someone
else's items — made required by branch protection. Plus the red catalogue: one
deliberately bad PR per check, refused by that check, kept closed as evidence.

**The thought process**

First decision: what earns a place at the gate. Every required check taxes
every future change forever, and a slow or flaky gate teaches people to route
around it. The entry bar is a named harm: a way a bad change could actually
reach main in this repository. Start from the harms and work back to checks —
never from a list of available tools.

Second: advice versus law. A local hook is advice; it runs on machines you do
not control and dies to `--no-verify`. The pipeline on the protected branch is
law. You want fast advice locally and slow law remotely, and you must never
have law that exists only locally.

Third: a check has to name itself. One fat "CI" job that fails is a puzzle at
the worst moment; four named jobs make red self-explanatory.

Fourth, the section's rule made physical: a gate is unproven until you have
watched it refuse. Building the refusals is not extra credit — it is the
deliverable.

**How to organise the prompts**

**1. The threat list.**

```
List every way a bad change could reach main in this repository today:
broken build, failing test, a committed secret, unformatted code, a
change that violates <the ownership rule>. Rank by damage. Propose
exactly one check per way. No configuration yet.
```

Check that every proposed check maps to a named harm. Anything justified only
as best practice gets cut.

**2. The pipeline.**

```
Implement those checks as one workflow with each check as a separate
named job, so a failure names itself. Show me a green run on a no-op
pull request.
```

Check the job list reads like the threat list, then check the green run
exists.

**3. The red suite.**

```
For each job, make the smallest change that must make it — and only
it — fail. Open one PR per change and report which job went red on
each.
```

Every job must have gone red exactly once. A job you cannot make fail is not a
check; it is decoration with a duration.

**4. The lock.**

```
Make all four checks required in branch protection, reopen the worst
red PR, and show me that merging is impossible. Then close it without
merging.
```

Keep the closed PRs. They are the proof, and you will re-run them whenever a
check changes.

**On AWS**

The comparison that matters: **GitHub Actions** versus **CodeBuild** versus
**CodePipeline**. Actions is the default — it lives next to the code, and it
is free on standard runners for public repositories, with 2,000 minutes a
month for private ones on the free plan (checked 2026-09-22). CodeBuild earns
its place when a check needs what hosted runners cannot give: a machine inside
your VPC to reach a private database, or more memory; its free tier is 100
build minutes a month on the smallest machine and, unusually, does not expire
after twelve months (checked 2026-09-22). CodePipeline is an orchestrator of
release stages, not a build machine — a merge gate has nothing for it to
orchestrate, so it is the wrong altitude here.

When any check touches AWS at all, use **OIDC role assumption, not stored
keys**: an IAM identity provider for GitHub's token issuer, a role whose trust
policy pins your repository and branch, and the credentials action to assume
it. It costs nothing, and a long-lived key sitting in repository secrets is
exactly the thing your own secret scan exists to catch.

**What productionising it means**

Decide who can bypass the gate and make bypass loud — an admin merge nobody
sees is a side door that voids the whole exercise. Give the pipeline a time
budget and treat a breach as a defect, because a slow gate quietly recreates
big batches: people amortise the wait. And when a required check starts
flaking, fix or quarantine it that day; a gate that cries wolf trains everyone
to stop reading it.

**The learning**

A pipeline is a list of claims about what cannot reach main, and every claim
is worth nothing until you have watched it refuse. Green only means something
where red is reachable — you now have four reds on file that prove yours is.

**How you would know it is wrong**

- Merge a red PR using admin bypass. If nothing records that it happened, there is a silent door.
- Add a fifth check but forget to mark it required: the red suite must expose that the check goes red while the merge stays possible.
- Plant a fake secret with a real key's shape in a branch. It must be stopped before merge, not found after.
- Time the pipeline monthly. Past the budget, watch PR sizes — they grow, and that undoes project 2.

---

### 4. The review you automate away

*You end up with your review comments sorted into machine work and judgment,
and the machine pile at zero on your next five pull requests.*

**Build**

A corpus of real review comments — project 2 supplies plenty — sorted into
what a machine could have said and what needed a person. Then the machine
layer: a formatter that rewrites, a linter and import order that enforce, and
a first-pass AI review constrained by contract to behaviour, risk and absence.
Then the count, re-run on your next five PRs.

**The thought process**

The first decision is the line itself. Mechanical means one right answer every
time it applies: formatting, import order, unused symbols, an obvious
footgun. Judgment means naming, design, "is this the right change at all".
The dangerous territory is the middle — rules that are right often but not
always — because every false positive spends the gate's credibility, and
credibility does not refill. Start strict and small; widen only with evidence.

Second: enforce beats advise. A formatter that rewrites the file ends the
argument; a linter that complains starts one. The end state you are buying is
that style stops being reviewable because it stops being variable — no
comment, no debate, no attention spent.

Third: adopting a formatter on an existing repo means one huge mechanical
diff. That is project 1's discipline arriving as policy: the reformat is its
own commit, behaviour identical, tests untouched, never mixed with anything.

Fourth: the AI pass gets a job description, and it is the section's first-pass
read — map where human attention should go, name what is absent, never
verdicts, and never style, because machines now own style twice over.

**How to organise the prompts**

**1. The sort.**

```
Here are the review comments from my last N pull requests. For each:
could a machine have made this comment every time it applies, yes or
no? For each yes, name the tool or rule. For each no, name the
judgment it needed.
```

Sample ten yeses and disagree where you disagree — a wrong yes is a future
false positive, and now is when it is cheap to argue.

**2. The tools, one at a time.**

```
Add the formatter as two commits: one that only reformats, with tests
untouched and green, and one that enforces it as a pipeline job. Then
the linter and import order, same shape. Show each enforcement going
red on a planted violation before we keep it.
```

Check the reformat commit's tests pass unmodified, and that every tool has
been seen red once. An enforcement never seen red joins project 3's list of
decorations.

**3. The AI pass, with a contract.**

```
Wire a first-pass review on every PR with this contract: comment only
on behaviour, risk, and what is absent — tests, migration, rollback.
Never comment on style or formatting. End with the three hunks most
deserving of human attention, and no verdict.
```

Test the contract: run it on a PR that is stylistically ugly and behaviourally
fine. One style comment is a contract breach — tighten and rerun.

**4. The count.**

```
For my next five PRs, sort every review comment into the two piles and
report the machine pile per PR. For each machine comment that still
occurred, name the missing or misconfigured rule.
```

The target is zero, and every non-zero names its own fix.

**On AWS**

The zero-setup machine pass is GitHub-side and already covered in
[the section](README.md). The AWS version exists for one reason: when the diff
must not leave your boundary, run the model through **Bedrock** from a small
**Lambda** on the PR webhook, with the pipeline assuming an **OIDC** role —
Bedrock rides IAM, so there is no vendor API key sitting in repository
secrets for project 3's scanner to find. Lambda beats **CodeBuild** for the
bot because a diff fits in memory and the work lasts seconds; a build
container is the wrong shape. The mechanical tools stay in Actions, where they
are ordinary free-tier work.

**What productionising it means**

Keep a false-positive ledger: a rule overridden more than about weekly gets
fixed or deleted, because an ignorable gate teaches ignoring gates. Pin the
formatter and linter versions — an unpinned formatter upgrade reformats the
world mid-PR. And decide in writing whether the AI pass fails open or closed
when its API is down; not deciding means discovering your choice during an
outage.

**The learning**

Reviewer attention is the loop's scarcest input, and every comment category
you automate is attention returned to the questions only a person can answer.
The quiet corollary: enforced checks disappear from consciousness, advisory
ones become noise, and there is almost nothing worth keeping in between.

**How you would know it is wrong**

- Plant one style violation and one real bug in the same PR. The machine must catch the style; the human pass must still catch the bug. If the bug sailed through on a green glow, you have automated complacency, which is worse than no tooling.
- The comment mix is unchanged after a month: the tools are advisory, or not required, or not running.
- Overrides are rising week on week: the rules are spending credibility faster than they earn it.
- Turn the formatter off locally and push. The pipeline must catch it — advice dies, law holds.

---

### 5. Two greens that make a red

*You end up having built the failure merge queues exist for — two PRs, each
green alone, red together — and the machinery that stops it reaching main.*

**Build**

PR A changes a function's contract; PR B, branched before A landed, adds a new
call site written against the old contract, in a different file. No textual
conflict. Both green on their own base. Together they break main — and then a
merge queue, real or hand-rolled, catches the second one before main ever
sees it.

**The thought process**

Start by naming why CI lied, because nothing here makes sense until you can:
"this PR is green" actually means "this PR was green against the main that
existed when its checks ran". It is a statement about a moment. Main moved,
and nobody tested the combination. No tool was wrong; the claim was smaller
than everyone assumed.

Second, the construction discipline: the two changes must merge cleanly. If
git reports a textual conflict you have built the wrong failure — that one is
caught for free. What you want is a semantic dependency with no textual
overlap, which is why the new call site lives in a different file.

Third, the prevention menu, because the queue is a choice, not a law:
require-branches-up-to-date makes humans serialise themselves and babysit
rebases; test-after-merge-and-revert is optimistic and lets main go red
sometimes, which tiny teams tolerate; a merge queue serialises machines
instead, testing each PR against main-plus-whatever-is-ahead and ejecting what
fails. Team size times CI duration picks the answer; the queue is the default
the platform converged on because it converts human waiting into machine time.

**How to organise the prompts**

**1. The construction brief.**

```
Describe two changes to this repository that each pass the full suite
on their own branch, merge into main with no textual conflict, and
make the suite fail once both are merged. Name the mechanism. Do not
write code yet.
```

Check the mechanism is a semantic dependency and the no-conflict claim is
specific about which files each change touches.

**2. The trap, proven.**

```
Build both branches from the same base. Show me four results: the
suite green on A, green on B, both merging cleanly into a scratch
branch, and the suite red there.
```

The four results are the artefact. A green scratch branch means the pair
demonstrates nothing — construct again.

**3. The prevention.**

```
Enable the merge queue — or write a landing script that refuses to
merge any PR until the suite passes on a temporary merge of that PR
onto current main plus everything ahead of it in line. Replay both
PRs through it and show me where the second one is stopped.
```

Check the failure happens inside the queue and main's own history stays green
throughout the replay.

**4. The limits.**

```
List what this queue still cannot catch, with one concrete example
from this repository for each.
```

At minimum: combinations that only fail at runtime under real data, and a
flaky suite — which the queue amplifies into everyone's problem. An answer
claiming the queue catches everything is selling, not thinking.

**On AWS**

A queue converts merge safety into CI capacity: every queued PR is another
full run against a speculative main, so merge throughput is now bounded by
build throughput. Hosted **Actions** minutes are the first wall for private
repositories — 2,000 a month on the free plan (checked 2026-09-22) — and
**CodeBuild** is the overflow: per-minute billing, bigger machines, same OIDC
pattern as project 3. The other half is not rebuilding what did not change:
build once per commit and store by SHA — container images in **ECR**, which
is a real registry that ECS, Lambda and Fargate pull from natively and that
scans what it stores, with 500 MB of private storage free for the first
twelve months (checked 2026-09-22); everything that is not an image — bundles,
coverage, reports — in **S3**. S3 can hold an image tarball, but nothing can
pull it as an image, which is the whole difference.

**What productionising it means**

The queue gets metrics — depth, time-in-queue, ejection rate — because a queue
nobody watches is a delay nobody can explain. Flakiness is now existential:
one flaky test ejects innocent PRs and stalls every merge behind them, so the
quarantine rule from [testing](../06-testing/) stops being optional. And the
bypass log from project 3 applies doubly at 6pm on a Friday.

**The learning**

Green is a statement about a moment, not a property of a change. Integration
is a race, the queue removes the race without a person holding a lock, and
you know exactly which failure it removes because you built that failure with
your own hands.

**How you would know it is wrong**

- Git reports a textual conflict between your pair: wrong construction, that case was already caught for free.
- The scratch branch is green: there is no semantic dependency, and nothing has been demonstrated.
- The queue passes both PRs: check which ref CI actually ran on. If it re-ran the stale PR head instead of the speculative merge, the queue is ceremony.
- After the ejection, rebase PR B and land it properly. If it still cannot pass, the original failure was something else and you proved less than you think.
