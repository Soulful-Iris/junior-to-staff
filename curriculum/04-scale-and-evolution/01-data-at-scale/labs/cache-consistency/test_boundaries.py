import asyncio
import unittest
from reference import CacheAside, Clock, LinkDelivery, OriginBudget, Unavailable, sticky_read, strict_read


class CacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_baseline_200_misses_and_fixed_one_flight(self):
        clock = Clock()
        calls = 0
        ready = asyncio.Event()
        async def load(key):
            nonlocal calls
            calls += 1
            await ready.wait()
            return 8
        baseline = [asyncio.create_task(load("hot")) for _ in range(200)]
        await asyncio.sleep(0)
        self.assertEqual(calls, 200)
        ready.set()
        await asyncio.gather(*baseline)
        calls = 0
        cache = CacheAside(clock, OriginBudget(clock))
        self.assertEqual(await asyncio.gather(*(cache.get("hot", load) for _ in range(200))), [8] * 200)
        self.assertEqual(calls, 1)
        clock.advance(6)
        await asyncio.gather(*(cache.get("hot", load) for _ in range(200)))
        self.assertEqual(calls, 2)
        self.assertFalse(cache.flights)

    async def test_ten_instances_and_many_keys(self):
        clock = Clock()
        budget = OriginBudget(clock, per_second=100, concurrent=100)
        async def load(key):
            await asyncio.sleep(0)
            return key
        caches = [CacheAside(clock, budget) for _ in range(10)]
        await asyncio.gather(*(caches[i % 10].get("hot", load) for i in range(200)))
        self.assertEqual(budget.total, 10)
        await asyncio.gather(*(caches[0].get(str(i), load) for i in range(20)))
        self.assertEqual(budget.total, 30)  # Coalescing distinct keys changes semantics.
        clock.advance(6)
        await asyncio.gather(*(caches[0].get(str(i), load) for i in range(20)))
        self.assertEqual(budget.total, 50)  # Twenty keys expire together: twenty loads.
        for i in range(20):
            caches[0].values[str(i)] = (clock.now + 5 + i / 10, str(i))
        clock.advance(5)
        await asyncio.gather(*(caches[0].get(str(i), load) for i in range(20)))
        self.assertEqual(budget.total, 51)  # Staggered expiry: one key expired so far.

    async def test_loader_exception_releases_every_waiter_and_retry(self):
        clock = Clock()
        cache = CacheAside(clock, OriginBudget(clock))
        calls = 0
        async def broken(key):
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            raise ValueError("origin failed")
        results = await asyncio.gather(*(cache.get("hot", broken) for _ in range(30)), return_exceptions=True)
        self.assertTrue(all(isinstance(value, ValueError) for value in results))
        self.assertEqual(calls, 1)
        self.assertEqual(cache.budget.active, 0)
        self.assertFalse(cache.flights)
        async def recovered(key):
            return 9
        self.assertEqual(await cache.get("hot", recovered), 9)

    async def test_waiter_and_loader_cancellation_have_different_scope(self):
        clock = Clock()
        cache = CacheAside(clock, OriginBudget(clock))
        entered, release = asyncio.Event(), asyncio.Event()
        async def load(key):
            entered.set()
            await release.wait()
            return 8
        first = asyncio.create_task(cache.get("hot", load))
        await entered.wait()
        second = asyncio.create_task(cache.get("hot", load))
        first.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await first
        release.set()
        self.assertEqual(await second, 8)
        clock.advance(6)
        entered.clear()
        release.clear()
        waiters = [asyncio.create_task(cache.get("hot", load)) for _ in range(2)]
        await entered.wait()
        cache.flights["hot"].cancel()
        results = await asyncio.gather(*waiters, return_exceptions=True)
        self.assertTrue(all(isinstance(value, asyncio.CancelledError) for value in results))
        self.assertFalse(cache.flights)
        self.assertEqual(cache.budget.active, 0)
        release.set()
        self.assertEqual(await cache.get("hot", load), 8)

    async def test_outage_caps_concurrency_and_rate_across_instances(self):
        clock = Clock()
        budget = OriginBudget(clock, per_second=100, concurrent=10)
        caches = [CacheAside(clock, budget) for _ in range(10)]
        for cache in caches:
            cache.cache_available = False
        async def load(key):
            await asyncio.sleep(0)
            return key
        results = []
        for wave in range(10):
            results += await asyncio.gather(*(caches[i % 10].get(f"{wave}:{i}", load) for i in range(100)), return_exceptions=True)
        self.assertEqual(budget.total, 100)
        self.assertEqual(budget.peak, 10)
        self.assertEqual(sum(isinstance(r, Unavailable) for r in results), 900)
        with self.assertRaises(Unavailable):
            await caches[0].get("extra", load)
        clock.advance(1)
        self.assertEqual(await caches[0].get("next-second", load), "next-second")


class ConsistencyTests(unittest.TestCase):
    def test_lag_outlives_pin_and_watermark_fallback(self):
        self.assertEqual(sticky_read(8, 7, now=6, pin_until=5), 7)
        self.assertEqual(strict_read(8, 7, minimum_version=8), 8)
        self.assertEqual(strict_read(None, 8, minimum_version=8), 8)
        with self.assertRaises(Unavailable):
            strict_read(None, 7, minimum_version=8)

    def test_warm_same_token_and_cold_revocation(self):
        delivery = LinkDelivery(Clock())
        self.assertEqual(delivery.get("A"), (200, "Ana 09:00"))
        del delivery.tokens["A"]
        self.assertEqual(delivery.get("A"), (403, None))
        delivery.cache.clear()
        self.assertEqual(delivery.get("A"), (403, None))
        self.assertEqual(delivery.origin_calls, 1)

    def test_token_tenant_isolation_and_origin_outage(self):
        delivery = LinkDelivery(Clock())
        self.assertNotEqual(delivery.get("A")[1], delivery.get("B")[1])
        delivery.origin_available = False
        self.assertEqual(delivery.get("A")[0], 200)
        del delivery.tokens["A"]
        self.assertEqual(delivery.get("A")[0], 403)
        delivery.cache.clear()
        self.assertEqual(delivery.get("B")[0], 503)
        delivery.auth_available = False
        self.assertEqual(delivery.get("B")[0], 503)

    def test_bounded_policy_expires_without_sliding_or_fail_open(self):
        clock = Clock()
        delivery = LinkDelivery(clock, policy="bounded", auth_ttl=5)
        self.assertEqual(delivery.get("A")[0], 200)
        del delivery.tokens["A"]
        clock.advance(4.999)
        self.assertEqual(delivery.get("A")[0], 200)
        clock.advance(.001)
        self.assertEqual(delivery.get("A")[0], 403)
        delivery.auth_available = False
        self.assertEqual(delivery.get("A")[0], 503)


if __name__ == "__main__":
    unittest.main()
