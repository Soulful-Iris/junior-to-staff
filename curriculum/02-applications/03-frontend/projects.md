# 03 · Frontend — five projects

> Junior tier · each one an afternoon · read [Connect a usable interface to an API](README.md) first

Five projects, rising: one screen, then the whole app's state, then the whole
flow under law, then speed on hardware you do not own, then hostile input. Each
one ends with something you can force, reproduce or replay — never with "it
looks right", because the machine it looks right on is the one machine that
proves nothing.

All five assume the P1 reading list exists in some form. If it does not yet,
build the smallest list-plus-form that qualifies and come back.

![The same reading-list screen shown four times — loading with pulsing placeholder bars, empty with an invitation to add the first link, error saying the list did not load with a retry button, and loaded with three rows. A ring steps across the four to show that at any moment some real user is seeing each of them, and only the loaded one is usually designed.](../../../assets/diagrams/four-states.svg)

---

### 1. The four states

*You end up with one screen where loading, empty, error and loaded are each
deliberately designed, and a switch that forces any of them on demand.*

**Build**

Take P1's list view and build all four states it already has whether you built
them or not: loading, empty, error, loaded. Add a way to summon each one at
will — a query parameter, a dev-only toggle — that works without editing code.

**The thought process**

The first decision is verbal, not visual: what does each state *say*? Loading:
"I heard you; the truth is in transit". Empty: "there is nothing; here is what
to do next". Error: "I could not find out — nothing was lost". Writing them
exposes the trap: error and empty rendered from the same "no rows" branch, so
*No links yet* appears over a failed request — a lie in a calm voice.

Second: the forcing mechanism comes before the states. A state you cannot
summon is reviewed once, the day it is written, and never again — your fast
network shows you loaded and nothing else.

Third: loading needs two numbers you choose — how long before it appears, and
how long before it gives up. A loading state with no exit is the error state
you refused to design.

**How to organise the prompts**

1. ```
   Here is my list view. Before any code: for each of the four states —
   loading, empty, error, loaded — write the exact copy the user sees and
   one sentence on what they can do next. Error and empty must not share
   a sentence. Do not write code yet.
   ```

   Review the copy as product, because it is. If the error text does not say
   whether the user's data is safe, send it back.

2. ```
   Implement the four states, plus a dev-only override — a query
   parameter like ?force=error — that makes the view render whichever
   state I name, regardless of what the server does.
   ```

   Walk all four with the override. Then stop the API for real and confirm you
   get the designed error, not a blank page and not the empty state.

3. ```
   List the states this screen can still reach that we did not design: a
   response arriving after the user navigated away, a retry that fails
   again, an empty result while a filter is active. For each, tell me
   what renders today.
   ```

   Make the model testify about its gaps. "Empty while filtered" catches
   almost everyone — "no results match" and "no links yet" are different
   sentences too.

**On AWS**

**Amplify Hosting** is the short road — CloudFront and S3 underneath, with
git-push deploys, branch previews and certificates handled; as of 2026-09-22
even the S3 documentation points static hosting at it. Plain **S3 +
CloudFront** is for when you want the pieces in your own
infrastructure-as-code, owning invalidations and certificates in exchange.
Both are near-free at this scale. Either way, CloudFront has an error state of
its own — the custom error response users see when your API dies behind it.
Force that path once and look at it.

**What productionising it means**

Gate the override out of production builds, or make it read-only by
construction. Empty-state copy becomes product surface somebody owns. And each
designed error state should emit a metric when a real user lands on it — the
cheapest availability number you will ever collect.

**The learning**

Loaded is one of four, and the other three are where trust is lost, because
your own chair never shows them to you. You will start noticing every spinner
that cannot end and every "no items" that might be a lie.

**How you would know it is wrong**

- Stop the API. A stranger must be able to tell the result from "empty" without reading code.
- Open a brand-new account. The first screen is your designed empty state, or the proof there never was one.
- Force loading and wait. It must resolve to the error state by itself; an eternal spinner is red.
- Apply a filter that matches nothing. "No links yet" is red, because it is not true.

---

### 2. Where does this state live

*You end up with a one-page inventory — every fact on the screen, exactly one
home each — and a URL that reproduces the view on any machine.*

**Build**

List every piece of state in P1's interface and give each exactly one home:
server, URL, shared store, or component memory. Move the ones living in the
wrong place, then prove it: a refresh mid-task and a link pasted into a
private window must both reproduce the view.

**The thought process**

You cannot place what you have not listed, so the inventory is the first
artefact and most of the work: the filter, the page, the half-typed URL, the
open dropdown, who is signed in, the list itself. Most state bugs are facts
nobody ever wrote down.

Then the placement rule, per fact: what must it survive? Another person or
device means the server. A refresh or a shared link means the URL. Far-apart
parts of the page needing it at the same moment means a shared store.
Everything else dies with the component. First yes wins.

The hard case is server data sitting on the page. That copy is legitimate only
as a declared cache — named staleness, a rule for when it refetches. Copied
"for convenience" and synchronised by effects, it is drift on a schedule.

And state in the URL has a consequence people skip: the URL becomes an
interface. Back-button behaviour is now a design decision — push or replace,
per change — and nothing secret may enter it, because query strings end up in
logs, bookmarks and screenshots.

**How to organise the prompts**

1. ```
   Read this interface. List every piece of state as a table: the fact,
   where it lives today, what it must survive (refresh, shared link,
   another device, none), and where it should live. Do not change any
   code yet.
   ```

   Argue with the table. If every row landed in a shared store, the question
   was avoided, not answered.

2. ```
   Move one misplaced fact: put the current filter and page in the URL
   and make the view render from them. Refreshing or opening the URL
   fresh must land on the same view. Do not touch any other fact yet.
   ```

   Refresh mid-task, then hand-edit the URL to a nonsense page number — the
   view must survive both. Repeat the ask per fact, one at a time.

3. ```
   Now list the state you deliberately did NOT put in the URL, and why.
   Then show me every place server data is copied into page memory, and
   for each copy: who invalidates it, and when.
   ```

   The second half is the drift hunt. A copy with no invalidation story is a
   bug that has not happened yet.

**On AWS**

URL-as-state is where the CDN starts to matter. **CloudFront**'s cache key
decides whether `?filter=unread` is one cached object or a miss for every
permutation: cache the app shell ignoring query strings, and cache API
responses by exactly the parameters that change the answer. For normalising
URLs at the edge — sorting parameters, stripping tracking junk so equivalent
links share a cache entry — **CloudFront Functions** is the tool and
**Lambda@Edge** the neighbour to refuse: checked 2026-09-22, Functions are
JavaScript-only, viewer-events-only, sub-millisecond, no network access —
exactly enough for this, and priced like it. Lambda@Edge earns its place only
when the edge must call something, which normalisation never does.

**What productionising it means**

Shared URLs are promises: renaming a query parameter breaks every bookmark in
the wild, so old names get redirects, not deletion. URL state is also user
input — a hand-edited `?page=-4` must degrade politely. And check what your
logs now capture, because the URL carries what the user was looking at.

**The learning**

"Where does this live" is a decision made per fact, not per app, and refresh
becomes a test you run on purpose. Once every fact has one home, the stale
copy, the vanished filter and the back button that exits stop being mysteries.

**How you would know it is wrong**

- Refresh in the middle of every task. Anything lost that should have survived is red.
- Paste a filtered URL into a private window. A different view is red.
- Press back after three filter changes. Leaving the app instead of stepping back through filters is red.
- Grep for server data assigned into local variables and kept fresh by effects. Each hit needs an invalidation story or it is red.
- Look for anything secret in the query string. One token is red.

---

### 3. The keyboard-only pass

*You end up having completed the whole flow without touching the mouse, with
contrast and focus order measured — and a defect list sorted by what the model
got wrong.*

**Build**

Unplug the mouse and get through all of P1: sign in, add a URL, tag it, mark
it read, delete it. Fix what blocks you, then measure what taste cannot: focus
visibility, Tab order, accessible names, contrast. The European Accessibility
Act (Directive (EU) 2019/882) has applied to services sold into the EU since
28 June 2025 — re-verified 2026-09-22 — with WCAG 2.2 AA as the working
benchmark, so this is a legal floor, not polish.

**The thought process**

First decision: what is *the flow*? The unit here is the journey, not the
element — a page of individually accessible controls in an order that jumps
around the screen still fails a real person.

Second: fix in dependency order. Reachability first (can Tab land on it at
all), then focus visibility, then order, then names, then contrast. Each check
is meaningless until the one before it passes.

Third — the judging skill this section promised — model-written interfaces
fail here in a pattern, not at random: a `<div>` with a click handler where a
button belonged; a placeholder doing a label's job; the focus outline deleted
because it "looked wrong"; ARIA sprinkled onto elements that would have
carried everything for free had they been the native ones. Judge by cause, not
symptom. The fix is almost always a more native element, almost never another
attribute.

**How to organise the prompts**

1. ```
   Audit this page against WCAG 2.2 AA, element by element: reachable
   with Tab? has an accessible name? focus visible on it? Tab order
   matching visual order? text contrast at least 4.5:1? List every
   failure with the exact line that causes it. Do not fix anything.
   ```

   Verify two findings by hand before trusting the rest — tab to one, measure
   one contrast with a checker. An audit you did not spot-check is a rumour.

2. ```
   Classify each failure by the mistake that produced it: clickable div,
   placeholder as label, removed focus indicator, decorative ARIA on the
   wrong element, or an invented attribute. One class per failure.
   ```

   This is the ask that teaches you to review interface code. The class
   predicts the fix, and after one pass you will recognise these five in any
   generated UI before running it.

3. ```
   Fix them, with the most native element available in each case. No
   aria-* where an element exists that does the job. The focus indicator
   may change; it may not disappear. Then re-run the audit from step 1.
   ```

   Re-audit, then give a screen reader five minutes — VoiceOver, Narrator or
   NVDA. Buttons must announce as buttons, with names. "Clickable, clickable,
   clickable" means the divs survived.

**On AWS**

Accessibility regresses one merged div at a time, so the durable version of
this project is the journey re-run on a schedule. **CloudWatch Synthetics** can
drive the whole flow with keyboard events only and screenshot every step
against production — and it beats a Lambda you assemble because the managed
headless browser is exactly the part that is miserable to package yourself.
The free first stop is the same script in **GitHub Actions** on every pull
request; Synthetics earns its per-run cost when you want the check against the
deployed site rather than your branch. Wire its alarm into **CloudWatch** like
any other canary, because a keyboard flow that broke on Tuesday is an outage
for someone.

**What productionising it means**

Put contrast into design tokens so a stray hex tweak cannot dip below 4.5:1
silently, and make the audit part of the pipeline rather than an event. In the
EU you also owe an accessibility statement describing conformance — the audit
output is its first draft, which is the most concrete reason to keep it
current.

**The learning**

Accessibility is mechanics you can measure, not empathy you perform. The
failures cluster exactly where looks diverge from semantics — which is why
model-written UI, fluent at looks, fails here more reliably than anywhere
else.

**How you would know it is wrong**

- Go end to end with no mouse. Anything unreachable, or focused invisibly, is red — and in the EU since June 2025, arguably illegal.
- Measure the greyest caption with a contrast tool. Your eye approving it is not evidence; your eye knows what the design intended.
- Remove a label on purpose and re-run your audit. If it stays green, the audit checks nothing and is itself red.
- Five minutes of a screen reader. A page announced as "clickable, clickable" failed, whatever the audit said.

---

### 4. Fast enough to feel

*You end up with before-and-after numbers from a throttled connection and a
mid-range device profile, and the one change that moved first useful paint.*

**Build**

Measure P1 loading cold — cache off, network throttled, CPU throttled — from a
clean profile. Find what actually delays the first useful paint, which is the
list rows, not the header. Make one change. Measure again, same conditions.

**The thought process**

First: what to measure. The field standard (re-checked 2026-09-22 at web.dev)
is Core Web Vitals at the 75th percentile of real visits: main content painted
within 2.5 s, interaction response within 200 ms, layout shift under 0.1. Your
laptop sits at the fast tail of that distribution, so the honest lab condition
is both throttles at once — network *and* CPU. The CPU one is the one everyone
skips, and it is where a big script bundle hurts twice: bytes arrive slowly
once, but they parse and execute slowly on every mid-range phone forever.

Second: define "first useful paint" for this page before measuring. The metric
tracks the largest paint; you care about the moment a person can start reading
their list. Know which element it is and whether the two agree.

Third: one change per measurement. A batch of five fixes that improves the
number teaches you nothing about which fix mattered — and one of the five
probably made things worse under cover of the other four.

**How to organise the prompts**

1. ```
   Do not change anything yet. Measure this page cold — cache disabled,
   network throttled to a mid-tier mobile profile, CPU throttled 4x —
   and report: the three Core Web Vitals numbers, which element was the
   largest paint, and where the time went: server wait, network
   transfer, script parse and execute, images.
   ```

   The checkable artefact is the baseline with its conditions named. No
   conditions, no baseline.

2. ```
   Rank the causes of the delay by evidence in that trace, not by what
   is usually slow in web apps. For each cause, name the number in the
   measurement that points at it.
   ```

   Asking for the evidence keeps it honest. "Bundles are usually the problem"
   is fashion; "1.8 s of script execution before first paint" is a fact.

3. ```
   Make the single highest-ranked change and nothing else. Re-measure
   under identical conditions and report the delta on all three numbers,
   including any that got worse.
   ```

   Then revert the change and measure once more. If the delta does not
   reverse, you were measuring noise, not the change.

**On AWS**

Two instruments, two questions. **CloudWatch RUM** answers "what do real users
get": a small snippet, a sampling percentage you choose — which is also how
you control what it costs — and page-load numbers broken down by device,
browser and geography; the 75th percentile of reality, verified in the docs
2026-09-22. **CloudWatch Synthetics** answers "what changed since yesterday":
a scripted browser on a schedule, perfectly consistent and perfectly
unrepresentative, because it only ever measures its own machine. Field tells
you the truth late; lab tells you a rumour early; you want both. **CloudFront**
helps with the bytes — closer, compressed — with the honest caveat that no CDN
shortens parse-and-execute on the user's phone. The interaction delay is paid
on the device.

**What productionising it means**

A budget in the pipeline: the build fails when the shipped script crosses a
line you wrote down, because regressions arrive by dependency bump, not by
your commit. RUM's p75 lives on a dashboard next to the lab number, so you
notice when the two stop agreeing — that gap means your lab has drifted from
your users.

**The learning**

"Feels fast" is your hardware talking. The user's phone is the only slow
machine involved and the only one you never sat in front of — until the
throttled cold run is a habit, you have never actually seen your own site.

**How you would know it is wrong**

- Run the identical throttled measurement twice, changing nothing. Wildly different numbers mean you are measuring noise, and every delta you report from it is fiction.
- Compare your lab number with RUM's p75 once real sessions exist. If lab is far rosier, your lab profile is a costume.
- Check the measured largest paint is the list, not the header or a spinner. Optimising the wrong element is a green light on the wrong road.
- Re-measure with a warm cache and note the gap. If you only ever demoed warm, the first-visit number was never measured at all.

---

### 5. The form the server does not trust

*You end up with an add-URL form whose server rejects everything the client
would have — proven by a transcript of raw requests that never touched your
page.*

**Build**

Give P1's add-URL form validation on both sides: client for fast feedback,
server as the law. Then bypass your own client entirely — curl, or any HTTP
tool — and attack the endpoint with requests the page would never send. Keep
the transcript.

**The thought process**

First: one definition of valid, two enforcement points. Either both sides read
the same schema, or you write the rules twice and add a check that proves they
still agree — two hand-kept copies of "valid" diverge one release after you
stop looking.

Second: the server's list is necessarily longer. The client can check shape;
only the server can check who is asking, whether they may touch this item
(P1's one non-negotiable rule), how often, how big — and, because P1 fetches
whatever URL it is given, *where that URL points*. A submitted
`http://169.254.169.254/` turns your title-fetcher into a probe inside your
own network; the trick is called SSRF, and refusing private and metadata
addresses before fetching is server work the client cannot even see.

Third: the double-submit pair. The disabled button during flight is a
courtesy; the server deciding what a duplicate *is* — same URL, or same URL
from the same person — and what happens then is the enforcement. Decide it in
writing before the model decides it by accident.

**How to organise the prompts**

1. ```
   For this form, write the validation rules as a table: rule, checked
   on the client, checked on the server. Then list the checks that exist
   ONLY on the server — identity, ownership, rate, size, and where the
   submitted URL is allowed to point. Do not write code yet.
   ```

   Checkable by inspection: every client rule must reappear on the server,
   and the server-only list must be non-empty or the design is wrong.

2. ```
   Implement both sides. Then produce a transcript of five raw requests
   sent straight to the endpoint, bypassing the page: a garbage URL, a
   missing field, an oversized body, another user's item id on the edit
   route, and an internal address like http://169.254.169.254/. For
   each: the request, the expected refusal, the actual response.
   ```

   Run the transcript yourself before believing it. Five refusals and zero
   new rows is the pass; anything else is the finding.

3. ```
   Make a submission take ten seconds. Show me what the button does
   during it, and what two fast clicks produce on the server. One row,
   or exactly the duplicate behaviour we wrote down — nothing else.
   ```

   Throttle the network and double-click yourself. Count rows in the
   database, not toasts on the screen.

**On AWS**

Defence in layers, outermost first. **AWS WAF** sits in front of CloudFront,
API Gateway or a load balancer and strips the internet's background radiation
— rate limits, oversized bodies, known-bad patterns via managed rule groups.
But it cannot know what a valid reading-list entry is: it filters classes of
hostile traffic, not your rules, and it is the layer that costs real money to
leave on, so it earns its place when the endpoint is public. **API Gateway**
request validation rejects malformed *shape* against a JSON Schema model
before your compute runs, at no extra charge on a gateway you already have —
the same contract idea the testing section builds on. The semantic checks —
ownership, duplicates, where the URL points — live only in your handler.
Three layers, and the innermost is the only one that is yours.

**What productionising it means**

Rejections become telemetry: a spike in validation failures is an attack or a
client you broke, and both deserve an alarm. Refusal messages must not echo
internals or reflect hostile input back. And logging rejected payloads is a
decision about other people's data — make it on purpose, not by default.

**The learning**

The client is a suggestion running on somebody else's machine. Everything else
in this section was about being kind to the user; this project is about not
believing them — client validation is a courtesy, server validation is the
only validation.

**How you would know it is wrong**

- Send garbage straight to the endpoint. Anything but a refusal and zero new rows means the validation was theatre.
- Delete the client validation entirely. Server behaviour must not change at all.
- Double-click add on a throttled connection and count database rows. Two rows you did not decide on is red.
- Submit an internal or metadata address, then check the fetcher's logs for an attempt. A refusal after the probe already fired is the same leak with better manners.
