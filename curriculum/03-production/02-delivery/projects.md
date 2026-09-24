# Practice compatible releases, deployment identity and recovery

[Chapter](README.md)

An application release changes running code while requests and background jobs continue. These exercises use a disposable application environment to separate artifact delivery, user exposure, persistent effects, and recovery. They do not require adding merge gates or tests to this guide’s publishing workflow.

## Choose your starting code

Read [the delivery lesson](delivery-pipeline.md). Use [the configuration case](cases/configuration-rollout.md) for a worked rollout and [the migration fixture](../../04-scale-and-evolution/04-migrations/labs/recovery-migration/migration.md) for mixed-version data.

![Deploying an artifact and exposing its behavior are separate decisions](../../../assets/diagrams/deploy-vs-release.svg)

<a id="1-the-green-that-proved-nothing"></a>

## 1. Observe whether a deployment actually serves the intended version

A command can exit successfully even when the new process never becomes ready.

**Your task.** Deploy a visible version change in the disposable environment. Query the running revision and the important user operation. Then use a startup-failure variant to observe whether old capacity remains and what the deployment reports.

**What to observe.** The report distinguishes “artifact uploaded”, “process started”, and “new version serving”. A successful shell status alone does not establish all three.

**Changed requirement.** Two independently compatible changes conflict when combined. Reproduce the combined behavior and decide which integration check fits this application’s workflow.

[Worked mechanism and implementation context](projects/twenty-deploys-a-day.md)

<a id="2-what-a-pull-request-can-reach"></a>

## 2. Map deployment permissions before changing them

A pull request can execute repository code during a build. The deployment job may separately hold authority to change production.

**Your task.** List each job’s code inputs, credential scope, and writable resources. Identify where untrusted code could inherit a privileged identity. Narrow that boundary and demonstrate an allowed action plus a refused action in a disposable environment.

**What to observe.** The recorded evidence includes permission metadata and request outcomes, never secret values. Short-lived credentials still have authority during their lifetime.

**Changed requirement.** A forked pull request needs a preview. Design an isolated preview identity with no production write path.

[Worked mechanism and implementation context](../03-infrastructure/configuration-and-environments.md)

<a id="3-the-rename-that-survives-a-rollback"></a>

## 3. Rename a field while old and new versions coexist

Old instances use `email`, while the new version reads `contact_email`. Both share persisted order data.

**Your task.** Expand the schema, deploy compatible readers and writers, backfill with a checkpoint, switch use, then retire the old field after its rollback window. Record the old-version behavior at each step.

**What to observe.** An old writer’s row remains readable by the new version. A rollback before retirement can read rows written by the new version.

**Changed requirement.** An offline client returns after the planned retirement date. Choose an explicit compatibility or rejection policy instead of assuming every consumer has upgraded.

[Worked mechanism and implementation context](../../04-scale-and-evolution/04-migrations/labs/recovery-migration/migration.md)

<a id="4-one-percent-then-everyone-then-the-funeral"></a>

## 4. Release a feature by cohort and define flag removal

A new title provider is deployed but should initially serve a small subset of requests. Cohort count alone does not reveal traffic exposure.

**Your task.** Choose a stable cohort rule and measure its actual traffic. Compare errors, latency, and completion behavior with the control path. Define a stop action, propagation delay, owner, and removal condition for the temporary flag.

**What to observe.** Turning the flag off changes new admissions. Already queued work and provider effects retain their own drain or repair policy.

**Changed requirement.** The first cohort has 30% of traffic despite being one of twenty groups. Recalculate exposure during detection and rollback.

[Worked mechanism and implementation context](cases/configuration-rollout.md)

<a id="5-destroy-it-and-get-it-back"></a>

## 5. Recreate an environment without confusing resources and data

Infrastructure code can recreate a database resource without restoring its former rows.

**Your task.** Inventory source, artifact, configuration, secret bindings, resource definitions, and backups. Recreate only a disposable environment. Record manual steps and verify the restored application with known data. Explain every unexpected infrastructure-plan difference.

**What to observe.** The application reports the intended version and returns the expected restored record. An empty infrastructure plan is not proof that the data or application behavior is correct.

**Changed requirement.** A retained bucket contains old object versions. Include retention and cleanup decisions rather than assuming deleting the stack removes every billed object.

[Worked mechanism and implementation context](../03-infrastructure/aws/labs/job-pipeline/README.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
