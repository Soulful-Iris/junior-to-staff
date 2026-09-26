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
| `drawer.js` | Haiku draws: the request, the reader's key, what comes back made safe, and where it goes on the board |
| `layout.js` | lays a drawing out the way AWS diagrams are drawn: flow left to right, zones as lanes, public above private |
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

## Haiku draws

Under each canvas: *"Tell Haiku what to draw, or what to change."* The reader
describes a design in their own words; `claude-haiku-4-5` turns it into a graph
with one forced call to a strict `draw` tool; `layout.js` places it. Edits work
the same way ("oh no, I meant a cache, not a database") because the current
diagram and the reader's earlier asks go with each request.

- **It never sees the exercise.** The request is built from the catalog, the
  board's rules, the diagram and the reader's words, and nothing else is passed
  in. If Haiku knew the question it would quietly fix the design and the checks
  would grade Haiku. Tested on six-word windows of every exercise string, in
  node and on the real page.
- **It draws what the reader said, mistakes included.** The checks are what say
  a queue cannot write to a database.
- **It never answers in words.** Forced tool use means the API itself allows no
  text; any text block is ignored anyway, and nothing from the model but the
  drawing reaches the page. A model that refuses forced tool use (Opus 5.5,
  Fable 5.1) is asked once more with `auto`: the model id is one constant.
- **The key is the reader's own Anthropic API key**, pasted once, kept in
  `sessionStorage` (or `localStorage` if they ask to be remembered), sent only to
  `api.anthropic.com` with `anthropic-dangerous-direct-browser-access`. A
  claude.ai session token, a subscription (OAuth) token and an admin key are
  refused by name: a site may not use anyone's claude.ai login, and those open
  a whole account. The page's Content-Security-Policy (`board_csp` in
  `site/reader.py`) lets only this site's scripts and two hashed inline ones run,
  and lets scripts talk only to this site and Anthropic.
- **Where things go is the code's, never the model's.** A redraw re-lays out
  the whole drawing, except when the reader has arranged it by hand and the
  change is only kinds, names or arrows: then everything stays where they put it.
  A drawing too big for 860 x 540 zooms the board out (same shape, up to 1.6x)
  rather than squeezing parts onto each other. One undo step per drawing.
- Haiku adds an AWS Cloud box whatever it is told; unless the board had one or
  the reader asked, it is unwrapped.

## Testing it

```bash
node --test site/designboard/test/*.test.mjs        # every check both ways; the drawer and the layout
CHROME_PATH=... node site/tools/designboard-check.mjs   # every gesture, in a real browser, on site/out
DESIGNBOARD_HAIKU_KEY=sk-ant-... node site/tools/designboard-check.mjs   # plus one drawing and one edit by the real model
```

The layout is tested on eleven real answers from Haiku (`test/haiku-drawings.json`):
every part lands in the box it was drawn in, nothing overlaps, no arrow runs
through a part, and it fits the canvas. The browser checks answer for Anthropic
with those same drawings, so they never spend anything; an unrouted call is
aborted.

The unit tests end with a gate that fails unless every check was seen both
passing and failing: a check that only ever passes its reference answer proves
nothing. The browser checks drive real pointer and key events at the places
things are drawn; each was also run against a deliberately broken board (no
arrows, no rename, break-it doing nothing, never saving, hover not redrawn)
and went red.
