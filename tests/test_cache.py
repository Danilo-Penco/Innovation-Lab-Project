import unittest

from Projeto.cache import MAX_TTL_SECONDS, MemoryTTLCache


class MemoryTTLCacheTests(unittest.TestCase):
    def test_entries_expire_and_clear_in_process(self) -> None:
        now = [10.0]
        cache: MemoryTTLCache[str, str] = MemoryTTLCache(
            max_entries=2,
            ttl_seconds=5,
            clock=lambda: now[0],
        )
        cache.set("key", "value")
        self.assertEqual(cache.get("key"), "value")

        now[0] = 15.0
        self.assertIsNone(cache.get("key"))
        self.assertEqual(len(cache), 0)

        cache.set("key", "value")
        cache.clear()
        self.assertIsNone(cache.get("key"))

    def test_capacity_is_bounded_and_reads_refresh_lru_order(self) -> None:
        cache: MemoryTTLCache[str, str] = MemoryTTLCache(max_entries=2)
        cache.set("first", "1")
        cache.set("second", "2")
        self.assertEqual(cache.get("first"), "1")
        cache.set("third", "3")

        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get("second"))
        self.assertEqual(cache.get("first"), "1")
        self.assertEqual(cache.get("third"), "3")

    def test_ttl_cannot_exceed_five_minutes(self) -> None:
        with self.assertRaises(ValueError):
            MemoryTTLCache[str, str](
                max_entries=1,
                ttl_seconds=MAX_TTL_SECONDS + 1,
            )

    def test_ttl_can_be_explicitly_extended_for_exchange_rates(self) -> None:
        now = [0.0]
        cache: MemoryTTLCache[str, str] = MemoryTTLCache(
            max_entries=1,
            ttl_seconds=3600,
            max_ttl_seconds=3600,
            clock=lambda: now[0],
        )
        cache.set("rate", "5.0")

        now[0] = 3599
        self.assertEqual(cache.get("rate"), "5.0")
        now[0] = 3600
        self.assertIsNone(cache.get("rate"))


if __name__ == "__main__":
    unittest.main()
