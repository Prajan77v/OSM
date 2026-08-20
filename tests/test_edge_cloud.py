"""
OMS Unit & Integration Tests — Edge Event Queue, Engine & Cloud API
"""

import os
import sys
import uuid
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge.events.schema import OMSEvent
from edge.events.queue import PersistentEventQueue
from edge.events.engine import EventEngine
from cloud.database.session import init_database, SessionLocal
from cloud.database.models import EdgeAgent, Camera, SurveillanceEvent


class TestEdgeAndCloudArchitecture(unittest.TestCase):

    def setUp(self):
        self.test_db_path = f"logs/test_queue_{uuid.uuid4().hex[:8]}.db"
        self.queue = PersistentEventQueue(self.test_db_path)
        self.engine = EventEngine(self.queue)
        init_database()

    def tearDown(self):
        # Allow Windows SQLite lock to release
        del self.queue
        del self.engine
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except Exception:
            pass

    def test_01_event_schema_and_queue(self):
        """Test event persistence in SQLite queue."""
        event = OMSEvent(
            event_type="intruder",
            camera_id="CAM_01",
            severity="high",
            confidence=0.92,
            location="Perimeter North"
        )
        self.assertTrue(self.queue.push(event))

        pending = self.queue.get_pending(limit=10)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].event_type, "intruder")
        self.assertEqual(pending[0].severity, "high")
        self.assertEqual(pending[0].confidence, 0.92)

        # Test mark synced
        self.assertTrue(self.queue.mark_synced([pending[0].event_id]))
        self.assertEqual(len(self.queue.get_pending()), 0)

    def test_02_event_engine_cooldown(self):
        """Test event deduplication and cooldown throttling."""
        evt1 = self.engine.trigger_event("person_detected", "CAM_01", "low", 0.85)
        self.assertIsNotNone(evt1)

        # Immediate second event should be throttled by cooldown
        evt2 = self.engine.trigger_event("person_detected", "CAM_01", "low", 0.85)
        self.assertIsNone(evt2)

        # Forced event bypasses cooldown
        evt3 = self.engine.trigger_event("person_detected", "CAM_01", "low", 0.85, force=True)
        self.assertIsNotNone(evt3)

    def test_03_cloud_db_persistence(self):
        """Test cloud database persistence."""
        with SessionLocal() as db:
            agent = EdgeAgent(id="test-edge-node", name="Test Node", status="ONLINE", gpu_name="CPU Mode")
            db.merge(agent)
            db.commit()

            retrieved = db.query(EdgeAgent).filter(EdgeAgent.id == "test-edge-node").first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.status, "ONLINE")


if __name__ == "__main__":
    unittest.main()
