import unittest
from datetime import datetime, timezone, timedelta
from sigsci_helper import get_until_time  # Replace with the actual module import

class TestGetUntilTime(unittest.TestCase):

    def test_reset(self):
        now = datetime.now(timezone.utc)
        from_time = now - timedelta(hours=12)
        delta = 3600  # 1 hour in seconds
        
        from_time_timestamp = int(from_time.timestamp())
        new_until_time, new_from_time = get_until_time(now, from_time_timestamp, delta, reset=True)
        
        self.assertLessEqual(new_from_time, int((now - timedelta(hours=24)).timestamp()))
        self.assertEqual(new_until_time, int((now - timedelta(seconds=delta)).timestamp()))
        print(f"reset: from_time: {from_time}, until_time: {new_until_time}")

    # def test_grdelta(self):
    #     now = datetime.now(timezone.utc)
    #     from_time = now - timedelta(hours=3)
    #     delta = 7200  # 2 hours in seconds
        
    #     from_time_timestamp = int(from_time.timestamp())
    #     new_until_time, new_from_time = get_until_time(now, from_time_timestamp, delta, grdelta=True)
        
    #     self.assertGreaterEqual(new_from_time, from_time_timestamp - delta)
    #     self.assertGreaterEqual(new_until_time, from_time_timestamp + delta)
    #     print(f"grdelta: from_time: {from_time}, until_time: {new_until_time}")

    # def test_regular_delta(self):
    #     now = datetime.now(timezone.utc)
    #     from_time = now - timedelta(hours=1)
    #     delta = 1800  # 30 minutes in seconds
        
    #     from_time_timestamp = int(from_time.timestamp())
    #     new_until_time, new_from_time = get_until_time(now, from_time_timestamp, delta)
        
    #     self.assertEqual(new_from_time, from_time_timestamp)
    #     self.assertEqual(new_until_time, from_time_timestamp + delta)
    #     print(f"regular_delta: from_time: {from_time}, until_time: {new_until_time}")

if __name__ == '__main__':
    unittest.main()
