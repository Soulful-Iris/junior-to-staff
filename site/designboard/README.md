# The design board

Draw an architecture with AWS's own parts, check it, then break it. It mounts
under each sketch on `curriculum/03-production/01-system-design/whiteboard.md`,
on a desktop; a phone keeps the page's reference sketches.

## How it hangs together

| file | what it is |
|---|---|
| `catalog.json` | every part and box: AWS's name, the short name printed under the icon, the **kind** the checks read, and where it runs (**placement**) |
| `icons/` | AWS Architecture Icons, unmodified, copied by `tools/curate_icons.py` (see `icons/CREDIT.md`) |
| `model.js` | the board's state is the graph; containment (zone, subnet, VPC) is computed from where a part is drawn, never stored |
| `rules.js` | which arrows AWS can actually make |
| `checks.js` | the checks: questions a reviewer would ask, answered in sentences that name the reader's own parts |
| `sim.js` | break it: what a member can still do when parts, zones or an outside service fail |
| `board.js`, `board.css`, `ui-icons.js` | the editor |
| `../../curriculum/.../whiteboard.board.json` | the four exercises: brief, which checks, what break-it measures, tips. Content lives with content |

Built by `site/tools/build-designboard.mjs` (one hashed file, icons included) and
mounted by `mount_designboard` in `site/reader.py`.

## The rules the board states, and the checks rely on

- **A → B means A sends a request or a message to B.** The answer rides back
  on the same arrow, so a reply is never its own arrow.
- **A part runs in the zone and subnet whose box holds its icon's centre.**
- Instances and containers (EC2, ECS, EKS) run in one zone. Managed services
  (Lambda, SQS, SNS, DynamoDB, S3, API Gateway, a load balancer) are regional
  and survive a zone. RDS, Aurora and ElastiCache are zonal until **Multi-AZ**
  is switched on for that part.
- A request waits for what it reaches, but not for what sits behind a queue.
- In break it, a part of yours that fails is gone; an outside service that
  fails **hangs**, and whatever calls it without a timeout hangs with it.

## Testing it

```bash
node --test site/designboard/test/*.test.mjs        # every check both ways
CHROME_PATH=... node site/tools/designboard-check.mjs   # every gesture, in a real browser, on site/out
```

The unit tests end with a gate that fails unless every check was seen both
passing and failing: a check that only ever passes its reference answer proves
nothing. The browser checks drive real pointer and key events at the places
things are drawn; each was also run against a deliberately broken board (no
arrows, no rename, break-it doing nothing, never saving, hover not redrawn)
and went red.
