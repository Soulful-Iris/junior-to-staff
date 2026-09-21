# 11 · Security

> Senior tier · feeds **P2 (it survives)**

## The one-liner

Security, as an application engineer practises it, is four questions asked of
every change: who is this, what may they do to this object, what did we just
install, and what can all of it reach. Authentication you mostly buy.
Authorisation you build — and it is where real applications actually break.

## The failure it prevents

Two shapes. One lives in code you wrote, one in code you installed.

**Yours.** The reading list has a rule: you may only delete your own items. It
is enforced in the UI — the delete button renders only on your items. A user
opens the network tab, copies the delete request, swaps in someone else's item
id, and sends it. It works. No error, no log line, nothing to notice until
somebody looks. This is the least clever vulnerability in the industry and the
most common: OWASP has ranked Broken Access Control the top web application
risk since 2021, and it keeps the spot in 2025. *(Checked 2026-09-21: owasp.org
presents Top 10:2025 as current — A01 Broken Access Control, now absorbing
SSRF; A02 Security Misconfiguration; a new A03 Software Supply Chain Failures.
No final publication date is shown and some pages still carry an RC1 label, so
read it as current but recently settled.)*

**Installed.** On 31 March 2026, two malicious versions of axios — an HTTP
client vendor write-ups put at over 100 million weekly downloads — appeared on
npm. Real releases went out through npm's OIDC trusted publishing, tied
cryptographically to CI. The attacker never had to defeat it: they published
manually, with a long-lived token stolen from the maintainer's compromised
machine — a parallel path nobody had closed. The malicious versions carried no
provenance, which is part of how responders spotted them, and were pulled in
about three hours. *(Checked 2026-09-21 against Datadog Security Labs, Huntress
and Tenable write-ups.)*

Same lesson twice: **the control existed, and a second path went around it.**
Most senior security work is hunting the second path.

## The mental model

### Authentication is bought; authorisation is built

**Authentication** answers *who is this*. Its parts — password storage,
sessions, MFA, recovery — are the same everywhere, so the senior move is not to
build them: a maintained library or provider, with passkeys as the mainstream
front door. The FIDO Alliance put passkeys at roughly five billion in use in
May 2026, offered by 48% of the top-100 websites — the consortium's own
figures; independent censuses find support thins sharply below the biggest
sites *(checked 2026-09-21)*. When authentication breaks, it breaks at the
edges someone built anyway: password reset, session lifetime, the OAuth
callback. And say one thing precisely: **OAuth 2.1 is an IETF Internet-Draft,
not a standard** — revision 16, dated 3 September 2026, not yet submitted to
the IESG *(IETF datatracker, checked 2026-09-21)*. Follow its profile — PKCE on
every code flow, no implicit grant — but do not cite it as settled.

**Authorisation** answers *may this identity do this to this object*. Nobody
sells it finished, because the rules are your product's rules — so it fails far
more. The distinction juniors blur: being signed in is authentication; holding
the `editor` role is coarse authorisation; neither says anything about *this
row*. Object-level checks are where the bodies are buried. SSRF — folded into
A01 in 2025 — is the same failure wearing a server: yours, talked into spending
its authority on someone else's request.

### Three ways to build authorisation, and how each fails

![Three authorisation models side by side, each with its failure mode: per-endpoint checks fail by omission when one route never gets a check; a central policy engine fails by drift when the policy stops matching the running code; a relationship graph fails by weight, because the graph is a second system that must be fed and kept in sync](../../../assets/diagrams/authz-failure-modes.svg)

- **Per-endpoint checks.** Every handler asks its own question. Simple, local,
  greppable. Fails by **omission**: nothing notices the handler that never
  asked. Defence: a route list diffed against a check list, mechanically, in CI.
- **A policy engine.** One module or service answers `may(user, action,
  object)`. One place to audit and test. Fails by **drift**: the policy is a
  description of the application, and descriptions rot — the new export
  endpoint ships, nobody maps it, and the policy governs a system that no
  longer exists. Defence: the engine is the only path, and unmapped routes are
  denied, not allowed.
- **A relationship graph.** Permissions as relations — user is member of team,
  team is editor of doc — answered by walking edges. The only model that
  survives real sharing and nesting. Fails by **weight**: the graph is a second
  stateful system. Every ownership change must be mirrored into it, it has its
  own consistency and downtime, and when it is unreachable you choose between
  refusing everyone and trusting everyone. You have not removed the problem;
  you have hired it a service.

Pick by the failure you can afford to hunt. A ten-route app on a relationship
graph is running a distributed system to guard a to-do list; a
two-hundred-route app on hand-written checks is a lottery on omission.

### Secrets: eliminate, then rotate what is left

The junior floor — nothing secret in the repo, rotation as the response to
exposure — is in [07 · Shipping it](../../01-junior/07-shipping-it/). The
senior direction is stronger: **the best secret is one that does not exist.**
Workload identity federation replaces stored keys: a CI job or service proves
what it is with a short-lived OIDC token from the platform running it, and
exchanges that for cloud credentials that live minutes. Nothing to store,
nothing to leak, nothing that outlives its owner.

Why this beats rotation is measured. GitGuardian retested secrets it had found
leaked on public GitHub in 2022: in its March 2026 report, more than 64% were
still valid in January 2026 — four years on. That is the vendor's own scanning
dataset, not an independent measurement, but the direction is unambiguous:
long-lived credentials outlive the person who made them, the ticket that
justified them, and everyone's memory that they exist. *(Checked 2026-09-21.)*

### The supply chain, past the basics

[07 · Shipping it](../../01-junior/07-shipping-it/) taught the floor —
committed lockfile, strict installs, lifecycle scripts off, rotate after
compromise — out of the Shai-Hulud worm. The senior layer is policy:

- **Cooldowns.** Most malicious releases are caught within hours — pnpm's
  documentation argues within one — so refusing versions younger than a day
  sidesteps most of the risk. pnpm ships a 24-hour `minimumReleaseAge` by
  default since v11 *(checked 2026-09-21)*; set the equivalent wherever you
  are, with an exclude list for urgent fixes.
- **Lockfile as reviewed code.** The lockfile diff in a pull request changes
  what runs in production. Read it like code; Request 3 below is that review.
- **Trusted publishing, with the token path closed.** Publishing from CI over
  OIDC — GA on npm since July 2025, with PyPI's PEP 740 attestations GA since
  November 2024 — removes the long-lived publish token. axios proves the
  corollary: **a provenance system with a parallel token path is a provenance
  system you do not have.** npm disabled new classic tokens in November 2025
  and revoked the rest that December *(GitHub changelogs, checked 2026-09-21)*;
  close every legacy path yourself, because an attacker needs only one.
- **Provenance and attestations.** Signed statements binding an artefact to the
  source and workflow that built it. The value is asymmetric: absence, on a
  package that normally has it, is a red flag tooling can check.
- **SBOMs.** A machine-readable inventory of what is inside the artefact, for
  the bad Tuesday when "are we affected?" should be a query, not archaeology.

### The ten-minute review

What a senior actually does on a change, in order. What can someone do after
this that they could not do before — and who counts as "someone"? Each new
route: where is its check, and is it object-level? Each new query: whose rows
can it return? Each new outbound request: can user input steer the destination?
Each new dependency: how old, what scripts, which publisher? Each new
credential: why not federation? And what would the logs show if this were
abused? Ten minutes. Most findings come from the first question.

## What good looks like

- Every non-public route can be pointed at its authorisation rule — file and
  line — and the mapping is generated or diffed, not remembered.
- Mutating endpoints check the object, not just the session or the role.
- Denials are logged with actor, object and rule, and someone would notice a
  spike.
- Authentication is a maintained library or provider; passkeys or strong MFA
  offered; nobody wrote password hashing this decade.
- CI and services reach the cloud by identity federation; the secret store is
  short, every entry with an owner and an expiry.
- New dependency versions wait out a cooldown; CI installs strictly from the
  lockfile; publishing has no token path.
- You can produce an SBOM for what is running now, not what shipped in spring.

Done badly, you see:

- The rule lives in the UI, and the API trusts the button.
- A role check where an ownership check was needed, so every "editor" can edit
  everything.
- A cloud key in CI from two years ago, "used by something", rotated never.
- A policy engine adopted with ceremony, now bypassed by three services
  "temporarily".
- A green vulnerability scan standing in for the question nobody asked: could a
  stolen token still publish?
- Security as a checklist run the week before launch, against a design fixed
  months earlier.

## Ask Claude for this

**Request 1 — the authorisation audit**

```
List every route or endpoint in this codebase. Produce a table: method and
path; handler; does it require authentication; the authorisation rule it
enforces, quoted; the file and line where that rule runs; and whether the
check is object-level (this specific record) or only role- or session-level.

Routes where you cannot point to a line are the finding, not a gap in your
answer — list them first. Do not fix anything, and do not summarise. I want
every route.
```

*Why it is asked that way:* the file-and-line requirement is the constraint
doing the work. Without it, a model sees an auth decorator on six routes and
reports a pattern; with it, every row needs evidence. Listing uncovered routes
first flips the incentive from reassurance to findings.

*What you should get back:* a complete table, and in any real codebase a few
rows saying "role only" or pointing at nothing. If everything is covered, read
three handlers yourself before believing it.

*Push back on:* "the auth middleware covers this." Middleware knows who the
user is; it almost never knows which row they are touching.

**Request 2 — the credential census, with an exit**

```
Find every credential this system uses: environment variables, CI secrets,
config files, cloud keys, database passwords. For each: what it grants, how
long it lives, and what breaks the moment it is revoked.

Then split the list in two. List A: credentials that workload identity
federation between the platforms involved could eliminate. List B:
credentials that genuinely must remain stored secrets. Propose rotation only
for list B. For list A, propose elimination.
```

*Why:* the split is the point. Ask only for a secrets audit and you get a
rotation schedule for everything, which quietly preserves keys that should not
exist.

*What you should get back:* most CI-to-cloud credentials in list A. If list A
comes back empty, name your CI system and cloud provider and ask again; the
OIDC pairing between the major ones exists.

*Push back on:* "rotate quarterly" applied to list A — diligence spent
maintaining the vulnerability.

**Request 3 — the lockfile diff, reviewed for tampering**

```
Here is the lockfile diff from this pull request. For every package added
or changed: days since this version was published; does it add or change
install scripts; is it published with provenance or attestations; has the
publisher or publishing method changed recently.

Do not report CVE counts. I am asking about tampering, not known bugs.
```

*Why:* CVE scanners answer "is this known bad", a different instrument from
"was this changed under me". The four columns are the tamper signals: fresh
version, new script, missing provenance, changed publisher.

*Push back on:* "no known vulnerabilities" as the conclusion. A package
compromised yesterday has no CVE yet.

## How you would know it is wrong

1. **Cross the user boundary by hand.** Signed in as one user, send a mutating
   request with another user's object id — directly, not through the UI. Expect
   a refusal and a log line. Then script it for every mutating endpoint and run
   it in CI, where it catches the regression you have not written yet.
2. **Diff routes against checks mechanically.** Enumerate both, subtract. The
   difference must be a named list of deliberately public routes, not a shrug.
   This is the check that catches omission — the forgotten route in the diagram.
3. **Revoke a credential and time the recovery.** In staging, on purpose, with
   a stopwatch. That number is your incident response time; if recovery needs a
   code change or a meeting, you found the work.
4. **Read the expiry on the credential CI uses.** Months means a stored key,
   whatever the dashboard calls it. Federation credentials live minutes.
5. **Try the bypass you believe is closed.** If trusted publishing is the only
   publish path, a dry-run token publish should be refused. The axios attacker
   found that check unrun.
6. **Count last week's authorisation denials.** Zero is not clean — the public
   internet probes everything. Zero means denials are not logged, and the check
   cannot go red.
7. **Age your newest production dependency.** If nobody can answer inside a
   minute, there is no cooldown, whatever the policy document says.

> The standing rule: **a check that cannot fail is not a check.** "We have
> never had an authorisation incident" and "we would not know if we had"
> produce identical dashboards.

## Your slice of the project

P1 gave the reading list one authorisation rule and one test for it. On **P2**,
harden the whole surface:

- The authorisation table, committed: every route, its rule, its file and line,
  object-level or not. Generated or hand-built, but diffable.
- The cross-user suite: for every mutating endpoint, a test that presents
  another user's object id and expects a refusal. Runs in CI.
- Denials logged with actor and object id, and one place you would see a spike.
- CI reaches your deploy target by OIDC federation; no long-lived cloud key in
  the repository's CI secrets.
- A cooldown on new dependency versions, and CI installing strictly from the
  lockfile with scripts disabled — 07 asked for the habit; now it is enforced
  configuration.
- One revocation drill, timed and written down.

**Acceptance criteria:**

- Delete one authorisation check; the cross-user suite goes red; restore it.
- Routes minus checks equals your published list of public routes, exactly.
- No stored credential in CI grants cloud access for longer than hours.
- You can state the age of your newest dependency, and the duration of your
  revocation drill, without searching for more than a minute.

## Words you now own

- **authentication** — establishing who is asking. Buy it, do not build it.
- **authorisation** — deciding whether they may do this to this object. Yours
  to build.
- **object-level authorisation** — the check against the specific record, not
  the role. Its absence is IDOR — change the id, get someone else's data.
- **SSRF** — server-side request forgery: your server talked into spending its
  authority for someone else. Filed under access control since 2025.
- **policy engine** — one central place that answers may(user, action, object).
- **relationship graph / ReBAC** — permissions as relations between users,
  groups and objects, answered by walking edges.
- **workload identity federation** — a service proves its identity with a
  platform-issued OIDC token and receives short-lived credentials. The
  eliminate-not-rotate mechanism.
- **cooldown** — refusing to install package versions younger than a set age.
- **trusted publishing** — packages published from CI over OIDC, with no
  long-lived token to steal.
- **provenance / attestation** — a signed, verifiable statement binding an
  artefact to the source and build that produced it.
- **SBOM** — software bill of materials: the machine-readable inventory of what
  is inside your artefact.
- **passkey** — a phishing-resistant public-key credential replacing passwords,
  unlocked by the device that holds it.

---

**Not covered here:** network and infrastructure security, WAFs, compliance
regimes, cryptography design, and formal threat modelling — the ten-minute
review is the working slice of that last one. Security of AI features, prompt
injection and the lethal trifecta live in [15 · AI systems](../15-ai-systems/).
The junior floor for secrets and dependencies is
[07 · Shipping it](../../01-junior/07-shipping-it/); this section assumed it.
