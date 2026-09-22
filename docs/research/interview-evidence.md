# Interview evidence · 2026-09-22 snapshot

**Review date: 2026-09-22. Dated evidence boundary: 2025-09-22 or later; preferred window: 2026-03-22 through 2026-09-22.** The selected firsthand-report table below uses the preferred window. Reports outside six months but inside one year may be retained separately with that limitation; older publications do not support recent conclusions. This is a dated, qualitative review, not a representative survey. We searched Reddit, LeetCode Discuss, first-person posts, interview-preparation sites, and official employer guidance. Old reports, recycled “2026” titles, unverified dates, and unrelated search results were not used to establish recent trends.

## What this evidence supports

Prepare both algorithms and practical implementation. The dated Amazon report below combines coding, low-level design, system design, and behavioral questions. The Google report describes graph reasoning and coding. Experienced-engineer discussions also describe API work, code review, and AI-assisted exercises. For senior/staff practice, add deeper follow-ups and evidence from real projects.

It does **not** support a precise “most asked” ranking, universal company loops, or exact pass thresholds. Authors self-select, outcomes are self-reported, multiple comments can describe the same experience, and location/team differences are substantial. We do not treat a poster's interpretation of interviewer feedback as the company's rubric.

## Dated evidence ledger

Read the original source before using a company-specific detail. Dates below distinguish the event from the post; an unknown event date stays unknown. All sources were accessed 2026-09-22.

| ID | Source and date basis | Level / location | Narrow observation | Curriculum consequence |
|---|---|---|---|---|
| R1 | [Amazon SDE II experience](https://leetcode.com/discuss/post/8457154/amazon-sde-ii-interview-experience-2026-19lzv/) — interview dates explicitly July 2, 27, 29, 31 and August 4, 2026; outcome August 11 | SDE II; location not established | Prefix-sum question, cache implementation, dependency scheduling, device-notification design, and behavioral follow-ups | Prefix sums, LRU, topological order, failure scenarios, implementation timeboxes |
| R2 | [Amazon experience and feedback request](https://leetcode.com/discuss/post/8096139/) — indexed publication April 24, 2026; individual interview dates unspecified | SDE II; location not established | Graph/tree tasks, substring window, feature-level read receipts, and an idempotency discussion | Windows/BFS; clarify whether interviewer wants feature implementation or whole-system design |
| R3 | [US Google L4 offer report](https://www.reddit.com/r/leetcode/comments/1u8qhwd/us_google_l4_swe_offer_interview_experience_tips/) — indexed publication June 18, 2026; individual event dates unspecified | L4, US; do not relabel L4 as senior | Weighted graph problem, clarifying discussion, implementation and optimization under time pressure | Dijkstra, dry runs, communicating assumptions |
| R4 | [What gets asked in 2026?](https://www.reddit.com/r/ExperiencedDevs/comments/1ur16w3/what_gets_asked_in_2026_interview/) — indexed publication July 8, 2026 | OP 5 YOE, US big tech; commenters vary | Respondents describe coding/design/behavioral alongside some practical API, PR review, and AI-enabled work | Keep both independent and practical/AI coding exercises |
| R5 | [Preparing for senior/staff roles](https://www.reddit.com/r/ExperiencedDevs/comments/1vxl03i/how_to_prep_for_seniorstaff_roles_in_2026/) — indexed publication August 25, 2026 | 15 YOE, frontend/full stack/product; SF Bay/NYC targets | Author reports deeper design probes, project-story difficulty, and both manual and agentic coding assessments | Staff ownership rubric; full-stack mutations; changing-constraint mocks |
| R6 | [2026 interview experience](https://www.reddit.com/r/ExperiencedDevs/comments/1uky9ws/2026_interview_experience/) — indexed publication July 2, 2026 | 7 YOE; mentions Anthropic and Databricks | Author found practical correctness under time pressure demanding | Test edge cases and finish runnable code; do not adopt the author's universal “perfect or fail” claim |
| R7 | [How is the interview process?](https://www.reddit.com/r/ExperiencedDevs/comments/1ttf0zp/hows_the_interview_process_these_days/) — indexed publication June 1, 2026 | Mixed companies/levels | A respondent describes no-AI live coding plus an AI-allowed assignment | Practice both modes; verify actual rules |
| R8 | [Designing experienced-dev interviews](https://www.reddit.com/r/ExperiencedDevs/comments/1su50a4/what_the_heck_does_a_good_experienced_dev/) — indexed publication April 24, 2026 | Interviewer perspective; mid/senior | Discussion favors probing actual decisions and alternatives in past projects | Decision-story questions; this is interviewer opinion, not a company mandate |
| R9 | [First-person preparation reflection](https://dev.to/karuha/why-i-stopped-grinding-leetcode-and-started-getting-offers-1c77) — published March 24, 2026 | Company/level not established | Author emphasizes communicating existing experience | Supplementary perspective only; no frequency claim or named-company inference |

R1–R3 are three named-company candidate narratives, not three random samples of the market. R4–R8 are discussion threads; do not count every reply as an independent verified interview. R9 is a personal reflection. Indexed publication dates provide coarse recency, not verification of interview dates or identity.

## Current official guidance, separate from recent reports

| Source | What it explicitly supports | Date limitation |
|---|---|---|
| [Amazon SDE III preparation](https://www.amazon.jobs/content/en/how-we-hire/sde-iii-interview-prep) | Coding, system design, high/low-level design resources, behavioral evaluation; executable code and testing | Live guidance accessed September 22; publication date not established |
| [Microsoft technical interviewing](https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing) | Problem solving, design, runnable coding, testing, and role-related experience | Live guidance accessed September 22; publication date not established |

These pages explain current published expectations. They are not counted as interviews in the six-month window. AWS, Python, ECMAScript, and Kafka primary documentation are used only for technical correctness and appear next to the relevant lessons.

## How questions are asked and how to practice beyond the baseline

| Reported shape | Baseline practice | Deeper follow-up | Level emphasis |
|---|---|---|---|
| Coding with added requirements | Correct code and explicit complexity | Change memory/ordering/streaming constraints; retest | Junior: core invariant; senior/staff: preserve correctness under change |
| Feature design inside an existing product | Model state, interfaces, and normal flow | Concurrent edits, offline users, out-of-order events | Junior: coherent feature; senior: failure behavior; staff: compatibility and ownership |
| Whole-system design | Requirements and complete data flow | Identify actual bottleneck, cost, recovery, and security boundary | Increasing depth and independence; no universal company mapping |
| Project deep dive | Explain your contribution and outcome | Rejected alternative, disagreement, evidence, and a decision you would change | Senior: ownership; staff: cross-team direction and influence |
| AI-assisted or repository task | Run, understand, modify, and test code | Catch generated mistakes; explain every critical boundary | All levels: own correctness; senior/staff: scope and system consequences |

These “deeper” columns are our teaching recommendations, informed by the sources, not official scoring criteria.

## Excluded or unresolved leads

| Lead | Why not used as current evidence |
|---|---|
| [Meta E5 offer / problem list](https://leetcode.com/discuss/post/7550296) | February 3, 2026 is within one year but outside the preferred six-month sample; not used to infer current Meta format |
| [Meta interview with AI-enabled round](https://leetcode.com/discuss/post/7374944) | November 25, 2025 is within one year but outside the preferred sample; no underlying event recency established here |
| [Stripe backend interview](https://leetcode.com/discuss/post/8372404/) | Useful-looking account, but publication/event date was not exposed in accessible text; no current Stripe claim is based on it |
| [Google L4 August lead](https://www.reddit.com/r/leetcode/comments/1vwzbg9/google_l4_interview_experience/) | Indexed date and rendered relative age disagree; excluded from dated trend conclusions |
| Generic “2026” lists and old reports in related-post panels | Title/crawl date does not establish a recent interview |
| Meta official preparation page | Could not retrieve the page in this research pass; no contents inferred |

**Coverage gaps:** no adequately verified recent junior-specific or named-company staff-loop sample; limited geographic coverage; no reliable Meta/Stripe/Microsoft recent question-frequency data. The junior and staff routes therefore use clearly marked practice standards and current official/general evidence, not invented company intelligence. This snapshot is useful but does not satisfy a statistical “what is most asked across top companies” claim.

## Refresh procedure

Before relying on this for a new application, check the recruiter packet. When updating the research, retain the old snapshot and record: source URL, publication date, interview date, company/team/location, level as stated, round type, narrow observation, and confidence. Exclude out-of-window evidence from recent conclusions. Cross-check a pattern across independent accounts before calling it recurring; never fabricate a percentage without a sampling method and denominator.

[Interview home](../../practice/interview-guide.md) · [Practice](../../practice/README.md)

## Trace older research claims before using them

The original research notes are now connected to [a claim-level ledger](claim-ledger.md) that distinguishes exact source, primary/secondary status, publication/event/access date, sample/role and curriculum inference. Unsupported statistics and consensus claims are explicitly withdrawn. This does not add named-company interviews to the sample above. Technical documentation and production reports cannot fill a missing recent lead-loop sample.

Run `python docs/research/check_claims.py` for local links and ledger structure; it does not verify source quality or event dates. Before using a company-specific assertion, read the exact source and ask which detail actually changes practice. A newly published repost of an older interview belongs to the older event; an undated live official guide has publication age unknown.
