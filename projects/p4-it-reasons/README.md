# P4 · it reasons, provably

> Senior tier · fed by section 15 · the question is **can you add a model to it and prove it is any good?**

Same reading list. Add one small feature that uses a model, and then spend most
of the project proving whether it works.

The feature is deliberately modest: when somebody saves a link, suggest tags for
it from the page's content. That is it. If you find yourself building a chat
interface, you have swapped this project for a different one, and the different
one teaches less.

**The feature is perhaps a fifth of the work. The other four fifths are the
evaluation, and that ratio is the lesson.**

## What done means

- [ ] Tag suggestions appear, and a person can accept, edit or ignore them.
- [ ] You read **thirty real outputs by hand** and grouped the failures into a taxonomy you wrote yourself.
- [ ] There is an eval set of at least twenty cases, each pass/fail against a stated rule.
- [ ] Some of those cases currently fail, and you know which and why.
- [ ] If you use a model as a judge, you measured how often it agrees with your own labels, and you can state that number.
- [ ] Cost is recorded per suggestion, and there is a hard cap in code that you have tested by hitting it.
- [ ] Time-to-first-token is measured from the browser, not from the API.
- [ ] Turning the model off leaves the product working, minus this feature.
- [ ] You wrote down why this is a model rather than a rule, honestly.
- [ ] There is a written trifecta analysis: what private data it sees, what untrusted content it reads, what it can send outward — and which leg you cut.

## The decisions you are being asked to make

1. **What exactly is the model deciding?** "Suggest tags" is a product sentence. The engineering version names the input, the allowed outputs, and what happens when it is unsure.
2. **Is the tag set open or closed?** A closed vocabulary makes evaluation tractable and the feature slightly worse. An open one is the reverse. Pick, and say what it costs.
3. **What does the untrusted content do to you?** The page you fetched is written by somebody else and your model is about to read it. That is the whole of prompt injection, in your own product, on purpose.
4. **What is a failure here?** A wrong tag, a missing obvious tag, a tag that leaks something from another user's item? They are different failures with different severities and your eval must tell them apart.
5. **What does the user see when it fails?** Silence, a guess, or an honest "could not suggest"? The third is usually right and is almost never what gets built.

## Working with Claude on it

**1. Error analysis before any metric.**

```
Here are 30 real outputs with their inputs.

Do not score them. Read them, and group the failures into categories you
derive from what you see. Report the count per category and two examples
of each.

Then tell me which single category, fixed, removes the most failures.
```

Why: a score is a number with nothing under it. A taxonomy derived from the data
is the shape of your actual problem, and the counts tell you where to spend.

**2. Build the eval so it can fail.**

```
Turn category <X> into a binary pass/fail eval with an explicit rule.

Then write three cases you expect to FAIL right now and show me them
failing. If everything passes, tell me the eval is too easy instead of
reporting success.
```

Why: an eval nobody has seen go red is not an instrument, it is decoration. This
is the same rule as the testing section, pointed at a model.

**3. The injection test on your own feature.**

```
Write a test page whose visible content includes text trying to redirect
the tagging model — for example instructing it to ignore its task.

Run it through the real pipeline and show me what the model produced.
Then tell me what in my architecture, not my prompt, would stop it.
```

Why: doing this to your own system, on purpose, once, is worth more than reading
about it. The second half forbids the answer "add a line to the prompt", which
is the answer everyone reaches for and the one that does not hold.

## How you would know it is wrong

1. **Replace the model with a stub that returns a fixed answer.** Anything in your eval that still passes was measuring nothing.
2. **Measure judge agreement on a labelled set.** Without that number, your judge's verdicts are unvalidated opinions produced at scale.
3. **Reorder the options in any pairwise comparison** and count how many verdicts flip. That is your noise floor.
4. **Check the cost on the worst case**, not the average — the longest page, the most tags, the retry — and confirm the cap actually stops it.
5. **Measure time-to-first-token from the browser.** The queue in front of the model is part of what the user feels.
6. **Feed it a page in another language, an empty page, and a page that is one image.** Three inputs, thirty seconds, and they will find more than an hour of thinking.
7. **Turn the model off** and use the product. What you experience is your degradation path whether or not you designed it.

## Break it on purpose

| do this | what should happen | what it teaches |
|---|---|---|
| make the model return malformed output | handled as a failure, not written to the database | anything that parses model output is parsing untrusted input |
| put instructions in the page content | the architecture limits the damage, not the prompt | prompt injection is a design problem |
| run the same input twice | you find out how non-deterministic your feature is | it is more than you think, and your eval must cope |
| let the cap fire mid-request | a clear, honest failure and no half-written state | a budget that corrupts data when it fires is worse than none |

## What P5 will do to this

P5 makes you replace something load-bearing in the system you now have, safely,
with a written design doc and a rollout plan — and the tagging feature is a
tempting thing to migrate, because it is the newest and the least certain.

Whatever you choose, P5 is where the guide stops being about building and starts
being about changing something other people depend on.
