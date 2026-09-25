# CrowdStrike · Go refresher, algorithm bank, and design study

Companion to the [CrowdStrike rehearsal](crowdstrike.md). Three parts: enough Go to read it, discuss it, and answer the concurrency questions their loops ask even when you code in Python; the algorithms that show up in their coding rounds and in their production systems; and the system-design material to study for the design review and for the first months on a cloud platform team. Everything here is labeled `[Generated]` unless it cites the company's engineering blog `[Official]` or a report `[Reported]`; the labels follow the [ledger](crowdstrike.md#every-problem-found-labeled-the-ledger) on the main page.

**Who this is for.** A senior backend engineer whose daily languages are Python and TypeScript, who last wrote Go years ago, and who will code in Python in the loop. The posting lists "Go, Python, or Java"; the company's own backend is heavily Go (Kafka consumers, Threat Graph handlers, the DSL that generates Go). Nobody will make you write Go on the spot if you chose Python, but the follow-up questions assume you can think in it: "what mechanism for a worker pool," "how would you assign work to workers," "goroutines versus OS threads" are all `[Reported]`.

## Part 1 · Go in an afternoon, for someone who will interview in Python

### What Go is, in five sentences you can say out loud

Go is a compiled, statically typed language with garbage collection, designed for services: fast startup, one binary, small memory footprint. Concurrency is built into the language: goroutines are cheap green threads scheduled by the runtime onto OS threads, and channels are typed queues you use to hand work between them. There are no exceptions; functions return errors as values and you check them. There is no inheritance; types satisfy interfaces implicitly by having the right methods. The standard library covers HTTP, JSON, testing, and profiling, so services carry few dependencies.

### Python to Go, the mapping you need to read code

| Python | Go | Note |
| --- | --- | --- |
| `x = 5` | `x := 5` | `:=` declares and infers; `var x int = 5` is the long form |
| `def f(a, b): return a+b` | `func f(a, b int) int { return a + b }` | Types after names; multiple returns are normal: `func f() (int, error)` |
| `list` | slice `[]int` | A slice is a view on an array: `append` may reallocate; two slices can share memory |
| `dict` | `map[string]int` | Writing to a nil map panics; iteration order is random on purpose |
| class with methods | `type Job struct{...}` + `func (j *Job) Run()` | Methods attach to types; pointer receiver mutates, value receiver copies |
| duck typing | `interface` | `type Scanner interface { Scan([]byte) (Verdict, error) }`; any type with that method satisfies it, no declaration |
| `try/except` | `v, err := f(); if err != nil { return fmt.Errorf("scan %s: %w", id, err) }` | `%w` wraps; `errors.Is` / `errors.As` inspect the chain |
| `with` / `finally` | `defer f.Close()` | Runs when the function returns, LIFO |
| `None` | `nil` | Valid for pointers, slices, maps, channels, interfaces, funcs |
| `Any` | `any` (alias of `interface{}`) | Type switch: `switch v := x.(type) { case int: ... }` |
| `threading.Thread(target=f).start()` | `go f()` | Starts a goroutine; the caller does not wait |
| `queue.Queue(maxsize=n)` | `make(chan Job, n)` | Buffered channel; `make(chan Job)` is unbuffered (a handoff) |
| `threading.Lock()` | `var mu sync.Mutex; mu.Lock(); defer mu.Unlock()` | `sync.RWMutex` for many readers |
| `concurrent.futures` / `asyncio.gather` | `sync.WaitGroup` or `errgroup.Group` | Wait for a set of goroutines; errgroup cancels the rest on first error |
| `asyncio.wait_for(coro, timeout)` | `ctx, cancel := context.WithTimeout(ctx, 2*time.Second)` | Context is the first parameter of anything that can block |
| generics `TypeVar` | `func Map[T any, U any](xs []T, f func(T) U) []U` | Since Go 1.18 |
| `pytest` | `go test ./...` with `func TestX(t *testing.T)` | Table-driven tests are the idiom; `go test -race` detects races |
| `print(f"{x=}")` | `fmt.Printf("%v %+v %T", x, s, x)` | `%+v` prints struct field names |

### Reading Go syntax you will see in a code review round

- `go func() { ... }()` — start an anonymous goroutine immediately.
- `ch <- v` sends, `v := <-ch` receives, `v, ok := <-ch` tells you if the channel is closed, `close(ch)` closes it, `for v := range ch` receives until closed.
- `chan<- T` is send-only, `<-chan T` is receive-only; functions take these to document direction.
- `select { case v := <-a: ... case b <- x: ... case <-ctx.Done(): return ctx.Err() case <-time.After(d): ... default: ... }` — wait on several channel operations; `default` makes it non-blocking.
- `struct{}{}` — a zero-size value; `chan struct{}` is a signal channel; `map[string]struct{}` is a set.
- `*T` pointer type, `&x` address, `*p` dereference; `p.Field` works on pointers too.
- `_` discards a value; unused variables and imports are compile errors.
- `iota` in a `const` block enumerates; `type Level int` with `const ( Low Level = iota; Medium; High )`.

### Concurrency, the part they actually ask about

**Goroutines versus OS threads** `[Reported]`. A goroutine starts with a ~2–8 KB stack that grows as needed; an OS thread has a fixed stack around 1–8 MB and a kernel context switch. The Go runtime multiplexes many goroutines onto a small pool of OS threads (M:N scheduling, work-stealing), so a service can hold hundreds of thousands of goroutines, one per connection or per in-flight message. Blocking system calls hand the thread back; channel waits park the goroutine without a thread. Say: "goroutines make it cheap to give every message its own worker; the cost that remains is coordination and memory, so I still bound them."

**Channels versus mutexes.** Channels move ownership of data between goroutines (a job queue, a result stream, a stop signal). Mutexes protect shared state that several goroutines read and write in place (a counter map, a cache). The Go proverb is "share memory by communicating," but the honest senior answer is "use a mutex for shared state, a channel for handoff, and never both for the same data."

**The worker pool** `[Reported follow-up]`. This is the pattern behind "what mechanism for a worker pool, how would you assign work to workers." Write it once in Go and once in Python until you can explain every line.

```go
func process(ctx context.Context, jobs <-chan Job, workers int) error {
	g, ctx := errgroup.WithContext(ctx)
	results := make(chan Result, workers)
	for i := 0; i < workers; i++ {
		g.Go(func() error {
			for {
				select {
				case <-ctx.Done():
					return ctx.Err()
				case j, ok := <-jobs:
					if !ok {
						return nil // producer closed the channel: drain finished
					}
					r, err := j.Run(ctx)
					if err != nil {
						return fmt.Errorf("job %s: %w", j.ID, err) // errgroup cancels ctx for everyone
					}
					results <- r
				}
			}
		})
	}
	go func() { g.Wait(); close(results) }()
	for r := range results {
		store(r)
	}
	return g.Wait()
}
```

Python equivalent to say alongside it: a `queue.Queue(maxsize=n)` fed by a producer, `n` threads from `ThreadPoolExecutor` pulling from it, a sentinel or `queue.join()` for shutdown, and an `Event` for cancellation; or `asyncio.Queue` with `asyncio.gather` of `n` consumer tasks for I/O-bound work.

**How to assign work to workers** `[Reported follow-up]`, the answers in order of sophistication:
1. Round-robin or "whoever is free" via one shared channel: simplest, best throughput, no ordering guarantee. CrowdStrike's published Kafka consumer does exactly this `[Official]`.
2. Hash the key (tenant, host, file hash) to a worker: preserves per-key order and gives cache locality; risk is a hot key pinning one worker. Mitigate with a bounded per-worker queue and a hot-key detector.
3. Work stealing or size-aware assignment when jobs vary wildly in cost.
Then the follow-up you should volunteer: **bound the queue** so a slow consumer applies backpressure to the producer instead of growing memory; **commit progress only after the batch completes** so a crash replays rather than loses; **make the work idempotent** so replay is safe.

**Stopping cleanly.** Producer closes the jobs channel → workers drain and return → `WaitGroup`/errgroup waits → results channel closed. For cancellation, pass a `context` and `select` on `ctx.Done()` in every loop. Never leave a goroutine blocked on a channel nobody will read: that is a goroutine leak, and it is the first thing a Go reviewer looks for.

**Other primitives to name.** `sync.Once` (init once), `sync.RWMutex`, `atomic.AddInt64` for counters, buffered channel as a semaphore (`sem <- struct{}{}` / `<-sem`) to cap concurrency, `time.Ticker` for periodic work, `context.WithCancel` for fan-out trees.

**Panics.** A panic in any goroutine that is not recovered crashes the whole process. Long-lived workers wrap the job call with `defer func() { if r := recover(); r != nil { ... } }()` and count it as a failed job. This is the "one malformed event must not stop the consumer" lesson from their Kafka post `[Official]`.

**Gotchas a reviewer will plant in code.** Loop variable captured by goroutines (fixed in Go 1.22, still common in older code); writing to a nil map; closing a channel twice; sending on an unbuffered channel with no receiver (deadlock, "all goroutines are asleep"); appending to a slice another goroutine reads; ignoring the returned `error`; `defer` inside a loop (runs at function end, not iteration end); `time.After` in a hot loop leaking timers; comparing with `==` on slices (compile error) or on structs containing them.

### The rest of the language in one pass

- **Packages and modules.** One directory is one package; `go.mod` pins dependencies; `internal/` packages cannot be imported from outside the module. Exported names start with a capital letter.
- **Errors.** Sentinel errors (`var ErrNotFound = errors.New("not found")`), typed errors (`type ScanError struct{...}` with an `Error()` method), wrapping with `%w`, checking with `errors.Is(err, ErrNotFound)` and `errors.As(err, &scanErr)`. Libraries return errors; only `main` decides to exit.
- **Structs and JSON.** A struct field carries a tag in backticks, such as json:"host", that tells the encoder the wire name; `json.Unmarshal(b, &e)` fills the struct; unknown fields are ignored by default.
- **HTTP services.** `net/http` handlers are `func(w http.ResponseWriter, r *http.Request)`; middleware is a function that wraps a handler; the posting names Gin as a framework option.
- **Testing.** Table-driven: a slice of cases with name, input, want; `t.Run(name, func(t *testing.T){...})`; `go test -race -cover ./...`; benchmarks with `func BenchmarkX(b *testing.B)`.
- **Performance.** `pprof` for CPU and heap; the GC is concurrent with sub-millisecond pauses; avoid allocations in hot loops (reuse buffers, `sync.Pool`), avoid boxing into `any`. CrowdStrike moved logging to zerolog for exactly this reason `[Official]`.
- **Generics.** `[T comparable]`, `[T constraints.Ordered]`; use for containers and helpers, not everywhere.

### Two hours of practice that makes this stick

1. Install Go, run `go run` on a file that starts 3 goroutines, sends 10 jobs down a buffered channel, waits with a WaitGroup, and prints results. Then break it: forget to close the channel and watch the deadlock message.
2. Add `context.WithTimeout` and make one job sleep past the deadline; confirm the others stop.
3. Run `go test -race` on a version with an unlocked shared counter; read the race report.
4. Read CrowdStrike's [Kafka consumer post](https://www.crowdstrike.com/en-us/blog/improving-fault-tolerance-in-apache-kafka-best-practices/) `[Official]` and rewrite its retry tiers (runtime retries, redrive topic, dead-letter) as a diagram in your own words.

## Part 2 · Algorithms and patterns, for the loop and for the job

The coding rounds are medium, framed as logs, hosts, events, and files, and often extended to streaming or concurrency `[Reported]`. The job is a trillion events a day through Kafka into LSM stores `[Official]`. The same handful of patterns serves both. Interview column: how it is asked. Job column: where it lives in their stack.

| Pattern | Interview shape | Where it runs at CrowdStrike | Python tools |
| --- | --- | --- | --- |
| Hash-map aggregation | Busiest host, count errors per service per minute, group by key | Every consumer that rolls up telemetry; per-tenant counters | `collections.Counter`, `defaultdict` |
| Top-k with a heap | K busiest hosts from a stream; k largest | Alerting on the noisiest endpoints without sorting everything | `heapq.nlargest`, a fixed-size min-heap |
| Merge k sorted streams | Merge event streams by timestamp | Compaction merges sorted SSTables; multi-partition ordered reads | `heapq.merge` |
| Sliding window and two pointers | Rate over the last N seconds; longest window under a limit | Windowed detection rules; rate limiters | `deque`, indices |
| Binary search on sorted history | Time-based key-value store; first event at or after `t` | Lookups in time-ordered SSTables and indexes | `bisect.bisect_right` |
| BFS / DFS / union-find | Number of islands; connected hosts; cycle detection | Graph traversal is the product: Threat Graph is an adjacency-list store `[Official]` | recursion with an explicit stack for big grids; a union-find class |
| Dijkstra and topological sort | Network delay time; task order with prerequisites | Dependency ordering in pipelines; rollout ordering across rings | `heapq`, Kahn's algorithm |
| Interval merge and sweep line | Merge outage windows; minimum concurrent workers | Maintenance windows, host-group update schedules | sort then sweep |
| LRU / LFU cache | Implement an in-memory cache "like Redis" `[Reported]` | Redis in front of hash lookups and sessions (posting names Redis) | `OrderedDict`, or dict plus doubly linked list; TTL with a heap |
| Token bucket / sliding-window rate limiting | Per-tenant `allow(t)` | Per-engine and per-tenant limits; API gateway rate limiting (posting) | integer math with timestamps; Redis `INCR` + `EXPIRE` in prod |
| Consistent hashing | "How would you shard?" `[Reported]` | Kafka partitions by key; Cassandra ring; their sharded clusters `[Official]` | a sorted ring of hashed node points, `bisect` to find the owner |
| Content hashing and streaming hashes | Dedupe uploads by SHA-256 without reading a 2 GB file into memory | File analysis, dedupe across tenants | `hashlib.sha256()` fed in chunks |
| Bloom filters | "Have we seen this hash?" with bounded memory | LSM read path uses bloom filters to skip SSTables `[Official]` | bit array + k hashes; explain false-positive rate |
| Count-min sketch and HyperLogLog | Approximate counts and cardinality over endless streams | Cardinality of hosts or hashes per tenant without a giant set | explain the idea; sketches are rarely coded live |
| Reservoir sampling | Uniform sample from a stream of unknown length | Sampling telemetry for black-box monitors | one pass, `random.randint` |
| Tries and prefix matching | Match paths or domains by prefix; autocomplete | Rule matching on process paths, domains | dict-of-dicts |
| String algorithms | Encode/decode with length prefixes; subsequence; templating `{{k}}` `[Reported]` | Log parsing, packet and record framing | `re`, manual scanning, `str.find` |
| Dynamic programming, light | Longest common subsequence; edit distance; dice sums | Similarity scoring of strings and binaries (their ML posts) | 2-D table, memoization with `lru_cache` |
| Bit manipulation | Flags, masks, packing | Sensor event flags, permission bits | `&`, `|`, `<<`, `bin` |
| External merge sort and compaction | "Sort 100 GB with 1 GB of RAM" | LSM compaction is a merge sort `[Official]` | chunk, sort, `heapq.merge` |
| Skip lists and LSM trees | "How does a write-optimized store work?" | Memtables are skip lists; SSTables are sorted runs; TTL by compaction `[Official]` | explain; do not implement live |
| Idempotency keys and dedupe windows | Apply each event once; replay safely | Every consumer; every API (posting: idempotent endpoints) | set with TTL eviction, or a sorted structure by time |
| Producer–consumer with a bounded queue | "Now it's a stream" / "now there are many workers" `[Reported]` | The worker pool in every Go consumer `[Official]` | `queue.Queue(maxsize)`, `ThreadPoolExecutor`, `asyncio.Queue` |

**Python toolkit to have at your fingertips.** `heapq` (`heappush`, `heappop`, `nlargest`, `merge`), `bisect`, `collections` (`deque`, `Counter`, `defaultdict`, `OrderedDict`), `itertools` (`groupby`, `islice`, `chain`), `functools.lru_cache`, generators for streaming input (`for line in f`), `hashlib`, `threading` (`Lock`, `Event`, `Semaphore`), `queue.Queue`, `concurrent.futures`, `asyncio` (`Queue`, `gather`, `wait_for`, `Semaphore`), `dataclasses`, `typing`. Say the complexity as you go and name the memory bound when the input is a stream.

**The streaming extension, which they add to almost anything** `[Reported]`. Whatever you solved on a list, be ready to answer: what if it never ends, what if it does not fit in memory, what if it arrives out of order, what if two workers process it. The answers are always some combination of: fixed-size window, sketch or heap instead of full sort, watermark for lateness, idempotent apply, and a bounded queue.

**Job-side extras worth an hour each.** Kafka partition assignment and rebalancing; how a consumer group commits offsets; SSTable and compaction mechanics; how a bloom filter sizes itself; consistent hashing with virtual nodes; token bucket versus leaky bucket; exponential backoff with jitter; circuit breakers; leases and fencing tokens (why a lease holder must present a fencing token when writing).

## Part 3 · System design and architecture study, for the review and for the job

### The building blocks, each with the sentence you say in the room

| Block | The sentence | CrowdStrike context |
| --- | --- | --- |
| API gateway and rate limiting | "Authenticate, rate-limit per tenant, route; keep it stateless so it scales flat." | Posting: JWT/OAuth, versioning, rate limiting, OpenAPI |
| Queue (Kafka) | "Partition by key for order, consumer groups for parallelism, offsets committed after the batch, at-least-once with idempotent consumers." | 1T events/day, sharded clusters, shard states, 1/(N−1) headroom `[Official]` |
| Stream processing | "Windows over event time, a watermark for lateness, idempotent sinks; exactly-once is a property of the sink, not the transport." | Detection pipelines; DSL-generated Go handlers `[Official]` |
| Cache (Redis) | "Cache-aside with TTL for reads; per-key locks or request coalescing against stampedes; know what is stale-tolerant." | Posting: Redis for caching and sessions |
| OLTP store (Postgres) | "Transactions, indexes chosen from the query, isolation level named on purpose, connection pooling." | Posting: Postgres with query optimization |
| Wide-column / LSM store (Cassandra) | "Write-optimized, partition key chosen for the read path, tombstones and compaction as a cost, TTL by time-window compaction." | Threat Graph, 40 PB, 6/7 writes, TWCS contributed by CrowdStrike `[Official]` |
| Blob storage | "Content-addressed keys collapse duplicates; pre-signed URLs keep bytes off the API tier; multipart for large files." | The VirusTotal case `[Reported]` |
| Search index (Elasticsearch/OpenSearch) | "Inverted index for full-text and log search; tune shards and retention; it is not the source of truth." | Posting; LogScale/Next-Gen SIEM |
| Sharding and consistent hashing | "Uniform key, virtual nodes, only 1/N moves on resize; never shard by tenant alone." | Reported design question; Kafka and Cassandra rings |
| Replication and consistency | "Quorum reads and writes where it matters; accept eventual consistency where a stale read is cheap; say which is which." | Multi-region in the posting |
| Idempotency and dedupe | "Idempotency key per request; dedupe window keyed by (source, sequence); replay is safe by construction." | Reported design questions on idempotent endpoints and consumers |
| Backpressure, shedding, breakers | "Bounded queues, consumer-lag-based autoscaling, throttle on dependency failure, circuit-break, retry with jitter." | KEDA on lag; throttling weighted by failures `[Official]` |
| Multi-tenant isolation | "Tenant in every key and query, per-tenant quotas and queue lanes, per-tenant encryption keys for stored bytes." | Security-flavored design rounds `[Aggregator]` |
| Observability | "Golden signals per service, consumer lag as the SLI, black-box probes for end-to-end latency, traces for cross-service root cause." | Burrow, Prometheus, Grafana, black-box monitors `[Official]`; posting: Jaeger/Zipkin, ELK |
| Deployment safety | "Canary, then rings gated by golden signals, automatic halt, customer pinning, rollback measured in minutes." | Post-2024 Content Distribution System `[Official]`; canary vs blue-green `[Aggregator]` |
| Security basics | "Short-lived identities, mTLS between services, KMS-managed keys with envelope encryption, least privilege, immutable audit log." | Cloud-architecture round topics |
| Infra | "Containers on Kubernetes with HPA/KEDA, Terraform for everything, CI/CD with staged promotion, multi-region active/active or warm standby." | Posting: Docker/Kubernetes, Terraform/CloudFormation, multi-region |
| Cost | "Name the expensive line: engine minutes, egress, hot storage, over-provisioned consumers; right-size to real traffic." | Reported interviewer advice: explain cost and trade-offs |

### The method for a ninety-minute review, in five moves

1. **Numbers first.** Events per second, bytes per event, retention, tenants, latency budget, peak versus average. Write them where everyone can see.
2. **One main path, six to eight boxes.** Agent or client → gateway → queue → processor → hot store → cold store → query/notify. Walk one event through it.
3. **Storage by category, then by product.** Say "append-only write-heavy store" before "Cassandra." Interviewers there have said so `[Reported]`.
4. **Failure modes before they ask.** Queue backlog, hot key, dependency down, poison message, region loss, duplicate delivery, lost completion event. For each: detection, containment, recovery.
5. **Trade-offs you dislike.** Name two. It is the most senior thing you can do in that room.

### Design cases to work, in order

1. The file-scanning platform (worked on the main page). 2. Real-time event message system: producers, topics, consumers, ordering per key, at-least-once with dedupe, replay from an offset, tenant isolation, and the security/availability trade-offs `[Reported]`. 3. Telemetry ingestion from millions of endpoints with local buffering and offline agents. 4. Content or rule rollout to every endpoint with rings, canary, pinning, and rollback. 5. Endpoint management control plane: host inventory, policy, command fan-out with acknowledgement, stale hosts. 6. Searchable event store with hot and cold tiers. 7. Rate limiter and distributed queue as building blocks. 8. Design Redis, briefly: data structures, eviction, persistence, replication, why single-threaded is fast `[Reported]`.

### Reading list, prioritized for this loop and this job

**Read first, in this order.**
- *Designing Data-Intensive Applications* (Kleppmann): chapter 3 (storage engines: LSM trees, SSTables, compaction, B-trees, bloom filters), chapter 6 (partitioning, consistent hashing, hot spots), chapter 11 (stream processing, Kafka semantics, exactly-once, watermarks), then chapters 5 (replication) and 7 (transactions).
- CrowdStrike engineering blog `[Official]`: [Sharding Kafka](https://www.crowdstrike.com/en-us/blog/how-we-improved-scale-and-reliability-by-sharding-kafka/), [Fault-tolerant Kafka consumers in Go](https://www.crowdstrike.com/en-us/blog/improving-fault-tolerance-in-apache-kafka-best-practices/), [Monitoring streaming infrastructure](https://www.crowdstrike.com/en-us/blog/how-to-monitor-streaming-data-infrastructure-at-scale/), [LSM trees and Threat Graph](https://www.crowdstrike.com/en-us/blog/how-log-structured-merge-trees-enable-crowdstrike-to-process-trillions-of-events-per-day/), [Graph database best practices](https://www.crowdstrike.com/en-us/blog/3-best-practices-for-building-high-performance-graph-database/), [Resilient by design](https://www.crowdstrike.com/en-us/blog/reflecting-on-building-resilience-by-design/), [July 2024 preliminary post-incident report](https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/). Two hours total; take one page of notes per post in your own words.
- *System Design Interview* vol. 1 (Xu): rate limiter, consistent hashing, key-value store, unique ID generator, notification system. Vol. 2: distributed message queue, metrics monitoring and alerting, real-time gaming leaderboard (for top-k on streams).
- Hello Interview's free system design guides (the January 2026 offer report credits them `[Reported]`): the core concepts pages and the "design a rate limiter," "design a distributed message queue," and "design an alerting system" walkthroughs.

**Then, for depth.**
- *Kafka: The Definitive Guide*, the consumer and reliability chapters (consumer groups, commits, rebalancing, at-least-once patterns).
- Apache Cassandra documentation on data modeling and TimeWindowCompactionStrategy (CrowdStrike contributed it `[Official]`).
- *Site Reliability Engineering* (Google), chapters on monitoring distributed systems, release engineering, and handling overload.
- *Concurrency in Go* (Cox-Buday) or, shorter, "Go by Example" and "A Tour of Go" concurrency sections; *Effective Go* once.
- Martin Fowler's "Patterns of Distributed Systems": lease, fencing token, idempotent receiver, write-ahead log, segmented log, consistent core.

**Skip for this loop.** Deep Kubernetes internals, Terraform module design, OS internals (those belong to sensor teams), ML system design.

### The first ninety days on a cloud platform team, if you want to prepare for the job and not only the loop

- Learn the team's Kafka conventions: topic naming, partition keys, consumer group per service, how offsets and redrives are handled, what "malformed" means and how it is counted `[Official]`.
- Read the on-call runbooks and the last three incident reviews before you are on the rotation; know the golden-signal dashboards and what consumer lag looks like on a bad day.
- Find the deploy pipeline's stages and gates; know how a rollback is done and how long it takes.
- Trace one request end to end with the tracing tool the posting names; know where spans are dropped.
- Write down the tenant-isolation rules for the stores you touch before you write a query.

### A four-week study path that fits around interviews

| Week | Coding | Go | Design | Reading |
| --- | --- | --- | --- | --- |
| 1 | One drill a day from the main page; write each streaming extension | Part 1 in one sitting; the two-hour practice | The file-scanning case, twice | DDIA ch. 3 and 6; two CrowdStrike posts |
| 2 | Worker pool and rate limiter twice each, Python and pseudocode | Rewrite the worker pool from memory; read the Kafka consumer post's code paths | Event message system take-home, then a mock review | DDIA ch. 11; Xu rate limiter and message queue |
| 3 | Islands, time-based KV, cache with TTL, merge k streams | `go test -race` on a broken counter; table-driven test | Rollout with rings; endpoint control plane | Resilient-by-design and the PIR; SRE monitoring chapter |
| 4 | Mixed timed set; code review of a 100-line PR out loud | Read one real Go service on GitHub for thirty minutes | Redis in fifteen minutes; failure modes drill | Kafka consumer chapter; Fowler patterns |

**Evidence.** Reported items and official posts are cited on the [main page's ledger](crowdstrike.md#every-problem-found-labeled-the-ledger). The Go and algorithm material is standard language and computer-science reference content, restated for this loop; it is not a claim about what any interviewer will ask.
