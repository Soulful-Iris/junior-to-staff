# 07 · Shipping it — five projects

> Junior tier · each one an afternoon · read [Provision and operate application infrastructure on AWS](README.md) first

Five projects, rising. The section said shipping is three questions — what
exactly did I deploy, where did its configuration come from, who can read its
secrets. These five make you answer each one about your own P1, with evidence:
a command a strange machine obeys, a digest you can point at, a rotation you
timed, an install you audited, a rollback you performed rather than assumed.

The code is the smallest part of all five. What you are practising is refusing
to believe a claim about a running system until the system has confirmed it
from the outside.

![One secret fans out to five places a copy lands through ordinary use — the repository history, the image layers, the CI log, a developer's laptop and the running process's error output — and each copy outlives deletion in its own way, which is why rotation, not deletion, is the response](../../../assets/diagrams/secret-blast-radius.svg)

---

### 1. The clean machine

*You end up with one command from clean clone to running system, and a list of
every step that was living in your head instead of the repository.*

**Build**

A single documented command that takes a fresh clone of P1 to a running,
answering system — proven on a machine that has never seen the project, not on
your laptop. The second deliverable is the finding list: every undocumented
step the clean machine exposed.

**The thought process**

The first decision is what "running" means, because until you fix it, "one
command" cannot fail. A process that started, a health endpoint answering, and
a person signing in against seeded data are three different claims. Pick one
that is observable from outside and let it define done.

Second, draw the line between the machine's job and the project's job. The
command may assume git and a container runtime; it may not assume a database is
already up, a language version installed, or a variable exported. Everything on
the project's side of the line must come from the repository.

Third, the witness must be clean, and it must stay clean. Your laptop can prove
nothing — years of global installs and a database that happens to be running.
And when the clean machine fails, the fix goes into the repository, the machine
gets wiped, and you run again from the clone. A clean machine you fix by hand
is just a second dirty machine.

**How to organise the prompts**

**1. The inventory, before any fixing.**

```
Read this repository. List every assumption it makes about the machine it
runs on: binaries and versions, environment variables, services expected
to be running, files read from outside the repo, network access.

Do not fix anything yet. Just the list.
```

You will recognise half the list; the other half is the finding. Argue with it
before moving on.

**2. The one command.**

```
Write a single entry point that checks its own preconditions and fails
with a message naming exactly what is missing, then builds, starts and
seeds the system, and finishes by curling the health endpoint.

It must exit non-zero if the health check does not answer.
```

The last line is the check that can fail. Run it on your own machine first.

**3. The loop on the clean machine.**

```
I will run this on a machine that has never seen the project. For each
failure I report, put the fix in the repository — script or README —
never on the machine. Then I wipe and re-run from the clone.
```

Stop at two consecutive clean runs from a fresh wipe. One clean run after a fix
might mean the fix worked — or that the machine was no longer clean.

**On AWS**

The honest clean machine is a fresh **EC2** instance from a stock Amazon Linux
AMI, used for an hour and terminated — the one project in this tier where EC2
is right, because you need an interactive machine you can watch fail, and
Lambda and Fargate give you no shell to watch from. Put the machine-side prep
in the instance's **user data**: if user data can take a stock AMI to "ready
for the one command", your machine prep is code too. Then terminate it.

The free option is **CloudShell** — no additional charge, 1 GB of persistent
storage per region, git and npm preinstalled, and it runs Docker (checked
2026-09-22). Its 1 GB ceiling is the real limit, and hitting it tells you your
image is bigger than you thought, which is also a finding.

**What productionising it means**

The clean-clone proof becomes a scheduled CI job, because a fresh runner is a
machine that has never seen the project. From then on the README quickstart is
tested rather than vowed. Pin the base image it runs on, or the proof rots
quietly as the world drifts under it.

**The learning**

"Works on my machine" is a claim about your machine, not about the software.
Either the repository contains everything needed to run the system, or the
missing pieces live in someone's head — and heads do not clone.

**How you would know it is wrong**

- If the clean run passes first try, suspect the witness: cached images, a mounted volume, an inherited variable. What would a genuinely clean machine have shown?
- Remove a file you know is needed and undocumented. The command must fail with a named instruction, not a stack trace.
- Have someone else run it from the README while you watch in silence. Every question they ask is a documentation bug.
- Re-run the proof two weeks later, unchanged. A failure now is drift, and drift is a finding too.

---

### 2. The artefact you build once

*You end up with one image digest running in every environment, and a system
that tells you its own commit from the outside.*

**Build**

P1 in a container image, built exactly once per merge, tagged with the commit,
pushed to a registry. A promote step moves the same digest from staging to
production without rebuilding. A `/version` endpoint reports the commit baked
in at build time, so "what is running?" is a lookup.

**The thought process**

First decision: what identifies the artefact — a tag or a digest. A tag is a
mutable pointer; `:latest` can move under you, and so can `:v3` if someone
pushes over it. The digest is a content hash and cannot lie. Deployments name
digests; tags become labels for humans. Then turn on ECR's immutable-tags
setting so even the labels cannot be reused.

Second, how the commit gets inside: at build time, a build argument stamped
into an environment variable and the OCI label
`org.opencontainers.image.revision`. Asking git at run time is wrong twice —
the running artefact has no `.git`, and if it did, it would report what was
checked out, not what was built.

Third, what "promote" means, precisely: nothing downstream ever rebuilds. If
the production deploy builds "to be safe", production runs something nobody
tested — and this project is where you catch your own pipeline doing it. The
tell is always the same: compare digests, not tags.

**How to organise the prompts**

**1. The stamp.**

```
Write the Dockerfile. The build takes a GIT_SHA argument and stamps it
into an env var and the OCI revision label. Add a /version endpoint that
returns it with the build time.
```

Verify by hand: build locally, `/version` equals `git rev-parse HEAD`. If the
stamp is wrong here, every later check inherits the lie.

**2. Build once, in CI.**

```
Add a CI job that on merge builds the image once, tags it with the commit
SHA, and pushes it. No :latest as a deploy target anywhere.

Show me how to list digests in the registry and match one to a commit.
```

Merge twice and look: two commits, two digests, each traceable. That listing
skill is the one you will want during an incident.

**3. The promotion.**

```
Write the promote step: read the digest currently running in staging and
deploy that digest to production. It must refuse to build, and refuse a
tag where a digest is expected.
```

After promoting, compare the digest production is actually running against
staging's. Equal, or the promotion is not what you think.

**4. The adversarial check.**

```
Now change the pipeline so promotion secretly rebuilds instead, and tell
me which of my checks catches it. If none does, say so plainly.
```

The digest comparison must go red. If nothing catches the rebuild, your proof
was decorative.

**On AWS**

**ECR** is the registry: same IAM as everything else, the immutable-tags flag
this project depends on, and tasks pull without leaving AWS. Storage is $0.10
per GB-month with 500 MB free monthly for the first year on new accounts
(checked 2026-09-22) — one small image is effectively free. Docker Hub is the
neighbour: fine for public images, but a second credential system and pull
limits you do not control.

Where it runs is where 2026 did the teaching. **App Runner** — the
point-at-an-image easy path this guide would have named a year ago — went to
maintenance mode and closed to new customers on 2026-04-30 (checked
2026-09-22). Its successor is **ECS Express Mode** (November 2025): give it an
image and it assembles the Fargate service, load balancer and HTTPS URL, no
charge for the mode itself, pay for the Fargate and ALB underneath. **Lambda**
runs containers but is request-shaped with a fifteen-minute ceiling — wrong
shape for a long-running app. **EC2** means owning the machine, so owning the
drift this section exists against. The durable lesson: the veneer was withdrawn
within a year; the primitives — ECR, ECS, Fargate, ALB — persist, and your
image does not care which veneer serves it. That indifference is what "build
once" buys.

**What productionising it means**

Retention becomes correctness: an ECR lifecycle policy that deletes old images
is deleting your rollbacks, so keep N versions and know what N is — project 5
spends this. And the deploy job must assert from outside that `/version` now
equals the SHA it deployed, failing loudly if not. A deploy that exits 0 either
way proves nothing.

**The learning**

Identity by content, not by name. Once deployments name digests, "what is
running?" stops being archaeology and becomes a lookup — and a whole family of
3am questions stops existing.

**How you would know it is wrong**

- Rebuild the same commit twice and compare digests. They usually differ — the argument for promoting over rebuilding, demonstrated on your own system.
- Ask production for `/version` and compare against what CI claims it deployed.
- Re-push an existing tag with different content. With immutable tags on, ECR must refuse. If it succeeds, your labels can be lied to.
- Grep the deploy path for `:latest`. Any hit is a mutable pointer in the one place you decided not to have one.

---

### 3. The five-minute rotation

*You end up with no secret in the repository or the image, and a measured
rotation time in place of a guessed one.*

**Build**

Every secret out of the repo and the image, into a store, injected at start-up.
The app refuses to boot when one is missing, naming it. A rotation runbook per
secret, as numbered steps. Then one real rotation, timed with a stopwatch, and
the old credential proven dead.

**The thought process**

Inventory before mechanism. The diagram above is the reason: a secret is not
"in the .env file", it is everywhere it has ever been — history, image layers,
CI log, the shell history of every machine that used it, the stack trace from
the night something broke. Write that copy map for one secret first, because
"we moved secrets to a store" without the map just secures the sixth copy.

Then choose the injection point by what it does to rotation cost. Baked into
the image: never — rotation means a rebuild, and the old value stays in the
layers anyway. Set at deploy time: rotation is a redeploy. Fetched from the
store at start-up: rotation is a restart. Each step is faster rotation bought
with a runtime dependency on the store. For P1, fetched at start-up is the
honest afternoon-sized answer — and on a missing secret the app refuses to
boot, naming the variable, never defaulting. A service that starts with an
empty password is quieter than one that will not start, and much worse.

Third: rotation is a two-key dance, not a swap. Create the new credential
alongside the old, roll the deployment onto the new, verify, then revoke the
old. The revoke is the rotation; everything before it is preparation. The
number you measure runs from "I have decided" to "the old value is dead and
the system is healthy".

**How to organise the prompts**

**1. The audit.**

```
Find every secret this project reads. For each: where the value comes
from at run time, whether it could appear in a log, an error message or
CI output, and what rotating it would require today.

Give me a table. Flag every row where rotation needs a code change.
```

The flagged rows are the work queue. Separately, grep `git log -p` — the
history, not the tree — for each current value. Any hit means rotate now;
scrubbing history is not a response, because clones exist.

**2. The move.**

```
Move every secret to the store, injected at start-up. On a missing secret
the app must refuse to boot and name the variable. No secret may ever be
written to a log.

Show me it refusing correctly when one is absent.
```

Then search the image filesystem and its build history for the values. Nothing
may appear — a value passed as a plain build argument is recorded in the image
even when no file contains it.

**3. The drill.**

```
Write the rotation runbook for the database password as numbered steps
using the two-key pattern: create new alongside old, roll onto new,
verify, revoke old. I will execute it with a stopwatch.
```

After the revoke, try the old credential on purpose. If it still works, you
have not rotated it — you have added a second key.

**On AWS**

**Parameter Store** SecureString, standard tier, is the junior default: no
additional charge, and no API charge at standard throughput (checked
2026-09-22). The neighbour, **Secrets Manager**, costs $0.40 per secret per
month plus $0.05 per 10,000 API calls (checked 2026-09-22) — the money buys
managed rotation (it runs the two-key dance in a Lambda on a schedule),
cross-account access and replication. Start on Parameter Store; promote a
secret the day you catch yourself running its rotation by hand every month.
Both inject into **ECS** tasks natively — `valueFrom` in the task definition —
so the image never contains them.

Then the credential CI itself uses: replace stored AWS keys with **OIDC** via
`aws-actions/configure-aws-credentials` — GitHub's provider
`token.actions.githubusercontent.com`, audience `sts.amazonaws.com`, trust
policy pinned to your repository (checked 2026-09-22). Nothing durable to
steal, nothing to rotate: the credential expires minutes after issue. That is
the best rotation time available — zero, because the secret was never durable.

**What productionising it means**

Rotation moves onto a calendar instead of waiting for incidents — a rotation
done twice calmly is one you can do at 3am. Alert when a secret has not rotated
in N days: Secrets Manager tracks this; on Parameter Store it is a tag and a
scheduled check. And the runbook is per secret — a page that says "rotate the
secrets" rotates nothing.

**The learning**

Exposure is not an event you clean up; it is a state you end, and rotation is
the only exit. Once the copy map exists you stop believing deletion, and once
the five-minute number is real, a leaked credential turns from a crisis into a
procedure.

**How you would know it is wrong**

- Plant a canary value in a log line on purpose and run your audit. If it misses the plant, the audit only finds what you already knew about.
- Time the drill honestly, fumbling included. An untimed rotation is a guess wearing a number.
- After rotating, use the old credential. It must be refused.
- Break the store's availability at boot (wrong region). The app must refuse loudly and name the store, not hang.
- Ask what your audit would have shown if a secret were in the history. If the answer is "the same, because I only searched the working tree", it proved nothing.

---

### 4. What you actually install

*You end up with three numbers: how many packages your lockfile really pulls
in, how many run code at install time, and how many you could replace with
thirty lines of your own.*

**Build**

A report generated from the lockfile — direct versus transitive counts, plus
the list of packages with install-time scripts, each with a verdict. CI
switched to strict, scripts-off installs with a justified allowlist. One
dependency replaced with your own thirty lines and the tests that prove them.

**The thought process**

The unit of trust is the resolved graph, not `package.json`. You chose a dozen
names; the lockfile chose the rest, and the section already showed what the
2025 worm did with that fact. This project is where the abstract worry becomes
your numbers, for your repository.

Second: which packages execute at install. Lifecycle scripts run arbitrary
code on your machine, with your environment, before your program has ever
started. Most packages do not need one; packages compiling native code do. npm
can query this directly — the documented selector is
`:attr(scripts, [postinstall])`, and the same shape works for `preinstall` and
`install` (checked 2026-09-22 against the npm CLI docs). Keep this question
separate from `npm audit` and Dependabot, which answer "is anything known
bad" — an advisory lookup. This audit answers "what can run code with my
credentials", and a clean advisory list does not make that list short.

Last, the thirty-lines judgment. The test is not "is it small" but "would I
have to read its source to trust it anyway". If reading is required either
way, writing is cheaper than trusting. But respect real complexity — dates,
encodings, anything cryptographic — where the thirty-line replacement is a bug
farm. The decision is per package, written down.

**How to organise the prompts**

**1. The graph.**

```
Parse the lockfile and report: total resolved packages, direct versus
transitive, and the five direct dependencies pulling in the largest
subtrees.
```

Spot-check the total against `npm ls --all` before trusting it. A report that
miscounts poisons every later number.

**2. The install-time list.**

```
List every package in the graph with a preinstall, install or postinstall
script. For each, read the script and say in one line what it does and
whether this package plausibly needs it.
```

Open two of the flagged `package.json` files yourself — the script text sits
right there in `node_modules`. Trust your reading over the summary.

**3. Scripts off in CI.**

```
Switch CI to npm ci --ignore-scripts. Tell me what breaks. For each
breakage, add a targeted npm rebuild for that one package, with a comment
saying why it needs its script.
```

Green CI with scripts off and a two-line allowlist is the end state. An
allowlist you cannot justify line by line is scripts-on with paperwork.

**4. The replacement.**

```
Here is the dependency I chose to replace: <name>. Write the same
behaviour in under thirty lines, plus tests for the edge cases that made
the library tempting in the first place.
```

The suite stays green and the resolved count drops — usually by more than one,
because the transitive tail leaves with it.

**On AWS**

This one lives in CI, not in a service — GitHub Actions, free for public
repositories, as the testing projects already used. What AWS changes is the
blast radius when an install script runs anyway: with the **OIDC** role from
project 3 there is no durable AWS key in the CI environment to take, and the
short-lived token that is there is pinned by IAM to the little CI needs — push
to one ECR repository, deploy one service. Scope the role tightly and the worst
case is bounded by policy rather than hope. The heavier neighbour is
**CodeArtifact**, a private registry that proxies and pins your upstream so
builds never talk straight to the public registry — right once a team wants one
vetted package set, oversized for an afternoon.

**What productionising it means**

The report runs on a schedule and alerts on the delta, because "a package
acquired an install script since last week" is exactly the event worth a human
look. And lockfile-only pull requests get reviewed like code, because that is
what they are: a change to what you execute.

**The learning**

You thought you had twelve dependencies; you have some hundreds, and a handful
run code before your program does. After this audit, "add a library" stops
being free in your head — it is a decision with a denominator.

**How you would know it is wrong**

- Build a scratch package of your own with a postinstall script that touches a marker file. The query must flag it, and CI with scripts off must never create the marker.
- If the install-script list comes back empty and you have any native dependency, suspect the query before celebrating the tree.
- Delete one behaviour from your thirty-line replacement. The tests that came with it must go red — the testing section's standard applies here too.
- If the resolved count did not drop after the replacement, something else still pulls the package in. Find what.

---

### 5. The rollback you have actually done

*You end up having deployed, rolled back and verified the old version serving —
timed — plus a written list of what in your system does not roll back.*

**Build**

Deploy a new version of P1 with a visible change, then roll back to the
previous artefact by digest and prove from outside that the old version is
serving. Alongside it, the list nobody writes: everything that did not come
back when the artefact did.

**The thought process**

Start with the rollback unit. The artefact rolls back in seconds — if you
deploy by digest and the old digest still exists. Configuration rolls back if
it is versioned. The database mostly does not roll back at all. So before
deploying, answer: what will not return? If the answer is "nothing", it is
wrong — the list always contains at least the data the new version wrote while
it was live.

Second: a rollback is a redeploy of a known artefact, never a
revert-and-rebuild. A rebuild produces a new artefact nobody tested, at the
worst possible moment to be running one. This is where project 2's retention
decision gets spent — the lifecycle policy that deleted old images deleted
your rollbacks.

Third, migrations, junior-sized: a schema change and the code that requires it
never land in the same deploy. You will not practise full expand-and-contract
this afternoon, but the poison test below shows you exactly why the rule
exists. And decide the trigger while calm — which observation means "roll
back", and who decides. Today it is you, by hand; wire the health check anyway,
so a machine could.

**How to organise the prompts**

**1. Before deploying anything.**

```
Write the rollback procedure as numbered steps, naming the exact command
and the digest it targets. Then list everything in the system that will
NOT roll back with the artefact.

If that list is empty, look harder: the database belongs on it.
```

The list exists before the deploy, or it gets written during an incident,
badly.

**2. The drill.**

```
Deploy the new version and confirm /version shows the new commit. Then
execute the rollback exactly as written while I time it, stopping when
/version, checked from outside, shows the previous commit.
```

Two numbers come out: how long it took, and how many steps the written
procedure was missing. Both go in the record.

**3. The poison test.**

```
Make the new version write one row the old version cannot read — a new
enum value or format in an existing column. Deploy, write the row, roll
back, and show me exactly what the old version does when it reads it.
```

An error, a crash, a silent misread — whichever, you now own a concrete
sentence: the artefact rolled back and the data did not. That sentence is the
whole migration rule, learned on your own system.

**4. The tripwire.**

```
Add the health-check alarm that would have caught a broken deploy
automatically. Then deploy a version that crashes on start and show me
the alarm firing and the deployment reverting on its own.
```

You are checking the instrument: see red once before trusting green.

**On AWS**

**ECS built-in blue/green** is the mechanism (added 2025-07-17, checked
2026-09-22): the old task set stays warm through a bake window, so rollback is
traffic shifting back — near-instant, no rebuild — and paired with a CloudWatch
alarm and the **deployment circuit breaker** it happens automatically on failed
health checks. The neighbour is **CodeDeploy** — no additional charge for
deployments to EC2, Lambda or ECS (checked 2026-09-22) — still the answer for
EC2 fleets and Lambda alias traffic-shifting. But for ECS, the native
strategies reached parity in October 2025 (canary and linear included) and
AWS's own guidance now defaults to native. The mechanisms are free; you pay
only the transient double compute while both versions run. If your P1 went
serverless instead, the same lesson wears Lambda clothes: aliases pointing at
immutable numbered versions, shifted and shifted back.

**What productionising it means**

The rollback becomes a scheduled drill, like the restore drill P2 will demand,
with time-to-detect and time-to-restore recorded each run. The
will-not-roll-back list becomes a living document reviewed at every schema
change. And the alarm from step 4 watches the same health check a human would
use, so the machine and the person read one instrument.

**The learning**

A rollback is only real once you have done it; before that it is a hope with a
button on it. And the artefact is the easy half — the state the new version
wrote is the half that does not come back, which is why schema changes and the
code that needs them travel separately.

**How you would know it is wrong**

- After rolling back, check `/version` from outside the deploy tooling. "Deployment succeeded" from the tool is the instrument talking, not the system.
- In a scratch environment, delete the old image and run the procedure. It must fail loudly at the pull — retention is part of rollback, not a storage detail.
- If the poison test produced no visible failure in the old version, the poison was too weak. Make it worse until you see the failure's shape.
- Run the drill twice. The second time must be faster because of the written procedure. If it is not, the procedure is decorative.
