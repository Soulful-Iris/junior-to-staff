# Research: what staff engineering actually is (read 2026-09-21)

Condensed from primary sources: the StaffEng guides, Dropbox's IC5 page, Etsy's
ladder, CircleCI's, Square's posts, the Rent the Runway ladder, Tanya Reilly's
Being Glue, Will Larson's 2025-26 writing, DORA 2025, METR's RCT, the Pragmatic
Engineer 2026 tooling survey.

## The line every published ladder draws

Senior means mastering the craft and delivering within a team. Staff means
**leverage across teams, over years**. Dropbox IC5 is "multi-year, multi-team
product or platform goals" and explicitly prefers org-optimal over locally
optimal decisions. Notably, Dropbox's **code-fluency expectations stop rising at
IC4** — growth past senior is direction, talent and culture, not deeper coding.
Etsy: "directing and implementing solutions to significantly complex, unscoped
problems." CircleCI splits E1-E3 (become highly effective) from E4-E6 (create
leverage across larger groups). Feedback loops stretch from days to months.

Most staff engineers still write code. Code stops being the output.

## The five kinds of work (StaffEng's survey of ~30 practitioners)

1. setting technical direction
2. mentorship, and — distinctly, and more costly — **sponsorship**
3. injecting engineering perspective into rooms where decisions get made
4. exploring ambiguous problems normal process cannot handle
5. glue work

## The four archetypes

- **Tech Lead** — guides one team or cluster. Commonest; roughly one per eight engineers.
- **Architect** — owns a domain (APIs, infra). Requires intimate business and user context; the ivory-tower version is the failure mode. Usually ~100+ engineers.
- **Solver** — pointed at one critical fire after another. Common where planning centres on individuals. Creates transience risk.
- **Right Hand** — extends an executive's attention, borrows their authority. Only at hundreds or thousands of engineers.

Fit is archetype × company stage, not preference. Choosing the wrong archetype
for the org is a named failure mode.

## The artefacts, and what makes them good

- **Design doc** (Google style, per Malte Ubl): informal, 3-20 pages, written before code. Context, goals **and non-goals**, the design, **alternatives considered**. The trade-offs are the content; an API listing is not a design doc.
- **RFC** (Uber, per Orosz): template, named approvers, broadcast org-wide. Disagreement during review is a cheap early warning that the project itself will slip.
- **Engineering strategy** (Larson): write five design docs, then synthesise the recurring controversial decisions into a strategy. Five strategies extrapolated two to three years become a vision. Good strategy is opinionated with visible rationale; "a great vision is usually so obvious that it bores."
- **Migration** (Larson): the only scalable fix to tech debt. De-risk with the hardest teams first, enable by programmatically migrating the easy 90%, then **finish** — lint out new legacy usage, track it, actually complete it. Started-and-abandoned migrations are the classic anti-artefact.

## Promotion, and what stalls it

Works: a promotion packet maintained over quarters (projects with linked design
docs, quantified impact, named advocates, acknowledged gaps); a sponsor in the
room; visible bets that matter.

Stalls: glue work without the title (Reilly — the engineer who coordinates,
mentors and prevents outages gets told she lacks "technical contribution", and
women do such work measurably more); **snacking** (easy, low impact);
**preening** (visible, low impact); **chasing ghosts** (imposing your last
company's solutions); manager changes silently resetting progress; structural
skew, with infra teams and HQ getting disproportionate staff slots.

The mythical heroic "staff project" is mostly optional — most staff engineers
never had one.

## What changed because of AI

- Pragmatic Engineer 2026 survey (906 respondents): 95% use AI weekly, 55% use agents, and **staff+ engineers are the heaviest agent users at 63.5%**. Context and judgment gate the tools.
- Larson (2026): AI does first-pass review and triage; durable high-ownership teams matter more, not less; the scarce skill is fast sound judgment and **designing the development harness**. His "software factory" writing shows staff work becoming loop design.
- DORA 2025: AI **amplifies existing organisational quality**. Returns come from platform quality and workflow clarity — which makes classic staff work the multiplier.
- Counterweight: METR's RCT found experienced developers **19% slower** with early-2025 tools while believing they were 20% faster. Knowing where AI actually pays is itself staff judgment.
- Osmani's "70% problem": the last 30% — edge cases, security, cascading debugging — is where experience compounds.

## Commonly missing from guides

Sponsorship as distinct from mentorship. The negative space (what to stop doing).
Archetype-to-stage fit. Promotion as a multi-quarter campaign artefact. The
finish discipline of migrations. That staff is a job change rather than a bigger
senior. AI-era people-evaluation now that code volume means nothing.

## Stale advice

"You need a heroic staff project." "Keep deepening coding skill to advance"
(Dropbox caps it at senior). "Architects sit above the business." "Glue work is
always career-positive." "AI is fancy autocomplete" (superseded by agent
orchestration). "Adopt tools and win" (DORA: amplifies dysfunction too).
"Ladders are checklists" — Dropbox publishes explicit guidance that theirs is not.

## Limits of this research

Square's per-level criteria live in a PDF that could not be fetched. CircleCI's
matrix was read via excerpts. No 2025-26 AI-specific writing by Tanya Reilly was
found. Etsy, DORA, METR and Pragmatic Engineer figures were read via extended
excerpts rather than full fetches.
