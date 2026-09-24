# Practice incident decisions, recovery and completed corrective work

[Chapter](README.md)

A status API may recover before its background refresh queue drains. An incident therefore has several observable milestones: impact begins, someone detects it, an action reduces harm, and useful work becomes current again. These exercises use those milestones to turn an incident report into operational improvement.

## Choose your starting code

Use the supplied [incident CSV and logs](labs/reliability/incident.md) if you have no suitable incident record. They are synthetic, so you can practice without causing a live outage. For retry and SLO implementation, the focused projects are linked after these response exercises.

![Detection, mitigation and lasting repair are separate incident milestones](../../../assets/diagrams/incident-timeline.svg)

<a id="1-the-two-timestamps"></a>

## 1. Measure detection delay without guessing the start time

An alert arrives at 10:05, but the oldest evidence of user impact is 10:02. Earlier logs are missing.

**Your task.** Build a timestamped timeline with source references and clock assumptions. Separate the earliest observed impact from an unknown actual start. Propose one signal that would have detected the supported failure earlier.

**What to observe.** The report gives a three-minute observed interval and labels the missing earlier evidence. It does not present an uncertain time as exact.

**Changed requirement.** The alert fires on CPU while users fail for another reason. Choose a user-outcome signal and explain missing-data behavior.

[Worked mechanism and implementation context](labs/reliability/incident.md)

<a id="2-the-game-day-with-the-roles-split"></a>

## 2. Run a contained response exercise with clear responsibilities

During an incident, the investigator can lose time answering status questions while several people issue conflicting changes.

**Your task.** Choose a local failure scenario, assign decision, investigation, and communication responsibilities, and keep an action log. A solo rehearsal can simulate the roles in separate notes. Make one bounded intervention at a time and state its expected effect.

**What to observe.** The timeline identifies who chose each action and whether its predicted observation occurred. Stopping the drill is an available outcome when the effects differ from expectations.

**Changed requirement.** The recovery tool depends on the failed discovery service. Add an independently reachable recovery path and document who can use it.

[Worked mechanism and implementation context](risk-and-incidents.md)

<a id="3-the-postmortem-with-no-should-in-it"></a>

## 3. Explain contributing conditions and a concrete repair

A worker retry bug triggered overload, but an unbounded queue and missing completion signal prolonged it. Naming only the triggering bug misses the recovery problem.

**Your task.** Write a timeline, contributing mechanisms, and the decisions made with the evidence then available. Replace “be more careful” with a specific system or process change. Preserve accurate human actions without using blame as the explanation.

**What to observe.** The review connects each proposed repair to a demonstrated failure path. It does not forbid mentioning human decisions or require inventing multiple causes.

**Changed requirement.** A proposed repair reduces availability to enforce a stronger safety rule. Make that tradeoff explicit and get the product decision recorded.

[Worked mechanism and implementation context](cases/retry-amplification.md)

<a id="4-the-action-items-nobody-checked"></a>

## 4. Finish a corrective action and check its effect

Several incident actions are marked complete, but one only produced a document and another never reached the deployed service.

**Your task.** Review a small action list, identify owner and intended outcome, and inspect the actual change. Choose one valuable unfinished action and complete it in the fixture. Record the behavior observed afterward.

**What to observe.** A completed retry limit bounds attempts in the stated scope. A percentage of closed tickets is not by itself a measure of reliability improvement.

**Changed requirement.** The fix belongs to another team with a different deadline. Agree on an interim containment boundary and a specific owner for final adoption.

[Worked mechanism and implementation context](../../04-scale-and-evolution/05-technical-decisions/engineering-effectiveness.md)

<a id="5-the-error-budget-policy-that-binds"></a>

## 5. Apply an error-budget policy to a concrete decision

At a 99.9% request objective, one million eligible operations allow 1,000 bad events. The team needs an agreed action when the allowance is consumed.

**Your task.** Write policy thresholds, action owners, allowed exceptions, and the evidence needed to resume normal delivery. Apply the policy to synthetic counts. A release pause is one possible response, not a universal requirement.

**What to observe.** The decision uses good and eligible counts, preserves request units, and records who owns the exception if one is made.

**Changed requirement.** Traffic is highly uneven. Recalculate from event counts rather than converting every outage minute into the same fraction of the budget.

[Worked mechanism and implementation context](projects/01-the-slo-you-would-actually-honour.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.

## Build the reliability mechanisms

- [Define and calculate a user-facing save SLO](projects/01-the-slo-you-would-actually-honour.md)
- [Implement burn-rate alert and incident state rules](projects/02-the-alert-that-fires-when-it-matters-and-not-before.md)
- [Bound retries across browser, API and SDK layers](projects/03-the-retry-storm-you-build-on-purpose.md)
- [Prioritize API work within a fixed capacity budget](projects/04-shedding-the-right-thing.md)
- [Recover a service trapped in expired work and retries](projects/05-the-failure-that-will-not-recover.md)
