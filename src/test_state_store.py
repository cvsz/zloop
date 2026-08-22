import tempfile
import unittest

try:
    from src.state_store import SQLiteStateStore
except ModuleNotFoundError:
    from state_store import SQLiteStateStore


class SQLiteStateStoreTests(unittest.TestCase):
    def test_checkpoint_round_trip_and_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStateStore(f"{tmp}/state.db")
            first = {"loop_id": "loop-1", "state": "PLAN", "iteration": 1}
            store.save_record("loop-1", first)
            self.assertEqual(store.load_record("loop-1"), first)

            second = {"loop_id": "loop-1", "state": "EXECUTE", "iteration": 2}
            store.save_record("loop-1", second)
            self.assertEqual(store.load_record("loop-1"), second)

    def test_missing_checkpoint_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStateStore(f"{tmp}/state.db")
            self.assertIsNone(store.load_record("missing"))

    def test_idempotency_succeeded_is_sticky(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStateStore(f"{tmp}/state.db")
            store.put_idempotency("loop:step:target", "IN_PROGRESS")
            store.put_idempotency("loop:step:target", "SUCCEEDED", {"sha": "abc"})
            record = store.get_idempotency("loop:step:target")
            self.assertEqual(record["status"], "SUCCEEDED")
            self.assertEqual(record["result"], {"sha": "abc"})
            with self.assertRaises(ValueError):
                store.put_idempotency("loop:step:target", "IN_PROGRESS")

    def test_invalid_idempotency_status_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStateStore(f"{tmp}/state.db")
            with self.assertRaises(ValueError):
                store.put_idempotency("key", "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
