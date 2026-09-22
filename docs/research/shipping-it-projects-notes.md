# Working notes — 07 · Shipping it, five projects

2026-09-22. Verifications done this session, for `tiers/01-junior/07-shipping-it/projects.md`.

## Verified today (2026-09-22)

**AWS App Runner is in maintenance mode.** AWS announced 2026-03-31 that App
Runner stops accepting new customers on **2026-04-30**. Existing services keep
running; no new features; no announced shutdown date. AWS's recommended path is
**Amazon ECS Express Mode** (announced 2025-11-21 at re:Invent): give it an
image + two roles, it builds Fargate service, ALB with HTTPS, autoscaling,
CloudWatch alarms, and a `*.ecs.<region>.on.aws` URL. No charge for Express Mode
itself; you pay for Fargate/ALB/logs underneath. Sources: aws.amazon.com
whats-new 2025/11 announcing-amazon-ecs-express-mode; apprunner docs release
notes; multiple 2026 write-ups (encore.dev, bex.co 2026-07-08). This changes
the guide's "which service runs my container" answer — write it as the 2026
answer, and use it as a lesson about veneers vs primitives.

**Amazon ECS native blue/green.** Announced **2025-07-17** (aws whats-new
"Amazon ECS enables built-in blue/green deployments"). Works with ALB, NLB,
Service Connect; no CodeDeploy required; keeps the old task set warm through a
bake window so rollback is near-instant; deployment lifecycle hooks; pairs with
CloudWatch alarms and the deployment circuit breaker for automatic rollback.
October 2025 added canary and linear strategies (parity with CodeDeploy). No
extra charge beyond transient double compute.

**CodeDeploy pricing** (AWS FAQ, via search 2026-09-22): no additional charge
for deployments to EC2, Lambda, ECS; **$0.02 per on-premises instance update**.

**Secrets Manager pricing** (aws.amazon.com/secrets-manager/pricing,
2026-09-22): **$0.40 per secret per month**, **$0.05 per 10,000 API calls**.
New-customer free tier is now the credits model (up to $200, 6 months to earn,
12 months to use).

**SSM Parameter Store pricing** (aws.amazon.com/systems-manager/pricing,
2026-09-22): standard parameters **no additional charge**, no API charge at
standard throughput. Advanced parameters $0.05/parameter/month; higher
throughput $0.05 per 10,000 interactions.

**ECR pricing** (aws.amazon.com/ecr/pricing, 2026-09-22): private storage
**$0.10 per GB-month**; free tier 500 MB/month private for one year (new
accounts); 50 GB/month public always-free.

**GitHub OIDC → AWS** (docs.github.com, 2026-09-22): provider
`https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`,
action `aws-actions/configure-aws-credentials` exchanges the JWT for short-lived
credentials; trust policy conditions on the subject claim pin it to a repo.

**npm query selector for install-time scripts** (docs.npmjs.com/cli/v11,
2026-09-22): documented example uses `:attr(scripts, [postinstall])`. Same
shape works for `[preinstall]` / `[install]`.

**AWS CloudShell** (aws.amazon.com/cloudshell/pricing + docs, 2026-09-22): no
additional charge; 1 GB persistent storage per region ($HOME only); Docker
Engine supported (added Jan 2024, InfoQ) but the 1 GB ceiling means small
images only; 1 vCPU / 2 GB RAM; git, npm, pip preinstalled on AL2023.

## Not re-verified, stated from stable knowledge (kept soft in prose)

- Build args and files written during build persist in image layers; deleting a
  file in a later layer hides it from the filesystem, not from the image
  (`docker history`, layer tarballs). BuildKit `RUN --mount=type=secret` is the
  escape hatch. Long-stable Docker behaviour.
- OCI conventional label `org.opencontainers.image.revision` for the source
  commit (OCI image-spec annotations).
- ECS task definition `secrets` / `valueFrom` accepts both Secrets Manager and
  Parameter Store ARNs, injected as env vars at container start.
- `npm ci` installs strictly from the lockfile and fails on mismatch;
  `--ignore-scripts` skips lifecycle scripts; `npm rebuild <pkg>` runs build
  scripts for just that package (the allowlist pattern).
- GitHub Actions masks registered secrets in logs; masking is best-effort and
  misses transformed values.

## Shape decisions

- Section README (checked 2026-09-21 by the section author) already tells the
  Shai-Hulud story with counts. Projects file refers to it, never restates
  counts.
- Rollback project teaches by digest, not tag; names ECS native blue/green as
  the 2026 default and CodeDeploy as the EC2/Lambda answer.
- Project 2 carries the App Runner story explicitly with dates — it is the
  best available example of "pick primitives, expose the commit, and assume the
  easy layer can be taken away."
- Diagram: `assets/diagrams/secret-blast-radius.svg` — one secret fanning out
  to repo history, image layers, CI log, laptops, runtime error output;
  animated dots as copies travelling; caption lands on rotation as the only
  move that covers every copy.
