# Teaching standard

Every substantive lesson needs a problem, a concept explanation, a visual, a worked example, an implementation exercise, failure cases, and a retrieval question. Do not replace teaching with a reading list.

## Visual standard

Use a comparison for “with versus without,” a sequence for event order, and a topology for ownership or dependencies. Label assumptions and the boundary of each guarantee. Show changing state and its cause. Animated highlights are teaching timelines, not performance benchmarks.

Keep all labels readable at normal GitHub width. Include descriptive alt text, a static alternative, and reduced-motion behavior. Use editable SVG and Mermaid; no external animation host is required. Every animation must have a prose explanation of its critical transition and a prediction question. The generator lives in [scripts](../../scripts/).

Follow the original `assets/diagrams` examples: geometry carries the explanation, short labels identify state, and motion represents a request, a boundary, or a resource changing. Do not use identical text boxes as a substitute for a mechanism. Keep entry pages short and ordered; move optional detail behind a link or disclosure. Verify actual playback after publishing, in addition to static layout checks.

Static architecture boxes are also a core learning skill. Show databases, caches, load balancers, services, queues, and trust boundaries when they explain the design. Label arrows. Ask the learner to redraw the system, remove a component, and predict the failure. Use ER diagrams for relationships, timelines for latency, and sequence diagrams for races. Preserve the original illustrations; additions should fill a new teaching need.

## Solution standard

State inputs, outputs, malformed-input policy, invariant, baseline, improved approach, time, auxiliary space, and where the improvement stops working. Use Python for algorithms and TypeScript for browser/async work. Avoid translating every example twice merely to double its length.

Ask before revealing a solution. Separate reference code from practice prompts. Follow a worked example with a changed requirement that cannot be solved by copying it. Include tests for the boundary cases the prose discusses.

## Evidence standard

Company-frequency statements need dated, independent reports and a defined denominator. Official pages accessed today are current guidance, not proof of a recent interview event. AWS documentation verifies technical behavior, not interview popularity. Never invent a pass threshold or describe a candidate's claimed solution as technically correct without checking it.

## Completeness standard

No empty chapter promises. State the implemented scope and remaining limits in [VALIDATION](VALIDATION.md). Add depth when a topic cannot be explained from this repository alone; external links supplement the explanation.
