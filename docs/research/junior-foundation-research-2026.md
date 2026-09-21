Research pass for the guide: what the JUNIOR foundation actually is in 2026, for someone who directs an AI and judges what comes back.

The spine of it, once the seven areas were laid side by side: every area has quietly reorganized around READING code rather than writing it. DORA 2025 calls AI an amplifier and names a verification tax; METR's RCT found experienced devs 19% SLOWER with AI while believing they were 20% faster (the perception gap is the junior lesson, not the slowdown); SO 2025 survey: 84% use AI, trust figures conflict across framings (33% trust accuracy vs 46% distrust, verified 2026-09-21; a separate 29% figure circulates), top frustration 'almost right but not quite' at 66%. GitClear: duplication up ~8x, refactoring collapsing, error-masking constructs +47%. So the foundation = judgment infrastructure.

Surprises worth keeping:
- Accessibility is now LAW, not polish: EAA enforced since 2025-06-28, WCAG 2.2 AA is the benchmark, FTC fined an overlay vendor. No roadmap I have seen teaches it as a legal floor.
- Postgres 18 (Sept 2025) added uuidv7() — the platform itself absorbed a classic junior mistake (random UUID PKs wrecking index locality).
- Lockfiles became security infrastructure after Shai-Hulud (Sept 2025, worm; 2.0 in Nov). CISA advisory exists. But PackageGate (Jan 2026) undermined even the post-worm defenses — teach defense in depth, not a checklist.
- Tests inverted into the spec you hand the AI. AI-written tests-after assert what the code DOES, not what it SHOULD do; self-referential mock tests pass by construction. That is 'count the instruments' wearing a test runner.
- GitHub shipped native stacked PRs (public preview July 2026) + merge queues + Copilot review GA — the whole change workflow is reshaping around review capacity as the bottleneck.

Could not fully verify: GraphQL numbers conflict (340% Fortune-500 growth vs 'down from 40% peak') — the agreed shape is retreat to internal federated layers. Did not verify current Node LTS; guide should teach 'check the release schedule' as the skill anyway.
