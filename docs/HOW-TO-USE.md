# How to use the AI-assisted path

For both learning paths, begin at [Choose your path](../paths/README.md).
This page describes Path A. The [interview path](../paths/interviews/README.md)
has its own reading order and independent exercises.

The short version is on the front page. This is the longer one, for when you
want to know why it is shaped like this.

## The one rule

**Build the slice. Run the checks.**

Reading a section and agreeing with it produces almost nothing. Every section
ends with a piece of the running project and a list of checks that can go red.
Those two are the section; the prose in front of them is preparation.

If you only ever do one thing from this guide, do the "how you would know it is
wrong" list, on real code, and watch at least one of them fail.

## The order

**The projects are ordered. The sections inside a tier are not, strictly.**

P1 through P5 are the same system under increasing pressure, so doing them out
of order does not work — P3 assumes the delivery pipeline you built in P2, and
P5 assumes there is something worth migrating.

Within a tier, read in whatever order the work demands. If you are about to add
a queue, read 13 first. The numbering is a reading order, not a lock.

Two exceptions:

- **02 · Working with an AI that writes the code** comes before everything,
  because it is the method the rest of the guide assumes.
- **16 · Scope and leverage** comes before the rest of the staff tier, because
  the other five sections are things a staff engineer does and that one is what
  the job actually is.

## What "done" means

Every section and every project states its acceptance criteria before the work.
That is deliberate: deciding what done looks like *after* you have built
something is how you end up grading your own homework.

A criterion is only worth having if you could fail it. "The code is clean" is
not a criterion. "A fresh clone runs with one command on a machine that has
never seen this project" is.

## How to work with Claude on this

You are expected to. The guide is written for someone who directs rather than
types, and the sections tell you what to ask.

Three habits are worth having from the start:

**Work in slices that end somewhere runnable.** A slice you can run is a slice
you can check. Asking for a whole feature at once leaves you with something you
must accept or debug whole.

**Ask for the failure modes before the solution.** "List the three decisions in
this design most likely to be wrong" gets you the model's own uncertainty, which
is the one thing you cannot read off the output.

**Keep the definition of done.** Do not ask what the acceptance criteria should
be. That is the part that was yours.

And the habit the whole guide is organised around: before you accept anything,
be able to say what would make it wrong. If you cannot, you have not finished,
whatever the screen shows.

## On rereading

Two things from the learning research are well supported and worth actually
doing, rather than nodding at:

**Retrieval beats rereading.** Closing the page and writing down what a section
said, badly, from memory, does more than reading it twice. The effect is
consistently measured and it is large.

**Spacing beats cramming.** Coming back to a section a week later, once, is
worth more than reading it three times tonight.

So: after you finish a project, go back to the sections it used and write the
"how you would know it is wrong" list from memory before looking. What you have
forgotten is the part you did not really learn.

*(Some popular learning advice is not supported — matching "learning styles" to
learners does not hold up, and the pyramid of retention percentages that
circulates in slide decks was fabricated. Ignore both.)*

## What the AI-assisted path will not do

- **It will not teach you a language or a framework.** Those are well covered
  elsewhere, they change, and knowing one is not the thing that was missing.
- **It will not give you interview answers.** System design here is the thinking
  process, not the ritual.
- **It will not make you a staff engineer.** The staff tier describes a job and
  gives you the artefacts to practise. The rest is organisational and takes
  years, and any guide that claims otherwise is selling something.
- **It will not stay right forever.** Anything with a date on it was checked on
  that date. Where something could not be verified, it says so.

## If you find something wrong

Open an issue. Specifically:

- a claim that is out of date — say what you checked and when
- a check that cannot actually go red
- a section where the acceptance criteria are not checkable
- a diagram that restates its paragraph instead of adding to it

Those four are the failure modes this guide is written against. Finding one is
useful, not rude.
