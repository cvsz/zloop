import tempfile
import time
import unittest

from src.job_queue import SQLiteJobQueue


class SQLiteJobQueueTests(unittest.TestCase):
    def test_enqueue_lease_ack(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = SQLiteJobQueue(f"{tmp}/queue.db")
            jid = q.enqueue({"task": "x"}, job_id="job-1")
            job = q.lease("worker-1", lease_seconds=30)
            self.assertEqual(job.job_id, jid)
            self.assertEqual(job.status, "LEASED")
            self.assertEqual(job.attempts, 1)
            q.ack(jid, "worker-1")
            self.assertEqual(q.get(jid).status, "SUCCEEDED")

    def test_expired_lease_is_reclaimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = SQLiteJobQueue(f"{tmp}/queue.db")
            jid = q.enqueue({"task": "x"})
            q.lease("worker-1", lease_seconds=0)
            reclaimed = q.lease("worker-2", lease_seconds=30)
            self.assertEqual(reclaimed.job_id, jid)
            self.assertEqual(reclaimed.lease_owner, "worker-2")
            self.assertEqual(reclaimed.attempts, 2)

    def test_retry_requires_lease_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = SQLiteJobQueue(f"{tmp}/queue.db")
            jid = q.enqueue({"task": "x"})
            q.lease("worker-1")
            with self.assertRaises(RuntimeError): q.retry(jid, "worker-2")
            q.retry(jid, "worker-1")
            self.assertEqual(q.get(jid).status, "READY")

    def test_cancel_and_deadline_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = SQLiteJobQueue(f"{tmp}/queue.db")
            cancelled = q.enqueue({"task": "x"})
            q.cancel(cancelled)
            self.assertEqual(q.get(cancelled).status, "CANCELLED")
            expired = q.enqueue({"task": "y"}, deadline=time.time() - 1)
            self.assertIsNone(q.lease("worker"))
            self.assertEqual(q.get(expired).status, "EXPIRED")

    def test_succeeded_job_cannot_be_cancelled(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = SQLiteJobQueue(f"{tmp}/queue.db")
            jid = q.enqueue({"task": "x"})
            q.lease("worker")
            q.ack(jid, "worker")
            with self.assertRaises(RuntimeError): q.cancel(jid)


if __name__ == "__main__": unittest.main()
