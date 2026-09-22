import unittest
from reference import ChangeSource, Conflict, FencedResult, HistoryExpired, IntentStore, Provider, Replica, Row, RoutingRegistry, apply, rollback_ready


class RecoveryTests(unittest.TestCase):
    def test_external_effect_before_or_after_marker_has_a_crash_gap(self):
        effects, markers = [], set()
        effects.append("email")  # Send succeeds; crash before marker.
        if "a" not in markers:
            effects.append("email")  # Naive replay repeats the external effect.
            markers.add("a")
        self.assertEqual(len(effects), 2)
        effects, markers = [], {"a"}  # Marker commits; crash before send.
        if "a" not in markers:
            effects.append("email")
        self.assertEqual(len(effects), 0)

    def test_paused_owner_can_overwrite_without_fence_but_is_rejected_with_it(self):
        naive = {"title": "new"}
        naive["title"] = "old"  # A resumes after B.
        self.assertEqual(naive["title"], "old")
        store = FencedResult()
        a = store.claim(0)
        b = store.claim(6)
        store.complete(b, 7, "new")
        with self.assertRaises(Conflict):
            store.complete(a, 8, "old")
        self.assertEqual(store.result, "new")
        with self.assertRaises(Conflict):
            store.complete(b, 11, "expired")

    def test_atomic_intent_outbox_and_changed_payload_quarantine(self):
        store = IntentStore()
        self.addCleanup(store.close)
        with self.assertRaises(RuntimeError):
            store.accept("a", {"title": "hello"}, crash_before_commit=True)
        self.assertEqual(store.db.execute("SELECT count(*) FROM intent").fetchone()[0], 0)
        self.assertEqual(store.db.execute("SELECT count(*) FROM outbox").fetchone()[0], 0)
        self.assertEqual(store.accept("a", {"title": "hello"}), "accepted")
        self.assertEqual(store.accept("a", {"title": "hello"}), "duplicate")
        with self.assertRaises(Conflict):
            store.accept("a", {"title": "different"})
        self.assertEqual(store.db.execute("SELECT count(*) FROM outbox").fetchone()[0], 1)

    def test_external_success_with_lost_response_and_reconciliation(self):
        store, provider = IntentStore(), Provider()
        self.addCleanup(store.close)
        store.accept("a", {"email": "hello"})
        provider.lose_next_response = True
        self.assertEqual(store.dispatch("a", provider), "uncertain")
        self.assertEqual(provider.effects, 1)
        provider.available = False
        self.assertEqual(store.dispatch("a", provider), "uncertain")
        provider.available = True
        self.assertEqual(store.dispatch("a", provider), "done")
        self.assertEqual(provider.effects, 1)
        with self.assertRaises(Conflict):
            provider.send("a", {"email": "changed"})

    def test_external_crash_after_receipt_before_local_commit(self):
        store, provider = IntentStore(), Provider()
        self.addCleanup(store.close)
        store.accept("a", [1, 2])
        with self.assertRaises(RuntimeError):
            store.dispatch("a", provider, crash_after_send=True)
        self.assertEqual(store.dispatch("a", provider), "done")
        self.assertEqual(provider.effects, 1)

    def test_expired_provider_dedup_window_permits_another_effect(self):
        provider = Provider()
        provider.send("a", [1])
        provider.receipts.clear()  # Explicit counterexample: retention contract expired.
        provider.send("a", [1])
        self.assertEqual(provider.effects, 2)


class MigrationTests(unittest.TestCase):
    def test_partial_write_stale_backfill_delete_and_repair(self):
        source, target = ChangeSource(), Replica()
        source.write("a", "v1")
        source.write("deleted", "old")
        baseline, position = source.snapshot()
        source.write("a", "v2")  # Independent target write fails here.
        source.write("deleted", deleted=True)
        self.assertEqual(set(target.differences(source)), {"a", "deleted"})
        target.checkpoint = position
        target.resume(source)  # Live mutations arrive before slow backfill.
        for key, row in baseline.items():
            apply(target.rows, key, row)
        self.assertEqual(target.rows["a"], Row(2, "v2"))
        self.assertTrue(target.rows["deleted"].deleted)
        self.assertFalse(target.differences(source))
        with self.assertRaises(Conflict):
            apply(target.rows, "a", Row(2, "different"))

    def test_crash_between_apply_and_checkpoint_replays_idempotently(self):
        source, target = ChangeSource(), Replica()
        source.write("a", "v1")
        with self.assertRaises(RuntimeError):
            target.resume(source, crash_after_apply=True)
        self.assertEqual(target.checkpoint, 0)
        target.resume(source)
        self.assertEqual(target.checkpoint, 1)
        self.assertFalse(target.differences(source))

    def test_history_expiry_demands_resnapshot_then_new_live_replay(self):
        source, target = ChangeSource(), Replica()
        source.write("a", "old")
        source.write("a", deleted=True)
        source.expire_through(2)
        with self.assertRaises(HistoryExpired):
            target.resume(source)
        target.resnapshot(source)
        source.write("b", "new")
        target.resume(source)
        self.assertFalse(target.differences(source))
        self.assertTrue(target.rows["a"].deleted)

    def test_rebalance_blocks_stale_route_and_incomplete_target(self):
        source, target, registry = ChangeSource(), Replica(), RoutingRegistry()
        source.write("tenant-a", "v1")
        with self.assertRaises(Conflict):
            registry.cutover(target, source)
        target.resnapshot(source)
        source.write("tenant-a", "v2")
        with self.assertRaises(Conflict):
            registry.cutover(target, source)
        target.resume(source)
        registry.cutover(target, source)
        with self.assertRaises(Conflict):
            registry.check_write("old", 1)
        registry.check_write("new", 2)

    def test_rollback_after_new_only_write_needs_reverse_repair(self):
        old = {"a": Row(1, "old")}
        new = dict(old)
        apply(new, "a", Row(2, "new"))
        apply(new, "b", Row(1, None, True))
        self.assertFalse(rollback_ready(old, new))
        for key, row in new.items():
            apply(old, key, row)
        self.assertTrue(rollback_ready(old, new))
        self.assertEqual(old["a"].value, "new")

    def test_dns_cached_route_and_async_region_data_loss_are_distinct(self):
        resolver = {"answer": "old", "until": 60}
        registry_answer = "new"
        self.assertEqual(resolver["answer"] if 10 < resolver["until"] else registry_answer, "old")
        existing_connection = "old"  # A new DNS answer doesn't move this socket.
        self.assertEqual(existing_connection, "old")
        primary, replica = {"a": Row(9, "acknowledged")}, {"a": Row(8, "older")}
        lost = {key for key in primary if primary[key] != replica.get(key)}
        self.assertEqual(lost, {"a"})
        remote_available = False
        sync_ack = remote_available  # Fail closed if policy requires remote commit.
        self.assertFalse(sync_ack)


if __name__ == "__main__":
    unittest.main()
