# Practice reproducible builds, runtime configuration and rollback

[Chapter](README.md)

A small bookmark API is useful only while somebody remembers how to run it. These exercises make its source revision, built artifact, configuration, persistent data, and recovery procedure explicit. Use the supplied local app first. A container image or cloud deployment is an extension you create.

## Choose your starting code

[Run the reading-list starter](../../../examples/reading-list-starter/README.md) and read [artifact and configuration boundaries](configuration-and-environments.md). For actual supplied infrastructure, the [queue lab](aws/labs/job-pipeline/README.md) includes its own SAM template and commands.

![Build one artifact and supply each environment’s configuration separately](../../../assets/diagrams/build-once-promote.svg)

<a id="1-the-clean-machine"></a>

## 1. Run from a fresh checkout without private setup

A teammate has the repository but none of your shell history, environment variables, or previously created database files.

**Your task.** Write the minimum supported runtime versions, setup command, run command, and expected response. Follow them from a fresh directory with an explicit disposable data path. Record each missing instruction you discover.

**What to observe.** A known request works, a restart preserves its row, and the instructions say how to stop the process and remove only the disposable data.

**Changed requirement.** A new dependency needs a native library. Document the build environment instead of assuming a lockfile installs the operating system too.

[Worked mechanism and implementation context](../../../examples/reading-list-starter/README.md)

<a id="2-the-artefact-you-build-once"></a>

## 2. Promote the same artifact and report its identity

A staging build succeeds, but production rebuilds later with different build inputs. The two environments may not run identical bytes.

**Your task.** Create a built artifact with recorded source revision and digest. Run that artifact in two environments with different non-secret configuration. Add a version response that reports the build identity without exposing credentials.

**What to observe.** Both environments report the same artifact identity. A source commit label alone is not substituted for a digest of the built bytes.

**Changed requirement.** The frontend embeds its API address at build time. Decide whether runtime configuration is needed or whether each build is intentionally a distinct artifact requiring its own evidence.

[Worked mechanism and implementation context](configuration-and-environments.md)

<a id="3-the-five-minute-rotation"></a>

## 3. Rotate a secret through the real reload path

The service reads a database credential at startup. Updating a secret store does not necessarily update the value already in memory.

**Your task.** Move real credential values outside source and artifact layers. Document acquisition, refresh, revocation, and recovery. Rotate a disposable credential, observe interruption, and confirm that old access ends.

**What to observe.** The record names elapsed time and affected operations. It distinguishes a source change from a configured restart, and contains no secret values.

**Changed requirement.** Old and new credentials must overlap for a short migration window. Define the final cutoff and how you discover a process that never refreshed.

[Worked mechanism and implementation context](../../02-applications/05-security/trust-and-authorization.md)

<a id="4-what-you-actually-install"></a>

## 4. Account for direct, transitive and install-time dependencies

One dependency declaration can resolve many packages and execute build scripts. Counting only direct imports misses part of the application’s supply chain.

**Your task.** Inspect the resolved dependency graph and install behavior. State why each direct package is needed and what its removal would have to preserve. Compare strict installation and an explicit script policy in an isolated build. Retaining a package is a valid result.

**What to observe.** A report connects the artifact to exact dependency inputs and permitted install behavior. No exercise requires replacing a mature parser or security library with a short imitation.

**Changed requirement.** A package update changes a transitive dependency without touching application imports. Identify the changed bytes and contract evidence before promotion.

[Worked mechanism and implementation context](../../02-applications/05-security/projects.md)

<a id="5-the-rollback-you-have-actually-done"></a>

## 5. Roll back the artifact and inspect what remains

Version B changes visible behavior and writes a new optional field. Restoring version A changes code, while B’s persisted records remain.

**Your task.** Deploy a visible change in a disposable environment, restore the earlier digest, and query the running revision and a known record. Time recovery and list every persistent or external effect that rollback did not undo.

**What to observe.** The old artifact serves successfully against the current schema, or the incompatibility is explicitly demonstrated and repaired.

**Changed requirement.** The new version sent an email or removed data. Define a compensating or restore action separately from artifact rollback.

[Worked mechanism and implementation context](../02-delivery/delivery-pipeline.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
