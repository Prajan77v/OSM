import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_engine import db_instance, DatabaseEngine
from auth_engine import auth_instance, hash_password, verify_password
import analytics_engine

class TestEnterpriseSuite(unittest.TestCase):
    def test_01_db_logging(self):
        db_instance.log_event('TEST_EVENT', 'cam0', 'P001', 'Test event detail', 'GREEN')
        events = db_instance.get_recent_events(10)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['event'], 'TEST_EVENT')

    def test_02_auth_login(self):
        user = auth_instance.login('admin', 'admin123')
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'Admin')

        token = user['token']
        self.assertTrue(auth_instance.check_permission(token, 'Viewer'))
        self.assertTrue(auth_instance.check_permission(token, 'Operator'))
        self.assertTrue(auth_instance.check_permission(token, 'Admin'))

    def test_03_analytics_heatmaps(self):
        heatmap = analytics_engine.generate_occupancy_heatmap(100, 100, [(50, 50), (20, 20)])
        self.assertEqual(heatmap.shape, (100, 100, 3))

    def test_04_distance_estimation(self):
        dist = analytics_engine.estimate_distance(height_px=200, frame_height=1080)
        self.assertGreater(dist, 0.0)

if __name__ == '__main__':
    unittest.main()